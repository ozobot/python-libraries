import asyncio
import typing

from loguru import logger
from ozobot.jsonrpc.framing import FrameDecoder, encode_frame


class Reader[T]:
    def __init__(self, reader: asyncio.StreamReader, deserializer: typing.Callable[[bytes], T]) -> None:
        self._frame_decoder = FrameDecoder()
        self._reader = reader
        self._deserialize = deserializer

    async def read(self) -> typing.AsyncIterator[T]:
        while True:
            data = await self._reader.read(256)
            logger.debug("Read data", len=len(data))

            for raw_message in self._frame_decoder.feed(data):
                logger.debug("Decoded data", len=len(raw_message))
                message = self._deserialize(raw_message)

                logger.debug("Parsed message", message=message)
                yield message


class Writer[T]:
    def __init__(self, writer: asyncio.StreamWriter, serializer: typing.Callable[[T], bytes]) -> None:
        self._writer = writer
        self._serialize = serializer

    async def write(self, message: T) -> None:
        message_raw = self._serialize(message)
        message_encoded = encode_frame(message_raw)
        self._writer.write(message_encoded)
        await self._writer.drain()
