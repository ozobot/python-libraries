from ozobot.webrtc.aiortc_wrapper import ReadyState
import asyncio

from ozobot.webrtc.datatypes import Message
from ozobot.webrtc.signaling import SignalingClient

from .testutils import create_channel_factory


async def test_channel_read_write() -> None:
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

    channel_caller = ret_caller[1][0]

    async with ret_callee[0].data_channels() as channels:
        channel_callee = await anext(channels)

    async with asyncio.timeout(1):
        assert await anext(channel_caller.ready_state()) == ReadyState.OPEN
        assert await anext(channel_callee.ready_state()) == ReadyState.OPEN

        await channel_caller.send("hello from caller")
        assert await anext(channel_callee.receive_str()) == "hello from caller"

        await channel_callee.send("hello from callee")
        assert await anext(channel_caller.receive_str()) == "hello from callee"

    # close the connections
    await ret_caller[0].close()
    await ret_callee[0].close()
