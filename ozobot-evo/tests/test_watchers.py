import asyncio
import contextlib
import typing
from unittest.mock import Mock, patch

import pytest
from ozobot.evo.api.watchers import (
    WatcherAllocator,
    WatcherManager,
    _flatten,
    _WatcherAllocation,
)
from ozobot.evo.protocol import PacketTypes, Types


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


def _ok_command(**response: typing.Any):
    async def _evts():
        return
        yield  # pragma: no cover - makes this an async generator

    @contextlib.asynccontextmanager
    async def _resp():
        yield Mock(callStatus=Types.CallStatus.CallSuccess, **response), _evts()

    return _resp()


def _make_control() -> Mock:
    return Mock(
        MemRead=Mock(side_effect=lambda *a, **k: _ok_command(data=[4, 4])),
        WatcherSetup=Mock(side_effect=lambda *a, **k: _ok_command()),
        WatcherRegionSetup=Mock(side_effect=lambda *a, **k: _ok_command()),
        packet_size_max=100,
    )


async def test_watcher_failure_propagation() -> None:
    """A failing watcher task surfaces as a flat exception, not an ExceptionGroup."""

    class CustomError(Exception):
        pass

    async def _failing_watch(self, watcher_id: int, update_counter_region_id: int) -> None:
        raise CustomError("watcher boom")

    control = _make_control()
    subs_info = Mock(address=0x1000, size=4, type=Mock(deserialize=Mock(return_value=Mock())))

    with patch.object(WatcherManager, "_watch", _failing_watch):
        with pytest.raises(CustomError) as excinfo:
            async with WatcherManager.open(control) as manager:
                await manager.enable(subs_info)
                # block until the task group cancels us because the watcher task failed
                await asyncio.Event().wait()

    # the failure must be flattened out of the TaskGroup's ExceptionGroup
    assert not isinstance(excinfo.value, BaseExceptionGroup)


def test_flatten_returns_first_non_cancelled_failure_and_logs_the_rest() -> None:
    first = ValueError("first")
    second = RuntimeError("second")
    group = BaseExceptionGroup(
        "watchers",
        [asyncio.CancelledError(), BaseExceptionGroup("nested", [first]), second],
    )

    with patch("ozobot.evo.api.watchers.logger") as logger_mock:
        result = _flatten(group)

    assert result is first
    logger_mock.exception.assert_called_once()


def test_flatten_falls_back_to_cancellation_when_no_other_failure() -> None:
    cancelled = asyncio.CancelledError()
    group = BaseExceptionGroup("watchers", [cancelled])

    assert _flatten(group) is cancelled


@pytest.mark.skip("not implemented")
async def test_evo_watcher():
    pass
