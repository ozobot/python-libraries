from __future__ import annotations

import asyncio
import math

from ozobot.actors.linefollower import move, rotate, set_led, set_velocity
from ozobot.linefollower.datatypes import LEDMask, NamedColor, RawColor


async def library_generate_circle(radius: float, speed: float, side: float, delay: float) -> None:
    diff = round(speed / radius) * side
    await set_velocity(speed, math.degrees(diff / 10), delay )

async def library_move_zigzag(speed: float) -> None:
    angular_speed = speed * 2850
    linear_speed = speed * 1000
    await rotate(-45, angular_speed)
    await move(10, linear_speed)
    for _ in range(2):
        await rotate(90, angular_speed)
        await move(20, linear_speed)
        await rotate(-90, angular_speed)
        await move(20, linear_speed)
    await rotate(90, angular_speed)
    await move(10, linear_speed)
    await rotate(-45, angular_speed)

async def library_move_wave(speed: float) -> None:
    angle_speed = abs(50 * speed)
    try:
        task = asyncio.create_task(rotate(math.degrees(1), math.degrees(angle_speed)))
        await asyncio.sleep(1 / angle_speed - 0.05)
        task = asyncio.create_task(set_velocity(speed * 1000, -math.degrees(angle_speed), 2 / angle_speed))
        await asyncio.sleep(2 / angle_speed - 0.05)
        task = asyncio.create_task(set_velocity(speed * 1000, math.degrees(angle_speed), 2 / angle_speed))
        await asyncio.sleep(2 / angle_speed - 0.05)
        await rotate(-math.degrees(1), math.degrees(angle_speed))
    finally:
        task.cancel()

async def library_animation_police_lights() -> None:
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    for _ in range(3):
        for _ in range(6):
            await set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_LEFT_CENTER, RawColor(100/127, 0, 0))
            await asyncio.sleep(0.05)
            await set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_LEFT_CENTER, NamedColor.BLACK)
            await asyncio.sleep(0.02)
        for _ in range(6):
            await set_led(LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_RIGHT, RawColor(0, 0, 100/127))
            await asyncio.sleep(0.05)
            await set_led(LEDMask.FRONT_RIGHT_CENTER | LEDMask.FRONT_RIGHT, NamedColor.BLACK)
            await asyncio.sleep(0.02)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)

async def library_animation_rainbow() -> None:
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    def _clamp(val: float) -> float:
        return max(0, min(val, 1))
    local_gradient = 0.0
    while local_gradient < 1:
        await set_led(LEDMask.ALL_FRONT | LEDMask.TOP, RawColor(_clamp(1 - local_gradient), _clamp(local_gradient), 0))
        local_gradient = local_gradient + 1 / 127
        await asyncio.sleep(0.01)
    while local_gradient > 0:
        await set_led(LEDMask.ALL_FRONT | LEDMask.TOP, RawColor(0, _clamp(local_gradient), _clamp(1 - local_gradient)))
        local_gradient = local_gradient - 1 / 127
        await asyncio.sleep(0.01)
    while local_gradient < 1:
        await set_led(LEDMask.ALL_FRONT | LEDMask.TOP, RawColor(_clamp(local_gradient), 0, _clamp(1 - local_gradient)))
        local_gradient = local_gradient + 1 / 127
        await asyncio.sleep(0.01)
    await set_led(LEDMask.ALL_FRONT | LEDMask.TOP, NamedColor.BLACK)

async def library_animation_traffic_lights() -> None:
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, RawColor(0, 1, 0))
    await asyncio.sleep(4)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, RawColor(1, 0.5, 0))
    await asyncio.sleep(1)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.FRONT_CENTER | LEDMask.TOP, RawColor(1, 0, 0))
    await asyncio.sleep(4)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.FRONT_LEFT_CENTER | LEDMask.FRONT_RIGHT_CENTER, RawColor(1, 0.5, 0))
    await asyncio.sleep(1)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)

async def library_set_front_lights(
    color_1: list[float],
    color_2: list[float],
    color_3: list[float],
    color_4: list[float],
    color_5: list[float],
) -> None:
    await set_led(LEDMask.FRONT_LEFT, RawColor(color_1[0], color_1[1], color_1[2]))
    await set_led(LEDMask.FRONT_LEFT_CENTER, RawColor(color_2[0], color_2[1], color_2[2]))
    await set_led(LEDMask.FRONT_CENTER, RawColor(color_3[0], color_3[1], color_3[2]))
    await set_led(LEDMask.FRONT_RIGHT_CENTER, RawColor(color_4[0], color_4[1], color_4[2]))
    await set_led(LEDMask.FRONT_RIGHT, RawColor(color_5[0], color_5[1], color_5[2]))

