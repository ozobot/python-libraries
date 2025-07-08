import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from ozobot.webrtc.datatypes import (
    ConnectionClosedBody,
    Message,
)
from ozobot.webrtc.exceptions import WebRTCConnectionUnexpectedStateError
from ozobot.webrtc.signaling.negotiation import SignalingClient, SignalingProcess

from .testutils import create_channel_factory


class InstrumentationError(Exception): ...


async def test_negotiation() -> None:
    to_caller = asyncio.Queue[Message]()
    from_caller = asyncio.Queue[Message]()

    caller_factory = create_channel_factory(to_caller, from_caller)
    callee_factory = create_channel_factory(from_caller, to_caller)
    handshake_channel_factory = create_channel_factory(inputs=[])

    async with handshake_channel_factory.create() as handshake_channel:
        caller = SignalingClient(caller_factory, handshake_channel, type="caller")
        callee = SignalingClient(callee_factory, handshake_channel, type="callee")

    async with asyncio.timeout(5):
        ret_caller, ret_callee = await asyncio.gather(caller.signal(channels=("test",)), callee.signal())

    connection_caller, channels_caller = ret_caller
    connection_callee, channels_callee = ret_callee

    assert len(channels_caller) == 1
    assert len(channels_callee) == 0

    async with connection_callee.data_channels() as channels, asyncio.timeout(1):
        channel = await anext(channels)
        assert channel.label == "test"

        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(0.1):
                _ = await anext(channels)

    await connection_caller.close()
    await connection_callee.close()


async def test_close() -> None:
    to_process = asyncio.Queue[Message]()
    from_process = asyncio.Queue[Message]()
    channel_factory = create_channel_factory(to_process, from_process)

    async with channel_factory.create() as channel:
        negotiation = SignalingProcess(channel, "caller")

        async with asyncio.timeout(5):
            with pytest.RaisesGroup(WebRTCConnectionUnexpectedStateError):
                await asyncio.gather(
                    to_process.put(Message(ConnectionClosedBody(), reply_to=None)),
                    negotiation.signal(tuple()),
                )


async def test_error_handling() -> None:
    to_process = asyncio.Queue[Message]()
    from_process = asyncio.Queue[Message]()
    channel_factory = create_channel_factory(to_process, from_process)

    with patch("ozobot.webrtc.signaling.negotiation.ConnectionFactory") as connection_factory_mock:
        connection_factory_mock().create_offer = AsyncMock(side_effect=InstrumentationError)
        async with channel_factory.create() as channel:
            negotiation = SignalingProcess(channel, "caller")

            with pytest.RaisesGroup(InstrumentationError):
                await negotiation.signal(tuple())
