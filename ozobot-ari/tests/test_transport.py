import asyncio
import typing

import pytest
from ozobot.ari.exceptions import UnknownMessageIdError
from ozobot.ari.framing import encode_frame
from ozobot.ari.protocol import notification, request, response
from ozobot.ari.protocol.serialization import serialize
from ozobot.ari.transport import FramingTransportLayer, SerializingTransportLayer


class _QueueTransport[T]:
    def __init__(self, to_transport: asyncio.Queue[T], from_transport: asyncio.Queue[T]) -> None:
        self._read_queue = to_transport
        self._write_queue = from_transport

    async def read(self) -> typing.AsyncIterator[T]:
        while True:
            yield await self._read_queue.get()

    async def write(self, data: T) -> None:
        await self._write_queue.put(data)


async def test_serializing_transport_context() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    tone_req = request.PlayToneRequest(id=1, params=request.PlayToneRequestParams(frequency=1, volume=2, duration=3))
    await transport.write(tone_req)

    sound_req = request.PlaySoundRequest(id=2, params=request.PlaySoundRequestParams(name="name", loop=False))
    await transport.write(sound_req)

    requests_sent = [
        await from_transport.get(),
        await from_transport.get(),
    ]
    assert requests_sent == [
        '{"id":1,"jsonrpc":"2.0","method":"PlayTone","params":{"frequency":1,"duration":3,"volume":2.0}}',
        '{"id":2,"jsonrpc":"2.0","method":"PlaySound","params":{"name":"name","loop":false}}',
    ]

    # notice the messages are the same, just the id differs
    await to_transport.put('{"id":2,"jsonrpc":"2.0","result":{"type": "success"}}')
    await to_transport.put('{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}')

    # we parsed the correct type by the id dispatch
    responses_received = [
        await anext(transport.read()),
        await anext(transport.read()),
    ]
    assert responses_received == [
        response.PlaySoundResponse(id=2, result=response.PlaySoundResponseBody(type="success")),
        response.PlayToneResponse(id=1, result=response.PlayToneResponseBody(type="success")),
    ]


async def test_serializing_transport_parse_notifications() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    req = request.MoveStraightRequest(id=1, params=request.MoveStraightRequestParams(distance=1, speed=2))
    await transport.write(req)

    req_sent = await from_transport.get()
    assert req_sent == '{"id":1,"jsonrpc":"2.0","method":"MoveStraight","params":{"distance":1.0,"speed":2.0}}'

    notifications = [
        notification.MotionNotification(
            id=1,
            result=notification.MotionNotificationBody(max_speed=i, overshot_distance=10 * i, overshot_time=100 * i),
        )
        for i in range(1, 4)
    ]

    for n in notifications:
        await to_transport.put(serialize(n))

    notifications_received = [await anext(transport.read()) for _ in range(3)]

    assert notifications_received == notifications


async def test_serializing_transport_deregister_after_response() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    req = request.PlayToneRequest(id=1, params=request.PlayToneRequestParams(frequency=1, volume=2, duration=3))
    await transport.write(req)

    req_sent = await from_transport.get()
    assert req_sent == '{"id":1,"jsonrpc":"2.0","method":"PlayTone","params":{"frequency":1,"duration":3,"volume":2.0}}'

    r = response.PlayToneResponse(id=1, result=response.PlayToneResponseBody(type="success"))
    await to_transport.put(serialize(r))

    response_received = await anext(transport.read())
    assert response_received == r

    # this fails because the response was already received
    await to_transport.put(serialize(r))
    with pytest.raises(UnknownMessageIdError):
        await anext(transport.read())


async def test_framing_transport_write() -> None:
    to_transport = asyncio.Queue[bytes]()
    from_transport = asyncio.Queue[bytes]()
    transport = FramingTransportLayer(_QueueTransport(to_transport, from_transport))

    await transport.write("hello")
    await transport.write("world")

    assert await from_transport.get() == encode_frame(b"hello")
    assert await from_transport.get() == encode_frame(b"world")

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await from_transport.get()


async def test_framing_transport_read() -> None:
    to_transport = asyncio.Queue[bytes]()
    from_transport = asyncio.Queue[bytes]()
    transport = FramingTransportLayer(_QueueTransport(to_transport, from_transport))

    for d in [b"hello", b"world"]:
        await to_transport.put(encode_frame(d))

    assert await anext(transport.read()) == "hello"
    assert await anext(transport.read()) == "world"

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(transport.read())


async def test_framing_transport_corrupted_data() -> None:
    to_transport = asyncio.Queue[bytes]()
    from_transport = asyncio.Queue[bytes]()
    transport = FramingTransportLayer(_QueueTransport(to_transport, from_transport))

    # data not framed
    data = b"hello world"
    await to_transport.put(data)

    # the corrupted data got dropped
    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            _ = await anext(transport.read())

    await to_transport.put(encode_frame(b"hi"))
    result = await anext(transport.read())
    assert result == "hi"
