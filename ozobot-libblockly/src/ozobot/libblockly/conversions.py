from __future__ import annotations

from typing import Any

from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.datatypes import Color, Direction, NamedColor


class InvalidValue(OzobotError):
    def __init__(self, value: str, _type: str) -> None:
        super().__init__(
            f'The value "{value}" is not a valid value of {_type!r}',
            context={"value": str(value), "type": str(_type)},
        )


def type_cast_number(value: Any) -> int | float:
    if isinstance(value, (int | float)):
        return value

    try:
        return int(str(value))
    except ValueError:
        pass
    try:
        return float(str(value))
    except ValueError as e:
        raise InvalidValue(value, "number") from e

    raise InvalidValue(value, "number")


def type_cast_bool(value: Any) -> bool:
    if isinstance(value, bool | int | float):
        return bool(value)
    if isinstance(value, str) and value.lower() in ("false",):
        return False
    return bool(value)


def type_cast_color(value: Any) -> Color:
    if isinstance(value, Color):
        return value

    if isinstance(value, str):
        name = _remove_prefix(value, "NamedColor.")
        attr_name = name.upper()
        if hasattr(NamedColor, attr_name):
            return getattr(NamedColor, attr_name)
        else:
            raise InvalidValue(name, "color")

    raise InvalidValue(value, "color")


def type_cast_direction(value: Any) -> Direction:
    if isinstance(value, Direction):
        return value

    if isinstance(value, str):
        name = _remove_prefix(value, "Direction.")
        attr_name = name.upper()
        if hasattr(Direction, attr_name):
            return getattr(Direction, attr_name)
        else:
            raise InvalidValue(name, "direction")

    raise InvalidValue(value, "direction")


def _remove_prefix(name: str, allowed_prefix: str) -> str:
    if name.startswith(allowed_prefix):
        prefix_len = len(allowed_prefix)
        return name[prefix_len:]
    else:
        return name
