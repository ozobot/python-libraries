from __future__ import annotations

import enum
import typing
from dataclasses import dataclass
from typing import TypeVar

from ozobot.ora import arithmetics
from ozobot.ora.units import Value, domains, quantities

_TIo = TypeVar("_TIo", bool, float)


class IoValueType(enum.StrEnum):
    DIGITAL = "digital"
    ANALOG = "analog"


@dataclass(frozen=True)
class IoName(typing.Generic[_TIo]):
    index: int
    value_type: IoValueType


@dataclass(frozen=True)
class IoValue(typing.Generic[_TIo]):
    index: int
    value: _TIo
    value_type: IoValueType


class ToolType(enum.Enum):
    NO_TOOL = "noTool"
    FINGER_GRIPPER = "fingerGripper"
    VACUUM_GRIPPER = "vacuumGripper"


class ReferenceFrameModifier(enum.Enum):
    ABSOLUTE = "global"
    RELATIVE = "relative"
    TOOL = "tool"


class FingerGripperState(enum.Enum):
    """
    The state of the finger gripper.
    """

    OPEN = "open"
    CLOSED = "close"
    OFF = "stop"


class VacuumGripperState(enum.Enum):
    """
    The state of the vacuum gripper.
    """

    ON = enum.auto()
    OFF = enum.auto()


type _TDistance = Value[domains.DistanceDomain] | float | int
type _TAngle = Value[domains.AngleDomain] | float | int


class Cartesian(arithmetics.ValueVector):
    """
    A structure representing a Cartesian pose.

    Instantiate by calling `Cartesian(x, y, z, w, p, r)`, where `x`, `y`, `z`, `w`, `p`, and `r` are the pose's x, y, z, yaw, pitch, and roll values, respectively. The values
    can be either plain numbers (`float` or `int`) or physical quantities. Mixing the two is allowed. Both positional and named arguments can be used. Omitted values default to 0.

    When using plain numbers, please make sure to use correct units. The default units are millimeters for distances and degrees for angles. For physical quantities, use the
    `DistanceDomain` for x, y, z and `AngleDomain` for w, p, r.

    For example, the following are equivalent:

    .. code-block:: python

        p1 = Cartesian(200, 50, 50, 0, 0, 180)

        p2 = Cartesian(
            x=units(0.2, m),
            y=50,
            z=50,
            r=units(pi, rad)
        )

    :var x: The x-coordinate of the pose represented as Value[DistanceDomain].

    :var y: The y-coordinate of the pose represented as Value[DistanceDomain].

    :var z: The z-coordinate of the pose represented as Value[DistanceDomain].

    :var w: The yaw angle represented as Value[AngleDomain].

    :var p: The pitch angle represented as Value[AngleDomain].

    :var r: The roll angle represented as Value[AngleDomain].
    """

    _quantities = {
        "x": quantities.mm,
        "y": quantities.mm,
        "z": quantities.mm,
        "w": quantities.deg,
        "p": quantities.deg,
        "r": quantities.deg,
    }

    def __init__(self, x: _TDistance = 0, y: _TDistance = 0, z: _TDistance = 0, w: _TAngle = 0, p: _TAngle = 0, r: _TAngle = 0):
        super().__init__(x=x, y=y, z=z, w=w, p=p, r=r)

    x = arithmetics.rw_property("x", Value[domains.DistanceDomain])
    y = arithmetics.rw_property("y", Value[domains.DistanceDomain])
    z = arithmetics.rw_property("z", Value[domains.DistanceDomain])
    w = arithmetics.rw_property("w", Value[domains.AngleDomain])
    p = arithmetics.rw_property("p", Value[domains.AngleDomain])
    r = arithmetics.rw_property("r", Value[domains.AngleDomain])

    def replace(
        self,
        *,
        x: _TDistance | None = None,
        y: _TDistance | None = None,
        z: _TDistance | None = None,
        w: _TAngle | None = None,
        p: _TAngle | None = None,
        r: _TAngle | None = None,
    ) -> Cartesian:
        """
        Create a new instance of :py:class:`Cartesian` with given components replaced leaving the instance intact.

         For example
         .. code-block:: python
             c1 = Cartesian(x=1, r=10)    # c1 = Cartesian(1, 0, 0, 10, 0, 0)
             c2 = c1.replace(x=2, y=2)    # c2 = Cartesian(2, 2, 0, 10, 0, 0), c1 remains the same
        """
        return Cartesian(
            x=x if x else self.x,
            y=y if y else self.y,
            z=z if z else self.z,
            w=w if w else self.w,
            p=p if p else self.p,
            r=r if r else self.r,
        )


