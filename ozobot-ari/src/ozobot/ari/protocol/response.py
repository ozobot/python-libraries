from __future__ import annotations

from typing import Literal as L

from .base import Model, Response


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
