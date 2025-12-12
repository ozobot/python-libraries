from __future__ import annotations

import contextlib
import typing

from ozobot.ora.datatypes import IoValueType
from ozobot.ora.driver import get_driver
from ozobot.ora.iogroups import InputFactory, OutputFactory
from ozobot.ora.sync import (
    Cartesian,
    FingerGripperState,
    Frame,
    Joints,
    OraSync,
    ReferenceFrameModifier,
    Tool,
    VacuumGripperState,
    wait,
)
from ozobot.ora.units import Value, domains, units
from ozobot.ora.units.quantities import deg, hour, inch, kg, m, minute, mm, percent, rad, s

_TIo = typing.TypeVar("_TIo", bool, float, int)

# FIXME: replace by actor api
_driver_cls = get_driver()
_driver = _driver_cls()
_ora = OraSync(_driver)


class move:
    """
    Class providing methods for moving single robot and setting the motion parameters. The methods are static, therefore they
    can be called without creating an instance of the class, for example:

    .. code-block:: python

        move.joint(...)
        move.linear(...)
        move.linear_rel(...)
        move.linear_tool(...)
        move.circ(...)
        move.set_default_radius(...)
        move.set_defaults_joint(...)
        move.set_defaults_linear(...)
    """

    @staticmethod
    def joint(
        pose: Joints | Cartesian,
        *,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
    ) -> None:
        """
        Move the robot to the specified position by a joint movement.

        The call is blocking.

        Joint movement is a movement in the joint space, where each individual joint angle is changed by the shortest movement possible.
        The path that the TCP follows is generally not a line. Does not suffer from :doc:`singularities <singularity>`. Robot may, and
        probably will, not go over a straight line between two points.

        .. code-block:: python

            # example code to move the robot to the specified joint configuration
            move.joint(Joints(0, 0, 0, 0, 0, 0))


        :param pose: :py:class:`Joints` configuration or :py:class:`Cartesian` pose to move the robot to.
        :param speed: Optional speed of the movement. If unset, the default speed is used.
        :param acceleration: Optional acceleration of the movement. If unset, the default acceleration is used.

        .. note::
            - To set default speed and acceleration, see :py:meth:`set_defaults_joint`

        """
        return _ora.move_joints(pose, speed=speed, acceleration=acceleration)

    @staticmethod
    def linear(
        pose: Cartesian,
        *,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
    ) -> None:
        """
        Move the robot to the specified :py:class:`Cartesian` pose along a linear path in Cartesian space.

        The call is blocking.

        Linear movement is a movement in the Cartesian space, where the robot moves in a straight line between two points. Robot may
        suffer from :doc:`singularities <singularity>`.

        The figure depicts reference frame relation. In this case, the Cartesian coordinates represent a transformation from the world frame to the desired Tool Frame.

        .. figure:: img/absolute-motion.svg
            :width: 60%
            :align: center

            The dotted line represents :code:`pose` parameter - the relation between the current robot frame (World Frame) and the Tool Frame.

        .. code-block:: python

            # example code to move the robot to the specified joint configuration
            move.linear(Cartesian(100, 0, 0, 0, 0, 180))

        :param pose: :py:class:`Cartesian` pose to move the robot to.
        :param speed: Optional speed of the movement. If unset, the default speed is used.
        :param acceleration: Optional acceleration of the movement. If unset, the default acceleration is used.

        .. note::
            - To set default speed and acceleration, see :py:meth:`set_defaults_linear`
        """
        return _ora.move_linear(pose, speed=speed, acceleration=acceleration, reference=ReferenceFrameModifier.ABSOLUTE)

    @staticmethod
    def linear_rel(
        offset: Cartesian,
        *,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
    ) -> None:
        """
        Move the robot by the specified :py:class:`Cartesian` offset along a linear path in Cartesian space.

        Same as :py:meth:`linear`, but the movement is relative to the current position of the robot.

        The figure depicts reference frame relation. In this case, the Cartesian coordinates represent an offset from point P1 to point P2 in the World Frame.
        In the example below, transformation from P1 to P2 would have positive X value and zero Y value, because we are in the World Frame.

        .. figure:: img/relative-motion.svg
            :width: 60%
            :align: center

            Dotted lines emphasise the :code:`offset` is relative the World Frame.

        :param offset: :py:class:`Cartesian` offset to move the robot to.
        :param speed: Optional speed of the movement. If unset, the default speed is used.
        :param acceleration: Optional acceleration of the movement. If unset, the default acceleration is used.
        """
        return _ora.move_linear(
            offset, speed=speed, acceleration=acceleration, reference=ReferenceFrameModifier.RELATIVE
        )

    @staticmethod
    def linear_tool(
        offset: Cartesian,
        *,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
    ) -> None:
        """
        Move the robot to the specified :py:class:`Cartesian` position in the tool coordinate frame along a linear path in Cartesian space.

        Same as :py:meth:`linear`, but the movement is relative to the current position of the robot.

        The figure depicts reference frame relation. In this case, the Cartesian coordinates represent a transformation of the Tool Frame from the current point P1 to
        the desired point P2. In the example below, transformation from P1 to P2 would have negative Y value and zero X value, because we are in the Tool Frame.

        .. figure:: img/tool-motion.svg
            :width: 60%
            :align: center

            Dotted line emphasises the :code:`offset` is relative the Tool Frame.

        :param offset: :py:class:`Cartesian` pose to move the robot to.
        :param speed: Optional speed of the movement. If unset, the default speed is used.
        :param acceleration: Optional acceleration of the movement. If unset, the default acceleration is used.
        """
        return _ora.move_linear(offset, speed=speed, acceleration=acceleration, reference=ReferenceFrameModifier.TOOL)

    @staticmethod
    def circ(
        p_aux: Cartesian,
        p_end: Cartesian,
        *,
        arc_angle: Value[domains.AngleDomain],
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
    ) -> None:
        """
        Move the robot to the specified :py:class:`Cartesian` position over a circular segment path in Cartesian space.

        The call is blocking.

        Circular segment movement is a movement in the Cartesian space, where the robot moves along a circular path between two points. The circle
        is defined by the current point, auxiliary point, the end point and the arc angle. Robot may suffer from :doc:`singularities <singularity>`.

        .. figure:: img/circular-motion.svg
            :width: 70%
            :align: center

            Figure shows the three-point circle definition and how the arc angle influences the arc length.

        :param p_aux: Auxiliary point on the circle.
        :param p_end: End point on the circle.
        :param arc_angle: Angle of the arc that the robot will move along.
        :param speed: Optional speed of the movement. If unset, the default speed is used.
        :param acceleration: Optional acceleration of the movement. If unset, the default acceleration is used.

        .. note::
            - To set default speed and acceleration, see :py:meth:`set_defaults_linear`
        """
        return _ora.move_circle(p_aux, p_end, arc_angle=arc_angle, speed=speed, acceleration=acceleration)

    @staticmethod
    def set_defaults_linear(
        *,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ) -> None:
        """
        Set default parameters for linear movement.

        All the parameters are optional, therefore it's possible to set only the ones that should be changed.

        .. seealso::
            See :doc:`units` for more information on how to use parameters with units.

        :param speed: Default speed for linear movement.
        :param acceleration: Default acceleration for linear movement.
        :param jerk: Default jerk for linear movement.
        """
        return _ora.set_defaults_linear(speed, acceleration, jerk)

    @staticmethod
    def set_defaults_joint(
        *,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        jerk: Value[domains.AngularJerkDomain] | None = None,
    ) -> None:
        """
        Set default parameters for joint movement.

        All the parameters are optional, therefore it's possible to set only the ones that should be changed.

        .. seealso::
            See :doc:`units` for more information on how to use parameters with units.

        :param speed: Default speed for joint movement.
        :param acceleration: Default acceleration for joint movement.
        :param jerk: Default jerk for joint movement.
        """
        return _ora.set_defaults_joint(speed, acceleration, jerk)


