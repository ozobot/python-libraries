from __future__ import annotations

import typing
from builtins import classmethod
from typing import Literal as L

from pydantic import AliasGenerator, BaseModel, ConfigDict, alias_generators


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
    jsonrpc: L["com/ozobot/jsonrpc/2.0/notification"] = "com/ozobot/jsonrpc/2.0/notification"


class Cancellation(Message):
    jsonrpc: L["com/ozobot/jsonrpc/2.0/cancellation"] = "com/ozobot/jsonrpc/2.0/cancellation"
    code: int
    message: str | None

    @classmethod
    def create(cls, id: int, code: int, message: str | None) -> Cancellation:
        return Cancellation(id=id, code=code, message=message)
