import asyncio
import contextlib
from typing import Any, AsyncIterator, Iterable
from unittest.mock import AsyncMock, seal

from ozobot.webrtc.datatypes import Message, MessageBody
from ozobot.webrtc.messaging import MessagingChannel, MessagingChannelFactory


class _MockChannel:
    def __init__(self, in_queue: asyncio.Queue[Message], out_queue: asyncio.Queue[Message]) -> None:
        self._in = in_queue
        self._out = out_queue
        self._destination: str | None = None

    def set_destination(self, destination: str) -> None:
        self._destination = destination

    async def send(self, body: MessageBody) -> None:
        message = Message(body=body, reply_to=self._destination)
        await self._out.put(message)

    @contextlib.asynccontextmanager
    async def receive(self) -> AsyncIterator[AsyncIterator[Message]]:
        yield self._receive()

    async def _receive(self) -> AsyncIterator[Message]:
        while True:
            msg = await self._in.get()
            yield msg


def create_channel_factory(
    inputs: Iterable[Message] | asyncio.Queue[Message], outputs: asyncio.Queue[Message] | None = None
) -> MessagingChannelFactory:
    if isinstance(inputs, asyncio.Queue):
        in_queue = inputs
    else:
        in_queue = asyncio.Queue()
        for input in inputs:
            in_queue.put_nowait(input)

    if not outputs:
        out_queue = in_queue
    else:
        out_queue = outputs

    factory = AsyncMock(spec=MessagingChannelFactory)

    @contextlib.asynccontextmanager
    async def _create_channel(*args: Any, **kwargs: Any) -> AsyncIterator[MessagingChannel]:
        ch = _MockChannel(in_queue, out_queue)
        yield ch  # type: ignore

    factory.create = _create_channel

    seal(factory)
    return factory
