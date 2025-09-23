from __future__ import annotations

from ozobot.evo.driver import EvoDriver, EvoVirtualMemory
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import RobotGeometry


class Evo(LineFollower):
    @property
    def geometry(self) -> RobotGeometry:
        return RobotGeometry(
            ticks_per_meter=18851,
            wheel_track=0.023,
            wheel_diameter=0.01182,
            encoder_ticks_per_wheel_revolution=8 * 2 * 21 * 25 / 12,
            max_speed_limit=0.3,
        )

    @property
    def memory(self) -> EvoVirtualMemory:
        return self._evo_driver.memory

    def __init__(self, driver: EvoDriver) -> None:
        super().__init__(driver)
        self._evo_driver = driver
