"""
BT3 Animation Worker main script
"""


import sys
from anim.bt3animation import Animation, UnconcatenableAnimationsError


LOGO = """
=============================
= BT3 Animation Worker v0.1 =
=                 by KkTeam =
=============================
"""

CMDS = (
    {"key": "L", "info": "Load an animation", "name": "load"},
    {"key": "I", "info": "Print information about the current loaded animation", "name": "print_info"},
    {"key": "1", "info": "Change animation speed", "name": "change_speed"},
    {"key": "2", "info": "Join current animation with another (one after the other)", "name": "concat"},
    {"key": "3", "info": "Mix current animation with another (import single bone animations)", "name": "mix"},
    {"key": "S", "info": "Save current animation", "name": "save"},
    {"key": "Q", "info": "Quit", "name": "quit"}
)

animation: Animation = None
animation_file_path: str = None


def __ask_user_command():
    """
    Print the possible commands on screen and ask the user to choose one of them
    """
    for cmd in CMDS:
        print(f"[{cmd['key']}] {cmd['info']}")

    while True:
        cmd_key = input("> ").upper()
        for cmd in CMDS:
            if cmd["key"] == cmd_key:
                return cmd
        print("Unrecognized command")


def __load_animation(file_path: str):
    """
    Load an animation from disk
    :param file_path: Animation file path
    """
    global animation, animation_file_path
    try:
        with open(file_path, "rb") as file:
            dump = file.read()
    except FileNotFoundError:
        print("File not found. Abort operation.")
        return
    if dump is None or len(dump) <= 0:
        print("Error opening animation. Wrong file path?")
        return
    animation_file_path = file_path
    animation = Animation(dump)


def __ask_and_load_animation():
    """
    Ask for a file path and load the animation from disk
    """
    tmp_animation_file_path = input("File path: ")
    tmp_animation_file_path = tmp_animation_file_path.replace("\"", "")
    __load_animation(tmp_animation_file_path)


def __print_animation_info():
    """
    Print animation info
    """
    if animation is None:
        print("No animation loaded")
        return
    print("Current loaded animation:")
    print(f"  File path: {animation_file_path}")
    print(f"  Magic number: {animation.get_magic()}")
    print(f"  Frame count: {animation.get_frame_count()}")
    print(f"  Animated bones: {animation.get_animated_bone_count()}")
    print(f"  Size: {len(animation.dump())}")


def __save_animation():
    """
    Save the animation on disk.
    The file path derives from the original (just add "_save" before ".unk").
    Does not change animation_file_path.
    """
    if animation is None or animation_file_path is None:
        print("No animation loaded")
        return
    out_file_path = animation_file_path
    if out_file_path.endswith(".unk"):
        out_file_path = out_file_path[:-4] + "_save.unk"
    else:
        out_file_path = out_file_path + "_save.unk"
    print(f"Saving on {out_file_path} ...")
    with open(out_file_path, "wb") as file:
        file.write(animation.dump())
    print("Done! :D")


def __change_animation_speed():
    """
    Ask the user for the new frame count and scale the animation to that frame count
    """
    if animation is None:
        print("No animation loaded")
        return

    print(
        "It's possible to change the animation speed by changing it's frame count. Less frames means a faster"
        "animation.\n"
        "When scaling an animation to a new frame count it looses precision. If you changes it a couple of times it's "
        "not a big deal, but the best approach is to store the original animation somewhere and, if you want to change "
        "the frame count again, do it with the original animation"
    )
    print(f"Current frame count is {animation.get_frame_count()}")
    try:
        new_frame_count = input("New frame count: ")
        new_frame_count = int(new_frame_count)
    except ValueError as e:  # And input(...)?
        print(f"Error reading the new frame count! Aborting operation\n Exception was {str(e)}")
        return

    if animation.get_frame_count() == new_frame_count:
        print(f"The animation already has a frame count of {new_frame_count}")
        return

    animation.scale_frame_count(new_frame_count)

    print(f"Animation scaled to {new_frame_count} frames")


def __mix_animations():
    """
    Ask the user for the file path of a second animation to import from them some bone animations
    """
    if animation is None:
        print("No animation loaded")
        return

    # Load the second animation
    file_path = input("File path of the animation from which extract bone animations: ")
    file_path = file_path.replace("\"", "")
    try:
        with open(file_path, "rb") as file:
            dump = file.read()
    except FileNotFoundError:
        print("File not found. Abort operation.")
        return
    if dump is None or len(dump) <= 0:
        print("Error opening animation. Wrong file path?")
        return
    second_animation = Animation(dump)

    # Animations must have the same frame count. Check it!
    # If the frame counts are different, the second animation has to be "scaled".
    if animation.get_frame_count() != second_animation.get_frame_count():
        print(
            f"This animation has not the same frame count of the one loaded!\n"
            f"It is {second_animation.get_frame_count()} instead of {animation.get_frame_count()}\n"
            f"This second animation will be scaled to the correct number of frames"
        )
        second_animation.scale_frame_count(animation.get_frame_count())

    # Which bone animations?
    print(
        "Which bone animations should I import? You can express them as a list of bone IDs (in decimal or hexadecimal "
        "form). For example:\n"
        "  3,4,21,10 to import the animations of bones (joints) number 3, 4, 10 and 21 and\n"
        "  0x03,0x04,0x15,0x0a to import the same bone animations (but using hexadecimal form)"
    )
    try:
        bone_list = [int(x, 0) for x in input("> ").replace(" ", "").replace("\t", "").replace(";", ",").split(",")]
    except ValueError as e:
        print(f"Error processing bone list: {str(e)}")
        return

    # Import the bone animations
    animation.import_bone_animations(source_animation=second_animation, bone_list=bone_list)
    print("Done! :D")


def __concat_animation():
    """
    Ask the user for the file path of a second animation and concat the current animation with that
    """
    if animation is None:
        print("No animation loaded")
        return

    # Load the second animation
    file_path = input("File path of the animation to join: ")
    file_path = file_path.replace("\"", "")
    try:
        with open(file_path, "rb") as file:
            dump = file.read()
    except FileNotFoundError:
        print("File not found. Abort operation.")
        return
    if dump is None or len(dump) <= 0:
        print("Error opening animation. Wrong file path?")
        return
    second_animation = Animation(dump)

    try:
        dropped = animation.concat(second_animation)
    except UnconcatenableAnimationsError as e:
        print(f"Unable to perform the operation -> {str(e)}")
        return

    print("Done! :D")
    print(f"During this last operation, {len(dropped)} bone animations have been dropped due to incompatibilities")
    if len(dropped) > 0:
        print(dropped)


def main():
    """
    Script entrypoint
    """
    print(LOGO)

    # If a file path is present as a command line argument, load the animation
    if len(sys.argv) > 1:
        __load_animation(sys.argv[-1])
        __print_animation_info()

    # Main loop
    while True:
        cmd = __ask_user_command()
        if cmd["name"] == "load":
            __ask_and_load_animation()
            __print_animation_info()
        if cmd["name"] == "print_info":
            __print_animation_info()
        elif cmd["name"] == "change_speed":
            __change_animation_speed()
        elif cmd["name"] == "concat":
            __concat_animation()
        elif cmd["name"] == "mix":
            __mix_animations()
            __print_animation_info()
        elif cmd["name"] == "save":
            __save_animation()
        elif cmd["name"] == "quit":
            print("Goodbye")
            return


if __name__ == "__main__":
    main()
