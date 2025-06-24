import contextlib
import typing
from ozobot.common.exceptions import (
    ActorNotFoundError,
    ActorAlreadyExistsError,
    CorruptedStateError,
)


class ActorDispatcher[T]:
    def __init__(self) -> None:
        self._stack: list[T] = []
        self._actors: dict[str, T] = {}

    def add(self, name: str, actor: T) -> None:
        if name in self._actors:
            raise ActorAlreadyExistsError(name)
        self._actors[name] = actor

    @contextlib.contextmanager
    def actor(self, name: str) -> typing.Iterator[None]:
        if name not in self._actors:
            raise ActorNotFoundError(name)
        actor = self._actors[name]
        self._stack.insert(0, actor)
        yield
        a = self._stack.pop(0)

        if a != actor:
            raise CorruptedStateError()

    def get_property[U](self, actor_type: type[T], value_type: type[U], name: str) -> U:
        actor = self._find_in_stack(actor_type)
        property: U = getattr(actor, name)
        return property

    def call[U, **P](
        self,
        actor_type: type[T],
        template: typing.Callable[typing.Concatenate[T, P], U],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> U:
        actor = self._find_in_stack(actor_type)
        method: typing.Callable[P, U] = getattr(actor, template.__name__)
        return method(*args, **kwargs)

    async def acall[U, **P](
        self,
        actor_type: type[T],
        template: typing.Callable[typing.Concatenate[T, P], typing.Coroutine[None, None, U]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> U:
        actor = self._find_in_stack(actor_type)
        method: typing.Callable[P, typing.Coroutine[None, None, U]] = getattr(actor, template.__name__)
        return await method(*args, **kwargs)

    def _find_in_stack[U](self, _type: type[U]) -> U:
        for actor in self._stack:
            if isinstance(actor, _type):
                return actor

        raise ActorNotFoundError(str(_type))
