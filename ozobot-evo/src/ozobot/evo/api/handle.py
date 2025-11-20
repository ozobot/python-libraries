import contextlib
import typing
from dataclasses import dataclass

from ozobot.evo.driver import get_driver

from .core import Evo


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
