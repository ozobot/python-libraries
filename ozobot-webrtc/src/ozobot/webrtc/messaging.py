from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import typing

import aiormq
import pydantic

from loguru import logger
from ozobot.webrtc.datatypes import (
    Message,
    MessageBody,
    parse_message,
)
from yarl import URL


@dataclasses.dataclass
class MessagingChannelConfig:
    device_id: str
    username: str
    password: str
    ssl: bool = dataclasses.field(default=True)
    host: str = dataclasses.field(default="rmq.editor.ozobot.com")
    port: int = dataclasses.field(default=5671)
    virtualhost: str = dataclasses.field(default="webrtc-signaling")
    exchange: str = dataclasses.field(default="webrtc-signaling")


@contextlib.asynccontextmanager
async def create_channel_factory(config: MessagingChannelConfig) -> typing.AsyncIterator[MessagingChannelFactory]:
    scheme = "amqps" if config.ssl else "amqp"
    url = URL.build(
        scheme=scheme,
        host=config.host,
        port=config.port,
        user=config.username,
        password=config.password,
        path="/" + config.virtualhost,
        query={
            "heartbeat": 10,
        },
    )

    connection = await aiormq.connect(
        url,
    )

    try:
        yield MessagingChannelFactory(connection, config.exchange)
    finally:
        await connection.close()


class MessagingChannelFactory:
    def __init__(self, connection: aiormq.abc.AbstractConnection, exchange_name: str):
        self._connection = connection
        self._exchange_name = exchange_name

    @contextlib.asynccontextmanager
    async def create(
        self, *, name: str | None = None, destination: str | None = None
    ) -> typing.AsyncIterator[MessagingChannel]:
        async with self._create(name or "", declare=True) as (channel, queue_name):
            yield MessagingChannel(channel, self._exchange_name, queue_name, destination)

    @contextlib.asynccontextmanager
    async def get(self, *, name: str, destination: str | None = None) -> typing.AsyncIterator[MessagingChannel]:
        async with self._create(name, declare=False) as (channel, queue_name):
            yield MessagingChannel(channel, self._exchange_name, queue_name, destination)

    @contextlib.asynccontextmanager
    async def _create(
        self,
        name: str,
        *,
        declare: bool,
    ) -> typing.AsyncIterator[tuple[aiormq.abc.AbstractChannel, str]]:
        logger.debug("Opening communication channel", name=name)
        channel = await self._connection.channel()
        if declare:
            resp = await channel.queue_declare(queue=name or "", auto_delete=True, exclusive=True)
            queue_name = resp.queue or ""
        else:
            queue_name = name
        _ = await channel.queue_bind(queue=queue_name, exchange=self._exchange_name, routing_key=queue_name)

        try:
            yield channel, queue_name
        finally:
            logger.debug("Closing channel")
            await channel.close()


class MessagingChannel:
    @property
    def name(self) -> str:
        return self._queue_name

    def __init__(self, channel: aiormq.abc.AbstractChannel, exchange: str, name: str, destination: str | None):
        self._channel = channel
        self._queue_name = name
        self._queue = asyncio.Queue[aiormq.abc.DeliveredMessage]()
        self._destination = destination
        self._exchange = exchange
        self._tag: str | None = None

    def set_destination(self, destination: str | None) -> None:
        self._destination = destination

    @contextlib.asynccontextmanager
    async def receive(self) -> typing.AsyncIterator[typing.AsyncIterator[Message]]:
        await self._subscribe()
        yield self._read()

    async def _subscribe(self) -> None:
        if not self._tag:
            resp = await self._channel.basic_consume(queue=self._queue_name, consumer_callback=self._queue.put)
            self._tag = resp.consumer_tag

    async def _read(self) -> typing.AsyncIterator[Message]:
        while True:
            message = await self._queue.get()
            logger.debug("Received message", message=repr(message), body=message.body.replace(b"\n", b"\\n"))
            try:
                parsed_message = parse_message(message.body, message.header.properties.reply_to)
            except pydantic.ValidationError:
                logger.exception("Ignoring message")
            else:
                logger.debug("Parsed message", body=parsed_message)
                yield parsed_message

    async def send(self, message_payload: MessageBody) -> None:
        if self._destination:
            raw_message_body = message_payload.model_dump_json().encode("utf8")
            await self._channel.basic_publish(
                raw_message_body,
                exchange=self._exchange,
                routing_key=self._destination,
                properties=aiormq.spec.Basic.Properties(reply_to=self._queue_name),
                mandatory=True,
            )

            logger.debug(
                "Sent message", body=raw_message_body, reply_to=self._queue_name, routing_key=self._destination
            )
        else:
            logger.warning("Message not send, no destination given")
