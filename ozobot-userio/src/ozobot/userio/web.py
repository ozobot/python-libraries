import asyncio
import contextlib
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


@contextlib.contextmanager
def _handle_ts_cancellation_error() -> typing.Iterator[None]:
    """Context manager that converts TSError(CanceledByUser) to asyncio.CancelledError"""
    # TODO: Fix this in the exception handler instead
    try:
        yield
    except TSError as err:
        if err.args[0] == "CanceledByUser":
            raise asyncio.CancelledError() from err


class UserIoPrintRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoPrint", "Print"] = "UserIoPrint"
    message: str

    @property
    def args(self) -> tuple:
        return (self.message,)


class UserIoAlertRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoAlert", "Alert"] = "UserIoAlert"
    message: str
    cancellable: bool

    @property
    def args(self) -> tuple:
        return (self.message, self.cancellable)


class UserIoPromptRequest(rpctypes.BaseRequest):
    method: typing.Literal["UserIoPrompt", "Prompt"] = "UserIoPrompt"
    message: str
    cancellable: bool
    type: TUserIoPrompt
    options: list[str | int | float | bool | TNamedColor | TDirection]

    @property
    def args(self) -> tuple:
        return (self.message, self.type, self.options, self.cancellable)


class UserIoWebDriverComponent:
    def __init__(self, rpc: Rpc, *, method_prefix: typing.Literal["UserIo", ""] = "UserIo") -> None:
        """
        Component that implements RPC on UserIO components. `method_prefix` can be optionally
        overwritten to use non uniform API that differs between Ari and Browser Terminal.
        """
        self._rpc = rpc
        self._method_prefix = method_prefix

    async def print(self, message: str) -> None:
        req = UserIoPrintRequest(method=f"{self._method_prefix}Print", message=message)
        _ = await self._rpc.execute(req, rpctypes.ValidatedAny)

    async def alert(self, message: str, *, cancellable: bool = False) -> None:
        req = UserIoAlertRequest(method=f"{self._method_prefix}Alert", message=message, cancellable=cancellable)
        with _handle_ts_cancellation_error():
            _ = await self._rpc.execute(req, rpctypes.ValidatedAny)

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

        req = UserIoPromptRequest(
            method=f"{self._method_prefix}Prompt",
            message=message,
            type=type_name,
            options=protocol_options,
            cancellable=cancellable,
        )
        response_model: pydantic.TypeAdapter[str | float | bool] = pydantic.TypeAdapter(str | float | bool)
        with _handle_ts_cancellation_error():
            response = await self._rpc.execute(req, response_model)
        return conversions.cast_web_prompt_response(_type, response)
