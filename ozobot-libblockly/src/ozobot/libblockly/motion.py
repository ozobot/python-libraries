from __future__ import annotations

import asyncio
import math

from ozobot.actors.actors import context
from ozobot.actors.linefollower import set_velocity
from ozobot.linefollower.api.core import LineFollower


async def set_wheel_speed(left_mmps: float, right_mmps: float) -> None:
    if left_mmps == 0 and right_mmps == 0:
        await set_velocity(0, 0, 0)
    else:
        dispatcher = context.dispatcher
        actor, _ = dispatcher._find_callable_in_stack(LineFollower.set_velocity)
        geometry = await actor.data.geometry.read()
        linear = (right_mmps + left_mmps) / 2
        angular_rad = (right_mmps - left_mmps) / geometry.wheel_track_mm
        angular = math.degrees(angular_rad)
        task = asyncio.create_task(set_velocity(linear, angular, -1))

        # on purpose, this API function doesn't block. It can still be cancelled (`set_wheel_speed(0, 0)`)
        # this is an escape hatch from the structured concurrency pattern that is needed
        # for backward compatibility with Blockly `set motors` and `stop` blocks

        # bind the async task to the cancellation of the upper task
        # this recovers at least the "cancellation" property of structured concurrency,
        # and ensures that if any loop with "setWheelSpeed" is cancelled, the robot stops...
        calling_task = asyncio.current_task()
        if calling_task:
            calling_task.add_done_callback(lambda t: task.cancel())
