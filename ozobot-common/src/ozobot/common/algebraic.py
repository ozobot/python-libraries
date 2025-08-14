import contextlib
import contextvars
import typing

from ozobot.common.exceptions import (
    ActorAlreadyExistsError,
    ActorNotFoundError,
    SuitableActorNotFoundError,
)


class ActorDispatcher:
    def __init__(self) -> None:
        default: tuple[typing.Any, ...] = tuple()
        self._stack = contextvars.ContextVar[tuple[typing.Any]]("stack", default=default)
        self._actors: dict[str, typing.Any] = {}

    def add(self, name: str, actor: typing.Any) -> None:
        if name in self._actors:
            raise ActorAlreadyExistsError(name)
        self._actors[name] = actor

    @contextlib.contextmanager
    def actor(self, *names: str) -> typing.Iterator[None]:
        for name in names:
            if name not in self._actors:
                raise ActorNotFoundError(name)

        actor_objects = [self._actors[name] for name in names]
        new_stack = tuple(reversed(actor_objects)) + self._stack.get()
        context_token = self._stack.set(new_stack)

        try:
            yield
        finally:
            self._stack.reset(context_token)

    @contextlib.contextmanager
    def mask(self, *names: str, all: bool = False) -> typing.Iterator[None]:
        for name in names:
            if name not in self._actors:
                raise ActorNotFoundError(name)

        if all:
            new_stack = []
        else:
            # select actors that are in `names` and in the stack at the same time
            actor_objects = [self._actors[name] for name in names]
            valid_actor_objects = set(self._stack.get()).intersection(actor_objects)
            new_stack = [*self._stack.get()]
            for obj in valid_actor_objects:
                new_stack.remove(obj)

        context_token = self._stack.set(tuple(new_stack))

        try:
            yield
        finally:
            self._stack.reset(context_token)

    def get_property[U](self, value_type: type[U], name: str) -> U:
        actor, property = self._find_field_in_stack(value_type, name)
        return property

    def call[U, **P](
        self,
        template: typing.Callable[typing.Concatenate[typing.Any, P], U],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> U:
        actor, method = self._find_callable_in_stack(template)
        return method(*args, **kwargs)

    async def acall[U, **P](
        self,
        template: typing.Callable[typing.Concatenate[typing.Any, P], typing.Coroutine[None, None, U]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> U:
        actor, method = self._find_callable_in_stack(template)
        return await method(*args, **kwargs)

    def _find_field_in_stack[U](self, _type: type[U], name: str) -> tuple[typing.Any, U]:
        for actor in self._stack.get():
            if hasattr(actor, name):
                _callable = getattr(actor, name)
                if not callable(_callable):
                    return actor, getattr(actor, name)

        raise SuitableActorNotFoundError(f"missing property {name}")

    def _find_callable_in_stack[U, **P](
        self, _type: typing.Callable[typing.Concatenate[typing.Any, P], U]
    ) -> tuple[typing.Any, typing.Callable[P, U]]:
        name = _type.__name__
        for actor in self._stack.get():
            if hasattr(actor, name):
                _callable = getattr(actor, name)
                if callable(_callable):
                    return actor, getattr(actor, name)

        raise SuitableActorNotFoundError(f"missing callable {name}")


dispatcher = ActorDispatcher()
