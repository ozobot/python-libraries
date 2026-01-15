from ozobot.common.exceptions import OzobotError


class EvoError(OzobotError):
    """Base EVO error"""


class OzobotProtocolCommandError(EvoError):
    def __init__(self, command: str, return_value: str, *, description: str | None = None) -> None:
        if description:
            details = f"(returned: {return_value}, description: {description})"
        else:
            details = f"({return_value})"

        super().__init__(f"Protocol command failed: {command} {details}")


class OzobotDataTypeError(EvoError):
    def __init__(self, expected_type: type, received_type: type) -> None:
        super().__init__(f"Unexpected type: expected '{expected_type}' but got '{received_type}'")


class UnsupportedColorCodeNumberError(EvoError):
    def __init__(self, number: int) -> None:
        super().__init__(f"Received color code has unsupported color segment: {number}")
