from ozobot.ari.api.core import Ari
from ozobot.common.sync import as_sync
from ozobot.linefollower.api.sync import (
    SyncLineFollower,
    SyncMemoryRegions,
)
from ozobot.linefollower.datatypes import ClassifiedColor, Direction


class SyncAri(SyncLineFollower):
    @property
    def data(self) -> SyncMemoryRegions:
        return SyncMemoryRegions(self._ari)

    def __init__(self, ari: Ari) -> None:
        self._ari = ari
        super().__init__(ari)

    @as_sync
    async def user_io_print(self, message: str) -> None:
        await self._ari.user_io_print(message)

    @as_sync
    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        await self._ari.user_io_alert(message, cancellable=cancellable)

    @as_sync
    async def user_io_prompt[T: (str, float, int, bool, ClassifiedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        return await self._ari.user_io_prompt(message, _type, options, cancellable=cancellable)
