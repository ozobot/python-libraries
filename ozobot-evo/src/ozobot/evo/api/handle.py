import contextlib
import typing
from dataclasses import dataclass

from ozobot.evo.driver import get_driver

from .core import Evo


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
            evo = Evo(driver)
            yield evo
