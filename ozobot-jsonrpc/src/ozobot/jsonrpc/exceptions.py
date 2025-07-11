from ozobot.common.exceptions import OzobotError


class FramingError(OzobotError): ...


class CancelledByServerError(OzobotError):
    def __init__(self, id: int, code: int, message: str) -> None:
        super().__init__(f"Request cancelled by server: {code} - {message} (request {id})")


class CancelledByClientError(OzobotError):
    def __init__(self, id: int, reason: str) -> None:
        super().__init__(f"Request cancelled by client: {reason} (request {id})")


class UnknownFrameDecoderStateError(FramingError):
    def __init__(self) -> None:
        super().__init__("Unknown frame decoder state encountered")