class gripper:
    """
    Class providing methods for controlling gripper of single robot. The methods are static, therefore they
    can be called without creating an instance of the class, for example:

    .. code-block:: python

        gripper.set_state(...)
    """

    @staticmethod
    def set_state(state: FingerGripperState | VacuumGripperState) -> None:
        """
        Set the state of the gripper.

        Sets the state of the gripper to the specified state. The correct gripper has to be configured and attached to the robot,
        there is no check for the tool's physical presence. If there are any commands in the queue, function only sets the gripper
        state after the last command is executed.

        .. code-block:: python

            # example code to close the finger gripper
            gripper.set_state(FingerGripperState.CLOSE)


        :param state: State of the gripper. Can be either :py:class:`FingerGripperState` or :py:class:`VacuumGripperState` value.

        .. seealso:: See :py:meth:`tool.set` to learn how to set the tool type.
        """
        return _ora.set_tool_state(state)


class tool:
    """
    Class providing methods for controlling tool (TCP, weight, control outputs) of single robot. The methods are static, therefore they
    can be called without creating an instance of the class, for example:

    .. figure:: img/user-tool.svg
        :align: center

        Robot's Cartesian pose the position of the current Tool Center Point (TCP) with respect to the selected Frame.

    .. code-block:: python

        tool.set(...)
        current_tool = tool.get()

        with tool.context(...):
            ...
    """

    @staticmethod
    def set(tool: Tool) -> None:
        """
        Set the tool.

        Sets the tool to the specified tool. The correct tool has to be attached to the robot, there is no check for
        the tool's physical presence. If there are any commands in the queue, function only sets the gripper
        state after the last command is executed.

        :param tool: Tool to set.

        .. code-block:: python

            # example code to set the vacuum gripper as a tool
            tool.set(tools.VACUUM_GRIPPER)

            # complex example with custom TCP offset
            my_tool = tools.VACUUM_GRIPPER
            my_tool.tcp += Frame(z=10)
            tool.set(my_tool)
        """
        return _ora.set_tool(tool)

    @staticmethod
    def get() -> Tool:
        """
        Get the current tool configuration.

        This is the software configuration, there is no check for the tool's physical presence.

        :return: Current tool configuration.
        """
        return _ora.get_tool()

    @staticmethod
    @contextlib.contextmanager
    def context(tool: Tool) -> typing.Iterator[None]:
        """
        Context manager for setting the tool for a block of code.

        Context manager that configures the selected tool for calls made within the code block.

        :param tool: Tool to set for the code block.

        .. code-block:: python

            tool.set(tools.FINGER_GRIPPER)
            move.linear(...)  # this movement is done with the finger gripper tool

            with tool.context(tools.VACUUM_GRIPPER):
                move.linear(...)  # this movement is done with the vacuum gripper tool
                move.linear(...)  # this movement is done with the vacuum gripper tool

            move.linear(...)  # this movement is done with the finger gripper tool
        """
        with _ora.tool(tool):
            yield


