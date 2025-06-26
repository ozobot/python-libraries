import contextlib
import typing
from dataclasses import dataclass

from ozobot.evo.driver import get_driver

from .core import Evo
from .sync import EvoSync, as_sync_context_manager


@dataclass(frozen=True, kw_only=True)
class EvoHandle:
    address: str | None = None
    id_prefix: str | None = None
    name: str | None = None

    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Evo]:
        Driver = get_driver()
        async with Driver.open(address=self.address, id_prefix=self.id_prefix, name=self.name) as driver:
            await driver.stop_all()
            async with Evo.open(driver) as evo:
                yield evo


@dataclass(frozen=True, kw_only=True)
class EvoSyncHandle:
    address: str | None = None
    id_prefix: str | None = None
    name: str | None = None

    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[EvoSync]:
        handle = EvoHandle(address=self.address, id_prefix=self.id_prefix, name=self.name)
        with as_sync_context_manager(handle.connect()) as evo:
            yield EvoSync(evo)
