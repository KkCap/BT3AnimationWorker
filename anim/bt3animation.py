"""
This module provides classes that represent BT3 animations
"""


import sys
import copy
import struct
from abc import ABC, abstractmethod
from myutils.pack_and_unpack import *


class UnconcatenableAnimationsError(Exception):
    pass


class Keyframe(ABC):
    """
    Just an abstract class for keyframes
    """

    @abstractmethod
    def get_rot_struct(self):
        pass

    @abstractmethod
    def get_timestamp(self):
        pass

    @abstractmethod
    def get_translation(self):
        pass

    @abstractmethod
    def set_timestamp(self, new_timestamp):
        pass


class KeyframeType1(Keyframe):
    """
    Real implementation for keyframes type 1
    """

    def __init__(self, rot_struct, timestamp):
        self.rot_struct = rot_struct
        self.timestamp = timestamp

    def get_rot_struct(self):
        return self.rot_struct

    def get_timestamp(self):
        return self.timestamp

    def get_translation(self):
        print("KeyframeType1 -> get_translation(...) -> Error: KeyframeType1 instances have no translations")
        return 0, 0, 0

    def set_timestamp(self, new_timestamp):
        self.timestamp = new_timestamp


class KeyframeType0(Keyframe):
    """
    Real implementation for keyframes type 1
    """

    def __init__(self, translation, rot_struct, timestamp):
        self.translation = translation
        self.rot_struct = rot_struct
        self.timestamp = timestamp

    def get_rot_struct(self):
        return self.rot_struct

    def get_timestamp(self):
        return self.timestamp

    def get_translation(self):
        return self.translation

    def set_timestamp(self, new_timestamp):
        self.timestamp = new_timestamp


class BoneAnimation:
    """
    An instance of this class represent an animation for a single bone (eg. the animation of Goku's tail during the
    stance in Character Reference)
    """

    def __init__(self, dump: bytes):
        # Check type. It can be 0 or 1.
        # 0 is for keyframe with rotations and positions, 1 is for keyframe with only rotations
        self._type = up16(dump[0:2])
        if self._type != 0 and self._type != 1:
            print("BoneAnimation -> __init__(...) -> Error: invalid dump (1)")
            sys.exit(1)

        # Keyframe count. It has to be equal or less than the number of the frame of the animation.
        self._keyframe_count = up16(dump[2:4])

        # Build the keyframe list
        self._keyframe_list = []
        if self._type == 1:
            for i in range(self._keyframe_count):
                cursor = 4 + i * 8
                timestamp_cursor = 4 + 8 * self._keyframe_count + i * 2
                self._keyframe_list.append(KeyframeType1(
                    rot_struct=dump[cursor:cursor+8],
                    timestamp=up16(dump[timestamp_cursor:timestamp_cursor+2])
                ))
        elif self._type == 0:
            for i in range(self._keyframe_count):
                cursor = 4 + i * 24
                self._keyframe_list.append(KeyframeType0(
                    translation=struct.unpack("fff", dump[cursor:cursor + 12]),
                    timestamp=up32(dump[cursor+12:cursor+12+4]),
                    rot_struct=dump[cursor+16:cursor+16+8]
                ))

    def __sum_timestamp_offset(self, offset: int):
        """
        Each timestamp is incremented by offset
        :param offset: Timestamp offset
        """
        for keyframe in self._keyframe_list:
            keyframe.set_timestamp(keyframe.get_timestamp() + offset)

    def scale_timestamps_according_to_frame_count(self, old_frame_count, new_frame_count):
        """
        Change the timestamps according to a change of frame count (from old_frame_count to new_frame_count.
        The animation is speed-uped or slow-downed.
        :param old_frame_count: Old frame count (needed to perform computations)
        :param new_frame_count: New frame count
        """
        if old_frame_count == new_frame_count:
            return

        for keyframe in self._keyframe_list:
            keyframe.set_timestamp(round(keyframe.get_timestamp() / old_frame_count * new_frame_count))

    def get_type(self) -> int:
        return self._type

    def concat(self, old_frame_count: int, source_bone_animation: "BoneAnimation"):
        """
        Concat self with source_animation.
        The final frame count is the sum of the 2 frame counts plus 1 (a frame is used to implement the animation from
        the last keyframe of self to the first of source_animation.
        :param old_frame_count: Old frame count
        :param source_bone_animation: The animation to append at the "end" of self
        """
        assert self._type == source_bone_animation._type
        source_bone_animation = copy.deepcopy(source_bone_animation)
        source_bone_animation.__sum_timestamp_offset(old_frame_count + 1)
        self._keyframe_list += source_bone_animation._keyframe_list
        self._keyframe_count = len(self._keyframe_list)

    def dump(self) -> bytes:
        """
        Compute and return the BT3's binary form of this Animation as bytes
        """

        if self._type != 0 and self._type != 1:
            print("BoneAnimation -> dump(...) -> Error: invalid self._type")
            sys.exit(1)

        dump = p16(self._type) + p16(self._keyframe_count)
        if self._type == 1:
            timestamp_dump = b""
            for keyframe in self._keyframe_list:
                dump += keyframe.get_rot_struct()
                timestamp_dump += p16(keyframe.get_timestamp())
            if len(timestamp_dump) % 4 != 0:
                timestamp_dump += p16(0)
            dump += timestamp_dump
        else:
            for keyframe in self._keyframe_list:
                dump += p_float(keyframe.get_translation()[0])
                dump += p_float(keyframe.get_translation()[1])
                dump += p_float(keyframe.get_translation()[2])
                dump += p32(keyframe.get_timestamp())
                dump += keyframe.get_rot_struct()

        return dump


