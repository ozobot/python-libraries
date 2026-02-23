Migrate from the legacy API
===========================

Beta Editor API got deprecated and it's up to the users to migrate their code to the current API so that their programs work correctly. The new API was designed to be more consistent across supported devices and more clean. The following
document introduces several examples showing the same program written using the legacy and the current API both :ref:`sync <sync_evo>` or :ref:`async <async_evo>`. The programs in the legacy API are presented using both the documented `object oriented` and legacy Blockly runtime `Device Manager` paradigms. 

While the `Device Manager` based API is slightly different, both the legacy and current API follow similar principles. Therefore the migration should be pretty straightforward in most cases and should mostly consist of replacing individual function calls by their newer equivalents.
The API for opening connections and managing sensors differs significantly. We suggest the users to take a look on the following examples and observe the differences between the pair of APIs they use.

.. _example_simple_motion:

Example - Simple motion
-----------------------

Let's start with the simple program that makes the robot follow a line segment, rotate right and move forward.

.. tabs::

    .. code-tab:: python Legacy Async [old]

        import ozobot
        import asyncio

        evo1 = ozobot.get_robot("Evo_1", "Evo", coro=True)

        async def main():
            await evo1.navigation.anavigate(ozobot.Directions.FORWARD, follow = True)
            await evo1.movement.arotate(-1.5707963267948966, 1)
            await evo1.movement.amove(100 / 1000.0, 30 / 1000.0)

        asyncio.run(main())

    .. code-tab:: Python Device Manager [old]

        import ozobot
        import asyncio
        from _ozo import DeviceManager
        from _ozo import get_robot

        dm = DeviceManager()

        dm.add_device("Evo_1", get_robot("Evo_1", "Evo"))


        async def main():
            await dm.navigation.anavigate(ozobot.Directions.FORWARD, follow = True)
            await dm.movement.arotate(-1.5707963267948966, 1)
            await dm.movement.amove(100 / 1000.0, 30 / 1000.0)

        asyncio.run(main())

.. tabs::

    .. code-tab:: Python Sync [new]

        from ozobot.evo import SyncEvoHandle
        from ozobot.linefollower import Direction

        with SyncEvoHandle(name="Evo_1") as evo1:
            evo1.follow_line(Direction.STRAIGHT)
            evo1.rotate(-90, 45)
            evo1.move(100, 30)


    .. code-tab:: Python Async [new]

        import asyncio
        from ozobot.evo import EvoHandle
        from ozobot.linefollower import Direction

        async def main():
            async with EvoHandle(name="Evo_1") as evo1:
                await evo1.follow_line(Direction.STRAIGHT)
                await evo1.rotate(-90, 45)
                await evo1.move(100, 30)

        asyncio.run(main())


Example - Multiple devices 
--------------------------

When dealing with multiple devices, the migration path is similar to that of :ref:`example_simple_motion`. 

.. tabs::

    .. code-tab:: python Legacy Async [old]

        import ozobot
        import asyncio

        robot = ozobot.get_robot("Evo_1", "Evo", coro=True)
        robot = ozobot.get_robot("Evo_1", "Evo", coro=True)

        async def main():
            await evo1.movement.amove(100 / 1000.0, 30 / 1000.0)
            await ari1.movement.amove(100 / 1000.0, 30 / 1000.0)

        asyncio.run(main())

    .. code-tab:: python Device Manager [old]

        import ozobot
        import asyncio
        from _ozo import DeviceManager
        from _ozo import get_robot

        dm = DeviceManager()API 

        dm.add_device("Evo_1", get_robot("Evo_1", "Evo"))
        dm.add_device("Ari_1", get_robot("Ari_1", "Ari"))


        async def main():
            with dm.use_Device("Evo_1"):
                await dm.movement.amove(100 / 1000.0, 30 / 1000.0)
            with dm.use_Device("Ari_1"):
                await dm.movement.amove(100 / 1000.0, 30 / 1000.0)

        asyncio.run(main())

.. tabs::

    .. code-tab:: Python Sync [new]

        from ozobot.ari import SyncAriHandle
        from ozobot.evo import SyncEvoHandle
        from ozobot.linefollower import Direction

        with SyncAriHandle(name="Ari_1") as ari1, SyncEvoHandle(name="Evo_1") as evo1:
            evo1.move(100, 30)
            ari1.move(100, 30)


    .. code-tab:: Python Async [new]

        import asyncio
        from ozobot.ari import AriHandle
        from ozobot.evo import EvoHandle
        from ozobot.linefollower import Direction

        async def main():
            async with AriHandle(name="Ari_1") as ari1, EvoHandle(name="Evo_1") as evo1:
                await evo1.move(100, 30)
                await ari1.move(100, 30)

        asyncio.run(main())


Example - Sensors
-----------------

