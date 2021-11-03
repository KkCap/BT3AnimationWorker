"""
This module offers some quick wrappers for struct.pack(...) and struct.unpack(...).
p8(...), p16(...), etc  -->  pack values in a little-endian byte, short, etc
up8(...), up16(...), etc  -->  do the opposite
"""


import struct


def p8(value: int) -> bytes:
    return struct.pack("B", value)


def p16(value: int) -> bytes:
    return struct.pack("H", value)


def p32(value: int) -> bytes:
    return struct.pack("I", value)


def p64(value: int) -> bytes:
    return struct.pack("Q", value)


def p_float(value: float) -> bytes:
    return struct.pack("f", value)


def up8(what: bytes) -> int:
    return struct.unpack("B", what)[0]


def up16(what: bytes) -> int:
    return struct.unpack("H", what)[0]


def up32(what: bytes) -> int:
    return struct.unpack("I", what)[0]


def up64(what: bytes) -> int:
    return struct.unpack("Q", what)[0]


def up_float(what: bytes) -> float:
    return struct.unpack("f", what)[0]
