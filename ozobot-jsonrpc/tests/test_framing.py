import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest
from ozobot.jsonrpc.framing import FrameDecoder as Decoder
from ozobot.jsonrpc.framing import FrameReader, FrameWriter, encode_frame


def test_frame_simple():
    data = b"hello"
    framed = encode_frame(data)

    assert framed[0] == Decoder.FRAME_FLAG
    assert framed[-1] == Decoder.FRAME_FLAG
    assert framed[1:-1] == data


def test_frame_with_flag_and_escape():
    data = bytes([1, Decoder.FRAME_FLAG, 2, Decoder.FRAME_ESCAPE, 3])
    framed = encode_frame(data)

    assert framed[0] == Decoder.FRAME_FLAG
    assert framed[-1] == Decoder.FRAME_FLAG
    # The FRAME_FLAG and FRAME_ESCAPE bytes should be escaped
    # After the initial FRAME_FLAG, next should be 1, then FRAME_ESCAPE, then FRAME_FLAG^ESCAPE_XOR, etc.
    expected = bytearray(
        [
            1,
            Decoder.FRAME_ESCAPE,
            Decoder.FRAME_FLAG ^ Decoder.FRAME_ALT,
            2,
            Decoder.FRAME_ESCAPE,
            Decoder.FRAME_ESCAPE ^ Decoder.FRAME_ALT,
            3,
        ]
    )
    assert framed[1:-1] == bytes(expected)


def test_deframer_simple():
    data = b"hello"
    framed = encode_frame(data)
    deframer = Decoder()
    result = list(deframer.feed(framed))
    assert result == [data]


def test_deframer_with_escapes():
    original = bytes([1, Decoder.FRAME_FLAG, 2, Decoder.FRAME_ESCAPE, 3])
    framed = encode_frame(original)
    deframer = Decoder()
    result = list(deframer.feed(framed))
    # The deframer should return the original data, not the escaped version
    assert result == [bytes([1, Decoder.FRAME_FLAG, 2, Decoder.FRAME_ESCAPE, 3])]


def test_deframer_multiple_frames():
    data1 = b"abc"
    data2 = b"def"
    framed1 = encode_frame(data1)
    framed2 = encode_frame(data2)
    deframer = Decoder()

    results = list(deframer.feed(framed1 + framed2))
    assert results == [data1, data2]


def test_deframer_partial_feed():
    data = b"hello"
    framed = encode_frame(data)
    deframer = Decoder()
    # Feed in two parts
    part1 = framed[:3]
    part2 = framed[3:]
    result1 = list(deframer.feed(part1))
    assert result1 == []
    result2 = list(deframer.feed(part2))
    assert result2 == [data]


def test_deframer_multiple_results_multiple_feeds():
    data1 = b"abc"
    data2 = b"def"
    data3 = b"ghi"

    frame1 = encode_frame(data1)
    frame2 = encode_frame(data2)
    frame3 = encode_frame(data3)

    frame3_part1 = frame3[:2]
    frame3_part2 = frame3[2:]

    deframer = Decoder()
    result1 = list(deframer.feed(frame1 + frame2 + frame3_part1))
    assert result1 == [data1, data2]

    result2 = list(deframer.feed(frame3_part2))
    assert result2 == [data3]


def test_deframer_consecutive_flags():
    # Should ignore consecutive FLAGs
    data = b"hi"
    framed = encode_frame(data)
    # Insert extra FLAGs between
    noisy = (
        bytes([Decoder.FRAME_FLAG, Decoder.FRAME_FLAG]) + framed[1:-1] + bytes([Decoder.FRAME_FLAG, Decoder.FRAME_FLAG])
    )
    deframer = Decoder()
    result = list(deframer.feed(noisy))
    assert result == [data]


def test_deframer_no_frame():
    deframer = Decoder()
    # No FLAGs, should return None
    result = list(deframer.feed(b"abcdef"))
    assert result == []


def test_deframer_escape_at_end():
    # Decoder.FRAME_ESCAPE at end of input should not crash, just wait for next byte
    deframer = Decoder()
    # Start a frame, Decoder.FRAME_ESCAPE at end
    result1 = list(deframer.feed(bytes([Decoder.FRAME_FLAG, Decoder.FRAME_ESCAPE])))
    assert result1 == []

    # Now feed the escaped byte
    result2 = list(deframer.feed(bytes([Decoder.FRAME_FLAG ^ Decoder.FRAME_ALT, Decoder.FRAME_FLAG])))
    assert result2 == [bytes([Decoder.FRAME_FLAG])]


async def test_reader() -> None:
    data = [encode_frame(d) for d in [b"hello", b"world"]]

    queue = asyncio.Queue[bytes]()
    readable = Mock(read=queue.get)
    reader = FrameReader(readable, lambda b: b.decode("utf8"))

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(reader.read())

    iter = reader.read()

    for d in data:
        await queue.put(d)

    result = await anext(iter)
    assert result == "hello"

    result = await anext(iter)
    assert result == "world"


async def test_reader_corrupted_data() -> None:
    queue = asyncio.Queue[bytes]()
    readable = Mock(read=queue.get)
    reader = FrameReader(readable, lambda b: b.decode("utf8"))

    # data not framed
    data = b"hello world"
    await queue.put(data)

    # the corrupted data got dropped
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(reader.read())

    await queue.put(encode_frame(b"hi"))
    result = await anext(reader.read())
    assert result == "hi"


async def test_writer() -> None:
    writable = Mock(write=AsyncMock())
    writer = FrameWriter[str](writable, lambda s: s.encode("utf8"))
    await writer.write("hello")
    await writer.write("world")

    writable.write.assert_has_calls(
        [
            call(encode_frame(b"hello")),
            call(encode_frame(b"world")),
        ]
    )
