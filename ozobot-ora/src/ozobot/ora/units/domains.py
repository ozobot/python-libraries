from __future__ import annotations

from .abstract import PhysicalQuantityDomain, PowerDomain, ProportionalRelationDomain, SecondPower, ThirdPower


class DistanceDomain(PhysicalQuantityDomain):
    """Physical quantity domain representing distance."""

    name = "distance"


class AngleDomain(PhysicalQuantityDomain):
    """Physical quantity domain representing angle."""

    name = "angle"


class TimeDomain(PhysicalQuantityDomain):
    """Physical quantity domain representing time."""

    name = "time"


class RatioDomain(PhysicalQuantityDomain):
    """Physical quantity domain representing ratios."""

    name = "ratio"


class WeightDomain(PhysicalQuantityDomain):
    """Physical quantity domain representing weight."""

    name = "weight"


type SpeedDomain = ProportionalRelationDomain[DistanceDomain, TimeDomain]
""" Physical quantity domain representing speed, distance over time. """

type AccelerationDomain = ProportionalRelationDomain[DistanceDomain, PowerDomain[TimeDomain, SecondPower]]
""" Physical quantity domain representing acceleration, distance over time squared. """

type JerkDomain = ProportionalRelationDomain[DistanceDomain, PowerDomain[TimeDomain, ThirdPower]]
""" Physical quantity domain representing jerk, distance over time cubed. """

type AngularAccelerationDomain = ProportionalRelationDomain[AngleDomain, PowerDomain[TimeDomain, SecondPower]]
""" Physical quantity domain representing angular acceleration, angle over time squared. """

type AngularJerkDomain = ProportionalRelationDomain[AngleDomain, PowerDomain[TimeDomain, ThirdPower]]
""" Physical quantity domain representing angular jerk, angle over time cubed. """

__all__ = [
    "DistanceDomain",
    "AngleDomain",
    "TimeDomain",
    "RatioDomain",
    "WeightDomain",
    "SpeedDomain",
    "AccelerationDomain",
    "JerkDomain",
    "AngularAccelerationDomain",
    "AngularJerkDomain",
]
