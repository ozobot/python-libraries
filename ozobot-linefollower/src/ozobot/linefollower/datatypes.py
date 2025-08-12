from __future__ import annotations

import datetime
import enum
import math
import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    red: float
    green: float
    blue: float

    @property
    def is_unknown(self) -> bool:
        return math.isnan(self.red) or math.isnan(self.green) or math.isnan(self.blue)


class Colors:
    BLACK = Color(0, 0, 0)
    RED = Color(1, 0, 0)
    GREEN = Color(0, 1, 0)
    BLUE = Color(0, 0, 1)
    WHITE = Color(1, 1, 1)
    CYAN = Color(0, 1, 1)
    MAGENTA = Color(1, 0, 1)
    YELLOW = Color(1, 1, 0)
    UNKNOWN = Color(float("nan"), float("nan"), float("nan"))


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


TNote: typing.TypeAlias = typing.Literal["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]


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
