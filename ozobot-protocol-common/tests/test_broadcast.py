import asyncio

import pytest
from ozobot.protocol_common.broadcast import BroadcastManager


def test_contains_context_manager() -> None:
    manager = BroadcastManager[int]()

    with manager.output() as queue:
        assert queue in manager

    assert queue not in manager


async def test_broadcast():
    m = BroadcastManager[int]()
    with m.output() as o1, m.output() as o2:
        await m.broadcast(1)

        async with asyncio.timeout(0.1):
            results = await asyncio.gather(*[queue.get() for queue in (o1, o2)])

    assert results == [1, 1]


async def test_context_manager_queue() -> None:
    manager = BroadcastManager[int]()

    with manager.output() as queue:
        await manager.broadcast(1)
        assert await queue.get() == 1

    await manager.broadcast(2)

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.1):
            await queue.get()


def test_context_manager_queue_close_before_done() -> None:
    manager = BroadcastManager[int]()

    with pytest.raises(GeneratorExit):
        with manager.output() as queue:
            assert queue in manager
            raise GeneratorExit()

    assert queue not in manager