async def library_animation_disco() -> None:
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.TOP, RawColor(1, 0, 0))
    await library_set_front_lights([1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0.5, 0], [0, 1, 1])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(0, 1, 0))
    await library_set_front_lights([0, 0, 1], [1, 0.5, 0], [0, 1, 1], [1, 0, 0], [1, 1, 0])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(0, 0, 1))
    await library_set_front_lights([0, 1, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1], [0, 1, 0])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(1, 0.5, 0))
    await library_set_front_lights([1, 1, 0], [1, 1, 1], [0, 1, 0], [1, 0, 0], [0.5, 0, 1])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(0, 1, 1))
    await library_set_front_lights([0, 1, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1], [1, 0.5, 0])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(1, 0, 0))
    await library_set_front_lights([0, 1, 0], [0, 0, 1], [1, 0.5, 0], [0, 1, 1], [1, 0, 0])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(1, 1, 0))
    await library_set_front_lights([1, 0.5, 0], [0, 1, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(1, 1, 1))
    await library_set_front_lights([1, 0, 0], [1, 1, 0], [1, 1, 1], [0, 1, 0], [100/127, 5/127, 29/127])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.TOP, RawColor(0, 1, 1))
    await library_set_front_lights([1, 1, 1], [0, 1, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1])
    await asyncio.sleep(0.1)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)

async def library_animation_christmas_tree() -> None:
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
    await set_led(LEDMask.TOP, RawColor(0, 1, 1))
    await library_set_front_lights([0, 1, 0], [1, 0, 0], [1, 0.5, 0], [0, 0, 1], [1, 1, 0])
    await asyncio.sleep(1)
    await set_led(LEDMask.TOP, RawColor(1, 1, 0))
    await library_set_front_lights([0, 1, 1], [0, 1, 0], [1, 0, 0], [1, 0.5, 0], [0, 0, 1])
    await asyncio.sleep(1)
    await set_led(LEDMask.TOP, RawColor(0, 0, 1))
    await library_set_front_lights([1, 1, 0], [0, 1, 1], [0, 1, 0], [1, 0, 0], [1, 0.5, 0])
    await asyncio.sleep(1)
    await set_led(LEDMask.TOP, RawColor(1, 0.5, 0))
    await library_set_front_lights([0, 0, 1], [1, 1, 0], [0, 1, 1], [0, 1, 0], [1, 0, 0])
    await asyncio.sleep(1)
    await set_led(LEDMask.TOP, RawColor(1, 0, 0))
    await library_set_front_lights([1, 0.5, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [0, 1, 0])
    await asyncio.sleep(1)
    await set_led(LEDMask.TOP, RawColor(0, 1, 0))
    await library_set_front_lights([1, 0, 0], [1, 0.5, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1])
    await asyncio.sleep(1)
    await set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)

async def library_animation_firework() -> None:
    all_lights = LEDMask.ALL_FRONT | LEDMask.TOP
    await set_led(all_lights, NamedColor.BLACK)
    local_timer = 0
    white_treshold = 7
    while local_timer < 127:
        color_value = (127 - local_timer) / 127
        white_value = (127 - local_timer * 8) / 127
        if local_timer < white_treshold:
            await set_led(all_lights, RawColor(white_value, white_value, white_value))
        else:
            await set_led(all_lights, RawColor(color_value, 0, 0))
        await asyncio.sleep(0.01)
        local_timer = local_timer + 1
    local_timer = 0
    while local_timer < 127:
        color_value = (127 - local_timer) / 127
        white_value = (127 - local_timer * 8) / 127
        if local_timer < white_treshold:
            await set_led(all_lights, RawColor(white_value, white_value, white_value))
        else:
            await set_led(all_lights, RawColor(0, color_value, 0))
        await asyncio.sleep(0.01)
        local_timer = local_timer + 1
    local_timer = 0
    while local_timer < 127:
        color_value = (127 - local_timer) / 127
        white_value = (127 - local_timer * 8) / 127
        if local_timer < white_treshold:
            await set_led(all_lights, RawColor(white_value, white_value, white_value))
        else:
            await set_led(all_lights, RawColor(0, 0, color_value))
        await asyncio.sleep(0.01)
        local_timer = local_timer + 1
    await asyncio.sleep(0.5)
    for _ in range(3):
        color_value = 0
        for _ in range(3):
            local_timer = 127
            while local_timer > 0:
                if local_timer > 127 - white_treshold:
                    await set_led(all_lights, RawColor(local_timer / 127, local_timer /127, local_timer / 127))
                else:
                    await set_led(all_lights, RawColor(local_timer / 127, local_timer / 127 if color_value == 1 else 0, local_timer / 127 if color_value == 0 else 0))
                await asyncio.sleep(0.01)
                local_timer = local_timer - 2
            local_timer = 0
            color_value = color_value + 1
    await set_led(all_lights, NamedColor.BLACK)
