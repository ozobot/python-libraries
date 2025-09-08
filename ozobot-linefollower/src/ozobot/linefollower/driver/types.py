import typing
from typing import Annotated
from typing import Literal as L

from annotated_types import Ge, Le
from ozobot.linefollower.datatypes import TDirection, TNamedColor
from pydantic import AliasGenerator, BaseModel, ConfigDict, RootModel, alias_generators


class Base(BaseModel):
    model_config = ConfigDict(
        frozen=True,
    )

    # @model_validator(mode='before')
    # @classmethod
    # def convert_keys_to_snake(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         data = {alias_generators.to_snake(k): v for k, v in data.items()}
    #     return data


class BaseRequest(Base):
    method: str

    @property
    def args(self) -> tuple[typing.Any, ...]:
        return tuple()


class MoveStraightRequest(BaseRequest):
    method: L["MoveStraight"] = "MoveStraight"
    distance_m: float
    speed_ms: float

    @property
    def args(self) -> tuple:
        return (self.distance_m, self.speed_ms)


class RotateRequest(BaseRequest):
    method: L["Rotate"] = "Rotate"
    angle_rad: float
    angular_speed_radps: float

    @property
    def args(self) -> tuple:
        return (self.angle_rad, self.angular_speed_radps)


class VelocityRequest(BaseRequest):
    method: L["Velocity"] = "Velocity"
    linear_speed_mps: float
    angular_speed_radps: float
    duration_ms: int

    @property
    def args(self) -> tuple:
        return (self.linear_speed_mps, self.angular_speed_radps, self.duration_ms)


class PlayToneRequest(BaseRequest):
    method: L["PlayTone"] = "PlayTone"
    frequency_hz: float
    duration_ms: float

    @property
    def args(self) -> tuple:
        return (self.frequency_hz, self.duration_ms)


TSetLedMaskItem = L[
    "top",
    "back",
    "button",
    "front_center",
    "front_left",
    "front_right",
    "front_left_center",
    "front_right_center",
]


class SetLedRequest(BaseRequest):
    method: L["SetLED"] = "SetLED"
    mask: dict[TSetLedMaskItem, bool]
    red: Annotated[int, Ge(0), Le(255)]
    green: Annotated[int, Ge(0), Le(255)]
    blue: Annotated[int, Ge(0), Le(255)]
    alpha: Annotated[int, Ge(0), Le(255)]

    @property
    def args(self) -> tuple:
        return (self.mask, self.red, self.green, self.blue)


class LineNavigationRequest(BaseRequest):
    method: L["LineNavigation"] = "LineNavigation"
    direction: TDirection
    follow: L["Follow", "DoNotFollow"]

    @property
    def args(self) -> tuple:
        return (self.direction, self.follow)


class StopExecutionRequest(BaseRequest):
    method: L["StopExecution"] = "StopExecution"

    @property
    def args(self) -> tuple:
        return tuple()


class MemReadRequest(BaseRequest):
    method: L["GetValue_wrapper"] = "GetValue_wrapper"
    name: str

    @property
    def args(self) -> tuple:
        return (self.name,)


class MemWriteNavigationSpeedRequest(BaseRequest):
    method: L["set_lineNavigationSpeed"] = "set_lineNavigationSpeed"
    speed: float

    @property
    def args(self) -> tuple:
        return (self.speed,)


class RetrieveFromDataStreamRequest(BaseRequest):
    method: L["retrieveFromDataStream_wrapper"] = "retrieveFromDataStream_wrapper"
    name: str
    last_value: typing.Any | None = None

    @property
    def args(self) -> tuple:
        if self.last_value is not None:
            return ({"type": self.name, "value": self.last_value},)
        else:
            return ({"type": self.name},)


class BaseResponse(Base):
    # hack that allows us to load camelCased keys as snake_cased
    #     e.g., load executionState as execution_state
    # Unfortunately this breaks using snake case in the constructor. Fix this
    # by upgrading pydantic to >=2.11 and using validate_by_alias field.
    model_config = ConfigDict(
        alias_generator=AliasGenerator(
            validation_alias=alias_generators.to_camel,
        ),
    )


class BaseExecutionStateResponse(BaseResponse):
    execution_state: L["FinishedNormal"] | str


class BaseCallStatusResponse(BaseResponse):
    call_status: L["CallSuccess"] | str


class IntersectionResponse(BaseExecutionStateResponse):
    intersection: dict[TDirection, bool]


class ValidatedFloat(RootModel[float]):
    pass


class ValidatedColor(RootModel[TNamedColor]):
    pass
