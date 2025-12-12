Simple API module
=================
This module implements a simple synchronous API for controlling a single Ozobot ORA robot. The API is designed to be simple and easy to use, while still providing
a high level of control over the robot. The module exports static classes or instantiated and ready to be used objects to reduce the boilerplate.
The API is synchronous, meaning that almost all calls will block the program execution until the robot has completed the requested action. This makes it easy to write
simple scripts that control the robot in a straightforward manner.

Datatypes
---------
The following datatypes are used throughout the library.

.. autoclass:: ozobot.ora.simple.Cartesian
.. autoclass:: ozobot.ora.simple.Frame
.. autoclass:: ozobot.ora.simple.Joints
.. autoclass:: ozobot.ora.simple.Tool

Motion control
--------------

.. autoclass:: ozobot.ora.simple.move
  :members: joint, linear, linear_rel, linear_tool, circ, set_defaults_joint, set_defaults_linear

Gripper state
-------------
To use the `gripper` class, extra types are necessary.

.. autoclass:: ozobot.ora.simple.gripper
    :members: set_state


.. autoclass:: ozobot.ora.datatypes.FingerGripperState
  :show-inheritance:

  .. autoattribute:: OPEN
      :no-value:
  .. autoattribute:: CLOSED
      :no-value:
  .. autoattribute:: OFF
      :no-value:

.. autoclass:: ozobot.ora.datatypes.VacuumGripperState
  :show-inheritance:

  .. autoattribute:: ON
      :no-value:
  .. autoattribute:: OFF
      :no-value:

.. attention::
  Enum values need to be referenced by their full name, for example `FingerGripperState.OPEN`, not just `OPEN`.



Input/output
------------
The following classes are used to read and write digital and analog signals.

.. autoclass:: ozobot.ora.simple.di
.. autoclass:: ozobot.ora.simple.do
.. autoclass:: ozobot.ora.simple.ai
.. autoclass:: ozobot.ora.simple.ao

State
-----
This section describes how to read robot states and how to change current tool and frame.

.. autoclass:: ozobot.ora.simple.tool
  :members: set, get, context

.. autoclass:: ozobot.ora.simple.frame
  :members: set, get, context

.. autoclass:: ozobot.ora.simple.state
    :members: get_joints, get_pose



Units
-----
Unit system allows to easily convert physical values with user preferred units to the units compatible with the robot. It
also allows to do some basic type checking to prevent typos and unit mismatch. Some units can be combined, for example
distance over time yields speed.

.. seealso:: Detailed description of the framework can be found in the :doc:`units` document.

.. automodule:: ozobot.ora.simple
  :members: units


.. toctree::
  :maxdepth: 2
  :caption: Contents:



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
