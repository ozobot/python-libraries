from __future__ import annotations

import asyncio
import typing
import uuid

from loguru import logger
from ozobot.webrtc.connection import Channel, Connection, ConnectionFactory
from ozobot.webrtc.datatypes import (
    ConnectionClosedBody,
    HandshakeRequestBody,
    HandshakeResponseBody,
    IceCandidateBody,
    LastIceCandidateData,
    SdpAnswerBody,
    SdpOfferBody,
)
from ozobot.webrtc.messaging import MessagingChannel, MessagingChannelFactory


class SignalingClient:
    def __init__(
        self,
        channel_factory: MessagingChannelFactory,
        handshake_channel: MessagingChannel,
        type: typing.Literal["caller", "callee"],
    ) -> None:
        self._channel_factory = channel_factory
        self._handshake_channel = handshake_channel
        self._type = type

    async def signal(self, *, channels: tuple[str, ...] = tuple()) -> tuple[Connection, tuple[Channel, ...]]:
        with logger.contextualize(signaling_uuid=uuid.uuid4()):
            async with self._channel_factory.create() as channel:
                match self._type:
                    case "caller":
                        await self._initiate_handshake(channel)
                    case "callee":
                        await self._accept_handshake(channel)
                    case _:
                        typing.assert_never(self._type)

                return await SignalingProcess(channel, self._type).signal(channels)

    async def _initiate_handshake(self, channel: MessagingChannel) -> None:
        payload = HandshakeRequestBody(name="python-library")
        logger.debug("Sending handshake request")
        await self._handshake_channel.send(payload)

        async with channel.receive() as messages:
            async for msg in messages:
                if isinstance(msg.body, HandshakeResponseBody):
                    logger.info("Received handshake response")
                    channel.set_destination(msg.reply_to)
                    return

    async def _accept_handshake(self, channel: MessagingChannel) -> None:
        async with self._handshake_channel.receive() as messages:
            async for msg in messages:
                if isinstance(msg.body, HandshakeRequestBody):
                    logger.info("Received handshake request")
                    channel.set_destination(msg.reply_to)
                    break

        payload = HandshakeResponseBody(status="accepted")
        logger.debug("Sending handshake response")
        await channel.send(payload)


class SignalingProcess:
    def __init__(self, channel: MessagingChannel, _type: typing.Literal["caller", "callee"]) -> None:
        self._channel = channel
        self._type = _type

    async def signal(self, channel_labels: tuple[str, ...]) -> tuple[Connection, tuple[Channel, ...]]:
        factory = ConnectionFactory()
        with logger.contextualize(type=self._type):
            async with asyncio.TaskGroup() as tg:
                channels = tuple([factory.create_data_channel(label) for label in channel_labels])

                if self._type == "caller":
                    await factory.create_offer()

                messages_task = tg.create_task(self._handle_messages(factory))
                local_candidates_task = tg.create_task(self._handle_local_candidates(factory))
                local_description_task = tg.create_task(self._handle_local_description(factory))

                try:
                    connection = await factory.construct()
                    logger.info("Opened a new connection", connection=connection)
                finally:
                    local_candidates_task.cancel()
                    local_description_task.cancel()
                    messages_task.cancel()

                return connection, channels

    async def _handle_messages(self, factory: ConnectionFactory) -> None:
        async with self._channel.receive() as messages:
            async for msg in messages:
                message_payload = msg.body

                if isinstance(message_payload, ConnectionClosedBody):
                    logger.info("Closing connection", reason=message_payload.reason)
                    await factory.close()
                    return
                elif isinstance(message_payload, SdpOfferBody):
                    logger.info(
                        "Received SDP offer description",
                        type=message_payload.data.type,
                        description=str(message_payload.data),
                    )
                    await factory.set_remote_description(message_payload.data)
                    await factory.create_answer()
                elif isinstance(message_payload, SdpAnswerBody):
                    logger.info(
                        "Received SDP answer description",
                        type=message_payload.data.type,
                        description=str(message_payload.data),
                    )
                    await factory.set_remote_description(message_payload.data)
                elif isinstance(message_payload, IceCandidateBody):
                    logger.info("Received ICE candidate", candidate=str(message_payload.data))
                    data = message_payload.data
                    if data is None:
                        logger.info("Remote ICE gathering done")
                    elif isinstance(data, LastIceCandidateData):
                        logger.info("Remote ICE last candidate")
                    else:
                        await factory.add_remote_candidate(data)
                        logger.debug("Added ICE candidate")
                else:
                    logger.warning("Ignoring unsupported message_payload", type=message_payload.type)

    async def _handle_local_candidates(self, factory: ConnectionFactory) -> None:
        async with factory.local_candidates as local_candidates:
            async for candidate in local_candidates.items():
                logger.debug("Sending ICE candidate", candidate=str(candidate))
                await self._channel.send(IceCandidateBody(data=candidate))

    async def _handle_local_description(self, factory: ConnectionFactory) -> None:
        async with factory.local_description as local_description:
            async for description in local_description.items():
                message: SdpAnswerBody | SdpOfferBody
                if description.type == "answer":
                    message = SdpAnswerBody(data=description)
                else:
                    message = SdpOfferBody(data=description)
                logger.debug("Sending SDP description", type=description.type, description=str(description))
                await self._channel.send(message)
