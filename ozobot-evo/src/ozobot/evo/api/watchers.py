from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass

from ozobot.common.broadcast import BroadcastManager
from ozobot.common.logging import logger
from ozobot.evo.driver.responses import handle_response
from ozobot.evo.protocol import AsyncControl, PacketTypes, Types, VirtualMemory


class _Deserializable(typing.Protocol):
    @classmethod
    def deserialize(cls, data: bytes) -> typing.Self: ...


@dataclass(frozen=True, kw_only=True)
class _WatcherAllocation[T]:
    watcher_id: int
    region_id: int
    address: int
    size: int
    type: type[T]


@dataclass(frozen=True, kw_only=True)
class _WatcherAllocationSummary:
    used_regions: list[int]
    num_used_bytes: int


class _SubscriptionInfo[T](typing.Protocol):
    address: int
    type: type[T]

    @property
    def size(self) -> int: ...


class RefCountedWatcher[T: _Deserializable]:
    def __init__(self, type: _SubscriptionInfo[T], manager: WatcherManager) -> None:
        self._type = type
        self._ref_count = 0
        self._watcher: _WatcherSubscription[T] | None = None
        self._manager = manager
        self._open_close_lock = asyncio.Lock()

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[T]]:
        async with self._open_close_lock:
            if self._watcher is None:
                watcher = await self._manager.enable(self._type)
                self._watcher = watcher
            else:
                watcher = self._watcher
            self._ref_count += 1

        try:
            assert watcher.broadcast is not None
            with watcher.broadcast.output() as output:

                async def _iter() -> typing.AsyncIterator[T]:
                    while True:
                        try:
                            yield await output.get()
                        except asyncio.QueueShutDown:
                            return

                yield _iter()
        finally:
            async with self._open_close_lock:
                self._ref_count -= 1
                if self._ref_count == 0:
                    await self._manager.disable(self._watcher)
                    self._watcher = None


class WatcherAllocator:
    """
    Watcher and region allocator.
    """

    def __init__(self, watcher_count: int, region_count: int, packet_size_max: int) -> None:
        self._watcher_count = watcher_count
        self._region_count = region_count
        self._packet_size_max = packet_size_max
        self._allocations: dict[int, list[_WatcherAllocation]] = {watcher_id: [] for watcher_id in range(watcher_count)}

    def allocate[T](self, size: int, address: int, _type: type[T]) -> _WatcherAllocation[T]:
        watcher_id, region_id = self._find_free_gap(size)
        allocation = _WatcherAllocation(
            watcher_id=watcher_id, region_id=region_id, size=size, address=address, type=_type
        )
        self._allocations[watcher_id].append(allocation)

        return allocation

    def deallocate(self, allocation: _WatcherAllocation) -> None:
        self._allocations[allocation.watcher_id].remove(allocation)

    def _find_free_gap(self, size: int) -> tuple[int, int]:
        max_size = self._packet_size_max - PacketTypes.PacketEvent_WatcherDirty.expected_length(None)

        logger.debug("Searching for free gap", size=size, max_size=max_size, allocations=self._allocations)
        allocation_summary = {
            watcher_id: _WatcherAllocationSummary(
                used_regions=[a.region_id for a in self._allocations.get(watcher_id, [])],
                num_used_bytes=sum([a.size for a in self._allocations.get(watcher_id, [])]),
            )
            for watcher_id in range(self._watcher_count)
        }

        # filter out watchers with no regions left or not enough free packet size
        available_watchers = {
            watcher_id: summary
            for watcher_id, summary in allocation_summary.items()
            if len(summary.used_regions) < self._region_count and max_size - summary.num_used_bytes >= size
        }

        logger.debug("Available watchers", available_watchers=available_watchers)

        # find watcher with lowest free memory (smallest gap) to prevent fragmentation
        watcher_id, watcher_allocation = max(
            available_watchers.items(), default=(None, None), key=lambda e: e[1].num_used_bytes
        )
        if watcher_id is None or watcher_allocation is None:
            raise Exception("No free watcher found")

        # get the first unused
        unused_region_ids = set(range(self._region_count)) - set(watcher_allocation.used_regions)
        region_id = min(unused_region_ids)

        return watcher_id, region_id


class PeekableAiter[T]:
    def __init__(self, aiter: typing.AsyncIterator[T]) -> None:
        self._aiter = aiter
        self._peeked: T | None = None

    async def __anext__(self) -> T:
        if self._peeked:
            p = self._peeked
            self._peeked = None
            return p

        return await anext(self._aiter)

    async def peek(self) -> T:
        if self._peeked:
            return self._peeked

        p = await anext(self._aiter)
        self._peeked = p
        return p


@dataclass(frozen=True, kw_only=True)
class _WatcherSubscription[T]:
    broadcast: BroadcastManager[T] | None
    allocation: _WatcherAllocation[T]