.. tabs::

    .. code-tab:: python Legacy Async [old]

        import ozobot
        import asyncio

        evo1 = ozobot.get_robot("Evo_1", "Evo", coro=True)

        async def main():
            await evo1.navigation.anavigate(ozobot.Directions.FORWARD, follow = True)
            intersection = await evo1.navigation.aget_last_intersection()
            print(intersection['intersection'])
            print(await evo1.sensors.aline_color())
            print(await evo1.sensors.asurface_color())
            print(await evo1.sensors.aproximity(ozobot.ProximitySensorLocation.LEFT_FRONT))
            print(await evo1.sensors.aproximity(ozobot.ProximitySensorLocation.RIGHT_FRONT))

        asyncio.run(main())

    .. code-tab:: Python Device Manager [old]

        import ozobot
        import asyncio
        from _ozo import DeviceManager
        from _ozo import get_robot

        dm = DeviceManager()

        dm.add_device("Evo_1", get_robot("Evo_1", "Evo"))


        async def main():
            await dm.navigation.anavigate(ozobot.Directions.FORWARD, follow = True)
            intersection = await dm.navigation.aget_last_intersection()
            print(intersection['intersection'])
            print(await dm.sensors.aline_color())
            print(await dm.sensors.asurface_color())
            print(await dm.sensors.aproximity(ozobot.ProximitySensorLocation.LEFT_FRONT))
            print(await dm.sensors.aproximity(ozobot.ProximitySensorLocation.RIGHT_FRONT))

        asyncio.run(main())

.. tabs::

    .. code-tab:: Python Sync [new]

        from ozobot.evo import SyncEvoHandle
        from ozobot.linefollower import Direction

        with SyncEvoHandle(name="Evo_1") as evo1:
            intersection, _ = evo1.follow_line(Direction.STRAIGHT)
            print(intersection)
            print(evo1.data.line_color.read())
            print(evo1.data.surface_color.read())
            # sync api does not currently support reading obstacle sensors


    .. code-tab:: Python Async [new]

        import asyncio
        from ozobot.evo import EvoHandle
        from ozobot.linefollower import Direction

        async def main():
            async with EvoHandle(name="Evo_1") as evo1:
                intersection = await evo1.follow_line(Direction.STRAIGHT)
                print(intersection)
                print(await evo1.data.line_color.read())
                print(await evo1.data.surface_color.read())
                print(await evo1.data.obstacle_left_front.read())
                print(await evo1.data.obstacle_right_front.read())

        asyncio.run(main())


Example - Lights and sounds
---------------------------

.. tabs::

    .. code-tab:: python Legacy Async [old]

        import ozobot
        import asyncio

        evo1 = ozobot.get_robot("Evo_1", "Evo", coro=True)

        async def main():
            await evo1.sounds.emotions.aplay_happy()
            await evo1.sounds.asay_color(ozobot.SurfaceColor.BLACK)
            await evo1.sounds.asay_number(0)
            await evo1.sounds.aplay_note(6, ozobot.Note.C, 0.5)
            await evo1.light_effects.aset_light_color(ozobot.SurfaceColor.BLUE, ozobot.Lights.FRONT_2 | ozobot.Lights.FRONT_4)
            await asyncio.sleep(1)
            await evo1.light_effects.aset_light_color_rgb(0.5, 0, 1, ozobot.Lights.FRONT_2 | ozobot.Lights.FRONT_4)

        asyncio.run(main())

    .. code-tab:: Python Device Manager [old]

        import ozobot
        import asyncio
        from _ozo import DeviceManager
        from _ozo import get_robot

        dm = DeviceManager()

        dm.add_device("Evo_1", get_robot("Evo_1", "Evo"))


        async def main():
            await dm.sounds.emotions.aplay_happy()
            await dm.sounds.asay_color(ozobot.SurfaceColor.BLACK)
            await dm.sounds.asay_number(0)
            await dm.sounds.aplay_note(6, ozobot.Note.C, 0.5)
            await dm.light_effects.aset_light_color(ozobot.SurfaceColor.BLUE, ozobot.Lights.FRONT_2 | ozobot.Lights.FRONT_4)
            await asyncio.sleep(1)
            await dm.light_effects.aset_light_color_rgb(0.5, 0, 1, ozobot.Lights.FRONT_2 | ozobot.Lights.FRONT_4)

        asyncio.run(main())

.. tabs::

    .. code-tab:: Python Sync [new]

        import time
        
        from ozobot.evo import SyncEvoHandle
        from ozobot.linefollower import ClassifiedColor, Color, Direction, LEDMask

        with SyncEvoHandle(name="Evo_1") as evo1:
            evo1.play_sound("happy")
            evo1.say_color(ClassifiedColor.BLACK)
            evo1.say_number(0)
            evo1.play_note("C", 6, 0.5, 100)
            evo1.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, ClassifiedColor.BLUE)
            time.sleep(1)
            evo1.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, Color(0.5, 0, 1))


    .. code-tab:: Python Async [new]

        import asyncio
        from ozobot.evo import EvoHandle
        from ozobot.linefollower import Direction

        async def main():
            async with EvoHandle(name="Evo_1") as evo1:
                await evo1.play_sound("happy")
                await evo1.say_color(ClassifiedColor.BLACK)
                await evo1.say_number(0)
                await evo1.play_note("C", 6, 0.5, 100)
                await evo1.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, ClassifiedColor.BLUE)
                await asyncio.sleep(1)
                await evo1.set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, Color(0.5, 0, 1))


        asyncio.run(main())
