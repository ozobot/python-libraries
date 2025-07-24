from __future__ import annotations

from typing import Literal as L

from .base import Model, Request
from .types import Color, Lights, TDirection


class MoveStraightRequestParams(Model):
    distance: float
    speed: float


class MoveStraightRequest(Request):
    method: L["MoveStraight"] = "MoveStraight"
    params: MoveStraightRequestParams


class RotateRequestParams(Model):
    angle: float
    speed: float


class RotateRequest(Request):
    method: L["Rotate"] = "Rotate"
    params: RotateRequestParams


class VelocityRequestParams(Model):
    expiration: int
    linear_speed: float
    rotation_speed: float


class VelocityRequest(Request):
    method: L["Velocity"] = "Velocity"
    params: VelocityRequestParams


class LineNavigationRequestParams(Model):
    direction: TDirection
    follow: L["Follow"] | L["DoNotFollow"]
    detect_color_codes: bool


class LineNavigationRequest(Request):
    method: L["LineNavigation"] = "LineNavigation"
    params: LineNavigationRequestParams


class SetLEDRequestParams(Model):
    lights: Lights
    color: Color


class SetLEDRequest(Request):
    method: L["SetLED"] = "SetLED"
    params: SetLEDRequestParams


class PlayToneRequestParams(Model):
    frequency: int
    duration: int
    volume: float


class PlayToneRequest(Request):
    method: L["PlayTone"] = "PlayTone"
    params: PlayToneRequestParams


class PlaySoundRequestParams(Model):
    name: str
    loop: bool
    volume: int


class PlaySoundRequest(Request):
    method: L["PlaySound"] = "PlaySound"
    params: PlaySoundRequestParams


class TimeOfFlightRequestParams(Model):
    latency: int | None = None


class TimeOfFlightRequest(Request):
    method: L["TimeOfFlight"] = "TimeOfFlight"
    params: TimeOfFlightRequestParams
