import asyncio
import dataclasses
import os

import pytest
from ozobot.webrtc.datatypes import HandshakeRequestBody
from ozobot.webrtc.messaging import MessagingChannelConfig, create_channel_factory

_tcp_config = MessagingChannelConfig(
    device_id="test-device",
    ssl=False,
    host="localhost",
    port=5672,
    virtualhost="/",
    exchange="amq.direct",
    username="guest",
    password="guest",
    transport="tcp",
)

_websocket_config = dataclasses.replace(_tcp_config, transport="websocket", port=15670)
parametrize_config = pytest.mark.parametrize(
    "config",
    [_tcp_config, _websocket_config],
    ids=["tcp", "websocket"],
)


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
@parametrize_config
async def test_open_anon_queue(config: MessagingChannelConfig) -> None:
    async with create_channel_factory(config) as channel_factory:
        async with channel_factory.create() as channel1:
            assert channel1.name.startswith("amq.")


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
@parametrize_config
async def test_open_named_queue(config: MessagingChannelConfig) -> None:
    async with create_channel_factory(config) as channel_factory:
        async with channel_factory.create(name="my-queue") as channel1:
            assert channel1.name == "my-queue"


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
@parametrize_config
async def test_send_receive(config: MessagingChannelConfig) -> None:
    q1 = "test-queue1"
    q2 = "test-queue2"

    async with create_channel_factory(config) as channel_factory:
        async with channel_factory.create(name=q1) as channel1, channel_factory.create(name=q2) as channel2:
            channel1.set_destination(q2)
            channel2.set_destination(q1)

            async with asyncio.timeout(1):
                await channel1.send(HandshakeRequestBody(name="channel1-client"))
                async with channel2.receive() as gen:
                    msg = await anext(gen)
                    assert isinstance(msg.body, HandshakeRequestBody)
                    assert msg.body.name == "channel1-client"
                    assert msg.reply_to == "test-queue1"

                await channel2.send(HandshakeRequestBody(name="channel2-client"))
                async with channel1.receive() as gen:
                    msg = await anext(gen)
                    assert isinstance(msg.body, HandshakeRequestBody)
                    assert msg.body.name == "channel2-client"
                    assert msg.reply_to == "test-queue2"


@pytest.mark.skipif("CI" not in os.environ, reason="Can only be run on CI with a broker set up")
@parametrize_config
async def test_send_receive_anonymous(config: MessagingChannelConfig) -> None:
    async with create_channel_factory(config) as channel_factory:
        async with channel_factory.create() as channel1, channel_factory.create() as channel2:
            channel1.set_destination(channel2.name)
            channel2.set_destination(channel1.name)

            async with asyncio.timeout(1):
                await channel1.send(HandshakeRequestBody(name="channel1-client"))
                async with channel2.receive() as gen:
                    msg = await anext(gen)
                    assert isinstance(msg.body, HandshakeRequestBody)
                    assert msg.body.name == "channel1-client"
                    assert msg.reply_to == channel1.name

                await channel2.send(HandshakeRequestBody(name="channel2-client"))
                async with channel1.receive() as gen:
                    msg = await anext(gen)
                    assert isinstance(msg.body, HandshakeRequestBody)
                    assert msg.body.name == "channel2-client"
                    assert msg.reply_to == channel2.name
