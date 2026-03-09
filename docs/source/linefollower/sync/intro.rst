.. _sync_evo:

Sync API - beginner
===================

If you are just beginning with Python programming, this is the library to use. It hides some of the complexities from you, so that you can focus on learning the language and basic principles of programming. However, this comes at a cost: - the Sync API has limitations such as no concurrency [#foot-threading]_, no cancellations and no guarantees that you will get all data when sampling the sensors.

There is a separate class for each robot type, but all of them share the same interface, so individual robots can be interchanged easily. This is true for functionality the robot actually supports. For example, since Evo does not have a display, there is no display-related functionality implemented.

.. _sync_connecting:

Opening the connection
----------------------

The connection to the robot can be opened with :py:class:`ozobot.ari.SyncAriHandle` or :py:class:`ozobot.evo.SyncEvoHandle` for Ari or Evo respectively. These
two classes accept connection selection filters on initialization and then provide a robot instance through a context manager, for example:

.. code-block:: python
  :linenos:

  from ozobot.ari import SyncAriHandle

  with SyncAriHandle(id="ABC*") as ari1, SyncAriHandle(name="Ari-CDEF") as ari2:
      # you can use ari1 and ari2 here

The specific filters depend on the robot, see the API documentation to learn more: :py:class:`ozobot.ari.SyncAriHandle` or :py:class:`ozobot.evo.SyncEvoHandle`.

Controlling the robot
---------------------

The robot can be controlled by calling functions that block the program execution until the given action is finished. All actions must be executed within the :ref:`connection context manager <sync_connecting>`.

A list of the supported actions with details can be found in the :ref:`API doc <sync_apidoc>`, but to help you get started, let's go through a few examples:

.. code-block:: python
  :caption: Set lights
  :linenos:

  import time
  from ozobot.evo import SyncEvoHandle
  from ozobot.linefollower import NamedColor, LEDMask, RawColor

  with SyncEvoHandle(name="OzoEvo-ABC*") as r:
      # set all front LEDs red
      r.set_led(LEDMask.ALL_FRONT, NamedColor.RED)
      time.sleep(1)

      # set three front center LEDs blue
      r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_CENTER, NamedColor.WHITE)
      time.sleep(1)

      # set the center LED to light blue
      r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_CENTER, RawColor(0, 0.8, 1))
      time.sleep(1)

      # turn off leftmost and rightmost front LEDs
      r.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, NamedColor.BLACK)
      time.sleep(1)

      # turn off left center and right center LEDs - do not use the predefined BLACK color this time
      r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, RawColor(0, 0, 0))
    
      # turn off the front center led
      r.set_led(LEDMask.FRONT_CENTER, NamedColor.BLACK)


.. code-block:: python
  :caption: Square walk  
  :linenos:

  from ozobot.evo import SyncEvoHandle

  def square_walk(r):
      for n in range(4):
          r.move(100, 120)
          r.rotate(90, 120)

  with SyncEvoHandle(name="OzoEvo-ABC*") as r:
      square_walk(r)


.. code-block:: python
  :caption: Tones and sounds
  :linenos:

  import time
  from ozobot.ari import SyncAriHandle
  from ozobot.linefollower import NamedColor, Direction

  with SyncAriHandle(name="Ari-ABCD") as r:
      # the robot can play preloaded sounds ..
      r.play_audio("happy")

      # .. colors ..
      r.say_color(NamedColor.RED)

      # .. directions ..
      r.say_direction(Direction.LEFT)

      # .. or numbers
      r.say_number(-111)

      # it can also play tones defined by note, its frequency or MIDI note number
      r.play_note("A", 4, 1, 100)
      time.sleep(0.5)
      r.play_tone(440, 1, 100)
      time.sleep(0.5)
      r.play_midi(69, 1, 100)


.. code-block:: python
  :caption: Multiple robots
  :linenos:
  
  from ozobot.ari import SyncAriHandle
  from ozobot.evo import SyncEvoHandle

  def square_walk(r):
      for n in range(4):
          r.move(100, 120)
          r.rotate(90, 120)

  with SyncAriHandle(name="Ari-ABCD") as ari1, SyncAriHandle(name="Ari-EFGH") as ari2, SyncEvoHandle(name="OzoEvo-XYZ*") as evo1:
      # now we have three robots connected
      # let them do a square walk one by one
      square_walk(ari1)
      square_walk(ari2)
      square_walk(evo1)
  
  
Sensor readouts
---------------
The robots have sensors, so let's read them.

Sensor data is accessible through a mechanism we call Virtual Memory (VM). The robot firmware reads and processes the raw data values and stores them in the VM. In Python,
its representation is available as :py:attr:`ozobot.evo.SyncEvo.data` and :py:attr:`ozobot.ari.SyncAri.data` for Evo and Ari respectively. Structures accessible through this property
represent individual sensors.

For the synchronous API, the data can be read by simply calling the `read` method on the relevant object, which looks into the VM and returns the current value.

.. code-block:: python
  :caption: Reading sensors
  :linenos:

  from ozobot.evo import SyncEvoHandle

  with SyncEvoHandle(name="OzoEvo-ABC*") as r:
      sample = r.data.obstacle_front_left.read()
      print(sample.value, sample.timestamp)


.. [#foot-threading] The library wraps our asyncio library under the hood, therefore the use of threading is not recommended. Take a look on the :ref:`async library <async_evo>` instead.
