from ozobot.ari.driver import AriDriver, AriVirtualMemory
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import Color, Direction, RobotGeometry


class Ari(LineFollower):
    @property
    def geometry(self) -> RobotGeometry:
        return RobotGeometry(
            ticks_per_meter=22281.69,
            wheel_track=0.0315,
            wheel_diameter=0.012,
            encoder_ticks_per_wheel_revolution=16 * 2 * 21 * 15 / 12.0,
            max_speed_limit=0.3,
        )

    @property
    def data(self) -> AriVirtualMemory:
        return self._ari_driver.memory

    def __init__(self, driver: AriDriver) -> None:
        super().__init__(driver)
        self._ari_driver = driver

    async def user_io_print(self, message: str) -> None:
        await self._ari_driver.user_io_print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        await self._ari_driver.user_io_alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        return await self._ari_driver.user_io_prompt(message, _type, options, cancellable=cancellable)
