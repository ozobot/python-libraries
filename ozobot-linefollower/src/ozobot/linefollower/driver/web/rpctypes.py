import typing
from typing import Annotated
from typing import Literal as L

from annotated_types import Ge, Le
from ozobot.linefollower.conversions import ALLOWED_NAMED_COLORS
from ozobot.linefollower.datatypes import TNamedColor
from pydantic import AliasGenerator, BaseModel, ConfigDict, RootModel, alias_generators

type TWebDirection = L["Straight", "Backward", "Left", "Right"]
type TWebColor = TNamedColor
ALLOWED_WEB_COLORS = ALLOWED_NAMED_COLORS
ALLOWED_WEB_DIRECTIONS = typing.get_args(TWebDirection.__value__)


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
    method: L["move"] = "move"
    distance_m: float
    speed_ms: float

    @property
    def args(self) -> tuple:
        return (self.distance_m, self.speed_ms)


class RotateRequest(BaseRequest):
    method: L["rotate"] = "rotate"
    angle_rad: float
    angular_speed_radps: float

    @property
    def args(self) -> tuple:
        return (self.angle_rad, self.angular_speed_radps)


class VelocityRequest(BaseRequest):
    method: L["velocity"] = "velocity"
    linear_speed_mps: float
    angular_speed_radps: float
    duration_ms: int

    @property
    def args(self) -> tuple:
        return (self.linear_speed_mps, self.angular_speed_radps, self.duration_ms)


class PlayToneRequest(BaseRequest):
    method: L["playTone"] = "playTone"
    frequency_hz: float
    duration_ms: float

    @property
    def args(self) -> tuple:
        return (self.frequency_hz, self.duration_ms)


class PlayAudioRequest(BaseRequest):
    method: typing.Literal["playAudio"] = "playAudio"
    filename: str

    @property
    def args(self) -> tuple:
        return (self.filename,)


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
    method: L["setLed"] = "setLed"
    mask: dict[TSetLedMaskItem, bool]
    red: Annotated[float, Ge(0), Le(1)]
    green: Annotated[float, Ge(0), Le(1)]
    blue: Annotated[float, Ge(0), Le(1)]

    @property
    def args(self) -> tuple:
        return (self.mask, self.red, self.green, self.blue)


class LineNavigationRequest(BaseRequest):
    method: L["lineNavigation"] = "lineNavigation"
    direction: TWebDirection
    follow: bool

    @property
    def args(self) -> tuple:
        return (self.direction, self.follow)


class MemReadRequest(BaseRequest):
    @classmethod
    def create(cls, name: str) -> typing.Self:
        return cls(method=f"memory.{name}.read")

    @property
    def args(self) -> tuple:
        return tuple()


class MemWriteRequest(BaseRequest):
    method: str
    data: typing.Any

    @classmethod
    def create(cls, name: str, data: typing.Any) -> typing.Self:
        return cls(method=f"memory.{name}.write", data=data)

    @property
    def args(self) -> tuple:
        return (self.data,)


class MemWatchRequest(BaseRequest):
    @classmethod
    def create(cls, name: str, last_value: typing.Any | None = None) -> typing.Self:
        return cls(method=f"memory.{name}.wait", last_value=last_value)

    last_value: typing.Any | None

    @property
    def args(self) -> tuple:
        if self.last_value is not None:
            return (self.last_value, False)
        else:
            return (None,)


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


class WatcherResponse[T](RootModel[list[T]]): ...


class ValidatedNone(RootModel[None]):
    pass


class ValidatedFloat(RootModel[float]):
    pass


class ValidatedInt(RootModel[int]):
    pass


class ValidatedBool(RootModel[bool]):
    pass


class ValidatedAny(RootModel[typing.Any]):
    pass


class IntersectionResponse(BaseResponse):
    intersection: dict[TWebDirection, bool]
    timestamp: int


class ColorCodeResponse(BaseResponse):
    colors: list[TWebColor]
    timestamp: int


class ColorResponse(BaseResponse):
    color: TWebColor | None
    timestamp: int


class ReadIrResponse(BaseResponse):
    message: int
    intensity: int
    timestamp: int


class IrProximityResponse(BaseResponse):
    value: float
    timestamp: int
