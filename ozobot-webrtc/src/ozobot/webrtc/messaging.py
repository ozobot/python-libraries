from __future__ import annotations

import asyncio
import contextlib
import typing

import aio_pika
import pydantic
from aio_pika.abc import (
    AbstractExchange,
    AbstractIncomingMessage,
    AbstractQueue,
    AbstractRobustConnection,
    ConsumerTag,
)
from aio_pika.robust_connection import connect_robust
from loguru import logger
from ozobot.webrtc.datatypes import (
    Message,
    MessageBody,
    parse_message,
)


class MessagingChannelConfig:
    polite = True
    ssl = True
    host = "rmq.editor.ozobot.com"
    port = 5672
    virtualhost = "webrtc-signaling"
    exchange = "webrtc-signaling"

    def get_device_id(self) -> str:
        raise NotImplementedError()

    def get_credentials(self) -> tuple[str, str]:
        raise NotImplementedError()


class WebSocketMessagingChannel:
    @classmethod
    @contextlib.asynccontextmanager
    async def create(cls) -> typing.AsyncIterator[typing.Self]:
        config = MessagingChannelConfig()

        username, password = config.get_credentials()

        connection = await connect_robust(
            host=config.host,
            port=config.port,
            ssl=config.ssl,
            login=username,
            password=password,
            virtualhost=config.virtualhost,
            heartbeat=10,
        )

        channel_factory = MessagingChannelFactory(connection, config.exchange)

        try:
            yield cls(channel_factory, config.get_device_id(), config.polite)
        finally:
            await connection.close()

    def __init__(
        self, messaging_channel_factory: MessagingChannelFactory, ingress_channel_identifier: str, polite: bool
    ):
        self._channel_factory = messaging_channel_factory
        self._ingress_channel_identifier = ingress_channel_identifier
        self._polite = polite


class MessagingChannelFactory:
    def __init__(self, connection: AbstractRobustConnection, exchange_name: str):
        self._connection = connection
        self._exchange_name = exchange_name

    @contextlib.asynccontextmanager
    async def create(
        self, *, name: str | None = None, destination: str | None = None
    ) -> typing.AsyncIterator[MessagingChannel]:
        async with self._create(name) as (exchange, queue):
            yield MessagingChannel(exchange, queue, destination)

    @contextlib.asynccontextmanager
    async def _create(self, name: str | None) -> typing.AsyncIterator[tuple[AbstractExchange, AbstractQueue]]:
        logger.debug("Opening communication channel", name=name)
        channel = await self._connection.channel()
        exchange = await channel.get_exchange(self._exchange_name)
        queue = await channel.declare_queue(name=name, auto_delete=True, exclusive=True)
        await queue.bind(exchange)

        try:
            yield exchange, queue
        finally:
            logger.debug("Closing channel")
            await channel.close()


class MessagingChannel:
    def __init__(self, exchange: AbstractExchange, receive_queue: AbstractQueue, destination: str | None):
        self._exchange = exchange
        self._route_name = receive_queue.name
        self._receive_queue = receive_queue
        self._queue = asyncio.Queue[AbstractIncomingMessage]()
        self._destination = destination
        self._tag: ConsumerTag | None = None

    def set_destination(self, destination: str | None) -> None:
        self._destination = destination

    @contextlib.asynccontextmanager
    async def receive(self) -> typing.AsyncIterator[typing.AsyncIterator[Message]]:
        await self._subscribe()
        yield self._read()

    async def _subscribe(self) -> None:
        if not self._tag:
            self._tag = await self._receive_queue.consume(callback=self._queue.put)

    async def _read(self) -> typing.AsyncIterator[Message]:
        while True:
            message = await self._queue.get()
            async with message.process():
                logger.debug("Received message", message=repr(message), body=message.body.replace(b"\n", b"\\n"))
                try:
                    parsed_message = parse_message(message)
                except pydantic.ValidationError:
                    logger.exception("Ignoring message")
                else:
                    logger.debug("Parsed message", body=parsed_message)
                    yield parsed_message

    async def send(self, message_payload: MessageBody) -> None:
        if self._destination:
            raw_message = message_payload.model_dump_json()
            message = aio_pika.Message(body=raw_message.encode("utf8"), reply_to=self._route_name)

            await self._exchange.publish(
                message=message,
                routing_key=self._destination,
            )

            logger.debug("Sent message", body=raw_message, reply_to=self._route_name, routing_key=self._destination)
        else:
            logger.warning("Message not send, no destination given")
