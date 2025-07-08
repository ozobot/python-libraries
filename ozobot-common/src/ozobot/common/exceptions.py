class OzobotError(Exception):
    """Base Ozobot library error"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AlgebraicError(Exception):
    """Base exception for algebraic errors."""


class ActorNotFoundError(AlgebraicError):
    def __init__(self, actor: str):
        super().__init__(f"Actor not found: {actor}")


class SuitableActorNotFoundError(AlgebraicError):
    def __init__(self, description: str):
        super().__init__(f"No suitable actor found: {description}")


class ActorAlreadyExistsError(AlgebraicError):
    def __init__(self, actor: str):
        super().__init__(f"Actor already exists: {actor}")


class CorruptedStateError(AlgebraicError):
    def __init__(self):
        super().__init__("Corrupted state: actor stack mismatch")
