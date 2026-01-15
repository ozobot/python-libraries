import typing

from ozobot.linefollower.driver.web import rpctypes


class ButtonResponse(rpctypes.BaseResponse):
    press: bool
    timestamp: int


class ChargerStateResponse(rpctypes.BaseResponse):
    state: typing.Literal["Connected", "Disconnected", "LowPower"]
    timestamp: int
