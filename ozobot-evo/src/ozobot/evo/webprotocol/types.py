import typing

from ozobot.web import rpctypes


class ExecuteFileRequest(rpctypes.BaseRequest):
    method: typing.Literal["ExecuteFile"] = "ExecuteFile"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class ProximityResponse(rpctypes.BaseResponse):
    left_rear: int
    left_front: int
    right_rear: int
    right_front: int
    timestamp: float


class ReadIrResponse(rpctypes.BaseResponse):
    message: int
    intensity: int
    timestamp: float


class ButtonResponse(rpctypes.BaseResponse):
    press: bool
    timestamp: float


class ChargerStateResponse(rpctypes.BaseResponse):
    state: typing.Literal["Connected", "Disconnected", "LowPower"]
    timestamp: float
