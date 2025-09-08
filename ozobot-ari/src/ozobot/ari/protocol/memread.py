from typing import Literal as L

from ozobot.linefollower.datatypes import TNamedColor

from .base import Model, Notification, Request, Response
from .types import FloatRange, VersionPair


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


class MemReadResponseLineSensorsCalibration(Model):
    type: L["lineSensorsCalibration"] = "lineSensorsCalibration"
    black: list[int]
    white: list[int]


class MemReadResponseLineSensors(Model):
    type: L["lineSensors"] = "lineSensors"
    position: float
    width: float
    under_left: bool
    under_right: bool
    under_all: bool
    active_sensors: list[bool]
    timestamp: int


class MemReadResponseLineSensorsRaw(Model):
    type: L["lineSensorsRaw"] = "lineSensorsRaw"
    sensors: list[int]


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


class MemReadResponseSentIr(Model):
    type: L["sentIr"] = "sentIr"
    message: int
    active: bool


class MemReadResponseVersion(Model):
    type: L["version"] = "version"
    ir: VersionPair
    sensor: VersionPair


class MemReadResponseWheels(Model):
    type: L["wheels"] = "wheels"
    count_left: int
    count_right: int
    timestamp: int


class MemReadResponseHardwareState(Model):
    type: L["state"] = "state"
    sensor: str
    ir: str


class MemReadResponseLog(Model):
    type: L["log"] = "log"
    level: int
    message: str


class MemReadResponsePickupADC(Model):
    type: L["pickupADC"] = "pickupADC"
    adc: list[int]
    timestamp: int


class MemReadResponseLineColor(Model):
    type: L["lineColor"] = "lineColor"
    color: TNamedColor
    light_source: bool
    timestamp: int


class MemReadResponseSurfaceColor(Model):
    type: L["surfaceColor"] = "surfaceColor"
    color: TNamedColor
    counter: int
    light_source: bool
    timestamp: int


class MemReadResponseEncoderDACReference(Model):
    type: L["encoderDACReference"] = "encoderDACReference"
    reference: list[float]


class MemReadResponseEncoderDACReferenceRange(Model):
    type: L["encoderDACReferenceRange"] = "encoderDACReferenceRange"
    ranges: list[FloatRange]


class MemReadResponseLinearVelocity(Model):
    type: L["linearVelocity"] = "linearVelocity"
    velocity: float


class MemReadResponseColorSensorCalibration(Model):
    type: L["colorSensorCalibration"] = "colorSensorCalibration"
    red: FloatRange
    green: FloatRange
    blue: FloatRange


class MemReadResponsePickupThreshold(Model):
    type: L["pickupThreshold"] = "pickupThreshold"
    threshold: int


type MemReadResponseBody = (
    MemReadResponseColorSensor
    | MemReadResponseLineSensorsCalibration
    | MemReadResponseLineSensors
    | MemReadResponseLineSensorsRaw
    | MemReadResponsePickup
    | MemReadResponsePosition
    | MemReadResponseProximity
    | MemReadResponseReadIr
    | MemReadResponseSentIr
    | MemReadResponseVersion
    | MemReadResponseWheels
    | MemReadResponseHardwareState
    | MemReadResponseLog
    | MemReadResponsePickupADC
    | MemReadResponseLineColor
    | MemReadResponseSurfaceColor
    | MemReadResponseEncoderDACReference
    | MemReadResponseEncoderDACReferenceRange
    | MemReadResponseLinearVelocity
    | MemReadResponseColorSensorCalibration
    | MemReadResponsePickupThreshold
)


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
