.. _async_actor:

Actor API
=========

This document describes the so-called Actor API - a Python library used to control multiple devices in Blockly-generated Python code.

To run a Blockly program, Ozobot Editor uses Python runtime. However, because Blockly program structure is not really on par with that of Python, we created an adaptation layer that allows us to generate simpler Python code.

.. note::
	The code generated from Blockly blocks is not idiomatic Python code. We do not recommend using it to learn Python, but it can serve as a starting point or inspiration.

The API needs to register all devices (called actors) to a common dispatcher. All the actor functions like movement or user IO are globally available and can be called without any direct reference to the actor itself. When the function is called, the dispatcher
selects the actor that offers the requested functionality. If multiple robots offer the functionality, the robots are looked up in the dispatcher stack. The user can `select` or `mask` actors to move them up or down in the lookup stack. 

Usage
-----

The API consists of a dispatcher class and specific actors' implementation. In short, the user needs to instantiate and register the dispatcher by calling :py:func:`~ozobot.actors.new_actor_dispatcher` and
add the actors by :py:meth:`~ozobot.actors.ActorDispatcher.add` or :py:meth:`~ozobot.actors.ActorDispatcher.connect`. The actors can then be selected or masked by calling :py:meth:`~ozobot.actors.ActorDispatcher.actor` or :py:meth:`~ozobot.actors.ActorDispatcher.mask` respectivelly.  

To call a function on the robot, a global function needs to be imported from a robot-specific module - for example `ozobot.actors.linefollower.move` provides `move` functionality for Evo and Ari.


.. autoclass:: ozobot.actors.ActorDispatcher
	:members: add, actor, connect, mask
	:undoc-members:

.. autofunction:: ozobot.actors.new_actor_dispatcher


Example
-------
The following example shows how to control two Evo robots. Notice the use of `actor` context manager and the invocation of the global `move` function.

.. code-block:: python
  :caption: Move two robots - Actor API
  :linenos:

  import asyncio
  from ozobot.actors.linefollower import move
  from ozobot.evo import EvoHandle
  from ozobot import actors

  dispatcher = actors.new_actor_dispatcher()

  async def main():
      async with (
          dispatcher.connect("FirstEvo", EvoHandle(name="Evo_1")) as evo_1,
          dispatcher.connect("SecondEvo", EvoHandle(name="Evo_2")) as evo_2,
      ):
          with dispatcher.actor("SecondEvo"):
              await move(100, 30)  # Move SecondEvo
              with dispatcher.actor("FirstEvo"):
                  await move(100, 30)  # MoveFirstEvo

              await move(100, 30)  # Move SecondEvo

  asyncio.run(main())


The example code can be easily rewritten to a proper object oriented programming (OOP) code:

.. code-block:: python
  :caption: Move two robots - OOP
  :linenos:

  import asyncio
  from ozobot.evo import EvoHandle

  async def main():
      async with (
          EvoHandle(name="Evo_1")) as evo_1,
          EvoHandle(name="Evo_2")) as evo_2,
      ):
          await evo_2.move(100, 30)
          await evo_1.move(100, 30)
          await evo_2.move(100, 30)

  asyncio.run(main())
