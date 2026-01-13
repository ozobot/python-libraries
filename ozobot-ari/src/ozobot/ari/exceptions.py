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
    """Virtual memory write operation fails."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Could not write virtual memory value: '{reason}' on {name}'")


class MemoryReadUnsuccessfulError(DriverError):
    """Virtual memory read operation fails."""

    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Could not read virtual memory: '{reason}' on '{name}'")