class Animation:
    """
    An instance of this class represent an animation (eg. the character stance in Character Reference)
    """

    BONE_COUNT = 56

    def __init__(self, dump: bytes):
        """
        Constructor
        :param dump: Animation file dump (bytes)
        """
        if len(dump) < 110:
            print("Animation -> __init__(...) -> Error: invalid dump (1)")
            sys.exit(1)

        # "Magic" and frame count
        self._magic = up16(dump[0:2])
        self._frame_count = up16(dump[2:4])

        # Divisions
        first_division_start_offset = None
        self._bone_animations = []
        for i in range(Animation.BONE_COUNT):
            division_start_offset = up16(dump[4 + i * 2:6 + i * 2]) * 4
            if division_start_offset == 0:
                self._bone_animations.append(None)
                continue
            self._bone_animations.append(BoneAnimation(dump[division_start_offset:]))
            if first_division_start_offset is None:
                first_division_start_offset = division_start_offset

        if first_division_start_offset is None:
            print("Animation -> __init__(...) -> Error: invalid dump (2)")
            sys.exit(1)

        # Other header info
        self._header_rem = dump[4 + Animation.BONE_COUNT * 2:first_division_start_offset]

    def get_magic(self) -> int:
        return self._magic

    def get_frame_count(self) -> int:
        """
        :return: the number of frames
        """
        return self._frame_count

    def get_animated_bone_count(self) -> int:
        """
        Compute and return the number of animated bones
        """
        ret = 0
        for keyframe in self._bone_animations:
            if keyframe is not None:
                ret += 1
        return ret

    def scale_frame_count(self, new_frame_count):
        """
        Change the frame count to new_frame_count. The animation is speed-uped or slow-downed.
        :param new_frame_count: New frame count
        """
        if self._frame_count == new_frame_count:
            return

        for bone_animation in self._bone_animations:
            if bone_animation is None:
                continue
            bone_animation.scale_timestamps_according_to_frame_count(self._frame_count, new_frame_count)

        self._frame_count = new_frame_count

    def import_bone_animations(self, source_animation: "Animation", bone_list):
        """
        Import some bone animations from source_animation. source_animation has to have the same frame count of self.
        :param source_animation: The source Animation
        :param bone_list: List of bones (IDs) to import
        """
        if self._frame_count != source_animation._frame_count:
            print("Animation -> import_bone_animations(...) -> Error: source_animation has wrong number of frames")
            return

        for bone_id in bone_list:
            if type(bone_id) != int or bone_id < 0 or bone_id >= Animation.BONE_COUNT:
                print(f"Animation -> import_bone_animations(...) -> Error: invalid bone_id ({bone_id}). Skipping.")
                continue
            self._bone_animations[bone_id] = source_animation._bone_animations[bone_id]

    def concat(self, source_animation: "Animation") -> list:
        """
        Concat self with source_animation.
        The final frame count is the sum of the 2 frame counts plus 1 (a frame is used to implement the animation from
        the last keyframe of self to the first of source_animation.
        :param source_animation: The animation to append at the "end" of self
        :return: Dropped bone animations (list of bone IDs)
        """
        for bone_id in range(self.BONE_COUNT):
            if self._bone_animations[bone_id] is not None and \
               source_animation._bone_animations[bone_id] is not None and \
               (self._bone_animations[bone_id].get_type() != source_animation._bone_animations[bone_id].get_type()):
                raise UnconcatenableAnimationsError(
                    f"Animation -> concat(...) -> Error: bone animation {bone_id} has wrong type"
                )

        dropped = []

        for bone_id in range(self.BONE_COUNT):
            if self._bone_animations[bone_id] is None and source_animation._bone_animations[bone_id] is not None or \
               self._bone_animations[bone_id] is not None and source_animation._bone_animations[bone_id] is None:
                self._bone_animations[bone_id] = None
                dropped.append(bone_id)
                continue
            if self._bone_animations[bone_id] is None and source_animation._bone_animations[bone_id] is None:
                self._bone_animations[bone_id] = None
                continue
            self._bone_animations[bone_id].concat(
                old_frame_count=self._frame_count, source_bone_animation=source_animation._bone_animations[bone_id]
            )

        self._frame_count += 1 + source_animation._frame_count

        return dropped

    def dump(self) -> bytes:
        """
        Compute and return the BT3's binary form of this Animation as bytes
        """
        # Header dump
        header_dump = p16(self._magic) + p16(self._frame_count)
        header_size = 4 + Animation.BONE_COUNT * 2 + len(self._header_rem)

        # Body dump
        body_dump = b""
        for i in range(Animation.BONE_COUNT):
            if self._bone_animations[i] is None:
                header_dump += p16(0)
                continue
            header_dump += p16((header_size + len(body_dump)) // 4)
            body_dump += self._bone_animations[i].dump()

        # Complete header dump
        header_dump += self._header_rem

        # Check len(header_dump)
        assert len(header_dump) == header_size

        # Padding and returning header_dump and body_dump as a single bytes
        dump = header_dump + body_dump
        while len(dump) % 16 != 0:
            dump += b"\x00"
        return dump
