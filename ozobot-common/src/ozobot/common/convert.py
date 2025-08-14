from __future__ import annotations

import functools
import operator
from typing import Any, Protocol


class _Serializable(Protocol):
    def __init__(self, val) -> None: ...
    def serialize(self) -> bytes: ...


class _Deserializable(Protocol):
    data_width: int

    @classmethod
    def deserialize(cls, data: bytes) -> _Deserializable: ...


def asciiz2str(asciiz: str | bytes) -> str:
    """Decodes ASCIIZ (C-string) to python string

    Function returns head of tring till first ``'\0'`` occourance. If ``'\0'`` not found,
    then entire string is returned. If input text is ``bytes``, then in is converted
    as ``ASCII`` to string.

    :param txt:    ASCIIZ string to be converted to python string

    :return:       Python string extracted from ASCIIZ
    """
    if isinstance(asciiz, str):
        asciiz = asciiz.encode("ascii")

    asciiz = asciiz.split(b"\x00", 1)[0]
    return asciiz.decode()


def str2asciiz(txt: str | bytes, size: int | None = None) -> bytes:
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
        raise ValueError(f"Provided string is larger than the limit: string {length}, limit: {size}")

    return txt


def deserialize_array[T: _Deserializable](member_type: type[str | T], data: bytes) -> str | list[T]:
    """Deserialize ``bytes`` to array of instances of requested type

    Takes bytes and creates array of items based on items sizes. If requested type is based on ``str``,
    then ``ASCIIZ is expected in bytes``.

    :param member_type:    Expected items type (see :py:class:`protocol_impl.Types`)
    :param data:           Bytes to be deserialized
    """
    if issubclass(member_type, str):
        return asciiz2str(data)
    elif hasattr(member_type, "py_pack") and member_type.py_pack == "B":  # type: ignore[attr-defined]
        # Array of bytes is always converted to bytes -> keep it as it is
        return data  # type: ignore[return-value]
    else:
        # The rest is converted to list of type based items
        return [
            member_type.deserialize(data[r : r + member_type.data_width])  # type: ignore[misc]
            for r in range(0, len(data), member_type.data_width)
        ]


def serialize_array[T: _Serializable](
    array: str | bytes | list[Any],
    member_type: type[str | bytes | T],
    size: int | None = None,
) -> bytes:
    """Serialize iterable of items to ``bytes``

    Takes array of items and serialize them into bytes according to size of elements.
    If an input array is ``str``, then ``ASCIIZ`` is created.

    :param array:    Iterable to be serialized
    :param size:     Size of final bytes buffer. Raises :py:meth:`ProtocolSizeError`
                     when size does not match to serialized data.
    """
    if issubclass(member_type, bytes | str):
        if isinstance(array, str | bytes):
            # Convert str to ASCIIZ
            data = str2asciiz(array, size)
        else:
            raise ValueError("Only str and bytes types can be serialized to str and bytes")
    else:
        # The rest is converted from list of type based items
        data = functools.reduce(operator.add, [member_type(x).serialize() for x in array])

    if size is not None and len(data) > size:
        raise ValueError(f"Expected array size does not match the real size, expected: {size}, real: {len(data)}")

    return data