def _flatten(eg: BaseExceptionGroup) -> BaseException:
    """
    Reduce a (possibly nested) exception group to a single flat exception.

    The first non-cancellation leaf (the original failure) is returned; any other non-cancellation leaves are logged so
    they are not silently lost. Cancellation exceptions are only returned if there is nothing else.
    """
    leaves: list[BaseException] = []

    def _collect(exc: BaseException) -> None:
        if isinstance(exc, BaseExceptionGroup):
            for sub in exc.exceptions:
                _collect(sub)
        else:
            leaves.append(exc)

    _collect(eg)

    non_cancelled = [exc for exc in leaves if not isinstance(exc, asyncio.CancelledError)]
    chosen = non_cancelled[0] if non_cancelled else leaves[0]

    for other in non_cancelled:
        if other is not chosen:
            logger.exception("Additional watcher failure suppressed", exc_info=other)

    return chosen


class WatcherManager:
    """
    Watcher (de)initialization.

    If opening a new watcher is requested, the manager makes sure it's not already open, allocates watcher and region, sets up the watchers and
    returns the new watching entity. In case the watcher is already set up, a cached copy is returned.

    Reference counting is used to keep track
    """

    @classmethod
    @contextlib.asynccontextmanager
    async def open(cls, control: AsyncControl) -> typing.AsyncIterator[WatcherManager]:
        """
        Open a `WatcherManager` bound to ``control`` as an async context manager.

        The per-watcher background tasks are owned by an :py:class:`asyncio.TaskGroup` that lives for the duration
        of the context. If any watcher task fails, the task group cancels the task that opened the manager (i.e. the
        task that opened the driver) and the failure is re-raised from this context manager's ``__aexit__`` as a flat
        exception (the first non-cancellation failure), rather than an :py:class:`ExceptionGroup`.
        """
        metadata = VirtualMemory.watchersInfo
        async with control.MemRead(metadata.address, metadata.type.data_width) as (resp, _):
            handle_response("MemRead", resp)
        watcher_info = metadata.type.deserialize(bytes(resp.data))
        allocator = WatcherAllocator(
            watcher_info.watcherCount, watcher_info.watcherRegionCount, control.packet_size_max
        )
        self = cls(control, allocator)

        try:
            async with asyncio.TaskGroup() as tg:
                self._tg = tg
                yield self
                # normal close: stop the never-ending per-watcher loops and wait for their teardown to finish
                self._closing = True
                tasks = list(self._watcher_tasks.values())
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except BaseExceptionGroup as eg:
            raise _flatten(eg) from None

    def __init__(self, control: AsyncControl, allocator: WatcherAllocator) -> None:
        """
        Instantiate `WatcherManager`.

        .. seealso::
            A helper class method :py:meth:`WatcherManager.open` that initializes dependencies and owns the
            per-watcher task group.
        """

        self._control = control
        self._allocator = allocator
        self._allocator_lock = asyncio.Lock()
        self._tg: asyncio.TaskGroup | None = None
        self._closing = False
        self._watcher_tasks: dict[int, asyncio.Task] = {}

        self._subscriptions: dict[int, list[_WatcherSubscription]] = {}
        """Per-watcher subscriptions, one per watched region. List of subscriptions indexed by watcher id."""

    async def enable[T: _Deserializable](self, subs: _SubscriptionInfo[T]) -> _WatcherSubscription[T]:
        if self._closing or self._tg is None:
            raise RuntimeError("WatcherManager is not open")

        async with self._allocator_lock:
            allocation = self._allocator.allocate(subs.size, subs.address, subs.type)

            # start per-watcher task if not running
            if allocation.watcher_id not in self._watcher_tasks:
                update_counter_region_id = await self._enable_update_counter_region(allocation.watcher_id)
                task = self._tg.create_task(self._watch(allocation.watcher_id, update_counter_region_id))
                self._watcher_tasks[allocation.watcher_id] = task

            handle = await self._configure_region(allocation, broadcast=BroadcastManager[T]())
            return handle

    async def disable(self, subs: _WatcherSubscription) -> None:
        async with self._allocator_lock:
            await self._deconfigure_region(subs.allocation)
            self._allocator.deallocate(subs.allocation)

            watcher_id = subs.allocation.watcher_id
            self._subscriptions[watcher_id].remove(subs)

            # check if any user subscriptions remain (counter subscriptions have broadcast=None)
            user_subs_remaining = any(s.broadcast is not None for s in self._subscriptions[watcher_id])
            if not user_subs_remaining:
                self._watcher_tasks.pop(watcher_id).cancel()

    async def _enable_update_counter_region(self, watcher_id: int) -> int:
        size = VirtualMemory.watcherUpdateCounters.type.data_width
        address = VirtualMemory.watcherUpdateCounters.address + watcher_id * size
        allocation = self._allocator.allocate(size, address, VirtualMemory.watcherUpdateCounters.type)
        handle = await self._configure_region(allocation, flags=Types.WatcherRegionFlags.DoNotSetDirty, broadcast=None)

        return handle.allocation.region_id

    async def _watch[T: _Deserializable](self, watcher_id: int, update_counter_region_id: int) -> None:
        async with self._watcher(watcher_id) as it_raw:
            it = PeekableAiter(it_raw)

            while True:
                subscriptions = sorted(self._subscriptions[watcher_id], key=lambda s: s.allocation.region_id)
                allocation_update_counter = await self._read_update_counter(watcher_id)
                last_update_counter = allocation_update_counter
                logger.debug("Reading watcher updates", update_counter=allocation_update_counter)

                def _parse_update_counter(data: bytes, subs: list[_WatcherSubscription]) -> Types.u8:
                    counter_sub = next(s for s in subs if s.broadcast is None)
                    preceding_sizes = sum(
                        [s.allocation.size for s in subs if s.allocation.region_id < counter_sub.allocation.region_id]
                    )
                    counter_data = bytes([data[preceding_sizes]])
                    return Types.u8.deserialize(counter_data)

                while allocation_update_counter == last_update_counter:
                    peeked_event = await it.peek()
                    update_counter = _parse_update_counter(peeked_event.data, subscriptions)

                    # if the counter does not match, the region has been updated,
                    #     leave the data be for the next cycle
                    if update_counter == allocation_update_counter:
                        event = await anext(it)
                        await self._send_parsed_data(bytes(event.data), subscriptions)

                    last_update_counter = update_counter

    async def _read_update_counter(self, watcher_id: int) -> int:
        size = VirtualMemory.watcherUpdateCounters.type.data_width
        address = VirtualMemory.watcherUpdateCounters.address + watcher_id * size

        async with self._control.MemRead(address, size) as (resp, _):
            data = bytes(resp.data)
            return Types.u8.deserialize(data)

    async def _send_parsed_data(self, event_data: bytes, subscriptions: list[_WatcherSubscription]) -> None:
        sorted_subscriptions = sorted(subscriptions, key=lambda s: s.allocation.region_id)
        total_size = sum([a.allocation.size for a in subscriptions])
        if len(event_data) < total_size:
            logger.warning("WatcherDirty event length wrong, skipping", expected=total_size, actual=len(event_data))
            return

        offset = 0
        for subs in sorted_subscriptions:
            event_slice = event_data[offset : offset + subs.allocation.size]
            offset += subs.allocation.size
            if subs.broadcast is not None:
                parsed_data = subs.allocation.type.deserialize(event_slice)
                await subs.broadcast.broadcast(parsed_data)

    @contextlib.asynccontextmanager
    async def _watcher(
        self, watcher_id: int
    ) -> typing.AsyncIterator[typing.AsyncIterator[PacketTypes.PacketEvent_WatcherDirty]]:
        logger.debug("Initializing watcher", watcher_id=watcher_id)
        flags = Types.WatcherFlags.Enabled | Types.WatcherFlags.DisableWhenDisconnected

        try:
            async with self._control.WatcherSetup(watcher_id, flags, 40, 0) as (resp, events):
                handle_response("WatcherSetup", resp)
                yield events
        finally:
            logger.debug("Deinitializing watcher", watcher_id=watcher_id)
            async with self._control.WatcherSetup(watcher_id, Types.WatcherFlags(0), 0, 0) as (resp, _):
                handle_response("WatcherSetup", resp)

    async def _configure_region[T: _Deserializable](
        self,
        allocation: _WatcherAllocation[T],
        *,
        flags: Types.WatcherRegionFlags | None = None,
        broadcast: BroadcastManager[T] | None = None,
    ) -> _WatcherSubscription[T]:
        logger.debug("Initializing watcher region", watcher_id=allocation.watcher_id, region_id=allocation.region_id)
        region_setup_rpc = self._control.WatcherRegionSetup(
            allocation.watcher_id,
            allocation.region_id,
            allocation.address,
            allocation.size,
            flags=flags or Types.WatcherRegionFlags(0),
        )

        async with region_setup_rpc as (resp, _):
            handle_response("WatcherRegionSetup", resp)

        handle = _WatcherSubscription(broadcast=broadcast, allocation=allocation)
        self._subscriptions.setdefault(allocation.watcher_id, []).append(handle)
        return handle

    async def _deconfigure_region(self, allocation: _WatcherAllocation) -> None:
        logger.debug("Deinitializing watcher region", watcher_id=allocation.watcher_id, region_id=allocation.region_id)
        flags = Types.WatcherRegionFlags.DoNotSendInNotify | Types.WatcherRegionFlags.DoNotSetDirty
        async with self._control.WatcherRegionSetup(allocation.watcher_id, allocation.region_id, 0, 0, flags=flags) as (
            resp,
            _,
        ):
            handle_response("WatcherRegionSetup", resp)
