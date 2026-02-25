import asyncio

import pytest
from ozobot.ora.queue import LazyTaskGroup, TaskQueue


async def _task_set_evt(event: asyncio.Event):
    await asyncio.sleep(0)
    event.set()


async def _task_wait_evt(event: asyncio.Event):
    await asyncio.sleep(0)
    await event.wait()


async def _task_wait_evt_failing(event: asyncio.Event):
    await asyncio.sleep(0)
    await event.wait()
    raise Exception("Houston, we have a problem")


async def _task_set_evt_failing(event: asyncio.Event):
    await asyncio.sleep(0)
    event.set()
    raise Exception("Houston, we have a problem")


async def _failing_task():
    await asyncio.sleep(0)
    raise Exception("Houston, we have a problem")


async def test_task_group_validate():
    event1 = asyncio.Event()
    event2 = asyncio.Event()

    tg = LazyTaskGroup()
    tg.create_task(_task_set_evt(event1))
    tg.create_task(_task_set_evt(event2))

    await event1.wait()

    tg.validate_state()

    assert event1.is_set()
    assert event2.is_set()


async def test_task_group_validate_running():
    event1 = asyncio.Event()
    event2 = asyncio.Event()

    tg = LazyTaskGroup()
    tg.create_task(_task_wait_evt(event1))
    tg.create_task(_task_wait_evt(event2))

    tg.validate_state()

    event1.set()
    event2.set()


async def test_task_group_validate_failed():
    event = asyncio.Event()

    tg = LazyTaskGroup()
    tg.create_task(_failing_task())
    tg.create_task(_failing_task())
    tg.create_task(_failing_task())
    tg.create_task(_task_set_evt(event))

    await event.wait()

    with pytest.raises(ExceptionGroup) as eg:
        tg.validate_state()

        assert eg.value.exceptions == 3


async def test_task_group_validate_no_tasks_running():
    tg = LazyTaskGroup()
    tg.validate_state()


async def test_task_group_waiting():
    tg = LazyTaskGroup()
    event = asyncio.Event()
    tg.create_task(_task_wait_evt(event))

    wait_task = asyncio.create_task(tg.wait_for_change())
    await asyncio.sleep(0.1)

    event.set()
    await wait_task
    assert wait_task.done()


async def test_task_group_waiting_filed():
    tg = LazyTaskGroup()
    event = asyncio.Event()
    tg.create_task(_failing_task())

    wait_task = asyncio.create_task(tg.wait_for_change())
    event.set()
    await wait_task

    assert wait_task.done()


async def test_task_group_waiting_no_tasks():
    tg = LazyTaskGroup()

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            await tg.wait_for_change()


async def test_task_group_waiting_exception_exists():
    tg = LazyTaskGroup()
    tg.create_task(_failing_task())

    await asyncio.sleep(0.1)

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            await tg.wait_for_change()


async def test_task_group_exception_during_wait():
    tg = LazyTaskGroup()
    event = asyncio.Event()
    tg.create_task(_task_wait_evt_failing(event))

    wait_task = asyncio.create_task(tg.wait_for_change())

    await asyncio.sleep(0.01)
    event.set()
    await wait_task

    assert wait_task.done()


async def test_queue_blocking():
    q = TaskQueue(3)
    counter = 0

    async def _task():
        nonlocal counter
        await asyncio.sleep(0)
        counter += 1

    await q.run_blocking(_task())
    await q.run_blocking(_task())
    await q.run_blocking(_task())
    await q.run_blocking(_task())

    assert counter == 4


async def test_queue_nonblocking():
    event = asyncio.Event()

    async with TaskQueue(3) as q:
        await q.run_nonblocking(_task_set_evt(event))
        await event.wait()

        assert event.is_set()


async def test_queue_mixed():
    event = asyncio.Event()

    async with TaskQueue(2) as q:
        await q.run_nonblocking(_task_wait_evt(event))
        await q.run_blocking(asyncio.sleep(0))

        event.set()
    assert event.is_set()


async def test_queue_full():
    events = [asyncio.Event() for _ in range(3)]
    tasks = [_task_wait_evt(event) for event in events]

    async with TaskQueue(3) as q:
        for task in tasks:
            await q.run_nonblocking(task)

        test_event = asyncio.Event()
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(0.1):
                t = _task_set_evt(test_event)
                await q.run_blocking(t)

        for event in events:
            event.set()

    t.close()
    assert not test_event.is_set()


