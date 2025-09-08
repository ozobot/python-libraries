from __future__ import annotations

from typing import Literal as L

from ozobot.linefollower.datatypes import TDirection

from .base import Model, Response
from .types import TNamedColorLowercase


class MoveStraightResponseBody(Model):
    type: L["finished"] | str


class RotateResponseBody(Model):
    type: L["finished"] | str


class VelocityResponseBody(Model):
    type: L["finished"] | str


class SetLEDResponseBody(Model):
    type: L["finished"] | str


class PlayToneResponseBody(Model):
    type: L["finished"] | str


class PlaySoundResponseBody(Model):
    type: L["finished"] | str


class LineNavigationResponseBody(Model):
    type: L["finished"] | str


class UserIoPromptStringResponseBody(Model):
    type: L["string"] = "string"
    value: str


class UserIoPromptNumberResponseBody(Model):
    type: L["number"] = "number"
    value: float | int


class UserIoPromptBooleanResponseBody(Model):
    type: L["boolean"] = "boolean"
    value: bool


class UserIoPromptSurfaceColorResponseBody(Model):
    type: L["surfaceColor"] = "surfaceColor"
    value: TNamedColorLowercase


class UserIoPromptLineColorResponseBody(Model):
    type: L["lineColor"] = "lineColor"
    value: TNamedColorLowercase


class UserIoPromptDirectionResponseBody(Model):
    type: L["direction"] = "direction"
    value: TDirection


type UserIoPromptResponseBody = (
    UserIoPromptStringResponseBody
    | UserIoPromptNumberResponseBody
    | UserIoPromptBooleanResponseBody
    | UserIoPromptSurfaceColorResponseBody
    | UserIoPromptLineColorResponseBody
    | UserIoPromptDirectionResponseBody
)


class MoveStraightResponse(Response):
    result: MoveStraightResponseBody


class RotateResponse(Response):
    result: RotateResponseBody


class VelocityResponse(Response):
    result: VelocityResponseBody


class LineNavigationResponse(Response):
    result: LineNavigationResponseBody


class SetLEDResponse(Response):
    result: SetLEDResponseBody


class PlayToneResponse(Response):
    result: PlayToneResponseBody


class PlaySoundResponse(Response):
    result: PlaySoundResponseBody


class UserIoPrintResponse(Response):
    result: bool


class UserIoAlertResponse(Response):
    result: bool


class UserIoPromptResponse(Response):
    result: UserIoPromptResponseBody
