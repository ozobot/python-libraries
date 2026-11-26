from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.linefollower.driver.web import Rpc
from ozobot.userio.web import UserIoWebDriverComponent

IMPLICIT_BROWSER_TERMINAL_NAME = "BROWSER_TERMINAL"


class BrowserTerminal:
    def __init__(self, name: str = IMPLICIT_BROWSER_TERMINAL_NAME):
        self.device_name = name
        rpc = Rpc(name)
        self._userio_component = UserIoWebDriverComponent(rpc)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def user_io_print(self, message: str):
        return await self._userio_component.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False):
        return await self._userio_component.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._userio_component.prompt(message, _type, options, cancellable=cancellable)
