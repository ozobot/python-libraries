from typing import Annotated

import pydantic
from ozobot.linefollower.datatypes import TNamedColor

from .base import Model


class Intersection(Model):
    model_config = pydantic.ConfigDict(
        frozen=True,
        validate_by_name=True,
        validate_by_alias=False,
        alias_generator=pydantic.AliasGenerator(
            alias=pydantic.alias_generators.to_pascal,
            validation_alias=pydantic.alias_generators.to_pascal,
        ),
    )

    backward: bool | None = False
    straight: bool | None = False
    left: bool | None = False
    right: bool | None = False


class Lights(Model):
    back: bool | None = False
    button: bool | None = False
    frontCenter: bool | None = False
    frontLeft: bool | None = False
    frontLeftCenter: bool | None = False
    frontRight: bool | None = False
    frontRightCenter: bool | None = False
    top: bool | None = False


class Color(Model):
    red: int
    green: int
    blue: int
    alpha: int | None = 255


class Version(Model):
    version: str
    hash: str


class VersionPair(Model):
    bundled: Version
    current: Version


type TNamedColorLowercase = Annotated[
    TNamedColor, pydantic.BeforeValidator(lambda x: str(x).capitalize()), pydantic.PlainSerializer(str.lower)
]
"""lowercase variant of `TNamedColor` used for specific message types"""
