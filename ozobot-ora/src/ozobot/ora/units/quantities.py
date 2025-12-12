import math

from .abstract import PhysicalQuantity
from .domains import AngleDomain, DistanceDomain, RatioDomain, TimeDomain, WeightDomain

mm = PhysicalQuantity("millimeter", "mm", DistanceDomain())
""" Millimetre, `DistanceDomain` """

m = PhysicalQuantity("meter", "m", DistanceDomain(), lambda v: v * 1000, mm)
""" Metre, `DistanceDomain`. 1 m = 1000 mm """

inch = PhysicalQuantity("inch", "in", DistanceDomain(), lambda v: v * 25.4, mm)
""" Inch. `DistanceDomain`. 1 in = 25.4 mm """

deg = PhysicalQuantity("degree", "deg", AngleDomain())
""" Degree, `AngleDomain`. """

rad = PhysicalQuantity("radian", "rad", AngleDomain(), lambda v: math.degrees(v), deg)
""" Radian, `AngleDomain`. 1 rad = 180/pi deg """

s = PhysicalQuantity("second", "s", TimeDomain())
""" Second, `TimeDomain`. """

minute = PhysicalQuantity("minute", "min", TimeDomain(), lambda v: v * 60, s)
""" Minute, `TimeDomain`. 1 min = 60 s """

hour = PhysicalQuantity("hour", "h", TimeDomain(), lambda v: v * 3600, s)
""" Hour, `TimeDomain`. 1 h = 3600 s """

percent = PhysicalQuantity("percent", "%", RatioDomain())
""" Percent, `RatioDomain`. """

kg = PhysicalQuantity("kilogram", "kg", WeightDomain())
""" Kilogram, `WeightDomain`. """

__all__ = ["m", "mm", "inch", "rad", "deg", "s", "minute", "hour", "kg", "percent"]
