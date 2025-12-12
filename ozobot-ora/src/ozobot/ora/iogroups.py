from __future__ import annotations

import typing

from ozobot.ora.datatypes import IoName, IoValueType
from ozobot.ora.sync import OraSync

_TIo = typing.TypeVar("_TIo", bool, float)


class InputGroup(typing.Generic[_TIo]):
    """A group of inputs that can be read together."""

    _inputs: typing.Sequence[IoName[_TIo]]
    _ora: OraSync

    def __init__(self, ora: OraSync, inputs: typing.Sequence[IoName[_TIo]]):
        self._inputs = inputs
        self._ora = ora

    def read(self) -> typing.Sequence[_TIo]:
        return self._ora.read_input(self._inputs)

    def wait(self, predicate: typing.Callable[[list[_TIo]], bool]) -> typing.Sequence[_TIo]:
        return self._ora.wait_for_input(self._inputs, predicate)


class OutputGroup(typing.Generic[_TIo]):
    """A group of outputs that can be written together."""

    _outputs: typing.Sequence[IoName[_TIo]]
    _ora: OraSync

    def __init__(self, ora: OraSync, outputs: typing.Sequence[IoName[_TIo]]):
        self._outputs = outputs
        self._ora = ora

    def write(self, values: typing.Sequence[_TIo]) -> None:
        self._ora.write_output(dict(zip(self._outputs, values, strict=False)))


class Input(typing.Generic[_TIo]):
    """A single input that can be read."""

    _group: InputGroup[_TIo]

    def __init__(self, ora: OraSync, io: IoName[_TIo]):
        self._group = InputGroup[_TIo](ora, [io])

    def read(self) -> _TIo:
        return self._group.read()[0]

    def wait(self, predicate: typing.Callable[[_TIo], bool]) -> _TIo:
        return self._group.wait(lambda i: predicate(i[0]))[0]


class Output(typing.Generic[_TIo]):
    """A single output that can be written."""

    _group: OutputGroup[_TIo]

    def __init__(self, ora: OraSync, io: IoName[_TIo]):
        self._group = OutputGroup[_TIo](ora, [io])

    def write(self, value: _TIo):
        return self._group.write([value])


class InputFactory(typing.Generic[_TIo]):
    """A factory for creating input groups and inputs."""

    _value_type: IoValueType
    _ora: OraSync

    @typing.overload
    @classmethod
    def _create(cls, ora: OraSync, type: typing.Literal[IoValueType.ANALOG]) -> InputFactory[float]: ...

    @typing.overload
    @classmethod
    def _create(cls, ora: OraSync, type: typing.Literal[IoValueType.DIGITAL]) -> InputFactory[bool]: ...

    @classmethod
    def _create(cls, ora: OraSync, type: IoValueType) -> InputFactory[float] | InputFactory[bool]:
        return InputFactory(ora, type)

    def __init__(self, ora: OraSync, value_type: IoValueType):
        self._value_type = value_type
        self._ora = ora

    @typing.overload
    def __getitem__(self, item: int) -> Input[_TIo]: ...

    @typing.overload
    def __getitem__(self, item: tuple[int, ...] | slice) -> InputGroup[_TIo]: ...

    def __getitem__(self, item: int | tuple[int, ...] | slice) -> Input[_TIo] | InputGroup[_TIo]:
        expanded_item = _expand_item(item)
        if isinstance(expanded_item, list):
            return InputGroup[_TIo](self._ora, [IoName(index, self._value_type) for index in expanded_item])
        return Input[_TIo](self._ora, IoName(expanded_item, self._value_type))


class OutputFactory(typing.Generic[_TIo]):
    """A factory for creating output groups and outputs."""

    _value_type: IoValueType
    _ora: OraSync

    @typing.overload
    @classmethod
    def _create(cls, ora: OraSync, type: typing.Literal[IoValueType.ANALOG]) -> OutputFactory[float]: ...

    @typing.overload
    @classmethod
    def _create(cls, ora: OraSync, type: typing.Literal[IoValueType.DIGITAL]) -> OutputFactory[bool]: ...

    @classmethod
    def _create(cls, ora: OraSync, type: IoValueType) -> OutputFactory[float] | OutputFactory[bool]:
        return OutputFactory(ora, type)

    def __init__(self, ora: OraSync, value_type: IoValueType):
        self._value_type = value_type
        self._ora = ora

    @typing.overload
    def __getitem__(self, item: int) -> Output[_TIo]: ...

    @typing.overload
    def __getitem__(self, item: tuple[int, ...] | slice) -> OutputGroup[_TIo]: ...

    def __getitem__(self, item: int | tuple[int, ...] | slice) -> Output[_TIo] | OutputGroup[_TIo]:
        expanded_item = _expand_item(item)
        if isinstance(expanded_item, list):
            return OutputGroup[_TIo](self._ora, [IoName(index, self._value_type) for index in expanded_item])
        return Output[_TIo](self._ora, IoName(expanded_item, self._value_type))


def _expand_item(item: int | tuple[int, ...] | slice) -> int | list[int]:
    if isinstance(item, int):
        return item
    elif isinstance(item, tuple):
        return list(item)
    elif isinstance(item, slice):
        start = item.start or 0
        stop = item.stop or 0
        step = item.step or 1
        return list(range(start, stop, step))
    else:
        raise ValueError(f"Invalid IO: {item}")
