import builtins
import typing

from ozobot.ora.units import PhysicalQuantity, Value
from ozobot.ora.units.abstract import units
from ozobot.ora.units.exceptions import IncompatiblePhysicalDomainError

_TUnbound = typing.TypeVar("_TUnbound")


def rw_property(idx: str, value_type: type[_TUnbound]) -> _TUnbound | float:
    def _getter(self):
        return self._values[idx]

    def _setter(self, value):
        if isinstance(value, Value) and value.is_in_domain(self._quantities[idx].domain):
            self._values[idx] = value
        elif isinstance(value, Value):
            raise IncompatiblePhysicalDomainError(value.physical_quantity.domain, self._quantities[idx].domain)
        else:
            self._values[idx] = Value(value, self._quantities[idx])

    return typing.cast(_TUnbound, builtins.property(_getter, _setter))


class ValueVector:
    _quantities: dict[str, PhysicalQuantity[typing.Any]]
    _values: dict[str, Value[typing.Any]]

    def __init__(self, **values: Value[typing.Any] | float | int):
        num_elements = len(self._quantities)
        if len(values) != num_elements:
            raise ValueError(f"Unexpected numer of values: expected, {num_elements}, got {len(values)}")

        self._values = {k: units(0, v) for k, v in self._quantities.items()}

        for name, value in values.items():
            setattr(self, name, value)

    @classmethod
    def _create_instance(cls, values: dict[str, Value]):
        return cls(**values)

    def __add__(self, other):
        if not isinstance(other, ValueVector) and self.__class__ != other.__class__:
            raise ValueError(f"Unsupported operation: {self.__class__} + {other.__class__}")

        if self._quantities != other._quantities:
            raise ValueError("Cannot add vectors: field names and physcail quantities must be the same")

        return self._create_instance({k: v + getattr(other, k) for k, v in self._values.items()})

    def __sub__(self, other):
        if not isinstance(other, ValueVector) and self.__class__ != other.__class__:
            raise ValueError(f"Unsupported operation: {self.__class__} - {other.__class__}")

        if self._quantities != other._quantities:
            raise ValueError("Cannot subtract vectors: field names and physcail quantities must be the same")

        return self._create_instance({k: v - getattr(other, k) for k, v in self._values.items()})

    def __neg__(self):
        return self._create_instance({k: -v for k, v in self._values.items()})

    def __eq__(self, other) -> bool:
        if other.__class__ != self.__class__:
            return False

        return self._values == other._values

    def __iter__(self) -> typing.Iterator[Value[typing.Any]]:
        return iter(self._values.values())

    def __str__(self) -> str:
        attrs = ", ".join(f"{n}={v}" for n, v in self._values.items())
        return f"[{attrs}]"

    def __repr__(self) -> str:
        attrs = ", ".join(f"{n}={v!r}" for n, v in self._values.items())
        return f"{self.__class__.__name__}({attrs})"
