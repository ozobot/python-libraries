import typing

from ozobot.linefollower.datatypes import Color, Direction
from ozobot.userio.web import UserIoWebDriverComponent
from ozobot.web import rpctypes
from ozobot.web.driver import WebDriver

__all__ = ["WebDriver"]


class ExecuteFileRequest(rpctypes.BaseRequest):
    method: typing.Literal["ExecuteFile"] = "ExecuteFile"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class AriWebDriver(WebDriver):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._userio_component = UserIoWebDriverComponent(self._rpc)

    async def play_audio(self, audio_name: str) -> None:
        req = ExecuteFileRequest(filename=audio_name)
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def user_io_print(self, message: str) -> None:
        return await self._userio_component.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        return await self._userio_component.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._userio_component.prompt(message, _type, options, cancellable=cancellable)
