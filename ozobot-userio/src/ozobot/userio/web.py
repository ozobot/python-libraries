import typing

import pydantic
from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    Direction,
    TNamedColor,
)
from ozobot.linefollower.driver.web import Rpc, rpctypes
from ozobot.linefollower.driver.web.rpctypes import TWebDirection
from ozobot.userio import conversions
from ozobot.userio.datatypes import TWebUserIoPrompt


class UserIoPrintRequest(rpctypes.BaseRequest):
    method: typing.Literal["userIoPrint"] = "userIoPrint"
    message: str

    @property
    def args(self) -> tuple:
        return (self.message,)


class UserIoAlertRequest(rpctypes.BaseRequest):
    method: typing.Literal["userIoAlert"] = "userIoAlert"
    message: str
    cancellable: bool

    @property
    def args(self) -> tuple:
        return (self.message, self.cancellable)


class UserIoPromptRequest(rpctypes.BaseRequest):
    method: typing.Literal["userIoPrompt"] = "userIoPrompt"
    message: str
    cancellable: bool
    type: TWebUserIoPrompt
    options: list[str | int | float | bool | TNamedColor | TWebDirection]

    @property
    def args(self) -> tuple:
        return (self.message, self.type, self.options, self.cancellable)


class UserIoWebDriverComponent:
    def __init__(self, rpc: Rpc) -> None:
        self._rpc = rpc

    async def print(self, message: str) -> None:
        req = UserIoPrintRequest(message=message)
        _ = await self._rpc.execute(req, rpctypes.ValidatedAny)

    async def alert(self, message: str, *, cancellable: bool = False) -> None:
        req = UserIoAlertRequest(message=message, cancellable=cancellable)
        _ = await self._rpc.execute(req, rpctypes.ValidatedAny)

    async def prompt[T: (str, float, int, bool, ClassifiedColor, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        type_name = conversions.get_web_type_name(_type)
        protocol_options = conversions.get_web_type_options(options, _type)

        req = UserIoPromptRequest(
            message=message,
            type=type_name,
            options=protocol_options,
            cancellable=cancellable,
        )
        response_model: pydantic.TypeAdapter[str | float | bool] = pydantic.TypeAdapter(str | float | bool)
        response = await self._rpc.execute(req, response_model)
        return conversions.cast_web_prompt_response(_type, response)
