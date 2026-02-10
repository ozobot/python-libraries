import typing

from ozobot.linefollower.datatypes import Direction, NamedColor


class UserIoInterface(typing.Protocol):
    async def user_io_print(self, message: str) -> None: ...

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None: ...

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T: ...
