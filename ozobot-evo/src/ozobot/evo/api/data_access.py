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


class FakeDataWatcherQueue[T]:
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


class FakeDataWatcher[T]:
    def __init__(self, queue: FakeDataWatcherQueue[T]):
        self._queue = queue

    @property
    def last(self) -> T:
        return self._queue.last

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[T]]:
        with self._queue.output() as events:

            async def _reader() -> typing.AsyncIterator[T]:
                while True:
                    yield await events.get()

            yield _reader()


class DataWatcher[T: _TimestampAndDeserializable, U]:
    def __init__(self, watcher: WatcherSubscription[T], from_protocol: typing.Callable[[T], U]) -> None:
        self._watcher = watcher
        self._from_protocol = from_protocol

    @property
    def last(self) -> Sample[U]:
        return sample_from_protocol(self._watcher.last, self._from_protocol)

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        async with self._watcher.read() as reader:

            async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
                async for r in reader:
                    yield sample_from_protocol(r, self._from_protocol)

            yield _reader_converted()
