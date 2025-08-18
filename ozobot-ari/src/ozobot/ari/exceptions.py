from ozobot.common.exceptions import OzobotError


class TransportError(OzobotError): ...


class DuplicateMessageIdError(TransportError):
    def __init__(self, id: int) -> None:
        super().__init__(f"Request with this message id is already pending: {id}")


class UnknownMessageIdError(TransportError):
    def __init__(self, id: int) -> None:
        super().__init__(f"Message with this message id is unexpected: {id}")


class MalformedMessageError(TransportError):
    def __init__(self) -> None:
        super().__init__("Unable to parse received message")


class AriProtocolError(OzobotError): ...


class AriProtocolCommandError(AriProtocolError):
    def __init__(self, command: str, return_value: str, *, description: str | None = None) -> None:
        if description:
            details = f"(returned: {return_value}, description: {description})"
        else:
            details = f"({return_value})"

        super().__init__(f"Ari protocol command failed: {command} {details}")


class DriverError(OzobotError): ...


class MemoryWriteUnsuccessfulError(DriverError):
    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Could not write virtual memory value: '{reason}' on {name}'")


class MemoryReadUnsuccessfulError(DriverError):
    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Could not read virtual memory: '{reason}' on '{name}'")


class UnexpectedUserIoPromptOptionTypeError(DriverError):
    def __init__(self, option: object, _type: type) -> None:
        super().__init__(
            f"Unexpected user io prompt option: '{option}' has type '{type(option)!r}' but '{_type!r}' expected"
        )


class UnexpectedUserIoPromptResponseReceivedError(DriverError):
    def __init__(self, value: object, _type: type) -> None:
        super().__init__(
            f"Unexpected user io prompt response received: {value} has type {type(value)!r} but '{_type!r}' expected"
        )


class UnexpectedUserIoPromptTypeError(DriverError):
    def __init__(self, _type: type) -> None:
        super().__init__(f"Unexpected user io prompt type given: {_type!r}")
