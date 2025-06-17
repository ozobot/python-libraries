from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True)
class Color:
    red: float
    green: float
    blue: float


class Colors:
    BLACK = Color(0, 0, 0)
    RED = Color(1, 0, 0)
    GREEN = Color(0, 1, 0)
    BLUE = Color(0, 0, 1)
    WHITE = Color(1, 1, 1)
    CYAN = Color(0, 1, 1)
    MAGENTA = Color(1, 0, 1)
    YELLOW = Color(1, 1, 0)


TDirection: TypeAlias = Literal["backward", "left", "right", "straight"]


class LEDMask(enum.Flag):
    FRONT_CENTER = enum.auto()
    FRONT_LEFT = enum.auto()
    FRONT_LEFT_CENTER = enum.auto()
    FRONT_RIGHT = enum.auto()
    FRONT_RIGHT_CENTER = enum.auto()
    TOP = enum.auto()

class Intersection(enum.Flag):
    BACKWARD = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    STRAIGHT = enum.auto()
