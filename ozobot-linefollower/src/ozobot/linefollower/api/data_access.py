from __future__ import annotations

import asyncio
import contextlib
import typing

from ozobot.common.broadcast import BroadcastManager
from ozobot.linefollower.datatypes import Sample


class _Watcher[T](typing.Protocol):
    async def read(self) -> Sample[T]: ...

    def watch(self) -> contextlib.AbstractAsyncContextManager[typing.AsyncIterator[Sample[T]]]: ...


class EventWatcherQueue[T]:
    def __init__(self, initial_value: Sample[T]) -> None:
        self.last = initial_value
        self._broadcast = BroadcastManager[Sample[T]]()

    async def write(self, value: Sample[T]) -> None:
        self.last = value
        await self._broadcast.broadcast(value)

    @contextlib.contextmanager
    def output(self) -> typing.Iterator[asyncio.Queue[Sample[T]]]:
        with self._broadcast.output() as out:
            yield out


class EventWatcher[T]:
    def __init__(self, queue: EventWatcherQueue[T]):
        self._queue = queue

    async def read(self) -> Sample[T]:
        return self._queue.last

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[T]]]:
        with self._queue.output() as events:

            async def _reader() -> typing.AsyncIterator[Sample[T]]:
                while True:
                    yield await events.get()

            yield _reader()


class DataWatcherProxy[T, U]:
    def __init__(
        self,
        watcher: _Watcher[T],
        *,
        convert: typing.Callable[[T], U],
    ) -> None:
        self._watcher = watcher
        self._convert = convert

    async def read(self) -> Sample[U]:
        sample = await self._watcher.read()
        return Sample(self._convert(sample.data), sample.timestamp)

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
                async for sample in reader:
                    yield Sample(self._convert(sample.data), sample.timestamp)

            yield _reader_converted()
