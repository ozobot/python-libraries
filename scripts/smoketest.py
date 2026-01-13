import asyncio

from ozobot import actors
from ozobot.actors.linefollower import (
    align_with_line,
    data,
    emit_midi,
    emit_note,
    emit_tone,
    follow_line,
    move,
    play_audio,
    rotate,
    set_led,
)
from ozobot.actors.userio import user_io_alert, user_io_print, user_io_prompt
from ozobot.ari import AriHandle
from ozobot.blocklyutils import BrowserTerminal, set_wheel_speed  # type: ignore[import]
from ozobot.evo import EvoHandle
from ozobot.linefollower import Color, Colors, Direction, LEDMask

name = "Ari_1"
# name = "Evo_1"
handle = AriHandle(name=name) if name.startswith("Ari") else EvoHandle(name=name)

dispatcher = actors.ActorDispatcher()

actors.set_actor_dispatcher(dispatcher)


async def main():
    async with handle.connect() as r, BrowserTerminal() as term:
        dispatcher.add(name, r)
        dispatcher.add("BROWSER_TERMINAL", term)

        await motion()
        # await line()
        # await led()
        # await sound()
        # await io()
        # await sensors()


async def motion():
    await move(100, 50)
    await rotate(180, 90)
    await set_wheel_speed(50, 50)
    await asyncio.sleep(2)
    await set_wheel_speed(0, 0)


async def sound():
    await play_audio("happy")
    await emit_note("A", 4, 1, 1)
    await asyncio.sleep(0.5)
    await emit_tone(440, 1, 1)
    await asyncio.sleep(0.5)
    await emit_midi(69, 1, 1)


async def led():
    await set_led(LEDMask.TOP | LEDMask.FRONT_CENTER, Colors.RED)
    await set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, Colors.BLUE)


async def io():
    await user_io_print("Hello world!")
    await asyncio.sleep(1)

    await user_io_alert("Confirm this", cancellable=False)

    try:
        await user_io_alert("Cancel this", cancellable=True)
    except asyncio.CancelledError:
        pass
    else:
        raise Exception("Cancellation expected")

    selections = [
        (int, [1, 2, 3]),
        (float, [1.0, 2.0, 3.0]),
        (str, ("one", "two", "three")),
        (Color, (Colors.RED, Colors.BLUE, Colors.GREEN)),
        (Direction, (Direction.LEFT, Direction.RIGHT)),
    ]

    for t, v in selections:
        r = await user_io_prompt("Select", t, v, cancellable=False)
        print("Selected ", r, type(r))


async def _watch(n, src):
    async with src.watch() as it:
        async for data in it:
            print(f"watch {n}: {data.value}")


async def line():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(_watch("intersections", data.intersection))
        t2 = tg.create_task(_watch("codes", data.color_code))
        t3 = tg.create_task(_watch("line", data.line_color))

        await follow_line(Direction.STRAIGHT)
        await align_with_line(Direction.RIGHT)
        await align_with_line(Direction.LEFT)

        t1.cancel()
        t2.cancel()
        t3.cancel()


async def read_watch_sensors(sensors):
    for name in sensors:
        if hasattr(data, name):
            sensor = getattr(data, name)

            val = await sensor.read()
            print(f"read {name}: {val.value} @ {val.timestamp}")

            t = asyncio.create_task(_watch(name, sensor))
            await user_io_alert("Confirm to continue")
            t.cancel()
        else:
            print(f"Skipping {name} - not present")


async def read_write_sensors(sensors):
    for name in sensors:
        if hasattr(data, name):
            sensor = getattr(data, name)
            val = await sensor.read()
            print(f"read {name}: {val}")
            await sensor.write(val)
            print(f"written {name}: {val}")
        else:
            print(f"Skipping {name} - not present")


async def sensors():
    read_watch_sensorlist = [
        "surface_color",
        "obstacle_left_front",
        "obstacle_right_front",
        "obstacle_right_rear",
        "obstacle_left_rear",
        "time_of_flight",
    ]

    # read_watch_sensorlist += [
    #     "ir_message_left_front",
    #     "ir_message_right_front",
    #     "ir_message_left_rear",
    #     "ir_message_right_rear",
    # ]

    await read_watch_sensors(read_watch_sensorlist)
    await read_write_sensors(["line_following_speed"])


asyncio.run(main())
