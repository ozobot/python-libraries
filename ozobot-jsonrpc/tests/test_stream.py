import asyncio
from unittest.mock import AsyncMock, Mock, call

import pytest
from ozobot.jsonrpc import framing, stream as s


async def test_reader() -> None:
    stream = asyncio.StreamReader()
    reader = s.Reader(stream, lambda b: b.decode("utf8"))

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(reader.read())

    iter = reader.read()
    stream.feed_data(framing.encode_frame(b"hello"))
    stream.feed_data(framing.encode_frame(b"world"))

    result = await anext(iter)
    assert result == "hello"

    result = await anext(iter)
    assert result == "world"


async def test_reader_corrupted_data() -> None:
    stream = asyncio.StreamReader()
    reader = s.Reader(stream, lambda b: b.decode("utf8"))

    # no framing here
    stream.feed_data(b"hello world")

    # the corrupted data got dropped
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(reader.read())

    stream.feed_data(framing.encode_frame(b"hi"))
    result = await anext(reader.read())
    assert result == "hi"


async def test_writer() -> None:
    mock_transport = Mock(spec=asyncio.Transport)
    mock_protocol = Mock(spec=asyncio.Protocol, _drain_helper=AsyncMock())

    stream = asyncio.StreamWriter(mock_transport, mock_protocol, None, asyncio.get_running_loop())
    writer = s.Writer[str](stream, lambda s: s.encode("utf8"))
    await writer.write("hello")
    await writer.write("world")

    mock_transport.write.assert_has_calls(
        [
            call(framing.encode_frame(b"hello")),
            call(framing.encode_frame(b"world")),
        ]
    )
    assert mock_protocol._drain_helper.call_count == 2
