import sys
import typing

from ozobot.linefollower.datatypes import Color, Direction
from ozobot.linefollower.driver.interface import Driver


class AriDriver(Driver, typing.Protocol):
    @classmethod
    def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
        connection_key: str | None = None,
    ) -> typing.AsyncContextManager[typing.Self]: ...

    async def user_io_print(self, message: str) -> None: ...

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None: ...

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T: ...


def get_driver() -> type[AriDriver]:
    if sys.platform == "emscripten":
        from .web import AriWebDriver

        return AriWebDriver
    else:
        from .native import NativeDriver

        return NativeDriver
