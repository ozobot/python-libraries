import typing

from ozobot.linefollower.driver.web import rpctypes


class PlayAudioRequest(rpctypes.BaseRequest):
    method: typing.Literal["playAudio"] = "playAudio"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class ButtonResponse(rpctypes.BaseResponse):
    press: bool
    timestamp: int


class ChargerStateResponse(rpctypes.BaseResponse):
    state: typing.Literal["Connected", "Disconnected", "LowPower"]
    timestamp: int
