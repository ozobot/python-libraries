from ozobot.common.exceptions import OzobotError


class LineFollowerError(OzobotError): ...


class FileNotFoundError(LineFollowerError):
    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")
