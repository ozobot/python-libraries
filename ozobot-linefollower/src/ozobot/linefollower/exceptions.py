from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.datatypes import Direction


class LineFollowerError(OzobotError): ...


class AudioFileNotFoundError(LineFollowerError):
    """Requested audio file is not found."""

    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")


class SingleDirectionRequiredError(LineFollowerError):
    """Single direction is expected but multiple or none were provided."""

    def __init__(self, dir: Direction) -> None:
        if dir == Direction(0):
            d = "none"
        else:
            d = ", ".join([str(d) for d in dir])

        super().__init__(f"Single direction is required for the call, got: {d}")


class DriverCommandFailedError(LineFollowerError):
    """Driver command fails with an unknown error."""

    def __init__(self, command_name: str, reason: str) -> None:
        super().__init__(f"Command failed with an error: {command_name} - {reason}")


class InvalidClassifiedColorError(LineFollowerError):
    """Object is not a valid classified color."""

    def __init__(self, obj: object) -> None:
        super().__init__(f"Object does not represent a classified color: {obj}")


class InvalidDirectionError(LineFollowerError):
    """Object is not a valid direction."""

    def __init__(self, obj: object) -> None:
        super().__init__(f"Object does not represent a direction: {obj}")


class LinefollowerFileNotFoundError(LineFollowerError):
    """File is not found."""

    def __init__(self):
        super().__init__("File not found")
