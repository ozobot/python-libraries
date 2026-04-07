# ozobot-ari

Interface for controlling Ozobot Ari. See the [monorepo](https://github.com/ozobot/python-libraries) for more details. 

**Work in progress, only a web runtime driver for Ozobot Editor available**

## Usage
```python
import asyncio
import random
from ozobot.ari import AriHandle, Ari
from ozobot.linefollower import NamedColor, LEDMask, Direction


async def monitor(it):
    async for data in it:
        print(f"Sample taken: {data.value}")


async def main():
    async with AriHandle(id="ABCDE*") as ari:
        await ari.move(100, 50)
        await ari.rotate(180, 90)

        velo_task = asyncio.create_task(ari.set_velocity(50, 0))
        await asyncio.sleep(2)
        velo_task.cancel()

        await ari.set_led(LEDMask.FRONT_CENTER | LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, NamedColor.BLUE)
        await ari.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, NamedColor.RED)

        await ari.play_sound("happy")
        await ari.play_note("A", 4, 1)

        await ari.follow_line(Direction.STRAIGHT)
        intersection = await ari.data.intersection.read()
        print(f"At intersection: {intersection.value}")

        async with ari.data.intersection.watch() as intersections, ari.data.color_code.watch() as codes:
            t1 = asyncio.create_task(_monitor(intersections))
            t2 = asyncio.create_task(_monitor(codes))

            await ari.follow_line(random.choice(list(intersection.value)))

            t1.cancel()
            t2.cancel()


asyncio.run(main())
```


