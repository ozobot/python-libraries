class OzobotProtocolCommandError(Exception):
    def __init__(self, command: str, return_value: str, *, description: str | None = None) -> None:
        if description:
            details = f"(returned: {return_value}, description: {description})"
        else:
            details = f"({return_value})"

        super().__init__(f"Protocol command failed: {command} {details}")


class OzobotDataTypeError(Exception):
    def __init__(self, expected_type: type, received_type: type) -> None:
        super().__init__(f"Unexpected type: expected '{expected_type}' but got '{received_type}'")


class AlgebraicError(Exception):
    """Base exception for algebraic errors."""

    pass


class ActorNotFoundError(AlgebraicError):
    def __init__(self, actor: str):
        super().__init__(f"Actor not found: {actor}")


class ActorAlreadyExistsError(AlgebraicError):
    def __init__(self, actor: str):
        super().__init__(f"Actor already exists: {actor}")


class CorruptedStateError(AlgebraicError):
    def __init__(self):
        super().__init__("Corrupted state: actor stack mismatch")
