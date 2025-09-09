from ozobot.ari.driver import AriDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import Color, Direction


class Ari(LineFollower):
    _driver: AriDriver

    def __init__(self, driver: AriDriver) -> None:
        super().__init__(driver)

    async def user_io_print(self, message: str) -> None:
        await self._driver.user_io_print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        await self._driver.user_io_alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        return await self._driver.user_io_prompt(message, _type, options, cancellable=cancellable)
