from __future__ import annotations

import asyncio
import contextlib
import typing

from ozobot.common.broadcast import BroadcastManager
from ozobot.linefollower.datatypes import Sample


class _Watcher[T](typing.Protocol):
    async def read(self) -> T: ...

    def watch(self) -> contextlib.AbstractAsyncContextManager[typing.AsyncIterator[Sample[T]]]: ...


class EventWatcherQueue[T]:
    def __init__(self, initial_value: T) -> None:
        self.last = initial_value
        self._broadcast = BroadcastManager[T]()

    async def write(self, value: T) -> None:
        self.last = value
        await self._broadcast.broadcast(value)

    @contextlib.contextmanager
    def output(self) -> typing.Iterator[asyncio.Queue[T]]:
        with self._broadcast.output() as out:
            yield out


class EventWatcher[T]:
    def __init__(self, queue: EventWatcherQueue[T]):
        self._queue = queue

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[T]]:
        with self._queue.output() as events:

            async def _reader() -> typing.AsyncIterator[T]:
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

    async def read(self) -> U:
        value = await self._watcher.read()
        return self._convert(value)

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
                async for sample in reader:
                    yield Sample(self._convert(sample.value), sample.timestamp)

            yield _reader_converted()


class DataReadConstant[T]:
    def __init__(self, factory: typing.Callable[[], T]) -> None:
        self._factory = factory

    async def read(self) -> T:
        return self._factory()
