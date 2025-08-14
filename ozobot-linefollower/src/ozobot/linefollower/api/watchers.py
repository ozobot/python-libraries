from __future__ import annotations

import asyncio
import contextlib
import typing
import uuid
from dataclasses import dataclass

from loguru import logger
from ozobot.common.broadcast import BroadcastManager
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

    @property
    def end(self) -> int:
        return self.address + self.end


@dataclass(frozen=True, kw_only=True)
class _WatcherAllocationSummary:
    used_regions: list[int]
    num_used_bytes: int


class _SubscriptionInfo[T](typing.Protocol):
    address: int
    type: type[T]

    @property
    def size(self) -> int: ...


class WatcherSubscription[T: _Deserializable]:
    @property
    def last(self) -> T:
        return self._last_value

    def __init__(self, initial_value: T) -> None:
        self._broadcast = BroadcastManager[T]()
        self._last_value = initial_value

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[T]]:
        with self._broadcast.output() as output:

            async def _read() -> typing.AsyncIterator[T]:
                while True:
                    yield await output.get()

            yield _read()

    @classmethod
    @contextlib.asynccontextmanager
    async def run(
        cls,
        events: typing.AsyncIterator[PacketTypes.PacketEvent_WatcherDirty],
        allocations: list[_WatcherAllocation],
        allocation: _WatcherAllocation[T],
    ) -> typing.AsyncIterator[WatcherSubscription[T]]:
        async with asyncio.TaskGroup() as tg:
            parsed_events = cls._parse(events, allocations, allocation)
            initial_value = await anext(parsed_events)
            subs = WatcherSubscription(initial_value)
            process_task = tg.create_task(subs._process(parsed_events))

            try:
                yield subs
            finally:
                process_task.cancel()
                await process_task

    @classmethod
    async def _parse(
        cls,
        events: typing.AsyncIterator[PacketTypes.PacketEvent_WatcherDirty],
        allocations: list[_WatcherAllocation],
        allocation: _WatcherAllocation[T],
    ) -> typing.AsyncGenerator[T]:
        logger.debug("finding offset", allocation=allocation, allocations=allocations)
        watcher_regions = list(filter(lambda e: e.watcher_id == allocation.watcher_id, allocations))
        preceding_regions = list(filter(lambda e: e.region_id < allocation.region_id, watcher_regions))

        logger.debug("computing offset", regions=preceding_regions)
        expected_len = sum(a.size for a in watcher_regions)
        offset = sum(r.size for r in preceding_regions)
        logger.debug("got offset", offset=offset, size=allocation.size)

        async for event in events:
            data = bytes(event.data)

            if len(data) != expected_len:
                logger.warning("WatcherDirty event length wrong, skipping", expected=expected_len, actual=len(data))
            else:
                yield allocation.type.deserialize(data[offset : offset + allocation.size])

    async def _process(self, events: typing.AsyncIterator[T]) -> None:
        async for event in events:
            self._last_value = event
            await self._broadcast.broadcast(event)


class WatcherAllocator:
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


class LineFollowerWatcher:
    def __init__(self, control: AsyncControl) -> None:
        self._control = control
        self._watcher_enabled = False

    # FIXME: the return type is not perfect, when/if https://github.com/python/typing/issues/1383 is resolved, fix this
    @contextlib.asynccontextmanager
    async def watch[T: _Deserializable](
        self, subscription_configs: tuple[_SubscriptionInfo[T], ...]
    ) -> typing.AsyncIterator[tuple[WatcherSubscription[T], ...]]:
        if self._watcher_enabled:
            raise Exception("Watcher already enabled")

        self._watcher_enabled = True

        async with contextlib.AsyncExitStack() as exit_stack:
            watcher_info = await self._read_watcher_info()
            allocator = WatcherAllocator(
                watcher_info.watcherCount, watcher_info.watcherRegionCount, self._control.packet_size_max
            )

            allocations = [allocator.allocate(sub.size, sub.address, sub.type) for sub in subscription_configs]
            watchers = [await exit_stack.enter_async_context(self._subscribe(allocation)) for allocation in allocations]
            watcher_ids = [allocation.watcher_id for allocation in allocations]

            async with self._enable_watchers(watcher_ids):
                subscriptions = [
                    await exit_stack.enter_async_context(WatcherSubscription.run(watcher, allocations, allocation))
                    for watcher, allocation in zip(watchers, allocations, strict=False)
                ]
                yield tuple(subscriptions)

            self._watcher_enabled = False

    @contextlib.asynccontextmanager
    async def _enable_watchers(self, watcher_ids: list[int]) -> typing.AsyncIterator[None]:
        logger.debug("Initializing watchers", watcher_ids=watcher_ids)
        flags = (
            Types.WatcherFlags.Enabled
            | Types.WatcherFlags.DisableWhenDisconnected
            | Types.WatcherFlags.SendInitialValue
        )
        for watcher_id in watcher_ids:
            await self._control.WatcherSetup(watcher_id, flags, 40, 200)

        try:
            yield
        finally:
            logger.debug("Deinitializing watchers", watcher_ids=watcher_ids)
            for watcher_id in watcher_ids:
                await self._control.WatcherSetup(watcher_id, Types.WatcherFlags(0), 40, 200)

    @contextlib.asynccontextmanager
    async def _subscribe[T: _Deserializable](
        self, allocation: _WatcherAllocation[T]
    ) -> typing.AsyncIterator[typing.AsyncIterator[PacketTypes.PacketEvent_WatcherDirty]]:
        with logger.contextualize(watcher=uuid.uuid4()):
            logger.debug("Subscribing watcher", address=allocation.address, size=allocation.size)

            watcher_id, region_id = allocation.watcher_id, allocation.region_id
            logger.debug("Found watcher", watcher_id=watcher_id, region_id=region_id)
            try:
                flags = Types.WatcherRegionFlags(0)
                region_setup_rpc = self._control.WatcherRegionSetup(
                    watcher_id, region_id, allocation.address, allocation.size, flags=flags
                )
                async with region_setup_rpc as (reply, events):
                    yield events
            finally:
                logger.debug("Removing watcher")
                flags = Types.WatcherRegionFlags.DoNotSendInNotify | Types.WatcherRegionFlags.DoNotSetDirty
                await self._control.WatcherRegionSetup(watcher_id, region_id, 0, 0, flags=flags)

    async def _read_watcher_info(self) -> Types.WatcherInfo:
        metadata = VirtualMemory.watchersInfo
        reply = await self._control.MemRead(metadata.address, metadata.type.data_width)
        data = bytes(reply.data)
        return metadata.type.deserialize(data)
