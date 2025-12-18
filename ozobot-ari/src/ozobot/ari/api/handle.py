import contextlib
import typing
from dataclasses import dataclass

from ozobot.ari.driver import AriDriver, get_driver
from ozobot.common.sync import as_sync_context_manager

from .core import Ari
from .sync import SyncAri


@dataclass(frozen=True, kw_only=True)
class AriHandle:
    connection_key: str | None = None
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Ari]:
        Driver = get_driver()
        async with Driver.open(
            address=self.address, id=self.id, name=self.name, connection_key=self.connection_key
        ) as driver:
            ari = Ari(driver)
            yield ari


@dataclass(frozen=True, kw_only=True)
class SyncAriHandle:
    connection_key: str | None = None
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncAri]:
        Driver = get_driver()
        cm_driver: typing.AsyncContextManager[AriDriver] = Driver.open(address=self.address, id=self.id, name=self.name)
        with as_sync_context_manager(cm_driver) as driver:
            evo = SyncAri(driver)
            yield evo
