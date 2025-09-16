import asyncio
import typing

import pydantic
from ozobot.common.exceptions import TSError
from ozobot.linefollower.datatypes import (
    Color,
    Direction,
    TDirection,
    TNamedColor,
)
from ozobot.userio import conversions
from ozobot.userio.datatypes import TUserIoPrompt
from ozobot.web import rpctypes
from ozobot.web.driver import Rpc


class UserIoPrintRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoPrint"] = "UserIoPrint"
    message: str

    @property
    def args(self) -> tuple:
        return (self.message,)


class UserIoAlertRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoAlert"] = "UserIoAlert"
    message: str
    cancellable: bool

    @property
    def args(self) -> tuple:
        return (self.message, self.cancellable)


class UserIoPromptRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoPrompt"] = "UserIoPrompt"
    message: str
    cancellable: bool
    type: TUserIoPrompt
    options: list[str | int | float | bool | TNamedColor | TDirection]

    @property
    def args(self) -> tuple:
        return (self.message, self.type, self.options, self.cancellable)


class UserIoWebDriverComponent:
    def __init__(self, rpc: Rpc) -> None:
        self._rpc = rpc

    async def print(self, message: str) -> None:
        req = UserIoPrintRequest(message=message)
        _ = await self._rpc.execute(req, rpctypes.ValidatedBool)

    async def alert(self, message: str, *, cancellable: bool = False) -> None:
        req = UserIoAlertRequest(message=message, cancellable=cancellable)
        try:
            _ = await self._rpc.execute(req, rpctypes.ValidatedBool)
        except TSError as err:
            raise asyncio.CancelledError() from err

    async def prompt[T: (str, float, int, bool, Color, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        type_name = conversions.get_type_name(_type)
        protocol_options = conversions.get_type_options(options, _type)

        req = UserIoPromptRequest(message=message, type=type_name, options=protocol_options, cancellable=cancellable)
        response_model: pydantic.TypeAdapter[str | float | bool] = pydantic.TypeAdapter(str | float | bool)
        response = await self._rpc.execute(req, response_model)
        return conversions.cast_web_prompt_response(_type, response)
