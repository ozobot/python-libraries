from __future__ import annotations

import asyncio
import contextlib
import sys
import typing

from loguru import logger
from ozobot.common.broadcast import BroadcastManager
from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.datatypes import Sample


class _Watcher[T](typing.Protocol):
    async def read(self) -> T: ...

    def watch(self) -> contextlib.AbstractAsyncContextManager[WatcherOutputContainer[Sample[T]]]: ...


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
    async def watch(self) -> typing.AsyncIterator[WatcherOutputContainer[T]]:
        with self._queue.output() as events:

            async def _reader() -> typing.AsyncGenerator[T, None]:
                while True:
                    yield await events.get()

            async with WatcherOutputContainerRunner[T]() as container_runner:
                await container_runner.start(_reader())
                yield container_runner.output_container


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
    async def watch(self) -> typing.AsyncIterator[WatcherOutputContainer[U]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncGenerator[U, None]:
                async for sample in reader:
                    yield self._convert(sample.value)

            async with WatcherOutputContainerRunner[U]() as container_runner:
                await container_runner.start(_reader_converted())
                yield container_runner.output_container


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

    try:
        async with asyncio.TaskGroup() as tg:
            t = tg.create_task(_read_task())
            try:
                yield _queue_to_aiter()
            finally:
                t.cancel()
                q.shutdown()
    except* OzobotError as e:
        # propagate the inner exception from _read_task()
        group = e.subgroup(OzobotError)
        if group:
            exceptions = group.exceptions
            if len(exceptions) > 1:
                logger.warning("Dropping exceptions", dropped_exception=exceptions[1:])
            raise exceptions[0] from e


class WatcherOutputContainer[T]:
    def __init__(self) -> None:
        self._buffer: list[T] = []
        self._data_pushed = asyncio.Condition()

    def collect(self) -> list[T]:
        return list(self._buffer)

    def __aiter__(self) -> typing.AsyncIterator[T]:
        async def _data() -> typing.AsyncIterator[T]:
            i = 0

            while True:
                while i < len(self._buffer):
                    yield self._buffer[i]
                    i += 1

                async with self._data_pushed:
                    await self._data_pushed.wait()

        return _data()

    async def _push(self, data: T) -> None:
        self._buffer.append(data)
        async with self._data_pushed:
            self._data_pushed.notify_all()


class WatcherOutputContainerRunner[T]:
    @property
    def output_container(self) -> WatcherOutputContainer[T]:
        return self._container

    def __init__(self) -> None:
        self._container = WatcherOutputContainer[T]()
        self._task: asyncio.Task[None] | None = None
        self._task_running = asyncio.Event()

    async def __aenter__(self) -> WatcherOutputContainerRunner[T]:
        return self

    async def __aexit__(self, *args) -> None:
        if self._task:
            self._task.cancel()
            await self._task

    async def start(self, it: typing.AsyncGenerator[T, None]) -> None:
        async def _run() -> None:
            self._task_running.set()
            while True:
                try:
                    data = await anext(it)
                    await self._container._push(data)
                except asyncio.CancelledError:
                    await it.aclose()
                except StopAsyncIteration:
                    return

        self._task = asyncio.create_task(_run())
        await self._task_running.wait()
