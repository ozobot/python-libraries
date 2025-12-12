from __future__ import annotations

import typing

from ozobot.ora.units.exceptions import IncompatiblePhysicalDomainError


class PhysicalQuantityDomain:
    name: str

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.name == other.name

    def __hash__(self):
        return hash((self.__class__, self.name))


_TDomain = typing.TypeVar("_TDomain", bound=PhysicalQuantityDomain)
_UDomain = typing.TypeVar("_UDomain", bound=PhysicalQuantityDomain)


class ProportionalRelationDomain(PhysicalQuantityDomain, typing.Generic[_TDomain, _UDomain]):
    def __init__(self, name: str):
        self.name = name

    @classmethod
    def create(cls, quantity1: _TDomain, quantity2: _UDomain):
        return ProportionalRelationDomain(f"{quantity1.name} over {quantity2.name}")


class PowerMagnitude:
    magnitude: int


class SecondPower(PowerMagnitude):
    magnitude = 2


class ThirdPower(PowerMagnitude):
    magnitude = 3


_TPowerMagnitude = typing.TypeVar("_TPowerMagnitude", bound=PowerMagnitude)


class PowerDomain(PhysicalQuantityDomain, typing.Generic[_TDomain, _TPowerMagnitude]):
    magnitude: int

    def __init__(self, name: str):
        self.name = name

    @classmethod
    def create(cls, quantity: _TDomain, magnitude: int):
        return PowerDomain(
            f"{quantity.name}^{magnitude}",
        )