class frame:
    """
    Class providing methods for controlling user frame of single robot. The methods are static, therefore they
    can be called without creating an instance of the class, for example:

    .. figure:: img/user-frame.svg
        :align: center

        Robot's Cartesian pose is the position with restpect to the selected Frame.

    .. code-block:: python

        frame.set(...)
        current_frame = frame.get()

        with frame.context(...):
            ...
    """

    @staticmethod
    def set(frame: Frame) -> None:
        """
        Set the current frame.

        :param frame: Frame to set.

        .. code-block:: python

            # example code to set the CONVEYOR user frame
            frame.set(frames.CONVEYOR)

            # complex example with modified frame
            modified_conveyor_frame = frames.CONVEYOR
            modified_conveyor_frame.z = 100
            frame.set(modified_conveyor_frame)
        """
        return _ora.set_frame(frame)

    @staticmethod
    def get() -> Frame:
        """
        Get the current frame.

        :return: Current frame.
        """
        return _ora.get_frame()

    @staticmethod
    @contextlib.contextmanager
    def context(frame: Frame):
        """
        Context manager for setting the current frame for a block of code.

        Context manager that configures the selected frame for calls made within the code block.

        :param frame: Frame to set for the code block.

        .. code-block:: python

            frame.set(frames.WORLD)
            move.linear(...)  # this movement is done in the world frame

            with tool.context(tools.CONVEYOR):
                move.linear(...)  # this movement is done in the conveyor frame

            move.linear(...)  # this movement is done in the world frame
        """
        with _ora.frame(frame):
            yield


