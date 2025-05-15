import asyncio

import pytest
from ozobot.protocol_common.rlock import RLock


async def test_rlock():
    lock = RLock()

    async with lock:
        assert lock.locked()
        async with lock:
            assert lock.locked()
            assert lock.owned()

        assert lock.locked()

    assert not lock.locked()
    assert not lock.owned()


async def test_rlock_two_tasks():
    lock = RLock()
    evt = asyncio.Event()

    async def task1():
        assert lock.owned()
        async with lock:
            await evt

    async def task2():
        await asyncio.sleep(0.01)
        assert not lock.owned()
        async with lock:
            pass

        async with asyncio.TaskGroup() as tg:
            tg.create_task(task1())
            with pytest.raises(TimeoutError):
                async with asyncio.timeout(0.1):
                    await asyncio.create_task(task2())

            evt.set()
