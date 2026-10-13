import asyncio
import typing

import pytest
from ozobot.ari.driver.transport import SerializingTransportLayer
from ozobot.ari.exceptions import MissingMessageIdError
from ozobot.ari.protocol import notification, request, response
from ozobot.ari.protocol.serialization import serialize
from ozobot.common.rpc.executor import StampedMessage


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

    tone_req = request.PlayToneRequest(params=request.PlayToneRequestParams(frequency=1, duration=2))
    await transport.write(StampedMessage(1, tone_req))

    sound_req = request.PlaySoundRequest(params=request.PlaySoundRequestParams(name="name", loop=False))
    await transport.write(StampedMessage(2, sound_req))

    requests_sent = [
        await from_transport.get(),
        await from_transport.get(),
    ]
    assert requests_sent == [
        '{"id":1,"jsonrpc":"2.0","method":"PlayTone","params":{"frequency":1,"duration":2.0}}',
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
        StampedMessage(2, response.PlaySoundResponse(result=response.PlaySoundResponseBody(type="success"))),
        StampedMessage(1, response.PlayToneResponse(result=response.PlayToneResponseBody(type="success"))),
    ]


async def test_serializing_transport_parse_notifications() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    req = request.MoveStraightRequest(params=request.MoveStraightRequestParams(distance=1, speed=2))
    await transport.write(StampedMessage(1, req))

    req_sent = await from_transport.get()
    assert req_sent == '{"id":1,"jsonrpc":"2.0","method":"MoveStraight","params":{"distance":1.0,"speed":2.0}}'

    notifications = [
        notification.MotionNotification(
            result=notification.MotionNotificationBody(max_speed=i, overshot_distance=10 * i, overshot_time=100 * i)
        )
        for i in range(1, 4)
    ]

    for n in notifications:
        await to_transport.put(serialize(StampedMessage(1, n)))

    notifications_received = [await anext(transport.read()) for _ in range(3)]

    assert notifications_received == [StampedMessage(1, n) for n in notifications]


async def test_serializing_transport_deregister_after_response() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    req = request.PlayToneRequest(params=request.PlayToneRequestParams(frequency=1, duration=2))
    await transport.write(StampedMessage(1, req))

    req_sent = await from_transport.get()
    assert req_sent == '{"id":1,"jsonrpc":"2.0","method":"PlayTone","params":{"frequency":1,"duration":2.0}}'

    r = response.PlayToneResponse(result=response.PlayToneResponseBody(type="success"))
    await to_transport.put(serialize(StampedMessage(1, r)))

    response_received = await anext(transport.read())
    assert response_received == StampedMessage(1, r)


async def test_serializing_transport_message_without_id_raises() -> None:
    to_transport = asyncio.Queue[str]()
    from_transport = asyncio.Queue[str]()
    transport = SerializingTransportLayer(_QueueTransport(to_transport, from_transport))

    await to_transport.put('{"jsonrpc":"2.0"}')

    with pytest.raises(MissingMessageIdError):
        await anext(transport.read())
