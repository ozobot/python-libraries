class WebRTCError(Exception): ...


class SignalingError(WebRTCError): ...


class UnknownSdpTypeError(SignalingError):
    def __init__(self, received: str) -> None:
        super().__init__(f"Received unknown sdp type: {received}")


class ConsumerAlreadyUsedError(SignalingError):
    def __init__(self) -> None:
        super().__init__("Consumer is already being consumed")


class QueueReaderError(WebRTCError): ...


class QueueReaderNotEnteredError(QueueReaderError):
    def __init__(self) -> None:
        super().__init__("QueueReader context manager is not entered")


class QueueReaderConcurrentUseNotSupportedError(QueueReaderError):
    def __init__(self) -> None:
        super().__init__("QueueReader can only be used by one context at a time")


class QueueReaderClosedError(QueueReaderError):
    def __init__(self) -> None:
        super().__init__("QueueReader is closed, open a new one")


class WebRTCChannelUnexpectedDatatypeError(WebRTCError):
    def __init__(self, expected: type, received: type) -> None:
        super().__init__(f"Unexpected message type received (expected {expected}, got {received})")


class WebRTCConnectionUnexpectedStateError(WebRTCError):
    def __init__(self, state: str) -> None:
        super().__init__(f"Unexpected WebRTC connection state: {state}")


class CouldNotGetSignalingTokenError(SignalingError):
    def __init__(self, status: int, text: str) -> None:
        super().__init__(f"Getting signaling token failed with {status}: {text}")
