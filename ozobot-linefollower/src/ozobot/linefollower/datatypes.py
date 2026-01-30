from __future__ import annotations

import abc
import enum
import math
import typing
from dataclasses import dataclass

_IS_COLOR_EPSILON = 0.01


type TNamedColor = typing.Literal["Green", "Black", "Red", "Blue", "White"]
type TDirection = typing.Literal["Forward", "Back", "Left", "Right"]


class Color(abc.ABC):
    """
    Abstract color representation.

    .. seealso::
        You will never need to instantiate this class, take a look on the referenced implementations instead.

        - :py:class:`RawColor`
        - :py:class:`ClassifiedColor`
    """

    @abc.abstractmethod
    def is_color(self, other: Color | None, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        """
        Compare similarity with other color.

        Compares with other :py:class:`ClassifiedColor` or :py:class:`RawColor`.

        :param other: Color to compare this color to
        :param epsilon: Maximum numeric RGB difference when comparing raw colors
        """


@dataclass(frozen=True, eq=False, repr=False)
class RawColor(Color):
    """
    RGB color.

    A color reading that was not classified and therefore has no known name. This color cannot be used in all places where
    :py:class:`ClassifiedColor` can. For example, one can use this class to set LED color, but cannot use it to say color from
    the speaker.

    .. seealso::
        A classified color with a name can be defined by :py:class:`ClassifiedColor`.
    """

    red: float
    """Red component in range 0.0 - 1.0"""

    green: float
    """Green component in range 0.0 - 1.0"""

    blue: float
    """Blue component in range 0.0 - 1.0"""

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
    """
    Classified color with name.

    Can be compared to other colors or converted to :py:class:`RawColor`

    .. seealso::
        Predefined colors are available as properties of this class, for example :py:attr:`ClassifiedColor.BLACK`.
        Generic (unclassified) color can be defined by :py:class:`RawColor`.
    """

    name: TNamedColor
    _representation: RawColor

    # we had to define the values below the clas definition because:
    #     - direct assignment is not possible as the class is not yet fully parsed when the individual fields are being assigned to
    #     - properties cannot be used in dataclasses
    #     - ClassVar cannot be used with dataclass.field
    BLACK: typing.ClassVar[ClassifiedColor]
    """Predefined color constant - black"""

    RED: typing.ClassVar[ClassifiedColor]
    """Predefined color constant - red"""

    GREEN: typing.ClassVar[ClassifiedColor]
    """Predefined color constant - green"""

    BLUE: typing.ClassVar[ClassifiedColor]
    """Predefined color constant - blue"""

    WHITE: typing.ClassVar[ClassifiedColor]
    """Predefined color constant - white"""

    def is_color(self, other: Color | None, *, epsilon: float = _IS_COLOR_EPSILON) -> bool:
        if isinstance(other, ClassifiedColor):
            return self == other
        elif isinstance(other, RawColor):
            return other.is_color(self._representation, epsilon=epsilon)
        else:
            return False

    def to_raw_color(self) -> RawColor:
        """
        Convert to :py:class:`RawColor`.
        """
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


ClassifiedColor.BLACK = ClassifiedColor("Black", RawColor(0, 0, 0))
ClassifiedColor.RED = ClassifiedColor("Red", RawColor(1.0, 0, 0))
ClassifiedColor.GREEN = ClassifiedColor("Green", RawColor(0, 1.0, 0))
ClassifiedColor.BLUE = ClassifiedColor("Blue", RawColor(0, 0, 1.0))
ClassifiedColor.WHITE = ClassifiedColor("White", RawColor(1.0, 1.0, 1.0))


class LEDMask(enum.Flag):
    """
    LED selector mask.

    Can be combined into a broader mask by using union operator:
    .. code-block::

        # select front center
        mask_c = LEDMask.FRONT_CENTER

        # select left and right
        mask_lr = LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT

        # convert the mask to a list
        assert list(mask_lr) == [LEDMask.FRONT_LEFT, LEDMask.FRONT_RIGHT]
    """

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
    """
    Direction.

    Can be combined into a broader direction set by using union operator:
    .. code-block::

        # select front center
        mask_c = LEDMask.FRONT_CENTER

        # select left and right
        mask_lr = LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT

        # convert the mask to a list
        assert list(mask_lr) == [LEDMask.FRONT_LEFT, LEDMask.FRONT_RIGHT]
    """

    BACKWARD = enum.auto()
    LEFT = enum.auto()
    RIGHT = enum.auto()
    STRAIGHT = enum.auto()


type TNote = typing.Literal["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
"""
Strings recognized as notes.
"""


type TAudio = typing.Literal["laugh", "happy", "sad", "surprised"]
"""
    Strings recognized as audio name.
"""


@dataclass(frozen=True, kw_only=True)
class ColorCode:
    """
    Color code detected by the robot.
    """

    colors: tuple[ClassifiedColor, ...]


@dataclass(frozen=True, kw_only=True)
class IRMessage:
    """
    IR message sensoric data.
    """

    message: int
    intensity: int


@dataclass(frozen=True, kw_only=True)
class TimeOfFlight:
    """
    Time of flight sensor readout
    """

    distance_mm: float
    deviation_mm: float


class SampleWithoutTimestamp[T]:
    """
    Data sample without a timestamp.
    """

    def __init__(self, value: T) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SampleWithoutTimestamp):
            return False

        return other.value == self.value

    def __hash__(self) -> int:
        return hash((SampleWithoutTimestamp, self.value))


class Sample[T](SampleWithoutTimestamp[T]):
    """
    Data sample with a timestamp.
    """

    def __init__(self, value: T, timestamp: float) -> None:
        super().__init__(value)
        self.timestamp = timestamp

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sample):
            return False

        if other.value != self.value:
            return False

        return other.timestamp == self.timestamp

    def __hash__(self) -> int:
        return hash((Sample, self.value, self.timestamp))


@dataclass(frozen=True, kw_only=True)
class RobotGeometry:
    """
    Parameters of the robot geometry.
    """

    ticks_per_mm: float
    wheel_track_mm: float
    wheel_diameter_mm: float
    encoder_ticks_per_wheel_revolution: float
    max_speed_limit_mmps: float
