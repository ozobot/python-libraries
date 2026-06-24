import json
import typing

import pydantic
from ozobot.ari.exceptions import DuplicateMessageIdError, MalformedMessageError, UnknownMessageIdError
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
from ozobot.jsonrpc.executor import Method


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
                if msg_id:
                    err_if_failure = UnknownMessageIdError(msg_id)
                parser = MessageTypeAdapter
            else:
                ctx = self._context[msg_id]
                if ctx.response:
                    parser = pydantic.TypeAdapter[Message](ctx.response | ctx.notification)
                else:
                    parser = pydantic.TypeAdapter[Message](ctx.notification)

            try:
                msg = deserialize(data, parser)
            except pydantic.ValidationError as err:
                if err_if_failure:
                    raise err_if_failure from err
                else:
                    raise MalformedMessageError() from err

            if isinstance(msg, Response | Cancellation | Error):
                _ = self._context.pop(msg.id)

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
