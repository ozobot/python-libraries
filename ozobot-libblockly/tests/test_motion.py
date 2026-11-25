import asyncio
from unittest.mock import AsyncMock, Mock, call, patch

from ozobot.libblockly.motion import set_wheel_speed


@patch("ozobot.libblockly.motion.set_velocity")
async def test_set_wheel_speed_stop(set_velocity_mock: AsyncMock) -> None:
    await set_wheel_speed(0, 0)
    set_velocity_mock.assert_called_with(0, 0, 0)


def _superseding_set_velocity():
    """Fake `set_velocity` imitating the robot: a new call ends the previous one."""
    superseded = asyncio.Event()

    async def set_velocity(linear_mmps: float, angular_degps: float, duration_s: float) -> None:
        nonlocal superseded
        superseded.set()
        superseded = asyncio.Event()
        if duration_s == -1:
            await superseded.wait()

    return set_velocity


def _mock_line_follower(context_mock: Mock) -> None:
    actor = Mock()
    actor.data.geometry.read = AsyncMock(return_value=Mock(wheel_track_mm=100))
    context_mock.dispatcher._find_callable_in_stack.return_value = (actor, None)


@patch("ozobot.libblockly.motion.context")
@patch("ozobot.libblockly.motion.set_velocity")
async def test_set_wheel_speed_stop_supersedes(set_velocity_mock: AsyncMock, context_mock: Mock) -> None:
    set_velocity_mock.side_effect = _superseding_set_velocity()
    _mock_line_follower(context_mock)

    tasks_init = asyncio.all_tasks()
    await set_wheel_speed(10, 10)

    new_tasks = asyncio.all_tasks() - tasks_init
    assert len(new_tasks) == 1
    velocity_task = new_tasks.pop()

    await asyncio.sleep(0)  # let the velocity task start its set_velocity call
    assert not velocity_task.done()

    await set_wheel_speed(0, 0)

    await asyncio.wait([velocity_task], timeout=1)
    assert velocity_task.done() and not velocity_task.cancelled()
    assert set_velocity_mock.call_args_list == [call(10, 0, -1), call(0, 0, 0)]


@patch("ozobot.libblockly.motion.context")
@patch("ozobot.libblockly.motion.set_velocity")
async def test_set_wheel_speed_cancelled_with_parent(set_velocity_mock: AsyncMock, context_mock: Mock) -> None:
    set_velocity_mock.side_effect = _superseding_set_velocity()
    _mock_line_follower(context_mock)

    wheels_set = asyncio.Event()

    async def parent() -> None:
        await set_wheel_speed(10, 10)
        wheels_set.set()
        await asyncio.Event().wait()  # keeps running, e.g. a Blockly loop

    tasks_init = asyncio.all_tasks()
    parent_task = asyncio.create_task(parent())
    await wheels_set.wait()

    new_tasks = asyncio.all_tasks() - tasks_init - {parent_task}
    assert len(new_tasks) == 1
    velocity_task = new_tasks.pop()
    assert not velocity_task.done()

    parent_task.cancel()

    await asyncio.wait([parent_task, velocity_task], timeout=1)
    assert parent_task.cancelled()
    assert velocity_task.cancelled()
