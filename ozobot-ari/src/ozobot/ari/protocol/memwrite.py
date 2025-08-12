from typing import Literal as L

from .base import Model, Request, Response


class MemWriteRequestIrLeftParams(Model):
    segment: L["irLeft"] = "irLeft"
    active: bool
    message: int


class MemWriteRequestIrRightParams(Model):
    segment: L["irRight"] = "irRight"
    active: bool
    message: int


class MemWriteRequestLineFollowingSpeedParams(Model):
    segment: L["lineFollowingSpeed"] = "lineFollowingSpeed"
    value: float


type MemWriteRequestParams = (
    MemWriteRequestIrLeftParams | MemWriteRequestIrRightParams | MemWriteRequestLineFollowingSpeedParams
)


class MemWriteRequest(Request):
    method: L["MemWrite"] = "MemWrite"
    params: MemWriteRequestParams


class MemWriteResponseBody(Model):
    type: L["finished"] = "finished"
    success: bool


class MemWriteResponse(Response):
    result: MemWriteResponseBody
