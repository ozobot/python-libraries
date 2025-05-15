import struct


class FloatOutOfRangeError(ValueError):
    def __init__(self, val: float | int):
        super().__init__(f"Float value out of supported range (-128, 128): {val}")


def float_to_s8_24(val: float) -> int:
    if -128 < val < 128:
        return int(val * float(1 << 24))
    else:
        raise FloatOutOfRangeError(val)


def s8_24_to_float(val: int) -> float:
    return val / float(1 << 24)


def s8_24_serialize(val: float) -> bytes:
    return struct.pack("<i", float_to_s8_24(val))


def s8_24_deserialize(val: bytes) -> float:
    return float(s8_24_to_float(*struct.unpack("<i", val)))