class Joints(arithmetics.ValueVector):
    """
    A structure representing a Joint configuration.

    Instantiate by calling `Joint(a1, a2, a3, a4, a5, a6)`, where `a1`, `a2`, `a3`, `a4`, `a5`, and `a6` are the joint angles. The values
    can be either plain numbers (`float` or `int`) or physical quantities. Mixing the two is allowed. Both positional and named arguments can be used. Omitted values default to 0.

    When using plain numbers, please make sure to use correct units. The default units are degrees. For physical quantities, use the `AngleDomain`.

    For example, the following are equivalent:

    .. code-block:: python

        j1 = Joints(0, 0, 90, 0, 90, 45)

        j2 = Joints(
            a3=90,
            a5=units(pi/2, rad),
            a6=units(45, deg)
        )

    :var a1: Angle of the first joint represented as `Value[AngleDomain]`.

    :var a2: Angle of the second joint represented as `Value[AngleDomain]`.

    :var a3: Angle of the third joint represented as `Value[AngleDomain]`.

    :var a4: Angle of the fourth joint represented as `Value[AngleDomain]`.

    :var a5: Angle of the fifth joint represented as `Value[AngleDomain]`.

    :var a6: Angle of the sixth joint represented as `Value[AngleDomain]`.

    """

    _quantities = {
        "a1": quantities.deg,
        "a2": quantities.deg,
        "a3": quantities.deg,
        "a4": quantities.deg,
        "a5": quantities.deg,
        "a6": quantities.deg,
    }

    def __init__(self, a1: _TAngle = 0, a2: _TAngle = 0, a3: _TAngle = 0, a4: _TAngle = 0, a5: _TAngle = 0, a6: _TAngle = 0):
        super().__init__(a1=a1, a2=a2, a3=a3, a4=a4, a5=a5, a6=a6)

    a1 = arithmetics.rw_property("a1", Value[domains.AngleDomain])
    a2 = arithmetics.rw_property("a2", Value[domains.AngleDomain])
    a3 = arithmetics.rw_property("a3", Value[domains.AngleDomain])
    a4 = arithmetics.rw_property("a4", Value[domains.AngleDomain])
    a5 = arithmetics.rw_property("a5", Value[domains.AngleDomain])
    a6 = arithmetics.rw_property("a6", Value[domains.AngleDomain])

    def replace(
        self,
        *,
        a1: _TAngle | None = None,
        a2: _TAngle | None = None,
        a3: _TAngle | None = None,
        a4: _TAngle | None = None,
        a5: _TAngle | None = None,
        a6: _TAngle | None = None,
    ) -> Joints:
        """
        Create a new instance of :py:class:`Joints` with given components replaced leaving the instance intact.

         For example
         .. code-block:: python
             j1 = Joints(a1=1, a4=10)      # j1 = Joints(1, 0, 0, 10, 0, 0)
             j2 = j1.replace(a1=2, a2=2)   # j2 = Joints(2, 2, 0, 10, 0, 0), j2 remains the same
        """
        return Joints(
            a1=a1 if a1 else self.a1,
            a2=a2 if a2 else self.a2,
            a3=a3 if a3 else self.a3,
            a4=a4 if a4 else self.a4,
            a5=a5 if a5 else self.a5,
            a6=a6 if a6 else self.a6,
        )


class Frame(arithmetics.ValueVector):
    """
    A structure representing a Frame.

    Instantiate by calling `Frame(x, y, z, w, p, r)`, where `x`, `y`, `z`, `w`, `p`, and `r` are the pose's x, y, z, yaw, pitch, and roll values, respectively. The values
    can be either plain numbers (`float` or `int`) or physical quantities. Mixing the two is allowed. Both positional and named arguments can be used. Omitted values default to 0.

    When using plain numbers, please make sure to use correct units. The default units are millimeters for distances and degrees for angles. For physical quantities, use the
    `DistanceDomain` for x, y, z and `AngleDomain` for w, p, r.

    For example, the following are equivalent:

    .. code-block:: python

        p1 = Frame(200, 50, 50, 0, 0, 180)

        p2 = Frame(
            x=units(0.2, m),
            y=50,
            z=50,
            r=units(pi, rad)
        )

    :var x: Frame origin x-coordinate represented as Value[DistanceDomain].

    :var y: Frame origin y-coordinate represented as Value[DistanceDomain].

    :var z: Frame origin z-coordinate represented as Value[DistanceDomain].

    :var w: Frame orientation yaw angle represented as Value[AngleDomain].

    :var p: Frame orientation pitch angle represented as Value[AngleDomain].

    :var r: Frame orientation roll angle represented as Value[AngleDomain].
    """

    _quantities = {
        "x": quantities.mm,
        "y": quantities.mm,
        "z": quantities.mm,
        "w": quantities.deg,
        "p": quantities.deg,
        "r": quantities.deg,
    }

    def __init__(self, x: _TDistance = 0, y: _TDistance = 0, z: _TDistance = 0, w: _TAngle = 0, p: _TAngle = 0, r: _TAngle = 0):
        super().__init__(x=x, y=y, z=z, w=w, p=p, r=r)

    x = arithmetics.rw_property("x", Value[domains.DistanceDomain])
    y = arithmetics.rw_property("y", Value[domains.DistanceDomain])
    z = arithmetics.rw_property("z", Value[domains.DistanceDomain])
    w = arithmetics.rw_property("w", Value[domains.AngleDomain])
    p = arithmetics.rw_property("p", Value[domains.AngleDomain])
    r = arithmetics.rw_property("r", Value[domains.AngleDomain])

    def replace(
        self,
        *,
        x: _TDistance | None = None,
        y: _TDistance | None = None,
        z: _TDistance | None = None,
        w: _TAngle | None = None,
        p: _TAngle | None = None,
        r: _TAngle | None = None,
    ) -> Frame:
        """
        Create a new instance of :py:class:`Frame` with given components replaced leaving the instance intact.

         For example
         .. code-block:: python
             f1 = Frame(x=1, r=10)        # f1 = Frame(1, 0, 0, 10, 0, 0)
             f2 = f1.replace(x=2, y=2)    # f2 = Frame(2, 2, 0, 10, 0, 0), f1 remains the same
        """

        return Frame(
            x=x if x else self.x,
            y=y if y else self.y,
            z=z if z else self.z,
            w=w if w else self.w,
            p=p if p else self.p,
            r=r if r else self.r,
        )


