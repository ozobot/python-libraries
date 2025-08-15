from __future__ import annotations

import typing
from builtins import classmethod
from typing import Literal as L

from pydantic import AliasGenerator, BaseModel, ConfigDict, PlainSerializer, alias_generators

NOTIFICATION_MESSAGE_LABEL: typing.Final = "com/ozobot/jsonrpc/2.0/notification"
CANCELLATION_MESSAGE_LABEL: typing.Final = "com/ozobot/jsonrpc/2.0/cancellation"


class Model(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        validate_by_alias=False,
        alias_generator=AliasGenerator(
            alias=alias_generators.to_camel,
            validation_alias=alias_generators.to_camel,
        ),
    )


class Message(Model):
    id: int
    jsonrpc: str


class Request(Message):
    jsonrpc: L["2.0"] = "2.0"
    method: str
    params: typing.Any


class Response(Message):
    jsonrpc: L["2.0"] = "2.0"
    result: typing.Any


class Notification(Message):
    jsonrpc: L["com/ozobot/jsonrpc/2.0/notification"] = NOTIFICATION_MESSAGE_LABEL


class Cancellation(Message):
    jsonrpc: L["com/ozobot/jsonrpc/2.0/cancellation"] = CANCELLATION_MESSAGE_LABEL
    code: typing.Annotated[int | None, PlainSerializer(lambda x: x, when_used="unless-none")] = None
    message: typing.Annotated[str | None, PlainSerializer(lambda x: x, when_used="unless-none")] = None

    @classmethod
    def create(cls, id: int, code: int, message: str | None) -> Cancellation:
        return Cancellation(id=id, code=code, message=message)
