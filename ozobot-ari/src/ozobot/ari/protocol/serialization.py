import json

from ozobot.ari.exceptions import MalformedMessageError, MissingMessageIdError
from ozobot.common.rpc.executor import StampedMessage
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


def serialize(message: StampedMessage[Message]) -> str:
    payload = message.message.model_dump(mode="json", by_alias=True)
    return json.dumps({"id": message.id, **payload}, separators=(",", ":"))


def deserialize(data: str, adapter: TypeAdapter[Message]) -> StampedMessage[Message]:
    parsed = json.loads(data)
    msg = adapter.validate_json(data, by_alias=True)
    try:
        id = parsed["id"]
    except KeyError:
        raise MissingMessageIdError(data) from None
    if isinstance(id, bool) or not isinstance(id, int):
        raise MalformedMessageError()

    return StampedMessage(id, msg)
