import typing

from ozobot.web import rpctypes


class ExecuteFileRequest(rpctypes.BaseRequest):
    method: typing.Literal["ExecuteFile"] = "ExecuteFile"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class TimeOfFlightResponse(rpctypes.BaseResponse):
    distance: float
    deviation: float
    timestamp: float


class ProximityResponse(rpctypes.BaseResponse):
    value: float
    timestamp: float


class ReadIrResponse(rpctypes.BaseResponse):
    message: int
    intensity: int
    timestamp: float
