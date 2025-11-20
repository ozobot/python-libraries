import typing
from typing import Annotated
from typing import Literal as L

from annotated_types import Ge, Le
from ozobot.linefollower.datatypes import TNamedColor
from pydantic import AliasGenerator, BaseModel, BeforeValidator, ConfigDict, RootModel, alias_generators

TWebDirection = L["Straight", "Backward", "Left", "Right"]
ALLOWED_NAMED_DIRECTIONS = ["Straight", "Backward", "Left", "Right"]


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
    direction: TWebDirection
    follow: L["Follow", "DoNotFollow"]

    @property
    def args(self) -> tuple:
        return (self.direction, self.follow)


class MemReadRequest(BaseRequest):
    method: L["GetValue_wrapper"] = "GetValue_wrapper"
    name: str

    @property
    def args(self) -> tuple:
        return (self.name,)


def _validate_set_prefix(name: str):
    assert isinstance(name, str) and name.startswith("set_")
    return name


class MemWriteRequest(BaseRequest):
    method: typing.Annotated[str, BeforeValidator(_validate_set_prefix)]
    speed: float

    @property
    def args(self) -> tuple:
        return (self.speed,)


class RetrieveFromDataStreamRequest(BaseRequest):
    method: L["retrieveFromDataStream_wrapper"] = "retrieveFromDataStream_wrapper"
    name: str
    last_value: typing.Any | None

    @property
    def args(self) -> tuple:
        if self.last_value is not None:
            return ({"type": self.name, "value": self.last_value},)
        else:
            return ({"type": self.name},)


class BaseResponse(Base):
    # note that `validate_by_alias` is not respected for pydantic<2.11,
    # therefore this is not respected by web python and constructors
    # do not accept the snake_case parameters
    model_config = ConfigDict(
        frozen=True,
        validate_by_name=True,
        validate_by_alias=False,
        alias_generator=AliasGenerator(
            alias=alias_generators.to_camel,
            validation_alias=alias_generators.to_camel,
        ),
    )


class BaseExecutionStateResponse(BaseResponse):
    execution_state: L["FinishedNormal"] | str


class BaseCallStatusResponse(BaseResponse):
    call_status: L["CallSuccess"] | str


class IntersectionResponse(BaseExecutionStateResponse):
    intersection: dict[TWebDirection, bool]


class WatcherResponse[T](RootModel[list[T]]): ...


class ValidatedFloat(RootModel[float]):
    pass


class ValidatedBool(RootModel[bool]):
    pass


class ValidatedAny(RootModel[typing.Any]):
    pass


class ColorResponse(BaseResponse):
    color: TNamedColor
    timestamp: float
