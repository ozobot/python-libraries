import typing

from ozobot.ari.protocol import types
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


def intersection_direction_to_protocol(direction: Direction) -> types.Intersection:
    if not len(direction) == 1:
        raise ValueError("Direction attribute needs to define exactly one direction")

    match direction:
        case Direction.LEFT:
            return types.Intersection(left=True)
        case Direction.RIGHT:
            return types.Intersection(right=True)
        case Direction.STRAIGHT:
            return types.Intersection(straight=True)
        case Direction.BACKWARD:
            return types.Intersection(backward=True)
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
