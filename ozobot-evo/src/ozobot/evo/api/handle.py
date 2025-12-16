import contextlib
import typing
from dataclasses import dataclass

from ozobot.common.sync import as_sync_context_manager
from ozobot.evo.driver import EvoDriver, get_driver

from .core import Evo
from .sync import SyncEvo


@dataclass(frozen=True, kw_only=True)
class EvoHandle:
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Evo]:
        Driver = get_driver()
        async with Driver.open(address=self.address, id=self.id, name=self.name) as driver:
            evo = Evo(driver)
            yield evo


@dataclass(frozen=True, kw_only=True)
class SyncEvoHandle:
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncEvo]:
        Driver = get_driver()
        cm_driver: typing.AsyncContextManager[EvoDriver] = Driver.open(address=self.address, id=self.id, name=self.name)
        with as_sync_context_manager(cm_driver) as driver:
            evo = SyncEvo(driver)
            yield evo
