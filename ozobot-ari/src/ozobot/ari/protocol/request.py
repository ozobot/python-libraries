from __future__ import annotations

from typing import Literal as L

from ozobot.linefollower.datatypes import TDirection, TNamedColor
from ozobot.userio.datatypes import TAriUserIoPromptDirections, TUserIoPrompt

from .base import Model, Request
from .types import Color, Lights


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
    expiration: float
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
    duration: float
    # volume is currently not supported by the user api
    # volume: float


class PlayToneRequest(Request):
    method: L["PlayTone"] = "PlayTone"
    params: PlayToneRequestParams


class PlaySoundRequestParams(Model):
    name: str
    loop: bool
    # we don't need to set the volume for now, see ANV-954
    # volume: float


class PlaySoundRequest(Request):
    method: L["PlaySound"] = "PlaySound"
    params: PlaySoundRequestParams


class TimeOfFlightRequestParams(Model):
    pass


class TimeOfFlightRequest(Request):
    method: L["TimeOfFlight"] = "TimeOfFlight"
    params: TimeOfFlightRequestParams


class UserIoPrintRequestParams(Model):
    message: str


class UserIoPrintRequest(Request):
    method: L["UserIoPrint"] = "UserIoPrint"
    params: UserIoPrintRequestParams


class UserIoAlertRequestParams(Model):
    message: str
    cancellable: bool


class UserIoAlertRequest(Request):
    method: L["UserIoAlert"] = "UserIoAlert"
    params: UserIoAlertRequestParams


class UserIoPromptRequestParams(Model):
    message: str
    cancellable: bool
    type: TUserIoPrompt
    options: list[str | int | float | bool | TNamedColor | TAriUserIoPromptDirections]


class UserIoPromptRequest(Request):
    method: L["UserIoPrompt"] = "UserIoPrompt"
    params: UserIoPromptRequestParams


class HealthCheckRequestParams(Model):
    expiration: float | None = None


class HealthCheckRequest(Request):
    method: L["HealthCheck"] = "HealthCheck"
    params: HealthCheckRequestParams
