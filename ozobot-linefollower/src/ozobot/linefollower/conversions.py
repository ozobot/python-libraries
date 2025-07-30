import typing

from ozobot.linefollower.datatypes import Sample


class _HasTimestamp(typing.Protocol):
    timestamp: int


def sample_from_protocol[T: _HasTimestamp, U](protocol_data: T, convertor: typing.Callable[[T], U]) -> Sample[U]:
    return Sample(
        convertor(protocol_data),
        protocol_data.timestamp,
    )
