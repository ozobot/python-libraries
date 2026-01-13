Async API - advanced
====================

To fully utilize what the robot has to offer, we recommend the async API. It runs on asyncio [#foot-asyncio]_, so some elementary knowledge of that framework is necessary as it provides
an elegant way for cancelling the current command or watching sensoric data for change. There is a class implemented for each individual robot type having the same interface, so individual robots can be
interchanged easily. This does hold for functionality the robot supports. For example, Evo does not have a display, there is no display related functionality implemented.

.. _connecting:

Opening the connection
----------------------

Connection to the robot can be open with :py:class:`ozobot.ari.AriHandle` or :py:class:`ozobot.evo.EvoHandle` for Ari or Evo respectivelly. These
two classes accept connection selection filters on initialization and then provide a robot instance through an asynchronnous context manager
provided by their `connect` methods, for example:

.. code-block:: python
  :linenos:

  import asyncio
  from ozobot.ari import AriHandle

  async def main():
    async with AriHandle(id="ABC*").connect() as ari1, AriHandle(name="Ari-CDEF").connect() as ari2:
      # you can use ari1 and ari2 here


  asyncio.run(main())

The specific filters depend on the robot, see the API documentation to learn more: :py:class:`ozobot.ari.AriHandle` or :py:class:`ozobot.evo.EvoHandle`.

Controlling the robot
---------------------

The robot can be controlled by awaiting blocking coroutines that block until the given action is finished or :ref:`cancelled <cancelling>`. All actions need to be executed within the :ref:`connection context
manager <connecting>`.

A list of the supported actions with details can be found in the :ref:`API doc <datatypes>`, but to quickly begin programming, lets go through a few examples:

.. code-block:: python
  :caption: Set lights
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle
  from ozobot.linefollower import Colors, LEDMask, RawColor

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      # set all front LEDs red
      await r.set_led(LEDMask.ALL_FRONT, Colors.RED)
      await asyncio.sleep(1)

      # set three front center LEDs blue
      await r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_CENTER, Colors.WHITE)
      await asyncio.sleep(1)

      # set the center LED to light blue
      await r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_CENTER, RawColor(0, 0.8, 1))
      await asyncio.sleep(1)

      # turn off leftmost and rightmost front LEDs
      await r.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, Colors.BLACK)
      await asyncio.sleep(1)

      # turn off left center and right center LEDs - do not use the predefined BLACK color this time
      await r.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, RawColor(0, 0, 0))
      
      #turn off the front center led
      await r.set(LEDMask.FRONT_CENTER, Colors.BLACK)

  asyncio.run(main())


.. code-block:: python
  :caption: Square walk  
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      for n in range(4):
        await r.move(100, 120)
        await r.rotate(90, 120)


  asyncio.run(main())


.. code-block:: python
  :caption: Tones and sounds
  :linenos:

  import asyncio
  from ozobot.ari import AriHandle
  from ozobot.linefollower import Colors, Direction


  async def main():
    async with AriHandle(name="Ari-ABCD").connect() as r:
      # the robot can play preloaded sounds ..
      await r.play_audio("happy")

      # .. colors ..
      await r.say_color(Colors.RED)

      # .. directions ..
      await r.say_direection(Direction.LEFT)

      # .. or numbers
      await r.say_number(-111)

      # it can also play tones defined by note, its frequency or midi sound number
      await emit_note("A", 4, 1, 1)
      await asyncio.sleep(0.5)
      await emit_tone(440, 1, 1)
      await asyncio.sleep(0.5)
      await emit_midi(69, 1, 1)