class state:
    """
    Class providing methods for getting the current state of the robot. The methods are static, therefore they
    can be called without creating an instance of the class, for example:

    .. code-block:: python

        pose = state.get_pose()
        joints = state.get_joints()
    """

    @staticmethod
    def get_pose() -> Cartesian:
        """
        Get the current pose of the robot in the current frame.
        """
        return _ora.get_pose()

    @staticmethod
    def get_joints() -> Joints:
        """
        Get the current joint configuration of the robot.
        """
        return _ora.get_joints()


di = InputFactory._create(_ora, IoValueType.DIGITAL)
"""
`di` is a object allows to create a readable digital input definition. 

Individual inputs can be accessed by using square brackets, the same way as the list is indexed. Input and output indexes are zero-based. 
Under the hood, its custom implementation of :code:`__getitem__` method supports both integer indices, slices and tuples of integers. In case of 
the tuple or slice, an :code:`InputGroup` object is returned, which allows to read multiple inputs at once. :code:`Input` object is returned otherwise.

Both types can be used to *read* the current input value. Both then return the value of the input which is a 
sequence of boolean values for input groups or a single boolean value for single inputs. High values on the input yield :code:`True` and low values :code:`False`. 

Both types can be used to *read* the current input value or to wait for the input match a predicate. All the operations then return the value of the input which is a 
sequence of :code:`bool` values for input groups or a single :code:`bool` value for single inputs. The `wait` function blocks until there is a sample
matching the given predicate - so for example, `my_input.wait(lambda i: not i)` would ignore samples `True` but it would return on `False`.
 
Examples
########

Reading
-------
.. code-block:: python

    fifth_input = di[5]
    state = fifth_input.read()
    # state now contains True or False value

    state = first_input.wait(lambda i: i)
    # state now contains value `True`, all `False` samples were ignored

Referencing an input group by slice
-----------------------------------
.. code-block:: python
    
    # or reading multiple inputs at once
    first_three_inputs = di[0:3]
    states = first_three_inputs.read()
    # states variable now contain list of True or False values, 
    # for example [True, False, True]

    state = first_input.wait(lambda i: i[0] and not i[1])
    # states variable now contain [True, False, ...], all the other samples were ignored

Referencing an input group by tuple
-----------------------------------
.. code-block:: python
    
    # or reading multiple inputs at once
    my_inputs = di[0, 1, 3]
    states = my_inputs.read()
    # states variable now contain list of True or False values, 
    # for example [True, False, True]

    state = first_input.wait(lambda i: i[0] and not i[1])
    # states variable now contain [True, False, ...], all the other samples were ignored

"""

do = OutputFactory._create(_ora, IoValueType.DIGITAL)
"""
`do` is a object allows to create a writable digital output definition. 

Individual outputs can be accessed by using square brackets, the same way as the list is indexed. Input and output indexes are zero-based. 
Under the hood, its custom implementation of :code:`__getitem__` method supports both integer indices, slices and tuples of integers. In case of 
the tuple or slice, an :code:`OutputGroup` object is returned, which allows to read multiple inputs at once. :code:`Output` object is returned otherwise.

Both types can be used to *write* boolean values to the output. A single value in case of :code:`Output`, a sequence of values in case of :code:`OutputGroup`. 

Examples
########

Writing
-------
.. code-block:: python
    
    fifth_output = do[4]
    fifth_output.write(True)
    # fifth output is now set to HIGH


Writing an output group
-----------------------
.. code-block:: python

    first_three_outputs = do[0:3]
    first_three_outputs.write([True, False, True])
    # first three outputs are now set to HIGH, LOW, HIGH
"""

