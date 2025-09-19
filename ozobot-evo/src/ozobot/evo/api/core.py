from __future__ import annotations

from ozobot.evo.driver import EvoDriver, EvoVirtualMemory
from ozobot.linefollower.api.core import LineFollower


class Evo(LineFollower):
    @property
    def memory(self) -> EvoVirtualMemory:
        return self._evo_driver.memory

    def __init__(self, driver: EvoDriver) -> None:
        super().__init__(driver)
        self._evo_driver = driver
