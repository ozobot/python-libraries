import asyncio

from ozobot import actors
from ozobot.actors.linefollower import (
    data,
    face_line_direction,
    follow_line,
    move,
    play_audio,
    play_midi,
    play_note,
    play_tone,
    rotate,
    set_led,
)
from ozobot.actors.userio import user_io_alert, user_io_print, user_io_prompt
from ozobot.ari import AriHandle
from ozobot.evo import EvoHandle
from ozobot.libblockly.actors import BrowserTerminal  # type: ignore[import]
from ozobot.libblockly.motion import set_wheel_speed  # type: ignore[import]
from ozobot.linefollower import Color, Direction, LEDMask, NamedColor

name = "Ari_1"
# name = "Evo_1"
handle = AriHandle(name=name) if name.startswith("Ari") else EvoHandle(name=name)

dispatcher = actors.new_actor_dispatcher()


async def main():
    async with handle as r, BrowserTerminal() as term:
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
    await play_note("A", 4, 1)
    await asyncio.sleep(0.5)
    await play_tone(440, 1)
    await asyncio.sleep(0.5)
    await play_midi(69, 1)


async def led():
    await set_led(LEDMask.TOP | LEDMask.FRONT_CENTER, NamedColor.RED)
    await set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, NamedColor.BLUE)


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
        (Color, (NamedColor.RED, NamedColor.BLUE, NamedColor.GREEN)),
        (Direction, (Direction.LEFT, Direction.RIGHT)),
    ]

    for t, v in selections:
        r = await user_io_prompt("Select", t, v, cancellable=False)
        print("Selected ", r, type(r))


async def _watch(n, src):
    async with src.watch() as cont:
        async for data in aiter(cont):
            print(f"watch {n}: {data.value}")


async def line():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(_watch("codes", data.color_code))
        t2 = tg.create_task(_watch("line", data.line_color))

        intersection = await follow_line(Direction.STRAIGHT)
        print(intersection)
        await face_line_direction(Direction.RIGHT)
        await face_line_direction(Direction.LEFT)

        t1.cancel()
        t2.cancel()


async def read_watch_sensors(sensors):
    for name in sensors:
        if hasattr(data, name):
            sensor = getattr(data, name)

            if hasattr(sensor, "read"):
                val = await sensor.read()
                print(f"read {name}: {val.value} @ {val.timestamp}")
            else:
                print(f"read {name} not available")

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
