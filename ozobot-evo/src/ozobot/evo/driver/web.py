import typing

from ozobot.evo.driver.shared import map_audio_name_to_filename
from ozobot.linefollower.driver.types import BaseExecutionStateResponse, BaseRequest
from ozobot.linefollower.driver.web import WebDriver

__all__ = ["WebDriver"]


class ExecuteFileRequest(BaseRequest):
    method: typing.Literal["ExecuteFile"] = "ExecuteFile"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


class EvoWebDriver(WebDriver):
    async def play_audio(self, audio_name: str) -> None:
        req = ExecuteFileRequest(
            filename=f"/system/audio/{map_audio_name_to_filename(audio_name)}.wav",
        )
        resp = await self._rpc.execute(req, BaseExecutionStateResponse)
        self._validate_response(req.method, resp)
