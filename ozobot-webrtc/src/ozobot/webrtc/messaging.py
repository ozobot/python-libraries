from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import ssl
import typing

import aiormq
import pydantic
import websockets
from ozobot.common.logging import logger
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
    port: int = dataclasses.field(default=15671)
    virtualhost: str = dataclasses.field(default="webrtc-signaling")
    exchange: str = dataclasses.field(default="webrtc-signaling")
    transport: typing.Literal["websocket", "tcp"] = dataclasses.field(default="websocket")


class WebsocketTransport(asyncio.transports.Transport):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        protocol: asyncio.StreamReaderProtocol,
        url: URL,
        ssl_context: ssl.SSLContext | None,
        extra: dict | None = None,
    ) -> None:
        super().__init__(extra)
        assert url.scheme in {"ws", "wss"}
        self.url = url

        self._loop = loop
        self._protocol = protocol
        self._ssl_context = ssl_context
        self._closing = False  # Set when close() or write_eof() called.
        self._paused = False
        self._paused_lock = asyncio.Lock()

        self._task = self._loop.create_task(self._handle_connection())

        self._write_queue = asyncio.Queue[bytes | str]()
        self._read_queue = asyncio.Queue[bytes | str]()

    async def _handle_connection(self) -> None:
        try:
            async with (
                asyncio.TaskGroup() as tg,
                websockets.connect(str(self.url), ssl=self._ssl_context) as connection,
            ):
                coros = [
                    self._handle_sending(connection),
                    self._handle_receiving(connection),
                    self._flush_receive_queue(),
                    connection.wait_closed(),
                ]
                tasks = [tg.create_task(coro) for coro in coros]
                _ = await asyncio.wait(
                    tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for t in tasks:
                    logger.debug("Websocket task completed", task=t)
                    # if t.done() and t.exception():
                    #     logger.debug("Websocket task raised an exception", task=t)
                    #     ex = t.exception()
                    #     if ex:
                    #         raise ex
                    # else:
                    # logger.debug("Cancelling Websocket task", task=t)
                    t.cancel()

        except websockets.exceptions.WebSocketException as err:
            logger.error("Websocket error encountered", error=err)
            err.__cause__ = aiormq.AMQPConnectionError()
            self._protocol.connection_lost(err)
        except Exception as e:
            logger.error("Websocket connection error", error=e)
            self._protocol.connection_lost(e)
        finally:
            self._protocol.connection_lost(None)

    async def _handle_sending(self, ws: websockets.asyncio.client.ClientConnection) -> None:
        while True:
            data = await self._write_queue.get()
            await ws.send(data)

    async def _handle_receiving(self, ws: websockets.asyncio.client.ClientConnection) -> None:
        async for msg in ws:
            if isinstance(msg, str):
                msg = msg.encode()
            await self._read_queue.put(msg)

        self._read_queue.shutdown()

    async def _flush_receive_queue(self) -> None:
        while True:
            async with self._paused_lock:
                try:
                    msg = await self._read_queue.get()
                except asyncio.QueueShutDown:
                    self._protocol.eof_received()
                    return

                self._protocol.data_received(msg if isinstance(msg, bytes) else msg.encode("utf8"))

    def get_protocol(self) -> asyncio.BaseProtocol:
        return self._protocol

    def set_protocol(self, protocol: asyncio.BaseProtocol) -> None:
        raise NotImplementedError()

    def is_closing(self) -> bool:
        return self._closing

    def write(self, data: typing.Any) -> None:
        self._write_queue.put_nowait(data)

    def is_reading(self) -> bool:
        return not self._paused and not self._closing

    def pause_reading(self):
        if not self._paused:
            asyncio.get_event_loop().call_soon(self._paused_lock.acquire)
        self._paused = True
        if self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self) -> None:
        if self._paused:
            self._paused_lock.release()
        if self._closing or not self._paused:
            return
        self._paused = False
        if self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    def can_write_eof(self) -> bool:
        return False

    def close(self) -> None:
        self._closing = True
        self._task.cancel()
        self._protocol.connection_lost(None)


class WebsocketTransportFactory(aiormq.TransportFactory):
    async def create(
        self, url: URL, **kwargs: dict[str, typing.Any]
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)

        if url.scheme == "wss":
            ssl_context_provider = typing.cast(aiormq.SSLContextProvider, kwargs.get("ssl_context_provider"))
            ssl_context = await ssl_context_provider.get_context()
        else:
            _ = kwargs.pop("ssl_context_provider", None)
            ssl_context = None
        transport = WebsocketTransport(loop, protocol, url, ssl_context=ssl_context, extra=kwargs)
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)

        return reader, writer


@contextlib.asynccontextmanager
async def create_channel_factory(config: MessagingChannelConfig) -> typing.AsyncIterator[MessagingChannelFactory]:
    transport_factory = WebsocketTransportFactory() if config.transport == "websocket" else None
    match config.transport, config.ssl:
        case "tcp", True:
            scheme = "amqps"
        case "tcp", False:
            scheme = "amqp"
        case "websocket", True:
            scheme = "wss"
        case "websocket", False:
            scheme = "ws"

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
        transport_factory=transport_factory,
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
