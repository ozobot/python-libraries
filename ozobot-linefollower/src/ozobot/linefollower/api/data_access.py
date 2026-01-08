from __future__ import annotations

import asyncio
import contextlib
import sys
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
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[U]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncIterator[U]:
                async for sample in reader:
                    yield self._convert(sample.value)

            yield _reader_converted()


class DataReadConstant[T]:
    def __init__(self, factory: typing.Callable[[], T]) -> None:
        self._factory = factory

    async def read(self) -> T:
        return self._factory()


# workaround for the web-python's Pyodide still having Python 3.12 which does not have `asyncio.Queue.shutdown`
#     TODO: remove when web-python has Python 3.13
if sys.version_info >= (3, 13):  # noqa: UP036
    _ShuttableQueue = asyncio.Queue
    _QueueShutDown = asyncio.QueueShutDown
else:

    class _QueueShutDown(Exception): ...

    class _ShuttableQueue[T](asyncio.Queue[T]):
        _shutdown_token = object()

        def __init__(self) -> None:
            self._shutdown = False
            super().__init__()

        def shutdown(self) -> None:
            self.put_nowait(self._shutdown_token)

        async def get(self) -> T:
            if self._shutdown:
                raise _QueueShutDown()

            v = await super().get()
            if v is self._shutdown_token:
                self._shutdown = True
                raise _QueueShutDown()

            return v


@contextlib.asynccontextmanager
async def buffered_iterator[T](
    unbuffered_iter: typing.AsyncIterator[T],
) -> typing.AsyncIterator[typing.AsyncIterator[T]]:
    """
    An async context manager consuming an async iterator and yielding a new async iterator that can be consumed even after the former one is closed.

    This is useful in cases where closing a (possibly infinite) iterator denotes an end of a lifetime of some task, but the buffered values
    are required after that happens.
    """
    q = _ShuttableQueue[T]()

    async def _queue_to_aiter() -> typing.AsyncIterator[T]:
        while True:
            try:
                yield await q.get()
            except _QueueShutDown:
                return

    async def _read_task() -> None:
        async for r in unbuffered_iter:
            await q.put(r)
        q.shutdown()

    async with asyncio.TaskGroup() as tg:
        t = tg.create_task(_read_task())
        try:
            yield _queue_to_aiter()
        finally:
            t.cancel()
            q.shutdown()
