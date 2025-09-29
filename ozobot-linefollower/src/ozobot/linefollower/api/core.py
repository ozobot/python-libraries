from __future__ import annotations

import typing

from loguru import logger
from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    Color,
    Colors,
    Direction,
    LEDMask,
    RawColor,
    RobotGeometry,
    TNote,
)
from ozobot.linefollower.driver.interface import Driver, VirtualMemoryRegions
from ozobot.linefollower.exceptions import InvalidClassifiedColorError


class LineFollower:
    @property
    def geometry(self) -> RobotGeometry:
        return RobotGeometry(
            ticks_per_meter=0,
            wheel_track=0,
            wheel_diameter=0,
            encoder_ticks_per_wheel_revolution=0,
            max_speed_limit=0,
        )

    @property
    def memory(self) -> VirtualMemoryRegions:
        return self._driver.memory

    def __init__(
        self,
        driver: Driver,
    ) -> None:
        self._driver = driver

    async def move(self, distance_mm: float, speed_mmps: float) -> None:
        logger.debug("Moving", distance=distance_mm, speed=speed_mmps)
        await self._driver.move(
            distance_mm,
            speed_mmps,
        )

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        logger.debug("Rotating", angle=angle_deg, anglle_speed=angular_speed_degps)
        await self._driver.rotate(
            angle_deg,
            angular_speed_degps,
        )

    async def set_velocity(self, linear_mmps: float, angular_degps: float, duration_s: float) -> None:
        logger.debug("Setting velocity", linear=linear_mmps, angular=angular_degps, duration=duration_s)
        await self._driver.velocity(
            linear_mmps,
            angular_degps,
            int(duration_s * 1000),
        )

    async def emit_tone(self, frequency_hz: int, duration_s: float, volume: int) -> None:
        logger.debug("Emitting tone", frequency=frequency_hz, duration=duration_s, volume=volume)
        await self._driver.play_tone(
            frequency_hz,
            int(duration_s * 1000),
            volume,
        )

    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume: int) -> None:
        notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
        note_idx = notes.index(note.upper())

        if note_idx < 0:
            raise ValueError(f"Invalid note: {note_idx}")

        frequency_hz = self._convert_note_to_frequency(octave, note_idx)
        await self.emit_tone(
            frequency_hz,
            duration_s,
            volume,
        )

    async def emit_midi(self, midi_number: int, duration_s: float, volume: int):
        frequency_hz = LineFollower._convert_key_to_frequency(midi_number, reference=69)
        await self.emit_tone(
            frequency_hz,
            duration_s,
            volume,
        )

    # credit goes to https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
    @staticmethod
    def _convert_note_to_frequency(octave: int, note_idx) -> int:
        key = note_idx + ((octave - 1) * 12) + 1
        if note_idx < 3:
            key += 12

        return LineFollower._convert_key_to_frequency(key, reference=49)

    @staticmethod
    def _convert_key_to_frequency(midi_number: int, *, reference: int) -> int:
        a4 = 440
        frequency = a4 * 2 ** ((midi_number - reference) / 12)
        return int(frequency)

    async def play_audio(self, name: str) -> None:
        logger.debug("Playing audio file", name=name)
        await self._driver.play_audio(name)

    async def say_number(self, number: int | float) -> None:
        numint = int(number)
        if not (-199 < numint < 199):
            raise ValueError(f"`say_number` only supports range -199 to 199, got {numint}")

        sounds: list[str] = []
        if numint < 0:
            sounds.append("minus")

        sounds.append(f"num{abs(numint)}")

        for sound in sounds:
            await self._driver.play_audio(sound)

    async def say_color(self, color: ClassifiedColor) -> None:
        match color:
            case Colors.BLACK:
                return await self.play_audio("black")
            case Colors.RED:
                return await self.play_audio("red")
            case Colors.GREEN:
                return await self.play_audio("green")
            case Colors.BLUE:
                return await self.play_audio("blue")
            case Colors.WHITE:
                return await self.play_audio("white")
            case _:
                raise InvalidClassifiedColorError(color)

    async def say_direction(self, direction: Direction) -> None:
        match direction:
            case Direction.LEFT:
                return await self.play_audio("left")
            case Direction.RIGHT:
                return await self.play_audio("right")
            case Direction.STRAIGHT:
                return await self.play_audio("forward")
            case Direction.BACKWARD:
                return await self.play_audio("backward")
            case _:
                typing.reveal_type(direction)

    async def set_led(self, mask: LEDMask, color: Color) -> None:
        logger.debug("Setting LED", mask=mask, color=color)
        if isinstance(color, RawColor):
            raw_color = color
        elif isinstance(color, ClassifiedColor):
            raw_color = color.to_raw_color()

        red = int(raw_color.red * 255)
        green = int(raw_color.green * 255)
        blue = int(raw_color.blue * 255)

        await self._driver.set_led(mask, red, green, blue)

    async def follow_line(self, direction: Direction) -> None:
        logger.debug("Following line", direction=direction)
        await self._driver.line_navigation(direction, follow=True)

    async def align_with_line(self, direction: Direction) -> None:
        logger.debug("Aligning with line", direTction=direction)
        await self._driver.line_navigation(direction, follow=False)
