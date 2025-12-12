import math
import typing

import pytest

from ozobot.ora.units import PhysicalQuantity, Value
from ozobot.ora.units.abstract import PowerDomain, ProportionalRelationDomain, SecondPower, number_to_value, units, value_to_number
from ozobot.ora.units.domains import AngleDomain, DistanceDomain, TimeDomain
from ozobot.ora.units.exceptions import IncompatiblePhysicalDomainError
from ozobot.ora.units.quantities import deg, hour, inch, m, minute, mm, rad, s


def test_units_to_base() -> None:
    assert units(10, mm) == Value(0.01, m)
    assert units(1, inch) == Value(0.0254, m)


def test_as_base_quantity() -> None:
    assert units(10, inch).as_base_quantity().value == 254


def test_physical_unit_equivalence() -> None:
    assert PhysicalQuantity("meter", "m", DistanceDomain()) == PhysicalQuantity("meter", "m", DistanceDomain())
    assert mm / s == mm / s


def test_equivalence() -> None:
    assert units(10, mm) == units(10, mm)
    assert units(10, inch) == units(0.254, m)
    assert units(1, mm) != units(1, inch)
    assert units(math.pi / 2, rad) == units(90, deg)


def test_ratio_quantities() -> None:
    assert units(10, mm / s) == Value(0.01, m / s)
    assert units(90, deg / s) == units(math.pi / 2, rad / s)


def test_combined_equivalence() -> None:
    assert units(3600, inch / hour) == units(25.4, mm / s)


def test_incomparable_equivalence() -> None:
    assert units(1, mm) != units(1, s)


def test_operator_precedence() -> None:
    assert 5 * units(5, mm) == units(25, mm)
    assert units(5, mm) * 5 == units(25, mm)
    assert 5 * units(5, mm / s) == Value(0.025, m / s)


def test_predefined_units_time_domain() -> None:
    assert units(3600, s) == units(1, hour)
    assert units(60, s) == units(1, minute)

    assert units(1, minute) == units(60, s)
    assert units(1, hour) == units(60, minute)


def test_predefined_units_angle_domain() -> None:
    assert units(90, deg) == units(math.pi / 2, rad)
    assert units(1, rad) == units(180 / math.pi, deg)

    typing.assert_type(deg, PhysicalQuantity[AngleDomain])


def test_predefined_units_length_domain() -> None:
    assert units(1, inch) == units(0.0254, m)
    assert units(1, inch) == units(25.4, mm)
    assert units(1, m) == units(1000, mm)

    assert units(1, m) != units(1, mm)


def test_speed_units() -> None:
    assert units(1, inch / s) == units(0.0254, m / s)
    assert units(1, inch / s) == units(25.4, mm / s)
    assert units(1, m / s) == units(1000, mm / s)

    assert units(1, m / s) != units(1, mm / s)

    typing.assert_type(m / s, PhysicalQuantity[ProportionalRelationDomain[DistanceDomain, TimeDomain]])


def test_acceleration_units() -> None:
    assert units(1, inch / s**2) == units(329184, m / hour**2)

    assert units(1, inch / s**2) != units(1, m / hour**2)

    typing.assert_type(m / s**2, PhysicalQuantity[ProportionalRelationDomain[DistanceDomain, PowerDomain[TimeDomain, SecondPower]]])


def test_convert_to_number() -> None:
    assert value_to_number(units(10, mm), expected_domain=DistanceDomain()) == 10
    assert value_to_number(units(10, inch), expected_domain=DistanceDomain()) == 254

    typing.assert_type(value_to_number(units(10, mm), expected_domain=DistanceDomain()), float)

    with pytest.raises(ValueError):
        value_to_number("10", expected_domain=DistanceDomain())  # type: ignore[arg-type]  # ignore because of that's what we want to test

    with pytest.raises(IncompatiblePhysicalDomainError):
        value_to_number(units(10, mm), expected_domain=AngleDomain())  # type: ignore[misc]  # ignore because of that's what we want to test

    values = value_to_number([units(10, mm), units(10, inch)], expected_domain=DistanceDomain())
    assert values == (10, 254)
    typing.assert_type(values, tuple[float, ...])


def test_convert_from_number() -> None:
    assert number_to_value(10, physical_quantity=mm) == units(10, mm)
    assert number_to_value(10, physical_quantity=inch) == units(254, mm)

    values = number_to_value([10, 20], physical_quantity=mm)
    assert values == (units(10, mm), units(20, mm))

    typing.assert_type(values, typing.Sequence[Value[DistanceDomain]])


def test_hash():
    assert hash(units(10, mm / s)) == hash(units(10, mm / s))
    assert hash(units(10, mm / s)) != hash(units(10, mm))


def test_as_float():
    assert float(units(10, mm)) == 10.0
    assert float(units(10, inch)) == 254.0


def test_addition():
    assert units(10, mm) + units(10, mm) == units(20, mm)
    assert units(10, mm) + 10 == units(20, mm)
    assert 10 + units(10, mm) == units(20, mm)

    with pytest.raises(ValueError):
        units(10, mm) + units(10, s)

    with pytest.raises(ValueError):
        units(10, mm) + units(10, inch)


def test_subtraction():
    assert units(5, mm) - units(10, mm) == units(-5, mm)
    assert units(5, mm) - 10 == units(-5, mm)
    assert 5 - units(10, mm) == units(-5, mm)

    with pytest.raises(ValueError):
        units(10, mm) - units(10, s)

    with pytest.raises(ValueError):
        units(10, mm) - units(10, inch)


def test_multiplication():
    assert units(5, mm) * 10 == units(50, mm)
    assert 5 * units(10, mm) == units(50, mm)

    with pytest.raises(ValueError):
        units(10, mm) * units(10, s)

    with pytest.raises(ValueError):
        units(10, mm) * units(10, inch)


def test_negation():
    assert units(-10, mm) == units(-10, mm)


def test_truediv():
    assert units(15, mm) / 10 == units(1.5, mm)
    assert 15 / units(10, mm) == units(1.5, mm)

    with pytest.raises(ValueError):
        units(10, mm) / units(10, mm)

    with pytest.raises(ValueError):
        units(10, mm) / units(10, s)

    with pytest.raises(ValueError):
        units(10, mm) / units(10, inch)


def test_floordiv():
    assert units(11, mm) // 10 == units(1, mm)
    assert 11 // units(10, mm) == units(1, mm)

    with pytest.raises(ValueError):
        units(10, mm) // units(10, mm)

    with pytest.raises(ValueError):
        units(10, mm) // units(10, s)

    with pytest.raises(ValueError):
        units(10, mm) // units(10, inch)
