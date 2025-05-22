from ozobot.protocol_common import convert


class _Serializable:
    def __init__(self, val: int):
        self._val = val

    def serialize(self) -> bytes:
        return bytes(range(self._val))


def test_asciiz() -> None:
    assert convert.asciiz2str(b"hello world\0") == "hello world"
    assert convert.asciiz2str("hello world\0") == "hello world"

    assert convert.str2asciiz("hello world") == b"hello world\0"
    assert convert.str2asciiz("hello world") == b"hello world\0"
    assert convert.str2asciiz("hello", 8) == b"hello\0\0\0"


def test_serialize_bytes_str() -> None:
    assert convert.serialize_array(b"hello", bytes, 8) == b"hello\0\0\0"
    assert convert.serialize_array("hello", str, 8) == b"hello\0\0\0"


def test_serialize_array() -> None:
    assert convert.serialize_array([5, 2], _Serializable) == b"\x00\x01\x02\x03\x04\x00\x01"


def test_deserialize_array() -> None:
    assert convert.deserialize_array(str, b"hello\0\0\0") == "hello"
