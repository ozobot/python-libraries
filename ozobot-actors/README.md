# ozobot-actors

Library that enables to control multiple Ozobot device using a globally defined functions. It mirrors the interface
of libraries implementing object oriented control of the individual robots. The library is primarily intended to be used by the Python code
generated from Blockly programs, as its semantics follows the actor based use by the [Ozobot Editor](https://editor.ozobot.com),
but can be used even in projects written from scratch.

## Installation
The library requires you to list all the robots to be supported, so for example to install Evo support, run
`pip install ozobot-actors[evo]`, to install both Ari and Evo support, run `pip install ozobot-actors[ari,evo]`.

The library currently supports:
 - [`ozobot-ari`](/ozobot-ari)
 - [`ozobot-evo`](/ozobot-evo)


## Usage
The library defines global functions that can control any robot supporting that specific functionality. Targeting a specific robot
can be done by using a context manager. When an API function is called, the context is searched for available robot and the function is
executed with the first matching robot. The robot selection follows a few simple rules:

 - Actors need to be registered in the dispatcher
 - Actors are put onto the stack as they are registered
 - Selecting an actor puts it on top of the current stack
 - Masking an actor removes it from the current stack
 - Stack is searched from the top
 - First robot having the required functionality is used, leaving the stack untouched


```python
import asyncio

from ozobot import actors
from ozobot.actors.linefollower import move
from ozobot.actors.userio import user_io_alert
from ozobot.ari import AriHandle
from ozobot.evo import EvoHandle

dispatcher = actors.ActorDispatcher()
actors.set_actor_dispatcher(dispatcher)

async def main() -> None:
  async with EvoHandle(name="OzoEvo-1234abcd").connect() as e1, EvoHandle(name="Ari-ABCD").connect() as a1:
    dispatcher.add("Evo_1", e1)
    dispatcher.add("Ari_1", a1)

    with dispatcher.actor("Ari_1"):  # this puts Ari onto the default stack
      await move(100, 50)  # moves Ari
      await user_io_alert("Hello from Ari!")  # displays message on Ari

      with dispatcher.actor("Evo_1"):  # this puts Evo on top of Ari
        await move(100, 50)  # moves Evo
        await user_io_alert("Hello again from Ari!")  # Ari shows the message, because Evo does not support `user_io_alert`
      # stepping out of the context manager block removes Evo from the top of the stack
      
      await move(-100, 50)  # moves Ari again


if __name__ == "__main__":
  asyncio.run(main())
```
