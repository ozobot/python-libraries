from pydantic import TypeAdapter

from . import request
from .base import Cancellation, Message

MessageTypeAdapter = TypeAdapter[Message](
    request.MoveStraightRequest
    | request.RotateRequest
    | request.VelocityRequest
    | request.LineNavigationRequest
    | request.SetLEDRequest
    | request.PlayToneRequest
    | request.PlaySoundRequest
    | request.TimeOfFlightRequest
    | Cancellation
)


def serialize(message: Message) -> str:
    return message.model_dump_json(by_alias=True)


def deserialize(data: str, adapter: TypeAdapter[Message]) -> Message:
    return adapter.validate_json(data, by_alias=True)
