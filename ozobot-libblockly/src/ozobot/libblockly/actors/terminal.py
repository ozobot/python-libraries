import sys
import typing
from types import TracebackType

from ozobot.common.exceptions import PlatformNotSupportedError
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.linefollower.driver.web import Rpc
from ozobot.userio.web import UserIoWebDriverComponent

IMPLICIT_BROWSER_TERMINAL_NAME = "BROWSER_TERMINAL"

if typing.TYPE_CHECKING:
    type TerminalDriver = UserIoWebDriverComponent
else:
    type TerminalDriver = typing.Any


def get_driver(name: str) -> TerminalDriver:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        return UserIoWebDriverComponent(Rpc(name))
    else:
        raise PlatformNotSupportedError("Terminal")


class BrowserTerminal:
    def __init__(self, name: str = IMPLICIT_BROWSER_TERMINAL_NAME) -> None:
        self.device_name = name
        self._driver = get_driver(name)

    async def __aenter__(self) -> typing.Self:
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        pass

    async def user_io_print(self, message: str) -> None:
        return await self._driver.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        return await self._driver.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._driver.prompt(message, _type, options, cancellable=cancellable)
