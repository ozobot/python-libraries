from __future__ import annotations

import asyncio
import typing

from loguru import logger
from ozobot.evo.driver import EvoDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import IRMessage, Sample
from ozobot.linefollower.driver.interface import ReadableWatchableRegion, VirtualMemoryRegions


class EvoVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def obstacle_right_rear(self) -> ReadableWatchableRegion[Sample[float]]:
        """
        Right rear IR sensor's measured intensity reflected from obstacle.
        """

    @property
    def obstacle_left_rear(self) -> ReadableWatchableRegion[Sample[float]]:
        """
        Left rear IR sensor's measured intensity reflected from obstacle.
        """

    @property
    def ir_message_left_rear(self) -> ReadableWatchableRegion[Sample[IRMessage]]:
        """
        Message received by the left rear IR sensor.
        """

    @property
    def ir_message_right_rear(self) -> ReadableWatchableRegion[Sample[IRMessage]]:
        """
        Message received by the right rear IR sensor.
        """


# this enables verbose errors when memory region implementations do not
# match the interfaces
if typing.TYPE_CHECKING:  # type: ignore[name-defined]
    _vm: EvoVirtualMemory
    from ozobot.evo.driver.native import NativeMemoryRegions
    from ozobot.evo.driver.web import EvoWebMemoryRegions

    _vm = EvoWebMemoryRegions()  # type: ignore[call-arg]
    _vm = NativeMemoryRegions()  # type: ignore[call-arg]


class Evo(LineFollower):
    @property
    def data(self) -> EvoVirtualMemory:
        return self._evo_driver.memory

    def __init__(self, driver: EvoDriver) -> None:
        super().__init__(driver)
        self._evo_driver = driver
        self._set_velocity_overridden = asyncio.Condition()

    async def set_velocity(self, linear_mmps: float, angular_degps: float, duration_s: float) -> None:
        logger.debug("Setting velocity", linear=linear_mmps, angular=angular_degps, duration=duration_s)

        # If the velocity command is called while another is running, Evo does not send any notification about this. This is problem especially
        # when a `set_velocity` call is made while another `set_velocity` execution is being executed in a task. The new call overrides the previous one,
        # but the library does not get any notification about that and the task hangs.
        #
        # This workaround makes the function also finish on a condition triggered by calling `set_velocity` rising asyncio.CancellationError
        async with self._set_velocity_overridden:
            self._set_velocity_overridden.notify()

            coros = [
                self._driver.velocity(
                    linear_mmps,
                    angular_degps,
                    int(duration_s * 1000),
                ),
                self._set_velocity_overridden.wait(),
            ]

            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(c) for c in coros]
                _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                # cancel pending task and propagate exception from the finished task
                for t in tasks:
                    if t.done():
                        await t
                    else:
                        t.cancel()
