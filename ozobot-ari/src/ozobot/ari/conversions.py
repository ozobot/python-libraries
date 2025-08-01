import typing

from ozobot.ari.protocol import types
from ozobot.ari.protocol.types import TDirection
from ozobot.linefollower.datatypes import Direction, LEDMask


def led_to_protocol(mask: LEDMask) -> types.Lights:
    return types.Lights(
        back=LEDMask.BACK in mask,
        button=LEDMask.BUTTON in mask,
        frontCenter=LEDMask.FRONT_CENTER in mask,
        frontLeft=LEDMask.FRONT_LEFT in mask,
        frontLeftCenter=LEDMask.FRONT_LEFT_CENTER in mask,
        frontRight=LEDMask.FRONT_RIGHT in mask,
        frontRightCenter=LEDMask.FRONT_RIGHT_CENTER in mask,
        top=LEDMask.TOP in mask,
    )


def intersection_direction_to_protocol(direction: Direction) -> TDirection:
    if not len(direction) == 1:
        raise ValueError("Direction attribute needs to define exactly one direction")

    match direction:
        case Direction.LEFT:
            return "Left"
        case Direction.RIGHT:
            return "Right"
        case Direction.STRAIGHT:
            return "Straight"
        case Direction.BACKWARD:
            return "Backward"
        case _:
            typing.assert_never(direction)


def intersection_bitmap_from_protocol(intersection_mask: types.Intersection) -> Direction:
    intersection = Direction(0)

    if intersection_mask.backward:
        intersection |= Direction.BACKWARD
    if intersection_mask.straight:
        intersection |= Direction.STRAIGHT
    if intersection_mask.left:
        intersection |= Direction.LEFT
    if intersection_mask.right:
        intersection |= Direction.RIGHT

    return intersection
