# ozobot-evo

Interface for controlling Ozobot Evo. See the [monorepo](https://github.com/ozobot/python-libraries) for more details. 

**Work in progress, only a web runtime driver for Ozobot Editor available**

## Usage
```python
import asyncio
import random
from ozobot.evo import EvoHandle, Evo
from ozobot.linefollower import NamedColor, LEDMask, Direction


async def monitor(it):
    async for data in it:
        print(f"Sample taken: {data.value}")


async def main():
    async with EvoHandle(id="ABCDE*") as evo:
        await evo.move(100, 50)
        await evo.rotate(180, 90)

        velo_task = asyncio.create_task(evo.set_velocity(50, 0))
        await asyncio.sleep(2)
        velo_task.cancel()

        await evo.set_led(LEDMask.FRONT_CENTER | LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, NamedColor.BLUE)
        await evo.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, NamedColor.RED)

        await evo.play_sound("happy")
        await evo.play_tone("A", 4, 1, 1)

        await evo.follow_line(Direction.STRAIGHT)
        intersection = await evo.data.intersection.read()
        print(f"At intersection: {intersection.value}")

        async with evo.data.intersection.watch() as intersections, evo.data.color_code.watch() as codes:
            t1 = asyncio.create_task(_monitor(intersections))
            t2 = asyncio.create_task(_monitor(codes))

            await evo.follow_line(random.choice(list(intersection.value)))

            t1.cancel()
            t2.cancel()


asyncio.run(main())
```

