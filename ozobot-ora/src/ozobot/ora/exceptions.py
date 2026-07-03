from ozobot.common.exceptions import OzobotError


class OraException(OzobotError): ...


class CancellationNotSupported(OraException):
    """Caused by canceling Ora command"""

    def __init__(self) -> None:
        super().__init__("Canceling Ora commands is not supported")


class CancellationCausedUndefinedState(OraException):
    """Ora is in undefined state caused by cancellation"""

    def __init__(self) -> None:
        super().__init__("Ora program cannot be resumed after cancelation")
