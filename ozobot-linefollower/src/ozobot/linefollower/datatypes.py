from __future__ import annotations

import datetime
import enum
import math
import typing
from dataclasses import dataclass

_IS_COLOR_EPSILON = 0.01


type TNamedColor = typing.Literal["Green", "Black", "Red", "Blue", "White"]
type TDirection = typing.Literal["Forward", "Back", "Left", "Right"]


class Color:
    def is_color(self, other: Color | None, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
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

    def is_color(self, other: Color | None, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        if other is None:
            return False
        elif isinstance(other, RawColor):
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
    _representation: RawColor

    def is_color(self, other: Color | None, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        if isinstance(other, ClassifiedColor):
            return self == other
        elif isinstance(other, RawColor):
            return other.is_color(self._representation, epsilon=epsilon)
        else:
            return False

    def to_raw_color(self) -> RawColor:
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
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self._representation!r})"


class Colors:
    BLACK = ClassifiedColor("Black", RawColor(0, 0, 0))
    RED = ClassifiedColor("Red", RawColor(1.0, 0, 0))
    GREEN = ClassifiedColor("Green", RawColor(0, 1.0, 0))
    BLUE = ClassifiedColor("Blue", RawColor(0, 0, 1.0))
    WHITE = ClassifiedColor("White", RawColor(1.0, 1.0, 1.0))


class LEDMask(enum.Flag):
    FRONT_CENTER = enum.auto()
    FRONT_LEFT = enum.auto()
    FRONT_LEFT_CENTER = enum.auto()
    FRONT_RIGHT = enum.auto()
    FRONT_RIGHT_CENTER = enum.auto()
    TOP = enum.auto()
    BACK = enum.auto()
    BUTTON = enum.auto()
    ALL_FRONT = FRONT_LEFT | FRONT_LEFT_CENTER | FRONT_CENTER | FRONT_RIGHT_CENTER | FRONT_RIGHT
    ALL_ROBOT = ALL_FRONT | TOP | BACK | BUTTON


class Direction(enum.Flag):
    BACKWARD = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    STRAIGHT = enum.auto()


type TNote = typing.Literal["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]


@dataclass(frozen=True, kw_only=True)
class ColorCode:
    colors: tuple[ClassifiedColor, ...]


@dataclass(frozen=True, kw_only=True)
class IRMessage:
    message: int
    intensity: int


@dataclass(frozen=True, kw_only=True)
class IRProximity:
    right_front: int
    left_front: int
    right_rear: int
    left_rear: int


@dataclass(frozen=True, kw_only=True)
class TimeOfFlight:
    distance: float
    deviation: float


class Sample[T]:
    @classmethod
    def now(cls, data: T) -> Sample[T]:
        return Sample(data, datetime.datetime.now())

    def __init__(self, value: T, timestamp: datetime.datetime | float) -> None:
        self.value = value
        self.timestamp = (
            timestamp if isinstance(timestamp, datetime.datetime) else datetime.datetime.fromtimestamp(timestamp / 1000)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sample):
            return False

        if other.value != self.value:
            return False

        return other.timestamp == self.timestamp


@dataclass(frozen=True, kw_only=True)
class RobotGeometry:
    ticks_per_meter: float
    wheel_track: float
    wheel_diameter: float
    encoder_ticks_per_wheel_revolution: float
    max_speed_limit: float
