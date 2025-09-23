import typing

from ozobot.actors.actors import context
from ozobot.linefollower.datatypes import Color, Direction


class UserIoEnabledRobot(typing.Protocol):
    async def user_io_print(self, message: str) -> None: ...

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None: ...

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T: ...


async def user_io_print(message: str) -> None:
    await context.dispatcher.acall(UserIoEnabledRobot.user_io_print, message)


async def user_io_alert(message: str, *, cancellable: bool = False) -> None:
    await context.dispatcher.acall(UserIoEnabledRobot.user_io_alert, message, cancellable=cancellable)


async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
    message: str, _type: type[T], options: list[T], *, cancellable: bool = False
) -> T:
    return await context.dispatcher.acall(
        UserIoEnabledRobot.user_io_prompt, message, _type, options, cancellable=cancellable
    )
