from __future__ import annotations

import asyncio
import contextlib
import json
import typing
from uuid import UUID

import pydantic
from ozobot.ari.driver.shared import TransportBackend
from ozobot.ari.exceptions import (
    BlocklyApplicationNotResponding,
    DuplicateMessageIdError,
    MalformedMessageError,
)
from ozobot.ari.framing import FrameDecoder, encode_frame
from ozobot.ari.protocol.base import (
    CANCELLATION_MESSAGE_LABEL,
    Cancellation,
    Error,
    Message,
    Notification,
    Request,
    Response,
)
from ozobot.ari.protocol.methods import REQUEST_METHODS
from ozobot.ari.protocol.serialization import (
    MessageTypeAdapter,
    deserialize,
    serialize,
)
from ozobot.ble.connection import Client, open_client
from ozobot.ble.exceptions import DeviceDescriptionError
from ozobot.common.logging import logger
from ozobot.jsonrpc.executor import Method
from ozobot.webrtc import messaging
from ozobot.webrtc.connection import Channel, Connection
from ozobot.webrtc.signaling import negotiation, token

_ROUTING_KEY_SERVICE_UUID = UUID(
    "6b63040a-520e-4d24-0000-65c78f1d0000"
)  # taken from anvil-control/src/lib/ble-setup.ts
_ROUTING_KEY_CHARACTERISTIC_UUID = UUID("6b63040a-520e-4d24-0000-65c78f1d0001")

_CONTROL_SERVICE_UUID = UUID("13376900-0002-49e7-b877-2881c89cb258")
_CONTROL_OUTBOUND_CHARACTERISTIC_UUID = UUID("13376901-0002-49e7-b877-2881c89cb258")
_CONTROL_INBOUND_CHARACTERISTIC_UUID = UUID("13376902-0002-49e7-b877-2881c89cb258")

_ROUTING_KEY_FETCH_TIMEOUT_S: float = 5.0


class _NoRoutingKeyError(Exception):
    """Raised when the WebRTC routing key cannot be obtained from the BLE device."""


class _MessageTransport[T](typing.Protocol):
    def read(self) -> typing.AsyncIterator[T]: ...
    async def write(self, data: T) -> None: ...


class SerializingTransportLayer:
    def __init__(self, transport: _MessageTransport[str]) -> None:
        self._context: dict[int, Method[Request, Response, Notification]] = {}
        self._transport = transport

    async def write(self, message: Message | Cancellation) -> None:
        if isinstance(message, Request):
            if message.id in self._context:
                raise DuplicateMessageIdError(message.id)

            self._context[message.id] = REQUEST_METHODS[type(message)]
        elif isinstance(message, Cancellation) and message.id in self._context:
            _ = self._context.pop(message.id)

        raw = serialize(message)
        await self._transport.write(raw)

    async def read(self) -> typing.AsyncIterator[Message | Error]:
        async for data in self._transport.read():
            parsed = json.loads(data)
            msg_id = parsed.get("id", None)
            has_id = msg_id is not None
            is_request = "method" in parsed and "params" in parsed
            is_error = "error" in parsed
            err_if_failure = None
            is_cancellation = parsed.get("jsonrpc", None) == CANCELLATION_MESSAGE_LABEL
            parser = None

            if not has_id:
                # if there is no ID, we'll just parse the message as the base type to get a consistent pydantic error
                parser = pydantic.TypeAdapter(Message)
            elif is_request:
                parser = MessageTypeAdapter
            elif is_cancellation:
                parser = pydantic.TypeAdapter(Cancellation)
            elif is_error:
                parser = pydantic.TypeAdapter(Error)
            elif msg_id not in self._context:
                logger.debug("Unknown message id received, ignoring", id=msg_id)
            else:
                ctx = self._context[msg_id]
                if ctx.response:
                    parser = pydantic.TypeAdapter[Message](ctx.response | ctx.notification)
                else:
                    parser = pydantic.TypeAdapter[Message](ctx.notification)

            try:
                if parser:
                    msg = deserialize(data, parser)
                else:
                    msg = None
            except pydantic.ValidationError as err:
                if err_if_failure:
                    raise err_if_failure from err
                else:
                    raise MalformedMessageError() from err

            if isinstance(msg, Response | Cancellation | Error):
                _ = self._context.pop(msg.id)

            if msg:
                yield msg


