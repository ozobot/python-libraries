Units
#####
Physical quantities and units are defined in the :py:mod:`units` module. The module provides a set of predefined units and unit
systems. It allows to do simple conversions between the user preferred and "base" units the robot understands. The framework
also provides a type checked interface that ensures that the physical domains are not mixed up (e.g., passing speed in m/s instead of percent).
Numeric values with units are represented as objects of the :code:`Value[]` generic class, for example :code:`Value[DistanceDomain]` or :code:`Value[AngleDomain]`.

Supported units
---------------
The following units are provided by the framework:

+------------------------+-------------------+----------------+
| Name                   | Domain            | Represented as |
+========================+===================+================+
| millimetre             | `DistanceDomain`  | `mm`           |
+------------------------+-------------------+----------------+
| metre                  | `DistanceDomain`  | `m`            |
+------------------------+-------------------+----------------+
| inch                   | `DistanceDomain`  | `inch`         |
+------------------------+-------------------+----------------+
| degree                 | `AngleDomain`     | `deg`          |
+------------------------+-------------------+----------------+
| radian                 | `AngleDomain`     | `rad`          |
+------------------------+-------------------+----------------+
| second                 | `TimeDomain`      | `s`            |
+------------------------+-------------------+----------------+
| minute                 | `TimeDomain`      | `minute`       |
+------------------------+-------------------+----------------+
| hour                   | `TimeDomain`      | `hour`         |
+------------------------+-------------------+----------------+
| percent                | `RatioDomain`     | `percent`      |
+------------------------+-------------------+----------------+
| kilogram               | `WeightDomain`    | `kg`           |
+------------------------+-------------------+----------------+

Additionally, the following unit systems are provided:

+------------------------+-----------------------------+-----------------------------+
| Name                   | Domain                      | Represented as              |
+========================+=============================+=============================+
| speed                  | `SpeedDomain`               | `mm/s`                      |
+------------------------+-----------------------------+-----------------------------+
| acceleration           | `AccelerationDomain`        | `mm/s ** 2`                 |
+------------------------+-----------------------------+-----------------------------+
| jerk                   | `JerkDomain`                | `mm/s ** 3`                 |
+------------------------+-----------------------------+-----------------------------+
| angular speed          | `SpeedDomain`               | `deg/s`                     |
+------------------------+-----------------------------+-----------------------------+
| angular acceleration   | `AngularAccelerationDomain` | `deg/s ** 2`                |
+------------------------+-----------------------------+-----------------------------+
| angular jerk           | `AngularJerkDomain`         | `deg/s ** 3`                |
+------------------------+-----------------------------+-----------------------------+


Using units
-----------
*Converting from number*

Object representing a physical quantity can be created using the `ozobot.ora.units.units` function. To create the object and assign it to a variable, the following syntax is used:

.. code-block:: python

  speed = units(0.1, m)

*Converting back to number*
The result of `units` function is not a number, but an object that represents a physical quantity. To get the value of the quantity, the default 
conversion function to `float` or `int` should be used. This yields the value in the base unit of the quantity. For example, to get the value of
the speed in m/s, the following syntax is used:

.. code-block:: python

  speed = units(10, mm/s)
  speed_m_s = float(speed)

*Combining units*

Units can be combined to create more complex units. For example, to create a speed object, the following syntax is used:

.. code-block:: python

  speed = units(10, mm/s)
  angular_acceleration = units(100, deg/s ** 2)

.. tip:: How do I know what units to use?

  See the function signature. For example :py:meth:`~ozobot.ora.simple.move.joint` accepts :code:`speed` as :code:`RatioDomain` quantity. After checking the `Supported Units`_ table we can
  see that :code:`RatioDomain` is represented as :code:`percent`. Therefore, the speed should be passed as :code:`~ozobot.ora.units.quantities.percent` quantity. For example,  :code:`move.joints(pose, speed=units(10, percent))`