class Value(typing.Generic[_TDomain]):
    _physical_quantity: PhysicalQuantity[_TDomain]
    _value: float | int

    @property
    def physical_quantity(self) -> PhysicalQuantity[_TDomain]:
        return self._physical_quantity

    @property
    def value(self) -> float | int:
        return self._value

    def __init__(self, value: float | int, physical_quantity: PhysicalQuantity[_TDomain]):
        self._physical_quantity = physical_quantity
        self._value = value

    def __str__(self):
        return f"{self._value}{self._physical_quantity}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value}, {self.physical_quantity})"

    def __eq__(self, other):
        if not isinstance(other, Value):
            return False

        self_as_base = self.as_base_quantity()
        other_as_base = other.as_base_quantity()

        return (
            self_as_base.value == other_as_base.value
            and self_as_base.physical_quantity == other_as_base.physical_quantity
        )

    def __hash__(self):
        return hash((self.__class__, self.value, self.physical_quantity))

    def __float__(self) -> float:
        return float(self.as_base_quantity().value)

    def __int__(self) -> int:
        return int(self.as_base_quantity().value)

    def __add__(self, other):
        other_value = self._check_value(other, "addition", "+")
        return Value(self.value + other_value, self.physical_quantity)

    def __radd__(self, other):
        other_value = self._check_value(other, "addition", "+")
        return Value(other_value + self.value, self.physical_quantity)

    def __sub__(self, other):
        other_value = self._check_value(other, "subtraction", "-")
        return Value(self.value - other_value, self.physical_quantity)

    def __rsub__(self, other):
        other_value = self._check_value(other, "subtraction", "-")
        return Value(other_value - self.value, self.physical_quantity)

    def __neg__(self):
        return Value(-self.value, self.physical_quantity)

    def __mul__(self, other):
        other_value = self._check_native_value(other, "multiplication", "*")
        return Value(self.value * other_value, self.physical_quantity)

    def __rmul__(self, other):
        other_value = self._check_native_value(other, "multiplication", "*")
        return Value(other_value * self.value, self.physical_quantity)

    def __truediv__(self, other):
        other_value = self._check_native_value(other, "division", "/")
        return Value(self.value / other_value, self.physical_quantity)

    def __rtruediv__(self, other):
        other_value = self._check_native_value(other, "division", "/")
        return Value(other_value / self.value, self.physical_quantity)

    def __floordiv__(self, other):
        other_value = self._check_native_value(other, "floor division", "//")
        return Value(self.value // other_value, self.physical_quantity)

    def __rfloordiv__(self, other):
        other_value = self._check_native_value(other, "floor division", "//")
        return Value(other_value // self.value, self.physical_quantity)

    def _check_value(self, other: typing.Any, operation_name: str, operator: str) -> float:
        if isinstance(other, int | float):
            return other

        if isinstance(other, Value):
            if self.physical_quantity != other.physical_quantity:
                raise ValueError(
                    f"Cannot do {operation_name} of values within different units: {self.physical_quantity} {operator} {other.physical_quantity}"
                )

            return other.value

        raise ValueError(f"Cannot do {operation_name} of values with {other}: {self} {operator} {other}")

    def _check_native_value(self, other: typing.Any, operation_name: str, operator: str) -> float:
        if isinstance(other, int | float):
            return other

        raise ValueError(f"Cannot do {operation_name} of values with {other}: {self} {operator} {other}")

    def as_base_quantity(self) -> Value[_TDomain]:
        return self.physical_quantity.as_base(self.value)

    def is_in_domain(self, domain: _TDomain) -> bool:
        return self.physical_quantity.domain == domain


class PhysicalQuantity(typing.Generic[_TDomain]):
    domain: _TDomain
    _name: str
    _abbreviation: str
    _base: PhysicalQuantity[_TDomain] | None
    _to_base: typing.Callable[[float], float]

    def __init__(
        self,
        name: str,
        abbreviation: str,
        domain: _TDomain,
        to_base: typing.Callable[[float], float] | None = None,
        base: PhysicalQuantity[_TDomain] | None = None,
    ) -> None:
        self._name = name
        self._abbreviation = abbreviation
        self._base = base
        self.domain = domain
        self._to_base = to_base or (lambda x: x)

    def as_base(self, value: float) -> Value[_TDomain]:
        return Value(self._to_base(value), self._get_base())

    def _get_base(self) -> PhysicalQuantity[_TDomain]:
        if self._base:
            return self._base
        return self

    def __str__(self) -> str:
        abbreviation = self._abbreviation

        return abbreviation

    def __repr__(self) -> str:
        name = self._name
        domain = self.domain.__class__.__name__
        abbreviation = self._abbreviation
        base = self._base

        return f"{self.__class__.__name__}({name=}, {abbreviation=}, {domain=}, to_base=..., {base=})"

    @typing.overload
    def __pow__(self, power: typing.Literal[2]) -> PhysicalQuantity[PowerDomain[_TDomain, SecondPower]]: ...

    @typing.overload
    def __pow__(self, power: typing.Literal[3]) -> PhysicalQuantity[PowerDomain[_TDomain, ThirdPower]]: ...

    def __pow__(self, power: typing.Literal[2, 3], modulo=None) -> PhysicalQuantity[PowerDomain]:
        domain = PowerDomain.create(self.domain, power)

        base = (
            PhysicalQuantity(f"{self._get_base()._name}^{power}", f"{self._get_base()._abbreviation}^{power}", domain)
            if self._base
            else None
        )

        return PhysicalQuantity(
            f"{self._name}^2", f"{self._abbreviation}^2", domain, lambda q: self._to_base(q) ** power, base
        )

    def __rtruediv__(self, other):
        if isinstance(other, Value):
            return Value(other.value, other.physical_quantity / self)

        raise ValueError(f"Cannot divide {type(other)} by {self.__class__.__name__}")

    def __truediv__(
        self, other: PhysicalQuantity[_UDomain]
    ) -> PhysicalQuantity[ProportionalRelationDomain[_TDomain, _UDomain]]:
        if isinstance(other, PhysicalQuantity):
            domain = ProportionalRelationDomain.create(self.domain, other.domain)

            base = (
                PhysicalQuantity(
                    f"{self._get_base()._name} per {other._get_base()._name}",
                    f"{self._get_base()._abbreviation} / {other._get_base()._abbreviation}",
                    domain,
                )
                if self._base or other._base
                else None
            )

            return PhysicalQuantity(
                f"{self._name} per {other._name}",
                f"{self._abbreviation} / {other._abbreviation}",
                domain,
                lambda q: self._to_base(q) / other._to_base(1),
                base,
            )

        raise ValueError(f"Cannot divide {self.__class__.__name__} by {type(other)}")

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (
            self._name == other._name
            and self._abbreviation == other._abbreviation
            and self.domain == other.domain
            and self._base == other._base
        )

    def __hash__(self):
        return hash((self.__class__, self._name, self._abbreviation, self.domain, self._base))


@typing.overload
def value_to_number(value: Value[_TDomain] | float, *, expected_domain: _TDomain) -> float: ...


@typing.overload
def value_to_number(
    value: typing.Iterable[Value[_TDomain] | float], *, expected_domain: _TDomain
) -> tuple[float, ...]: ...


def value_to_number(
    value: Value[_TDomain] | float | typing.Iterable[Value[_TDomain] | float], *, expected_domain: _TDomain
) -> float | tuple[float, ...]:
    if isinstance(value, typing.Iterable):
        return tuple(_value_to_number(item, expected_domain=expected_domain) for item in value)

    return _value_to_number(value, expected_domain=expected_domain)


def _value_to_number(value: Value[_TDomain] | float, *, expected_domain: _TDomain) -> float:
    if isinstance(value, Value) and not value.is_in_domain(expected_domain):
        raise IncompatiblePhysicalDomainError(value.physical_quantity.domain.name, expected_domain.name)

    if not isinstance(value, int | float | Value):
        raise ValueError(f"Cannot convert {type(value)} to number")

    return float(value)


@typing.overload
def number_to_value(number: float, *, physical_quantity: PhysicalQuantity[_TDomain]) -> Value[_TDomain]: ...


@typing.overload
def number_to_value(
    number: typing.Sequence[float], *, physical_quantity: PhysicalQuantity[_TDomain]
) -> typing.Sequence[Value[_TDomain]]: ...


def number_to_value(
    number: float | typing.Sequence[float], *, physical_quantity: PhysicalQuantity[_TDomain]
) -> Value[_TDomain] | typing.Sequence[Value[_TDomain]]:
    if isinstance(number, typing.Sequence):
        return tuple(Value(item, physical_quantity) for item in number)

    return Value(number, physical_quantity)


def units(number: float, units: PhysicalQuantity[_TDomain]) -> Value[_TDomain]:
    """
    Create an object representing numeric value with units.

    .. note::
        See :doc:`units` for more information.

    :param number: The numeric value.
    :param units: The units.
    """

    return number_to_value(number, physical_quantity=units)
