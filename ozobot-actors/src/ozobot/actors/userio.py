from ozobot.actors.actors import context
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.userio.interface import UserIoInterface


async def user_io_print(message: str) -> None:
    return await context.dispatcher.acall(UserIoInterface.user_io_print, message)


async def user_io_alert(message: str, *, cancellable: bool = False) -> None:
    return await context.dispatcher.acall(UserIoInterface.user_io_alert, message, cancellable=cancellable)


async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
    message: str, _type: type[T], options: list[T], *, cancellable: bool = False
) -> T:
    return await context.dispatcher.acall(
        UserIoInterface.user_io_prompt, message, _type, options, cancellable=cancellable
    )
