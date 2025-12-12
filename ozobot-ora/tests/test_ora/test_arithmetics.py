import typing

import pytest
from ozobot.ora import arithmetics
from ozobot.ora.units import Value, domains, units
from ozobot.ora.units.quantities import kg, mm


class _DummyDistanceVector(arithmetics.ValueVector):
    _quantities = {"x": mm, "y": mm, "z": mm}

    def __init__(
        self,
        x: Value[domains.DistanceDomain] | float = 0,
        y: Value[domains.DistanceDomain] | float = 0,
        z: Value[domains.DistanceDomain] | float = 0,
    ):
        super().__init__(x=x, y=y, z=z)

    x = arithmetics.rw_property("x", Value[domains.DistanceDomain])
    y = arithmetics.rw_property("y", Value[domains.DistanceDomain])
    z = arithmetics.rw_property("z", Value[domains.DistanceDomain])


class _OtherDummyDistanceVector(arithmetics.ValueVector):
    _quantities = {"val": kg}

    val = arithmetics.rw_property("val", Value[domains.WeightDomain])

    def __init__(self, val):
        super().__init__(val=val)


def test_assignment():
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    test.z = units(100, mm)

    assert test.x == units(10, mm)
    assert test.y == units(20, mm)
    assert test.z == units(100, mm)


def test_addition() -> None:
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    test += _DummyDistanceVector(y=units(100, mm))
    test.z += units(100, mm)

    assert test.y == units(120, mm)
    assert test.z == units(130, mm)

    with pytest.raises(ValueError):
        test.x += units(100, kg)

    with pytest.raises(ValueError):
        test += _OtherDummyDistanceVector(val=units(100, kg))


def test_subtraction():
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    test -= _DummyDistanceVector(y=units(100, mm))
    test.z -= units(100, mm)

    assert test.y == units(-80, mm)
    assert test.z == units(-70, mm)

    with pytest.raises(ValueError):
        test.x -= units(100, kg)

    with pytest.raises(ValueError):
        test -= _OtherDummyDistanceVector(val=units(100, kg))


def test_negation():
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    test = -test

    assert test.x == units(-10, mm)
    assert test.y == units(-20, mm)
    assert test.z == units(-30, mm)


def test_equality():
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))
    other = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    assert test == other

    other = _DummyDistanceVector(units(10, mm), units(20, mm), units(40, mm))
    assert test != other


def test_to_float():
    test = _DummyDistanceVector(units(10, mm), units(20, mm), units(30, mm))

    assert tuple(test) == (units(10, mm), units(20, mm), units(30, mm))


def test_is_iterable():
    test = _DummyDistanceVector(1, 2, 3)

    assert tuple(test) == (units(1, mm), units(2, mm), units(3, mm))
    assert isinstance(test, typing.Iterable)
