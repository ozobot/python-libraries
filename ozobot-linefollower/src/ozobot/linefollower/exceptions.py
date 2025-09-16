from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.datatypes import Direction


class LineFollowerError(OzobotError): ...


class FileNotFoundError(LineFollowerError):
    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")


class SingleDirectionRequiredError(LineFollowerError):
    def __init__(self, dir: Direction) -> None:
        if dir == Direction(0):
            d = "none"
        else:
            d = ", ".join([str(d) for d in dir])

        super().__init__(f"Single direction is required for the call, got: {d}")


class DriverCommandFailedError(LineFollowerError):
    def __init__(self, command_name: str, reason: str) -> None:
        super().__init__(f"Command failed with an error: {command_name} - {reason}")