class FramingTransportLayer:
    def __init__(self, transport: _MessageTransport[bytes]) -> None:
        self._transport = transport
        self._decoder = FrameDecoder()

    async def write(self, message: str) -> None:
        await self._transport.write(encode_frame(message.encode("utf8")))

    async def read(self) -> typing.AsyncIterator[str]:
        async for data in self._transport.read():
            for msg in self._decoder.feed(data):
                yield msg.decode("utf8")


async def _fetch_routing_key(ble_client: Client) -> str:
    try:
        char = ble_client.get_characteristic(
            _ROUTING_KEY_SERVICE_UUID,
            _ROUTING_KEY_CHARACTERISTIC_UUID,
        )
    except DeviceDescriptionError as err:
        raise BlocklyApplicationNotResponding() from err

    device_id_bytes = await char.read()
    return device_id_bytes.decode("utf8")


async def _fetch_routing_key_with_timeout(ble_client: Client) -> str:
    try:
        async with asyncio.timeout(_ROUTING_KEY_FETCH_TIMEOUT_S):
            routing_key = await _fetch_routing_key(ble_client)
    except TimeoutError as err:
        raise _NoRoutingKeyError("routing key fetch timed out") from err

    if not routing_key:
        raise _NoRoutingKeyError("empty routing key")
    return routing_key


async def _create_webrtc_channel(connection_key: str) -> tuple[Connection, Channel]:
    jwt = await token.get_jwt_token(token.TOKEN_ENDPOINT_URL, device_id=connection_key, mode="server")
    config = messaging.MessagingChannelConfig(device_id=connection_key, username="", password=jwt)
    async with messaging.create_channel_factory(config) as channel_factory:
        client = negotiation.SignalingCaller(channel_factory, connection_key)
        connection, channels = await client.signal(channels=("control",))

    return connection, channels[0]


class _WebrtcTransportAdapter:
    def __init__(self, channel: Channel) -> None:
        self._channel = channel

    async def write(self, data: str) -> None:
        logger.debug("Sending message", message=data)
        await self._channel.send(data)

    async def read(self) -> typing.AsyncIterator[str]:
        async for raw_data in self._channel.receive_str():
            logger.debug("Received message", message=raw_data)
            yield raw_data


@contextlib.asynccontextmanager
async def _webrtc_transport_from_routing_key(routing_key: str) -> typing.AsyncIterator[_WebrtcTransportAdapter]:
    connection, channel = await _create_webrtc_channel(routing_key)
    try:
        yield _WebrtcTransportAdapter(channel)
    finally:
        channel.close()
        await connection.close()


@contextlib.asynccontextmanager
async def _create_webrtc_transport(
    *,
    address: str | None = None,
    id: str | None = None,
    name: str | None = None,
    connection_key: str | None = None,
) -> typing.AsyncIterator[_WebrtcTransportAdapter]:
    if connection_key:
        routing_key = f"anvil.{connection_key}"
    else:
        async with open_client(address=address, id=id, name=name, product="ari") as ble_client:
            routing_key = await _fetch_routing_key_with_timeout(ble_client)

    async with _webrtc_transport_from_routing_key(routing_key) as transport:
        yield transport


