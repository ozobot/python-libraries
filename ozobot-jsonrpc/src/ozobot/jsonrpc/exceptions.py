from ozobot.common.exceptions import OzobotError


class FramingError(OzobotError): ...


class CancelledByServerError(OzobotError):
    def __init__(self, id: int, code: int | None, message: str | None) -> None:
        if code is not None and message is not None:
            msg = f"{code} - {message}"
        elif code is None and message:
            msg = message
        elif code is not None and not message:
            msg = str(code)
        else:
            msg = "unknown reason"

        super().__init__(f"Request cancelled by server: {msg} (request {id})")


class CancelledByClientError(OzobotError):
    def __init__(self, id: int, reason: str) -> None:
        super().__init__(f"Request cancelled by client: {reason} (request {id})")


class UnknownFrameDecoderStateError(FramingError):
    def __init__(self) -> None:
        super().__init__("Unknown frame decoder state encountered")
