import typing

from ozobot.web import rpctypes


class PlayAudioRequest(rpctypes.BaseRequest):
    method: typing.Literal["playAudio"] = "playAudio"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class TimeOfFlightResponse(rpctypes.BaseResponse):
    distance: float
    deviation: float
    timestamp: float
