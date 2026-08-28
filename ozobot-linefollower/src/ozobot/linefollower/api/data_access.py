from __future__ import annotations

import asyncio
import contextlib
import typing

from ozobot.common.asyncutils import BackgroundTask
from ozobot.common.broadcast import BroadcastManager
from ozobot.linefollower.conversions import _HasTimestamp


class _Watcher[T](typing.Protocol):
    async def read(self) -> T: ...

    def watch(self) -> contextlib.AbstractAsyncContextManager[WatcherOutputContainer[T]]: ...


async def deduplicate_samples[T: _HasTimestamp](
    it: typing.AsyncIterator[T], initial_value: float | None = None
) -> typing.AsyncGenerator[T]:
    """
    Deduplicates consecutive samples by timestamp:

    :param it: iterator to deduplicate
    :param initial_value: if set, an initial value that is not yielded by the iterator
    """

    if initial_value is not None:
        last_timestamp = initial_value
    else:
        last_val = await anext(it)
        yield last_val
        last_timestamp = last_val.timestamp

    async for val in it:
        timestamp = val.timestamp
        if timestamp != last_timestamp:
            yield val
        last_timestamp = timestamp


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


class DataWatcherProxy[T: _HasTimestamp, U]:
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
                async for value in deduplicate_samples(aiter(reader)):
                    yield self._convert(value)

            async with WatcherOutputContainerRunner[U]() as container_runner:
                await container_runner.start(_reader_converted())
                yield container_runner.output_container


class DataReadConstant[T]:
    def __init__(self, factory: typing.Callable[[], T]) -> None:
        self._factory = factory

    async def read(self) -> T:
        return self._factory()


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

    def __init__(self, *, skip_initial_value: bool = False) -> None:
        self._container = WatcherOutputContainer[T]()
        self._background_task = BackgroundTask()
        self._task_running = asyncio.Event()
        self._skip_initial_value = skip_initial_value

    async def __aenter__(self) -> typing.Self:
        await self._background_task.__aenter__()
        return self

    async def __aexit__(self, *args) -> None:
        await self._background_task.__aexit__(*args)

    async def start(self, it: typing.AsyncGenerator[T, None]) -> None:
        async def _run() -> None:
            self._task_running.set()
            if self._skip_initial_value:
                _ = await anext(it)  # drop initial value
            while True:
                try:
                    data = await anext(it)
                    await self._container._push(data)
                except asyncio.CancelledError:
                    await it.aclose()
                except StopAsyncIteration:
                    return

        self._background_task.start(_run())
        await self._task_running.wait()
