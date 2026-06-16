from __future__ import annotations

import asyncio
import contextlib
import typing

from ozobot.common.broadcast import BroadcastManager
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


class DataWatcherDeduplicated[T]:
    def __init__(
        self,
        watcher: _Watcher[T],
        *,
        convert_to_comparable: typing.Callable[[Sample[T]], typing.Any],
    ) -> None:
        self._watcher = watcher
        self._convert_to_comparable = convert_to_comparable

    async def read(self) -> T:
        return await self._watcher.read()

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[WatcherOutputContainer[Sample[T]]]:
        async with self._watcher.watch() as reader:

            async def _reader_deduplicated() -> typing.AsyncGenerator[Sample[T], None]:
                previous_value = object()
                async for sample in reader:
                    compared_value = self._convert_to_comparable(sample)
                    if compared_value != previous_value:
                        yield sample

                    previous_value = compared_value

            async with WatcherOutputContainerRunner[Sample[T]]() as container_runner:
                await container_runner.start(_reader_deduplicated())
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

    def __init__(self) -> None:
        self._container = WatcherOutputContainer[T]()
        self._task: asyncio.Task | None = None
        self._base_task = asyncio.current_task()
        self._task_running = asyncio.Event()

    async def __aenter__(self) -> WatcherOutputContainerRunner[T]:
        return self

    async def __aexit__(self, *args) -> None:
        if self._task:
            self._task.remove_done_callback(self._on_task_done)
            if not self._task.done():
                self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    def _on_task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return

        self._task_exception = task.exception()

        if self._base_task and not self._base_task.done():
            self._base_task.cancel()

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
        self._task.add_done_callback(self._on_task_done)
        await self._task_running.wait()