class _BleTransport:
    """BLE transport with 4-byte length-prefix framing and MTU-aware write chunking.

    Writes go to the outbound characteristic; reads come from inbound characteristic
    notifications. Implements _MessageTransport[str] for use with SerializingTransportLayer.
    """

    _LENGTH_PREFIX_SIZE = 4

    def __init__(
        self,
        write_session: _MessageTransport[bytes],
        read_session: _MessageTransport[bytes],
        packet_size_max: int,
    ) -> None:
        self._write_session = write_session
        self._read_session = read_session
        self._packet_size_max = packet_size_max
        self._write_lock = asyncio.Lock()

    async def read(self) -> typing.AsyncIterator[str]:
        buffer = bytearray()
        expected: int | None = None
        async for data in self._read_session.read():
            buffer += data
            while True:
                if expected is None:
                    if len(buffer) < self._LENGTH_PREFIX_SIZE:
                        break
                    expected = int.from_bytes(buffer[: self._LENGTH_PREFIX_SIZE], "big")
                    del buffer[: self._LENGTH_PREFIX_SIZE]
                if len(buffer) < expected:
                    break
                message = bytes(buffer[:expected])
                del buffer[:expected]
                expected = None
                logger.debug("Received message", message=message.decode("utf8"))
                yield message.decode("utf8")

    async def write(self, data: str) -> None:
        async with self._write_lock:
            logger.debug("Sending message", message=data)
            payload = data.encode("utf8")
            frame = len(payload).to_bytes(self._LENGTH_PREFIX_SIZE, "big") + payload
            for offset in range(0, len(frame), self._packet_size_max):
                await self._write_session.write(frame[offset : offset + self._packet_size_max])


@contextlib.asynccontextmanager
async def _create_ble_transport_from_client(ble_client: Client) -> typing.AsyncIterator[_BleTransport]:
    try:
        outbound_char = ble_client.get_characteristic(
            _CONTROL_SERVICE_UUID,
            _CONTROL_OUTBOUND_CHARACTERISTIC_UUID,
        )
        inbound_char = ble_client.get_characteristic(
            _CONTROL_SERVICE_UUID,
            _CONTROL_INBOUND_CHARACTERISTIC_UUID,
        )
    except DeviceDescriptionError as err:
        raise BlocklyApplicationNotResponding() from err

    async with outbound_char.open_session() as write_session, inbound_char.open_session() as read_session:
        yield _BleTransport(write_session, read_session, outbound_char.packet_size_max)


@contextlib.asynccontextmanager
async def _create_ble_transport(
    *,
    address: str | None = None,
    id: str | None = None,
    name: str | None = None,
    client: Client | None = None,
) -> typing.AsyncIterator[_BleTransport]:
    if client is not None:
        async with _create_ble_transport_from_client(client) as transport:
            yield transport
    else:
        async with open_client(address=address, id=id, name=name, product="ari") as ble_client:
            async with _create_ble_transport_from_client(ble_client) as transport:
                yield transport


@contextlib.asynccontextmanager
async def _create_auto_transport(
    *,
    address: str | None = None,
    id: str | None = None,
    name: str | None = None,
) -> typing.AsyncIterator[_WebrtcTransportAdapter | _BleTransport]:
    async with open_client(address=address, id=id, name=name, product="ari") as ble_client:
        try:
            routing_key = await _fetch_routing_key_with_timeout(ble_client)
        except (BlocklyApplicationNotResponding, _NoRoutingKeyError):
            async with _create_ble_transport_from_client(ble_client) as transport:
                yield transport
            return

    async with _webrtc_transport_from_routing_key(routing_key) as transport:
        yield transport


@contextlib.asynccontextmanager
async def _open_transport(
    *,
    address: str | None,
    id: str | None,
    name: str | None,
    connection_key: str | None,
    transport_backend: TransportBackend,
) -> typing.AsyncIterator[_MessageTransport[str]]:
    if connection_key is not None and transport_backend != "webrtc":
        raise ValueError("connection_key can only be used together with 'webrtc' transport backend")

    if transport_backend == "ble":
        async with _create_ble_transport(address=address, id=id, name=name) as transport:
            yield transport

    elif transport_backend == "webrtc":
        async with _create_webrtc_transport(
            address=address,
            id=id,
            name=name,
            connection_key=connection_key,
        ) as transport:
            yield transport

    else:
        async with _create_auto_transport(address=address, id=id, name=name) as transport:
            yield transport