.. code-block:: python
  :caption: Multiple robots and concurrency
  :linenos:
  
  import asyncio
  from ozobot.ari import AriHandle
  from ozobot.evo import EvoHandle
  from ozobot.linefollower import Colors, Direction


  async def main():
    async with AriHandle(name="Ari-ABCD").connect() as ari1, AriHandle(name="Ari-EFGH").connect() as ari2, EvoHandle(name="OzoEvo-XYZ*") as evo1:
      # now we have three robots connected
      # let them do a square walk one by one
      await square_walk(ari1)
      await square_walk(ari2)
      await square_walk(evo1)

      # and this time concurrently while leveraging asyncio functionality
      await asyncio.gather(
        square_walk(ari1),
        square_walk(ari2),
        square_walk(evo1),
      )

      # and display that we are finished on the screen
      #   of course, we can only do that on ari, because evo does not have a screen
      await asyncio.gather(
        ari1.user_io_alert("Success!")
        ari2.user_io_alert("Success!")
        # evo1.user_io_alert("Success!")  # this would fail
      )

  async def square_walk(r):
    for n in range(4):
      await r.move(100, 120)
      await r.rotate(90, 120)
  
  
.. _cancelling:

Cancelling the actions
~~~~~~~~~~~~~~~~~~~~~~

Any action can be cancelled, in most cases by `task cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_ or `timeouts <https://docs.python.org/3/library/asyncio-task.html#timeouts>`_.

.. code-block:: python
  :caption: Timeouts - square walking for defined time
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      try:
        async with asyncio.timeout(10):  # let it walk for 10 seconds
          while True:
            await square_walk(r)
      except asyncio.CancelledError:
        print("square walk cancelled")
      
  async def square_walk(r):
    for n in range(4):
      await r.move(100, 120)
      await r.rotate(90, 120)

  asyncio.run(main())


.. code-block:: python
  :caption: Task cancellation - flashing LEDs during square walk
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle
  from ozobot.linefollower import Colors, LEDMask

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      t = asyncio.create_task(flashing(r))
      await square_walk(r)
      t.cancel()

  async def flashing(r):
    try:
      while True:
          await r.set_led(LEDMask.ALL_FRONT, Colors.BLUE)
          await asyncio.sleep(1)
          await r.set_led(LEDMask.ALL_FRONT, Colors.BLACK)
          await asyncio.sleep(1)
    except asyncio.CancelledError:
      print("flashing cancelled")

  async def square_walk(r):
    for n in range(4):
      await r.move(100, 120)
      await r.rotate(90, 120)

  asyncio.run(main())


.. _sensors:

Sensor readouts
---------------
The robots have sensors, so let's read it.

Sensoric data are accessible through a mechanism we call Virtual Memory (VM). Robot firmware reads and processes the raw data and stores it to the VM for reading. Its
representation is available as :py:attr:`ozobot.evo.Evo.data` and :py:attr:`ozobot.ari.Ari.data` for Evo and Ari respectivelly. Structures accessible through this property
represent individual sensors.

There are two ways of getting the sensoric data from the VM, some sensors only support one of those. The first method is reading which works by simply calling `read` method on the
relevant object which looks into the VM and returns the current value.

.. code-block:: python
  :caption: Reading sensors
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      sample = await r.data.obstacle_front_left.read()
      print(sample.value, sample.timestamp)

  asyncio.run(main())


This way is simple and less verbose, but does not guarantee you'll get all the data - what if the data changes several times between two consecutive reads? This is where
watching comes in. Most of the sensors have a `watch` method providing an asynchronnous context manager attached. The context manager provides an asynchronnous iterator over
all the sampled sensoric data. The sampling is stopped when the context manager closes, but the sampled data are available until the iterator goes out of scope.

.. code-block:: python
  :caption: Watching sensors
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle

  async def main():
    async with EvoHandle(name="OzoEvo-ABC*").connect() as r:
      await move_until_obstacle(r)      

  async def move_until_obstacle(r):
    move_task = asyncio.create_task(r.set_velocity(50, 0))
    
    async with r.data.obstacle_front_left.watch() as it:
      async for data in it:
        if data.value > 100:
          move_task.cancel()
          return

  asyncio.run(main())
  




.. [#foot-asyncio] asyncio documentation `<https://docs.python.org/3/library/asyncio-task.html>`_
