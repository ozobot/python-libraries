from typing import Literal as L

from ozobot.linefollower.datatypes import TNamedColor

from .base import Model, Notification, Request, Response
from .types import VersionPair


class MemReadResponseColorSensor(Model):
    type: L["color"] = "color"
    red: int
    green: int
    blue: int
    mixed: int
    color: int
    has_light_source: bool
    saturation_analog: bool
    saturation_digital: bool
    is_valid: bool
    timestamp: int


class MemReadResponseLineSensors(Model):
    type: L["lineSensors"] = "lineSensors"
    position: float
    width: float
    under_left: bool
    under_right: bool
    under_all: bool
    active_sensors: list[bool]
    timestamp: int


class MemReadResponsePickup(Model):
    type: L["pickup"] = "pickup"
    is_picked_up: bool
    timestamp: int


class MemReadResponsePosition(Model):
    type: L["position"] = "position"
    origin_count: int
    x: float
    y: float
    angle_x: float
    angle_y: float
    timestamp: int


class MemReadResponseProximity(Model):
    type: L["proximity"] = "proximity"
    value: int
    timestamp: int


class MemReadResponseReadIr(Model):
    type: L["readIr"] = "readIr"
    message: int
    intensity: int
    timestamp: int


class MemReadResponseVersion(Model):
    type: L["version"] = "version"
    ir: VersionPair
    sensor: VersionPair


class MemReadResponseWheels(Model):
    type: L["wheels"] = "wheels"
    count_left: int
    count_right: int
    timestamp: int


class MemReadResponsePickupADC(Model):
    type: L["pickupADC"] = "pickupADC"
    adc: list[int]
    timestamp: int


class MemReadResponseLineColor(Model):
    type: L["lineColor"] = "lineColor"
    color: TNamedColor | None
    light_source: bool
    timestamp: int


class MemReadResponseSurfaceColor(Model):
    type: L["surfaceColor"] = "surfaceColor"
    color: TNamedColor | None
    counter: int
    light_source: bool
    timestamp: int


class MemReadResponseLinearVelocity(Model):
    type: L["linearVelocity"] = "linearVelocity"
    velocity: float


type MemWatchResponseBody = (
    MemReadResponseColorSensor
    | MemReadResponseLineSensors
    | MemReadResponsePickup
    | MemReadResponsePosition
    | MemReadResponseProximity
    | MemReadResponseReadIr
    | MemReadResponseWheels
    | MemReadResponsePickupADC
    | MemReadResponseLineColor
    | MemReadResponseSurfaceColor
)


type MemReadResponseBody = MemWatchResponseBody | MemReadResponseVersion | MemReadResponseLinearVelocity


class MemReadRequestParams(Model):
    segment: str


class MemReadRequest(Request):
    method: L["MemRead"] = "MemRead"
    params: MemReadRequestParams


class MemReadResponse(Response):
    result: MemReadResponseBody


class WatchRequest(Request):
    method: L["Watch"] = "Watch"
    params: MemReadRequestParams


class WatchNotification(Notification):
    notification: MemReadResponseBody
