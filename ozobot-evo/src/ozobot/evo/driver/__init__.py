import sys
import typing

from ozobot.linefollower.driver.interface import Driver

__all__ = ["get_driver"]


class EvoDriver(Driver, typing.Protocol):
    @classmethod
    def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncContextManager[typing.Self]: ...

    async def stop_all(self): ...


def get_driver() -> type[EvoDriver]:
    if sys.platform == "emscripten":
        from .web import WebDriver

        return WebDriver
    else:
        from .native import NativeDriver

        return NativeDriver
