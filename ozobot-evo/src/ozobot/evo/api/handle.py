import contextlib
import typing
from types import TracebackType

from ozobot.common.sync import as_sync_context_manager
from ozobot.evo.driver import EvoDriver, get_driver
from ozobot.linefollower.api.handle import BaseHandle

from .core import Evo
from .sync import SyncEvo


class EvoHandle(BaseHandle):
    def __init__(self, *, address: str | None = None, id: str | None = None, name: str | None = None) -> None:
        super().__init__(address=address, id=id, name=name)
        self._exit_stack = contextlib.AsyncExitStack()

    async def __aenter__(self) -> Evo:
        Driver = get_driver()
        # the cast is essential for mypy to correctly infer `enter_async_context` return value
        driver_context = typing.cast(
            contextlib.AbstractAsyncContextManager[EvoDriver],
            Driver.open(address=self.address, id=self.id, name=self.name),
        )
        driver = await self._exit_stack.enter_async_context(driver_context)
        return Evo(driver)

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)


class SyncEvoHandle(BaseHandle):
    def __init__(self, *, address: str | None = None, id: str | None = None, name: str | None = None) -> None:
        super().__init__(address=address, id=id, name=name)
        self._exit_stack = contextlib.ExitStack()

    def __enter__(self) -> SyncEvo:
        async_handle = EvoHandle(address=self.address, id=self.id, name=self.name)
        handle_context = self._exit_stack.enter_context(as_sync_context_manager(async_handle))
        return SyncEvo(handle_context)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
