import contextlib
import contextvars
import typing
from dataclasses import dataclass

from ozobot.common.exceptions import (
    ActorAlreadyExistsError,
    ActorNotFoundError,
    SuitableActorNotFoundError,
)


@dataclass(frozen=True)
class _Masked:
    name: str


@dataclass(frozen=True)
class _Selected:
    name: str


class ActorDispatcher:
    def __init__(self) -> None:
        self._stack = contextvars.ContextVar[tuple[_Masked | _Selected, ...]]("stack", default=tuple())
        self._actors: dict[str, typing.Any] = {}

    def add(self, name: str, actor: typing.Any) -> None:
        """
        Add an existing actor to the dispatcher.

        Example:

        .. code-block:: python

            from ozobot import actors

            dispatcher = actors.new_actor_dispatcher()

            async with EvoHandle(name="Evo-ABCDE") as e:
                dispatcher.add("MyEvo", e)
        """

        if name in self._actors:
            raise ActorAlreadyExistsError(name)
        self._actors[name] = actor

    def _remove(self, name: str) -> None:
        if name not in self._actors:
            raise ActorNotFoundError(name)

        self._actors.pop(name)

    @contextlib.asynccontextmanager
    async def connect[T](self, name: str, handle: contextlib.AbstractAsyncContextManager[T]) -> typing.AsyncIterator[T]:
        """
        Open the given handle, add it as an actor and close on exit.

        Example:

        .. code-block:: python

            from ozobot import actors

            dispatcher = actors.new_actor_dispatcher()

            async with dispatcher.connect("MyEvo", EvoHandle(name="Evo-ABCDE"):
                ...

        Calling this is roughly equivalent to:

        .. code-block:: python

            from ozobot import actors

            dispatcher = actors.new_actor_dispatcher()

            async with EvoHandle(name="Evo-ABCDE") as e:
                dispatcher.add("MyEvo", e)


        """
        async with handle as instance:
            self.add(name, instance)
            try:
                yield instance
            finally:
                self._remove(name)

    @contextlib.contextmanager
    def actor(self, *names: str) -> typing.Iterator[None]:
        """
        Pushe the agent on top of the stack.

        Example:

        .. code-block:: python

            from ozobot import actors

            dispatcher = actors.new_actor_dispatcher()

            async with dispatcher.connect("MyEvo", EvoHandle(name="Evo-ABCDE"):
                with dispatcher.actor("MyEvo"):
                    # evo is selected here

        """
        for name in names:
            if name not in self._actors:
                raise ActorNotFoundError(name)

        actor_objects = [_Selected(name) for name in names]
        new_stack = tuple(reversed(actor_objects)) + self._stack.get()
        context_token = self._stack.set(new_stack)

        try:
            yield
        finally:
            self._stack.reset(context_token)

    @contextlib.contextmanager
    def mask(self, *names: str, all: bool = False) -> typing.Iterator[None]:
        """
        Mask the agent on top of the stack.

        Example:

        .. code-block:: python

            from ozobot import actors

            dispatcher = actors.new_actor_dispatcher()

            async with dispatcher.connect("MyEvo", EvoHandle(name="Evo-ABCDE"):
                with dispatcher.mask("MyEvo"):
                    # evo won't be accessible here

                    with dispatcher.agent("MyEvo"):
                        # the masking gets overwritten again
        """
        if all:
            names = tuple(self._actors.keys())

        for name in names:
            if name not in self._actors:
                raise ActorNotFoundError(name)

        mask_objects = [_Masked(name) for name in names]
        new_stack = tuple(reversed(mask_objects)) + self._stack.get()
        context_token = self._stack.set(new_stack)

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

    def _iterate_actors(self) -> typing.Iterator[typing.Any]:
        masked = set()
        items_with_defaults = [*self._stack.get(), *[_Selected(a) for a in self._actors.keys()]]
        for actor in items_with_defaults:
            if actor.name in self._actors:
                if isinstance(actor, _Masked):
                    masked.add(actor.name)
                elif actor.name not in masked:
                    yield self._actors[actor.name]

    def _find_field_in_stack[U](self, _type: type[U], name: str) -> tuple[typing.Any, U]:
        for actor in self._iterate_actors():
            if hasattr(actor, name):
                _callable = getattr(actor, name)
                if not callable(_callable):
                    return actor, getattr(actor, name)

        raise SuitableActorNotFoundError(f"missing property {name}")

    def _find_callable_in_stack[U, **P](
        self, _type: typing.Callable[typing.Concatenate[typing.Any, P], U]
    ) -> tuple[typing.Any, typing.Callable[P, U]]:
        name = _type.__name__
        for actor in self._iterate_actors():
            if hasattr(actor, name):
                _callable = getattr(actor, name)
                if callable(_callable):
                    return actor, getattr(actor, name)

        raise SuitableActorNotFoundError(f"missing callable {name}")


class _Context:
    def __init__(self, dispatcher: ActorDispatcher) -> None:
        self.dispatcher = dispatcher


context = _Context(ActorDispatcher())


def set_actor_dispatcher(dispatcher: ActorDispatcher) -> None:
    context.dispatcher = dispatcher


def new_actor_dispatcher() -> ActorDispatcher:
    """
    Create new actor dispatcher and overwrite the old one.
    """
    dispatcher = ActorDispatcher()
    context.dispatcher = dispatcher

    return dispatcher
