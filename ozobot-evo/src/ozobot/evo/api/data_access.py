import asyncio
import contextlib
import typing

from ozobot.common.broadcast import BroadcastManager
from ozobot.evo.api.watchers import WatcherSubscription
from ozobot.evo.conversions import sample_from_protocol
from ozobot.evo.datatypes import Sample
from ozobot.evo.driver.driver import Deserializable, Driver, MemoryProperty


class _HasTimestamp(typing.Protocol):
    timestamp: int


class _TimestampAndDeserializable(_HasTimestamp, Deserializable, typing.Protocol):
    pass


class DataAccessRead[T: _TimestampAndDeserializable, U]:
    def __init__(self, driver: Driver, property: MemoryProperty[T], from_protocol: typing.Callable[[T], U]) -> None:
        self._driver = driver
        self._property = property
        self._from_protocol = from_protocol

    async def read(self) -> Sample[U]:
        val = await self._driver.mem_read(self._property)
        return sample_from_protocol(val, self._from_protocol)


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


class DataWatcher[T: _TimestampAndDeserializable, U]:
    def __init__(
        self,
        driver: Driver,
        property: MemoryProperty[T],
        watcher: WatcherSubscription[T],
        from_protocol: typing.Callable[[T], U],
    ) -> None:
        self._watcher = watcher
        self._reader = DataAccessRead(driver, property, from_protocol)
        self._from_protocol = from_protocol

    async def read(self) -> Sample[U]:
        return await self._reader.read()

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
                async for r in reader:
                    yield sample_from_protocol(r, self._from_protocol)

            yield _reader_converted()
