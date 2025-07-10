from ozobot.common.exceptions import OzobotError


class FramingError(OzobotError): ...


class UnknownFrameDecoderStateError(FramingError):
    def __init__(self) -> None:
        super().__init__("Unknown frame decoder state encountered")