ai = InputFactory._create(_ora, IoValueType.ANALOG)
"""
`ai` is a object allows to create a readable analog input definition. 

Individual inputs can be accessed by using square brackets, the same way as the list is indexed. Input and output indexes are zero-based. 
Under the hood, its custom implementation of :code:`__getitem__` method supports both integer indices, slices and tuples of integers. In case of 
the tuple or slice, an :code:`InputGroup` object is returned, which allows to read multiple inputs at once. :code:`Input` object is returned otherwise.

Both types can be used to *read* the current input value or to wait for the given input to match a predicate. All the operations then return the value of the input which is a 
sequence of :code:`float` values for input groups or a single :code:`float` value for single inputs. The `wait` function blocks until there is a sample
matching the given predicate - so for example, `my_input.wait(lambda i: i > 5)` would ignore samples `0.1` and `1` but it would return on `5.5`.

Examples
########

Reading
-------
.. code-block:: python

    first_input = ai[0]

    state = first_input.read()
    # state now contains a `float` value, for example 4.5

    state = first_input.wait(lambda i: i > 0.5)
    # state now contains a `float` value, for example 4.5
    #   if a sample not matching the predicate (e.g., 0.1) would be taken, it
    #   would be dropped and the function would wait for another sample


Referencing an input group by slice
-----------------------------------
.. code-block:: python

    # or reading multiple inputs at once
    first_two_inputs = ai[0:2]
    states = first_two_inputs.read()
    # states variable now contain list of `float` values, 
    # for example [0.1, 2.34]

    state = first_input.wait(lambda i: i[0] > 0.5 or i[1] > 0.5)
    # states variable now contain list of `float` values, 
    # for example [1, 2.34]


Referencing an input group by tuple
-----------------------------------
.. code-block:: python

    # or reading multiple inputs at once
    my_inputs = ai[0, 1]
    states = my_inputs.read()
    # states variable now contain list of `float` values, 
    # for example [0.1, 2.34]

    state = first_input.wait(lambda i: i[0] > 0.5 or i[1] > 0.5)
    # states variable now contain list of `float` values, 
    # for example [1, 2.34]   

"""


ao = OutputFactory._create(_ora, IoValueType.ANALOG)
"""
`ao` is a object allows to create a writable analog output definition. 

Individual outputs can be accessed by using square brackets, the same way as the list is indexed. Input and output indexes are zero-based. 
Under the hood, its custom implementation of :code:`__getitem__` method supports both integer indices, slices and tuples of integers. In case of 
the tuple or slice, an :code:`OutputGroup` object is returned, which allows to read multiple inputs at once. :code:`Output` object is returned otherwise.

Both types can be used to *write* :code:`float` values to the output. A single value in case of :code:`Output`, a sequence of values in case of :code:`OutputGroup`. 

Examples
########

Writing
-------
.. code-block:: python

    fifth_output = do[4]
    fifth_output.write(True)
    # fifth output is now set to HIGH


Writing an output group
-----------------------
.. code-block:: python

    first_three_outputs = do[0:3]
    first_three_outputs.write([True, False, True])
    # first three outputs are now set to HIGH, LOW, HIGH
"""

__all__ = (
    "di",
    "do",
    "ai",
    "ao",
    "units",
    "move",
    "gripper",
    "tool",
    "frame",
    "state",
    "wait",
    "Cartesian",
    "Frame",
    "Tool",
    "Joints",
    "FingerGripperState",
    "VacuumGripperState",
    "s",
    "kg",
    "minute",
    "hour",
    "deg",
    "rad",
    "inch",
    "mm",
    "m",
    "percent",
)
