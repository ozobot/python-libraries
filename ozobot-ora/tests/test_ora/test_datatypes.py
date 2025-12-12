from ozobot.ora.datatypes import Cartesian, Frame, Joints, Tool, ToolCollider, ToolType
from ozobot.ora.units.abstract import units
from ozobot.ora.units.quantities import deg, kg, m, mm


def test_cartesian_str() -> None:
    c = Cartesian(y=20, z=units(0.3, m))
    c.x = 10
    assert str(c) == "[x=10mm, y=20mm, z=0.3m, w=0deg, p=0deg, r=0deg]"


def test_cartesian_repr() -> None:
    c = Cartesian(y=20, z=units(0.3, m))
    c.x = 10
    assert (
        repr(c)
        == "Cartesian(x=Value(10, mm), y=Value(20, mm), z=Value(0.3, m), w=Value(0, deg), p=Value(0, deg), r=Value(0, deg))"
    )


def test_joints_str() -> None:
    j = Joints(a1=10, a2=units(20, deg))
    assert str(j) == "[a1=10deg, a2=20deg, a3=0deg, a4=0deg, a5=0deg, a6=0deg]"


def test_joins_repr() -> None:
    j = Joints(a1=10, a2=units(20, deg))
    assert (
        repr(j)
        == "Joints(a1=Value(10, deg), a2=Value(20, deg), a3=Value(0, deg), a4=Value(0, deg), a5=Value(0, deg), a6=Value(0, deg))"
    )


def test_frame_str() -> None:
    f = Frame(y=20, z=units(0.3, m))
    assert str(f) == "[x=0mm, y=20mm, z=0.3m, w=0deg, p=0deg, r=0deg]"


def test_frame_repr() -> None:
    f = Frame(y=20, z=units(0.3, m))
    assert (
        repr(f)
        == "Frame(x=Value(0, mm), y=Value(20, mm), z=Value(0.3, m), w=Value(0, deg), p=Value(0, deg), r=Value(0, deg))"
    )


def test_tool_collider_str() -> None:
    c = ToolCollider(0)
    assert str(c) == "type 0"


def test_tool_collider_repr() -> None:
    c = ToolCollider(0)
    assert repr(c) == "ToolCollider(model_type=0)"


def test_tool_str() -> None:
    t = Tool(
        type=ToolType.FINGER_GRIPPER,
        tcp=Frame(z=30),
        center_of_gravity=(units(0, mm),) * 3,
        weight=units(0.1, kg),
        collider=ToolCollider(1),
    )
    assert (
        str(t)
        == "[type=ToolType.FINGER_GRIPPER, tcp=[x=0mm, y=0mm, z=30mm, w=0deg, p=0deg, r=0deg], center_of_gravity=[0mm, 0mm, 0mm], weight=0.1kg, collider=type 1]"
    )


def test_tool_repr() -> None:
    t = Tool(
        type=ToolType.FINGER_GRIPPER,
        tcp=Frame(z=30),
        center_of_gravity=(units(0, mm),) * 3,
        weight=units(0.1, kg),
        collider=ToolCollider(1),
    )

    fields = [
        "type=ToolType.FINGER_GRIPPER",
        "tcp=Frame(x=Value(0, mm), y=Value(0, mm), z=Value(30, mm), w=Value(0, deg), p=Value(0, deg), r=Value(0, deg))",
        "center_of_gravity=(Value(0, mm), Value(0, mm), Value(0, mm))",
        "weight=Value(0.1, kg)",
        "collider=ToolCollider(model_type=1)",
    ]

    assert repr(t) == f"Tool({', '.join(fields)})"


def test_cartesian_replace() -> None:
    assert Cartesian(x=1, y=2, z=3, r=4, p=5, w=6).replace(y=20, p=50) == Cartesian(x=1, y=20, z=3, r=4, p=50, w=6)


def test_joint_replace() -> None:
    assert Joints(a1=1, a2=2, a3=3, a4=4, a5=5, a6=6).replace(a2=20, a5=50) == Joints(
        a1=1, a2=20, a3=3, a4=4, a5=50, a6=6
    )


def test_frame_replace() -> None:
    assert Frame(x=1, y=2, z=3, r=4, p=5, w=6).replace(y=20, p=50) == Frame(x=1, y=20, z=3, r=4, p=50, w=6)


def test_tool_collider_replace() -> None:
    assert ToolCollider(model_type=1).replace(model_type=2) == ToolCollider(model_type=2)


def test_tool_replace() -> None:
    original = Tool(
        type=ToolType.NO_TOOL,
        tcp=Frame(x=1, y=2, z=3, r=4, p=5, w=6),
        center_of_gravity=(units(1, mm), units(2, mm), units(3, mm)),
        weight=units(1, kg),
        collider=ToolCollider(model_type=1),
    )
    expected = Tool(
        type=ToolType.FINGER_GRIPPER,
        tcp=Frame(x=1, y=20, z=3, r=4, p=5, w=6),
        center_of_gravity=(units(1, mm), units(2, mm), units(3, mm)),
        weight=units(2, kg),
        collider=ToolCollider(model_type=1),
    )

    assert (
        original.replace(
            type=ToolType.FINGER_GRIPPER,
            tcp=original.tcp.replace(y=20),
            weight=units(2, kg),
        )
        == expected
    )
