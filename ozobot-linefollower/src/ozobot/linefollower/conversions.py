import typing

from ozobot.linefollower.datatypes import Sample, TDirection, TNamedColor


class _HasTimestamp(typing.Protocol):
    @property
    def timestamp(self) -> float: ...


def sample_from_protocol[T: _HasTimestamp, U](protocol_data: T, convertor: typing.Callable[[T], U]) -> Sample[U]:
    return Sample(
        convertor(protocol_data),
        protocol_data.timestamp,
    )


ALLOWED_NAMED_COLORS = typing.get_args(TNamedColor.__value__)
ALLOWED_NAMED_DIRECTIONS = typing.get_args(TDirection.__value__)


def is_named_color(value: typing.Any) -> typing.TypeGuard[TNamedColor]:
    return value in ALLOWED_NAMED_COLORS


def is_named_direction(value: typing.Any) -> typing.TypeGuard[TDirection]:
    return value in ALLOWED_NAMED_DIRECTIONS
