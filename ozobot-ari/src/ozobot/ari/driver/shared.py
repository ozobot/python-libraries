from ozobot.ari import conversions
from ozobot.ari.exceptions import UnexpectedUserIoPromptOptionTypeError, UnexpectedUserIoPromptTypeError
from ozobot.ari.protocol.types import TUserIoPrompt
from ozobot.linefollower.datatypes import Color, Direction, TDirection, TNamedColor


def get_user_io_type_name(_type: type[str | int | float | bool | Color | Direction]) -> TUserIoPrompt:
    if _type == str:
        return "string"
    elif _type == int or _type == float:
        return "number"
    elif _type == bool:
        return "boolean"
    elif _type == Color:
        return "surfaceColor"
    elif _type == Direction:
        return "direction"
    else:
        raise UnexpectedUserIoPromptTypeError(_type)


def get_user_io_type_options[T: (str, float, int, bool, Color, Direction)](
    options: list[T], _type: type[T]
) -> list[str | float | int | bool | TNamedColor | TDirection]:
    for opt in options:
        if not isinstance(opt, _type):
            raise UnexpectedUserIoPromptOptionTypeError(opt, _type)

    protocol_options: list[str | float | int | bool | TNamedColor | TDirection] = []
    for opt in options:
        if isinstance(opt, Color):
            protocol_options.append(conversions.color_to_protocol(opt))
        elif isinstance(opt, Direction):
            protocol_options.append(conversions.intersection_direction_to_protocol(opt))
        else:
            protocol_options.append(opt)

    return protocol_options