async def test_queue_without_context_manager():
    task_queue = await TaskQueue(3).__aenter__()
    await task_queue.run_nonblocking(asyncio.sleep(0))

    for _ in range(10):
        await asyncio.sleep(0)


async def test_queue_failing_without_context_manager():
    async def _failing():
        await asyncio.sleep(0)
        raise Exception("Houston, we have a problem")

    task_queue = await TaskQueue(3).__aenter__()
    await task_queue.run_nonblocking(_failing())

    for _ in range(10):
        await asyncio.sleep(0)


async def test_queue_error_blocking():
    task_queue = TaskQueue(5)

    with pytest.raises(Exception, match="Houston, we have a problem"):
        await task_queue.run_blocking(_failing_task())


async def test_queue_error_nonblocking():
    """Test if an error in a non-blocking task is ignored"""
    task_queue = TaskQueue(5)

    await task_queue.run_nonblocking(_failing_task())


async def test_queue_detect_error_by_nonblocking():
    """Test if an error in a non-blocking task is detected by the next non-blocking call"""

    task_queue = TaskQueue(5)
    event = asyncio.Event()

    task = await task_queue.run_nonblocking(_failing_task())

    task.add_done_callback(lambda t: event.set())
    await event.wait()  # synchronize to make sure the failing task is finished

    with pytest.raises(ExceptionGroup) as excinfo:
        await task_queue.run_nonblocking(asyncio.Future())

        assert list(excinfo.value.exceptions) == [Exception("Houston, we have a problem")]


async def test_queue_detect_error_by_blocking():
    """Test if an error in a non-blocking task is detected by the next blocking call"""

    task_queue = TaskQueue(5)
    event = asyncio.Event()

    task = await task_queue.run_nonblocking(_failing_task())

    task.add_done_callback(lambda t: event.set())
    await event.wait()  # synchronize to make sure the failing task is finished

    with pytest.raises(ExceptionGroup) as excinfo:
        await task_queue.run_blocking(asyncio.Future())

        assert list(excinfo.value.exceptions) == [Exception("Houston, we have a problem")]


async def test_queue_error_during_blocking():
    task_queue = TaskQueue(5)
    trigger_failure_event = asyncio.Event()

    await task_queue.run_nonblocking(_task_wait_evt_failing(trigger_failure_event))

    with pytest.raises(ExceptionGroup) as excinfo:
        asyncio.get_running_loop().call_later(
            0.1,  # make sure the task is already running
            lambda: trigger_failure_event.set(),
        )

        await task_queue.run_blocking(asyncio.Future())

        assert list(excinfo.value.exceptions) == [Exception("Houston, we have a problem")]


async def test_queue_error_during_wait_for_queue():
    """Test if an error in a non-blocking task is detected when the run command blocks until the queue is free"""

    task_queue = TaskQueue(2)
    trigger_failure_event = asyncio.Event()

    await task_queue.run_nonblocking(_task_wait_evt_failing(trigger_failure_event))
    await task_queue.run_nonblocking(asyncio.Future())

    with pytest.raises(ExceptionGroup) as excinfo:
        asyncio.get_running_loop().call_later(
            0.1,  # make sure the task is already running
            lambda: trigger_failure_event.set(),
        )

        await task_queue.run_blocking(asyncio.Future())

        assert list(excinfo.value.exceptions) == [Exception("Houston, we have a problem")]


async def test_queue_abort_on_error_in_blocking():
    task_queue = TaskQueue(3)

    t1 = await task_queue.run_nonblocking(asyncio.Future())
    t2 = await task_queue.run_nonblocking(asyncio.Future())

    with pytest.raises(Exception, match="Houston, we have a problem"):
        await task_queue.run_blocking(_failing_task())

    _ = await asyncio.gather(t1, t2, return_exceptions=True)
    assert t1.cancelled()
    assert t2.cancelled()


async def test_queue_abort_on_error_in_nonblocking():
    task_queue = TaskQueue(3)

    t1 = await task_queue.run_nonblocking(asyncio.Future())
    t2 = await task_queue.run_nonblocking(asyncio.Future())

    await task_queue.run_nonblocking(_failing_task())

    _ = await asyncio.gather(t1, t2, return_exceptions=True)
    assert t1.cancelled()
    assert t2.cancelled()