class ToolCollider:
    model_type: int

    def __init__(self, model_type: int):
        self.model_type = model_type

    def __eq__(self, other):
        if not isinstance(other, ToolCollider):
            return False

        return self.model_type == other.model_type

    def __str__(self) -> str:
        return f"type {self.model_type}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model_type={self.model_type})"

    def replace(self, *, model_type: int | None = None) -> ToolCollider:
        return ToolCollider(
            model_type=model_type if model_type else self.model_type,
        )


class Tool:
    type: ToolType
    tcp: Frame
    center_of_gravity: tuple[Value[domains.DistanceDomain], Value[domains.DistanceDomain], Value[domains.DistanceDomain]]
    weight: Value[domains.WeightDomain]
    collider: ToolCollider

    def __init__(
        self,
        *,
        type: ToolType,
        tcp: Frame,
        center_of_gravity: tuple[Value[domains.DistanceDomain], Value[domains.DistanceDomain], Value[domains.DistanceDomain]],
        weight: Value[domains.WeightDomain],
        collider: ToolCollider,
    ):
        self.type = type
        self.tcp = tcp
        self.center_of_gravity = center_of_gravity
        self.weight = weight
        self.collider = collider

    def __eq__(self, other):
        if not isinstance(other, Tool):
            return False

        return self.type == other.type and self.tcp == other.tcp and self.center_of_gravity == other.center_of_gravity and self.weight == other.weight and self.collider == other.collider

    def __str__(self) -> str:
        # we want __str__ string for all fields but `center_of_gravity` where we want a custom format
        patched_fields = {**{k: str(v) for k, v in self.__dict__.items()}, "center_of_gravity": f"[{', '.join(str(v) for v in self.center_of_gravity)}]"}

        return f"[{', '.join(f'{n}={v!s}' for n, v in patched_fields.items())}]"

    def __repr__(self) -> str:
        # we want __repr__ string for all fields but `type` where we want the __str__ version to get `ToolType.TOOL_NAME` format
        patched_fields = {
            **{k: repr(v) for k, v in self.__dict__.items()},
            "type": str(self.type),
        }

        return f"{self.__class__.__name__}({', '.join(f'{n}={v}' for n, v in patched_fields.items())})"

    def replace(
        self,
        *,
        type: ToolType | None = None,
        tcp: Frame | None = None,
        center_of_gravity: tuple[Value[domains.DistanceDomain], Value[domains.DistanceDomain], Value[domains.DistanceDomain]] | None = None,
        weight: Value[domains.WeightDomain] | None = None,
        collider: ToolCollider | None = None,
    ) -> Tool:
        """
        Create a new instance of :py:class:`Tool` with given components replaced leaving the instance intact.

         For example
         .. code-block:: python
             t1 = Tool(type=ToolType.NO_TOOL, tcp=Frame(z=30, w=90), ...)

             t2 = t1.replace(type=ToolType.FINGER_GRIPPER, tcp=Frame(z=40, w=90))
             t3 = t1.replace(type=ToolType.FINGER_GRIPPER, tcp=t1.replace(z=40))   # replace can be nested
             # t2, t3 both contain Tool(type=ToolType.FINGER_GRIPPER, tcp=Frame(z=40, w=90), ...)
        """

        return Tool(
            type=type if type else self.type,
            tcp=tcp if tcp else self.tcp,
            center_of_gravity=center_of_gravity if center_of_gravity else self.center_of_gravity,
            weight=weight if weight else self.weight,
            collider=collider if collider else self.collider,
        )
