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

    @typing.overload
    def connect(self, *, get_async: typing.Literal[False] = False) -> typing.ContextManager[EvoSync]: ...

    @typing.overload
    def connect(self, *, get_async: typing.Literal[True]) -> typing.AsyncContextManager[Evo]: ...

    def connect(self, *, get_async: bool = False) -> typing.ContextManager[EvoSync] | typing.AsyncContextManager[Evo]:
        @contextlib.asynccontextmanager
        async def connect_async() -> typing.AsyncIterator[Evo]:
            Driver = get_driver()
            async with Driver.open(address=self.address, id_prefix=self.id_prefix, name=self.name) as driver:
                await driver.stop_all()
                async with Evo.open(driver) as evo:
                    yield evo

        if get_async:
            return connect_async()
        else:

            @contextlib.contextmanager
            def connect_sync() -> typing.Iterator[EvoSync]:
                with as_sync_context_manager(connect_async()) as evo:
                    yield EvoSync(evo)

            return connect_sync()
