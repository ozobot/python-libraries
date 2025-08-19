class OzobotError(Exception):
    """Base Ozobot library error"""

    @property
    def context(self) -> dict[str, str]:
        return self._context

    def __init__(self, message: str, *, context: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self._context = context or {}

    def add_context(self, key: str, value: str) -> None:
        self._context[key] = value

    def __str__(self) -> str:
        context_lines = [f"{k}={v}" for k, v in self._context.items()]
        return "\n".join([self.args[0], *context_lines])

    def __repr__(self) -> str:
        message_str = f'"{self.args[0]}"'
        if self._context:
            context_items = [f'"{k}": "{v}"' for k, v in self._context.items()]
            context_str = f"context={{{', '.join(context_items)}}}"
            args = [message_str, context_str]
        else:
            args = [message_str]
        name = self.__class__.__name__
        return f"{name}({', '.join(args)})"


class ActorError(Exception):
    """Base exception for actor errors."""


class ActorNotFoundError(ActorError):
    def __init__(self, actor: str):
        super().__init__(f"Actor not found: {actor}")


class SuitableActorNotFoundError(ActorError):
    def __init__(self, description: str):
        super().__init__(f"No suitable actor found: {description}")


class ActorAlreadyExistsError(ActorError):
    def __init__(self, actor: str):
        super().__init__(f"Actor already exists: {actor}")


class CorruptedStateError(ActorError):
    def __init__(self):
        super().__init__("Corrupted state: actor stack mismatch")
