import functools
import operator
from enum import IntEnum, IntFlag
from typing import Any, List, Optional, Protocol, Type, Union, cast


class _Serializable(Protocol):
    def serialize(self) -> bytes: ...


class ProtocolSizeError(RuntimeError):
    def __init__(self, what, size, max_size):
        super().__init__(
            f"{what} size ({size}) exceeded maximal allowed size ({max_size}) by protocol"
        )


def asciiz2str(txt: Union[str, bytes]) -> str:
    """Decodes ASCIIZ (C-string) to python string

    Function returns head of tring till first ``'\0'`` occourance. If ``'\0'`` not found,
    then entire string is returned. If input text is ``bytes``, then in is converted
    as ``ASCII`` to string.

    :param txt:    ASCIIZ string to be converted to python string

    :return:       Python string extracted from ASCIIZ
    """
    if isinstance(txt, str):
        txt = txt.encode("ascii")

    txt = txt.split(b"\x00", 1)[0]
    return txt.decode()


def str2asciiz(txt: Union[str, bytes], size: Optional[int] = None) -> bytes:
    """Encodes python string to ASCIIZ (C-string)

    Function returns python string as bytes with ``ASCII`` encoding terminated by ``b'\0'``.
    If `size` is defined, then bytes of this size will be returned containing ``ASCII``
    encoded bytes where rest of bytes is filled in by ``b'\0'`` characters. When there is not
    enough space to store encoded ``ASCIIZ``, then exception :py:class:`ProtocolSizeError`
    is raised.

    :param txt:    Python string to be converted as ``ASCIIZ``
    :param size:   Final size of buffer to store ``ASCIIZ``. Raises :py:class:`ProtocolSizeError`
                   when buffer is too small to pass whole string.

    :return:       Bytes encoded as ``ASCIIZ``
    """
    if isinstance(txt, str):
        txt = txt.encode("ascii")

    length = len(txt)

    if size is None:
        size = length + 1

    if length < size:
        txt += b"\0" * (size - length)
    elif length > size:
        raise ProtocolSizeError(txt, length, size)

    return txt


def convert_to[T](expected_type: Type[T], value: Any) -> T:
    """Process conversion of value to expected type

    :param expected_type:    Target type
    :param value:            Value to be converted to target type
    """
    # If we are expected type, just return us - always
    if isinstance(value, expected_type):
        return value

    # If expected type is based on bytes (we are expecting that value is either string or not-iterable).
    if issubclass(expected_type, bytes):
        value = (
            expected_type(value, "ascii")
            if isinstance(value, str)
            else expected_type([value])
        )
    # If converting bytes to str, use bytes.decode to avoid the b'' stringification.
    elif issubclass(expected_type, str) and isinstance(value, bytes):
        value = expected_type(value.decode("ascii"))
    # If we are not bytes, then lets try to convert us directly
    elif issubclass(expected_type, (IntEnum, IntFlag)):
        value = expected_type(value)
    elif isinstance(value, dict):
        value = expected_type(**value)
    else:
        value = expected_type(value)  # type: ignore[call-arg]

    return value


def deserialize_array(member_type, data: bytes) -> Union[List, str, bytes]:
    """Deserialize ``bytes`` to array of instances of requested type

    Takes bytes and creates array of items based on items sizes. If requested type is based on ``str``,
    then ``ASCIIZ is expected in bytes``.

    :param member_type:    Expected items type (see :py:class:`protocol_impl.Types`)
    :param data:           Bytes to be deserialized
    """
    if issubclass(member_type, (bytes, str)):
        # Convert ASCIIZ to str
        return asciiz2str(data)
    elif (
        hasattr(member_type, "py_pack") and (member_type.py_pack == "B")
    ) or issubclass(member_type, bytes):
        # Array of bytes is always converted to bytes -> keep it as it is
        return data
    else:
        # The rest is converted to list of type based items
        return [
            member_type.deserialize(data[r : r + member_type.data_width])
            for r in range(0, len(data), member_type.data_width)
        ]


def serialize_array[T: bytes | str | _Serializable](
    array: List[T], member_type: Type[T], size: Optional[int] = None
) -> bytes:
    """Serialize iterable of items to ``bytes``

    Takes array of items and serialize them into bytes according to size of elements.
    If an input array is ``str``, then ``ASCIIZ`` is created.

    :param array:    Iterable to be serialized
    :param size:     Size of final bytes buffer. Raises :py:meth:`ProtocolSizeError`
                     when size does not match to serialized data.
    """
    if issubclass(member_type, (bytes, str)):
        # Convert str to ASCIIZ
        array_str_bytes = cast(Union[str, bytes], array)
        data = str2asciiz(array_str_bytes, size)
    else:
        # The rest is converted from list of type based items
        data = functools.reduce(
            operator.add, [convert_to(member_type, x).serialize() for x in array]
        )  # type: ignore[attr-defined]

    if size is not None and len(data) > size:
        raise ProtocolSizeError(data, len(data), size)

    return data
