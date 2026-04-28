from ozobot.common.exceptions import OzobotError


class ActorError(OzobotError):
    """Base exception for actor errors."""


class ActorNotFoundError(ActorError):
    def __init__(self, actor: str):
        super().__init__(f"Actor not found: {actor}", context={"name": actor})


class SuitableActorNotFoundError(ActorError):
    def __init__(self, method: str, *, compatible: list[str] | None = None):
        context: dict[str, str | list[str]] = {
            "method": method,
        }

        if compatible:
            context["compatibleDevices"] = compatible
        super().__init__(f"No suitable actor found: {method}", context=context)


class ActorAlreadyExistsError(ActorError):
    def __init__(self, actor: str):
        super().__init__(f"Actor already exists: {actor}")


class CorruptedStateError(ActorError):
    def __init__(self):
        super().__init__("Corrupted state: actor stack mismatch")
