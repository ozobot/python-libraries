from ozobot.evo.driver import EvoDriver
from ozobot.linefollower.api.sync import (
    SyncLineFollower,
    SyncMemoryRegions,
)


class SyncEvo(SyncLineFollower):
    @property
    def data(self) -> SyncMemoryRegions:
        return SyncMemoryRegions(self._driver)

    def __init__(self, driver: EvoDriver) -> None:
        self._driver = driver
        super().__init__(self._driver)
