import typing
from unittest.mock import Mock

import pytest
from ozobot.linefollower.api.watchers import (
    WatcherAllocator,
    WatcherSubscription,
    _WatcherAllocation,
)
from ozobot.evo.protocol import PacketTypes


def test_allocator() -> None:
    allocator = WatcherAllocator(4, 4, 18)
    alloc1 = allocator.allocate(5, 0, Mock())  # type: ignore[var-annotated]

    assert alloc1.watcher_id == 0
    assert alloc1.region_id == 0

    alloc2 = allocator.allocate(5, 1, Mock())  # type: ignore[var-annotated]
    assert alloc2.watcher_id == 0
    assert alloc2.region_id == 1

    alloc3 = allocator.allocate(10, 10, Mock())  # type: ignore[var-annotated]
    assert alloc3.watcher_id == 1
    assert alloc3.region_id == 0


def test_allocator_type() -> None:
    allocator = WatcherAllocator(4, 4, 18)
    alloc = allocator.allocate(5, 0, PacketTypes.PacketEvent_Shutdown)

    typing.assert_type(alloc, _WatcherAllocation[PacketTypes.PacketEvent_Shutdown])


async def test_subscription() -> None:
    allocator = WatcherAllocator(4, 4, 18)

    type1_mock = Mock(deserialize=lambda e: bytes(e))
    allocation1 = allocator.allocate(5, 0, type1_mock)  # type: ignore[var-annotated]

    type2_mock = Mock(deserialize=lambda e: bytes(e))
    allocation2 = allocator.allocate(3, 5, type2_mock)  # type: ignore[var-annotated]

    async def _iter() -> typing.AsyncIterator[PacketTypes.PacketEvent_WatcherDirty]:
        yield PacketTypes.PacketEvent_WatcherDirty(0, [0, 0, 0, 0, 0, 1, 1, 1])
        yield PacketTypes.PacketEvent_WatcherDirty(0, [10, 10, 10, 10, 10, 11, 11, 11])
        yield PacketTypes.PacketEvent_WatcherDirty(0, [20, 20, 20, 20, 20, 21, 21, 21])

    async with WatcherSubscription.run(_iter(), [allocation1, allocation2], allocation1) as subs1:
        async with subs1.watch() as read1:
            assert subs1.last == bytes([0, 0, 0, 0, 0])
            data1 = [await anext(read1) for _ in range(2)]

    async with WatcherSubscription.run(_iter(), [allocation1, allocation2], allocation2) as subs2:
        assert subs2.last == bytes([1, 1, 1])
        async with subs2.watch() as read2:
            data2 = [await anext(read2) for _ in range(2)]

    assert data1 == [
        bytes([10, 10, 10, 10, 10]),
        bytes([20, 20, 20, 20, 20]),
    ]

    assert data2 == [
        bytes([11, 11, 11]),
        bytes([21, 21, 21]),
    ]


@pytest.mark.skip("not implemented")
async def test_evo_watcher():
    pass
