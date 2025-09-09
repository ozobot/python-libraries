import typing

import pydantic
from ozobot.ari import conversions
from ozobot.ari.conversions import is_named_color, is_named_direction
from ozobot.ari.driver import shared
from ozobot.ari.exceptions import UnexpectedUserIoPromptResponseReceivedError
from ozobot.ari.protocol.types import TUserIoPrompt
from ozobot.linefollower.datatypes import (
    Color,
    Direction,
    TDirection,
    TNamedColor,
)
from ozobot.linefollower.driver import types
from ozobot.linefollower.driver.web import WebDriver

__all__ = ["WebDriver"]


class ExecuteFileRequest(types.BaseRequest):
    method: typing.Literal["ExecuteFile"] = "ExecuteFile"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class UserIoPrintRequest(types.BaseRequest):
    method: typing.Literal["UserIoPrint"] = "UserIoPrint"
    message: str

    @property
    def args(self) -> tuple:
        return (self.message,)


class UserIoAlertRequest(types.BaseRequest):
    method: typing.Literal["UserIoAlert"] = "UserIoAlert"
    message: str
    cancellable: bool

    @property
    def args(self) -> tuple:
        return (self.message, self.cancellable)


class UserIoPromptRequest(types.BaseRequest):
    method: typing.Literal["UserIoPrompt"] = "UserIoPrompt"
    message: str
    cancellable: bool
    type: TUserIoPrompt
    options: list[str | int | float | bool | TNamedColor | TDirection]

    @property
    def args(self) -> tuple:
        return (self.message, self.type, self.options, self.cancellable)


def _cast_user_io_prompt_response[T](_type: type[T], value: str | float | bool) -> T:
    if _type is str:
        return typing.cast(T, value)
    elif _type is int:
        return typing.cast(T, int(value))
    elif _type is float:
        return typing.cast(T, float(value))
    elif _type is bool:
        return typing.cast(T, bool(value))
    elif _type is Color and isinstance(value, str) and is_named_color(value):
        return typing.cast(T, conversions.color_from_protocol(value))
    elif _type is Direction and isinstance(value, str) and is_named_direction(value):
        return typing.cast(T, conversions.intersection_direction_from_protocol(value))
    else:
        raise UnexpectedUserIoPromptResponseReceivedError(value, _type)


class AriWebDriver(WebDriver):
    async def play_audio(self, audio_name: str) -> None:
        req = ExecuteFileRequest(filename=audio_name)
        resp = await self._rpc.execute(req, types.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def user_io_print(self, message: str) -> None:
        req = UserIoPrintRequest(message=message)
        _ = await self._rpc.execute(req, types.ValidatedBool)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        req = UserIoAlertRequest(message=message, cancellable=cancellable)
            _ = await self._rpc.execute(req, types.ValidatedBool)

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        type_name = shared.get_user_io_type_name(_type)
        protocol_options = shared.get_user_io_type_options(options, _type)

        req = UserIoPromptRequest(message=message, type=type_name, options=protocol_options, cancellable=cancellable)
        response_model: pydantic.TypeAdapter[str | float | bool] = pydantic.TypeAdapter(str | float | bool)
        response = await self._rpc.execute(req, response_model)
        return _cast_user_io_prompt_response(_type, response)
