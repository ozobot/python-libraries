from __future__ import annotations

import datetime
import enum
import math
import typing
from dataclasses import dataclass

_IS_COLOR_EPSILON = 0.01


def _is_unknown_color_representation(color: object) -> typing.TypeIs[typing.Literal["unknown"]]:
    return color == "unknown"


type TNamedColor = typing.Literal["green", "black", "red", "blue", "white", "unknown"]


class Color:
    def __new__(cls, *args, **kwargs) -> Color:
        if cls is Color:
            return RawColor(*args, **kwargs)
        else:
            return super().__new__(cls)

    def is_color(self, other: Color, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        return False


@dataclass(frozen=True, eq=False, repr=False)
class RawColor(Color):
    red: float
    green: float
    blue: float

    def __post_init__(self) -> None:
        for name, value in zip(["red", "green", "blue"], [self.red, self.green, self.blue], strict=True):
            if value < 0 or value > 1:
                raise ValueError(f"Color component out of bounds [0, 1]: {name}={value}")

    def is_color(self, other: Color, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        if isinstance(other, RawColor):
            values = zip(
                (self.red, self.green, self.blue),
                (other.red, other.green, other.blue),
                strict=True,
            )
            return all([math.isclose(s, o, abs_tol=epsilon) for s, o in values])
        else:
            return other.is_color(self, epsilon=epsilon)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RawColor):
            return (self.red, self.green, self.blue) == (other.red, other.green, other.blue)
        elif isinstance(other, ClassifiedColor):
            return other == self  # this calls ClassifiedColor's __eq__
        else:
            return False

    def __hash__(self) -> int:
        return hash((self.__class__, self.red, self.green, self.blue))

    def __str__(self) -> str:
        red, green, blue = self.red, self.green, self.blue
        return f"{red=}, {green=}, {blue=}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"


@dataclass(frozen=True, eq=False, repr=False)
class ClassifiedColor(Color):
    name: TNamedColor
    _representation: RawColor | typing.Literal["unknown"]

    def is_color(self, other: Color, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        if _is_unknown_color_representation(self._representation):
            return False

        if isinstance(other, ClassifiedColor):
            return self == other
        elif isinstance(other, RawColor):
            return other.is_color(self._representation, epsilon=epsilon)
        else:
            return False

    def to_raw_color(self) -> RawColor:
        if _is_unknown_color_representation(self._representation):
            raise Exception("UNKNOWN color")  # TODO: fix

        return self._representation

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ClassifiedColor):
            return self.name == other.name
        elif isinstance(other, RawColor):
            return self._representation == other
        else:
            return False

    def __hash__(self) -> int:
        return hash((self.__class__, self.name))

    def __str__(self) -> str:
        if _is_unknown_color_representation(self._representation):
            return self._representation

        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self._representation!r})"


class Colors:
    BLACK = ClassifiedColor("black", RawColor(0, 0, 0))
    RED = ClassifiedColor("red", RawColor(1.0, 0, 0))
    GREEN = ClassifiedColor("green", RawColor(0, 1.0, 0))
    BLUE = ClassifiedColor("blue", RawColor(0, 0, 1.0))
    WHITE = ClassifiedColor("white", RawColor(1.0, 1.0, 1.0))
    UNKNOWN = ClassifiedColor("unknown", "unknown")


class LEDMask(enum.Flag):
    FRONT_CENTER = enum.auto()
    FRONT_LEFT = enum.auto()
    FRONT_LEFT_CENTER = enum.auto()
    FRONT_RIGHT = enum.auto()
    FRONT_RIGHT_CENTER = enum.auto()
    TOP = enum.auto()
    BACK = enum.auto()
    BUTTON = enum.auto()


class Direction(enum.Flag):
    BACKWARD = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    STRAIGHT = enum.auto()


type TNote = typing.Literal["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]


@dataclass(frozen=True, kw_only=True)
class ColorCode:
    colors: tuple[Color, ...]


class Sample[T]:
    @classmethod
    def now(cls, data: T) -> Sample[T]:
        return Sample(data, datetime.datetime.now())

    def __init__(self, data: T, timestamp: datetime.datetime | float) -> None:
        self.data = data
        self.timestamp = (
            timestamp if isinstance(timestamp, datetime.datetime) else datetime.datetime.fromtimestamp(timestamp)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sample):
            return False

        if other.data != self.data:
            return False

        return other.timestamp == self.timestamp
