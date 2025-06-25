import asyncio
import typing

import pytest
from ozobot.common.algebraic import ActorDispatcher
from ozobot.common.exceptions import (
    ActorAlreadyExistsError,
    ActorNotFoundError,
)


@typing.runtime_checkable
class _ValueStore(typing.Protocol):
    def get_val(self) -> str: ...
    async def aget_val(self) -> str: ...


class _ValueStore1:
    def __init__(self, val: str) -> None:
        self.val = val

    def get_val(self) -> str:
        return self.val.upper()

    async def aget_val(self) -> str:
        return self.val.upper()


class _ValueStore2:
    def __init__(self, val: str) -> None:
        self.val = val

    def get_val(self) -> str:
        return self.val.upper()

    async def aget_val(self) -> str:
        return self.val.upper()


class _DummyClass:
    def __init__(self, field: str) -> None:
        self.field = field

    def get_field_reverse(self) -> str:
        return self.field[::-1]


def test_dispatcher_get_property():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))

    with dispatcher.actor("one"):
        assert dispatcher.get_property(_ValueStore, str, "val") == "a"

    with dispatcher.actor("two"):
        assert dispatcher.get_property(_ValueStore, str, "val") == "b"

    dispatcher2 = ActorDispatcher()
    with pytest.raises(ActorNotFoundError):
        dispatcher2.get_property(_ValueStore, str, "val")


def test_dispatcher_call():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))

    with dispatcher.actor("one"):
        assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"

    with dispatcher.actor("two"):
        assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"


async def test_dispatcher_acall():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))

    with dispatcher.actor("one"):
        assert (await dispatcher.acall(_ValueStore, _ValueStore.aget_val)) == "A"

    with dispatcher.actor("two"):
        assert (await dispatcher.acall(_ValueStore, _ValueStore.aget_val)) == "B"


def test_dispatcher_actor_not_found():
    dispatcher = ActorDispatcher()
    with pytest.raises(ActorNotFoundError):
        with dispatcher.actor("missing"):
            pass


def test_dispatcher_actor_already_exists():
    dispatcher = ActorDispatcher()
    with pytest.raises(ActorAlreadyExistsError):
        dispatcher.add("one", _ValueStore1(""))
        dispatcher.add("one", _ValueStore1(""))


def test_dispatcher_nested():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))

    with dispatcher.actor("one"):
        assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"

        with dispatcher.actor("two"):
            assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"

            with dispatcher.actor("one"):
                assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"

            assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"

        assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"


def test_dispatcher_protocol():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))
    dispatcher.add("three", _DummyClass("dummy"))

    with dispatcher.actor("one"):
        assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"

        with dispatcher.actor("two"):
            assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"

            with dispatcher.actor("three"):
                assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"
                assert dispatcher.call(_DummyClass, _DummyClass.get_field_reverse) == "ymmud"


async def test_dispatcher_state_consistency_concurrent():
    dispatcher = ActorDispatcher()
    dispatcher.add("one", _ValueStore1("a"))
    dispatcher.add("two", _ValueStore2("b"))

    async def task_one():
        for _ in range(10):
            with dispatcher.actor("one"):
                await asyncio.sleep(0.01)
                assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "A"

    async def task_two():
        for _ in range(10):
            with dispatcher.actor("two"):
                await asyncio.sleep(0.01)
                assert dispatcher.call(_ValueStore, _ValueStore.get_val) == "B"

    await asyncio.gather(task_one(), task_two())
