from __future__ import annotations

import typing

from loguru import logger
from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    Color,
    Direction,
    LEDMask,
    RawColor,
    TAudio,
    TNote,
)
from ozobot.linefollower.driver.interface import Driver, VirtualMemoryRegions
from ozobot.linefollower.driver.shared import map_audio_name_to_filename
from ozobot.linefollower.exceptions import (
    AudioFileNotFoundError,
    InvalidClassifiedColorError,
    InvalidDirectionError,
    LinefollowerFileNotFoundError,
)


class LineFollower:
    @property
    def data(self) -> VirtualMemoryRegions:
        """
        Robot sensors.

        Contains virtual memory and sensor structures allowing a subset of read, write and watch methods.
        """

        return self._driver.memory

    def __init__(
        self,
        driver: Driver,
    ) -> None:
        self._driver = driver

    async def move(self, distance_mm: float, speed_mmps: float) -> None:
        """
        Move the robot straight.

        Move the robot forward by the given distance at the given speed for or positive distance, or backwards for negative distance.

        :param distance_mm: Distance to move in millimeters. If negative, the robot moves backwards.
        :param speed_mmps: Movement speed at millimeters per second. The sign is ignored.
        :See also: :py:meth:`rotate`, :py:meth:`set_velocity`

        .. code-block:: python

            # move robot 200mm forward and backward
            await robot.move(200, 50)
            await robot.move(-200, 50)
        """

        logger.debug("Moving", distance=distance_mm, speed=speed_mmps)
        await self._driver.move(
            distance_mm,
            abs(speed_mmps),
        )

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        """
        Rotate the robot.

        Rotate the robot counter clockwise when the angle is positive, or clockwise when the angle is negative.

        :param angle_deg: Angle to rotate counter clockwise in degrees. If negative, the robot rotates clockwise.
        :param speed_mmps: Rotation speed in degrees per second. The sign is ignored.
        :See also: :py:meth:`move`, :py:meth:`set_velocity`

        .. code-block:: python

            # move robot 90deg counter clockwise and clockwise
            await robot.rotate(90, 45)
            await robot.rotate(-90, 45)

        """

        logger.debug("Rotating", angle=angle_deg, anglle_speed=angular_speed_degps)
        await self._driver.rotate(
            angle_deg,
            abs(angular_speed_degps),
        )

    async def set_velocity(self, linear_mmps: float, angular_degps: float, duration_s: float) -> None:
        """
        Move with duration.

        Provided linear and angular velocity components, the robot moves at given velocity with a given duration. Robot stops after the duration passes.

        :param linear_mmps: Linear velocity component in millimeters per second
        :param angular_degps: Angular velocity component in degrees per second
        :param duration: Movement duration in seconds, -1 for infinity.
        :See also: :py:meth:`move`, :py:meth:`rotate`

        .. note::
            Although bad practice, the `duration_s` parameter is here for ergonomic reasons. If you want to follow asyncio idioms, you can use such as :ref:`timeouts <https://docs.python.org/3/library/asyncio-task.html#timeouts>`_ or
            :ref:`tasks <https://docs.python.org/3/library/asyncio-task.html#creating-tasks>`_, you can use `duration_s=-1` for an infinite duration.


        .. code-block:: python

            # move for 2.5 seconds the ergonomic way
            await robot.set_velocity(100, 0, 2.5)

            # or the asyncio idiomatic way
            async with asyncio.timeout(2.5):
                await robot.set_velocity(100, 0, -1)
        """

        logger.debug("Setting velocity", linear=linear_mmps, angular=angular_degps, duration=duration_s)
        await self._driver.velocity(
            linear_mmps,
            angular_degps,
            int(duration_s * 1000),
        )

    async def emit_tone(self, frequency_hz: int, duration_s: float, volume_percent: int) -> None:
        """
        Emit sound defined by frequency.

        Given a frequency and a duration, emit sound.

        :param frequency_hz: Sound frequency in Hertz
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`emit_note`, :py:meth:`emit_midi`

        .. code-block:: python

            # emit 440 Hz (A4) for one second
            await robot.emit_tone(440, 1, 50)
        """

        logger.debug("Emitting tone", frequency=frequency_hz, duration=duration_s, volume=volume_percent)
        await self._driver.play_tone(
            frequency_hz,
            int(duration_s * 1000),
            int(volume_percent),
        )

    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume_percent: int) -> None:
        """
        Emit sound defined by note and octave.

        Given a note, octave and a duration, emit sound.

        :param note: String containing the note in capital letters with sharp, such as A or F#
        :param octave: Sound octave
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`emit_tone`, :py:meth:`emit_midi`

        .. code-block:: python

            # emit A4 (440Hz) for one second
            await robot.emit_note("A", 4, 1, 50)
        """

        notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
        note_idx = notes.index(note.upper())

        if note_idx < 0:
            raise ValueError(f"Invalid note: {note_idx}")

        frequency_hz = self._convert_note_to_frequency(octave, note_idx)
        await self.emit_tone(
            frequency_hz,
            duration_s,
            volume_percent,
        )

    async def emit_midi(self, midi_number: int, duration_s: float, volume_percent: int):
        """
        Emit sound defined its midi number.

        Given a midi number and a duration, emit sound.

        :param midi_number: Tone midi number
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`emit_tone`, :py:meth:`emit_note`

        .. code-block:: python

            # emit midi 69 (A4, 440Hz) for one second
            await robot.emit_note(69, 1, 50)
        """

        frequency_hz = LineFollower._convert_key_to_frequency(midi_number, reference=69)
        await self.emit_tone(
            frequency_hz,
            duration_s,
            volume_percent,
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

    async def play_audio(self, name: TAudio) -> None:
        """
        Play audio file.

        :param name: Audio name

        :raises AudioFileNotFoundError: When the audio file does not exist
        :See also: :py:meth:`say_color`, :py:meth:`say_direction`, :py:meth:`say_number`

        .. code-block:: python

            # play audio file called "happy"
            await robot.play_audio("happy")
        """
        logger.debug("Playing audio file", name=name)
        asset_name = map_audio_name_to_filename(name)
        try:
            await self._driver.play_audio_asset(asset_name)
        except LinefollowerFileNotFoundError as err:
            raise AudioFileNotFoundError(name) from err

    async def say_number(self, number: int | float) -> None:
        """
        Say number.

        Play audio file(s) given by number. Only integers from -199 to 199 supported.

        :param number: Number to say

        :raises ValueError: When the number is out of bounds
        :See also: :py:meth:`say_color`, :py:meth:`say_direction`, :py:meth:`play_audio`

        .. code-block:: python

            # say number 95
            await robot.say_number(95)

            # say number -15
            await robot.say_number(-15)
        """

        numint = int(number)
        if not (-199 < numint < 199):
            raise ValueError(f"`say_number` only supports range -199 to 199, got {numint}")

        sounds: list[str] = []
        if numint < 0:
            sounds.append("010400FF")  # minus

        asset_name = f"010400{format(abs(numint), 'x').rjust(2, '0').upper()}"
        sounds.append(asset_name)

        for sound in sounds:
            await self._driver.play_audio_asset(sound)

    async def say_color(self, color: ClassifiedColor) -> None:
        """
        Say (classified) color.

        Play audio file given by :py:class:`~ozobot.linefollower.datatypes.ClassifiedColor` such as `ClassifiedColor.BLACK`. Raw colors defined by RGB value are not supported.

        :param color: Classified color to say

        :raises InvalidClassifiedColorError: If the parameter is not a known classified color.
        :See also: :py:meth:`say_direction`, :py:meth:`say_number`, :py:meth:`play_audio`

        .. code-block:: python

            from ozobot.linefollower import ClassifiedColor

            # say "red"
            await robot.say_color(ClassifiedColor.RED)
        """

        match color:
            case ClassifiedColor.BLACK:
                return await self._driver.play_audio_asset("01040200")
            case ClassifiedColor.RED:
                return await self._driver.play_audio_asset("01040201")
            case ClassifiedColor.GREEN:
                return await self._driver.play_audio_asset("01040202")
            case ClassifiedColor.BLUE:
                return await self._driver.play_audio_asset("01040204")
            case ClassifiedColor.WHITE:
                return await self._driver.play_audio_asset("01040207")
            case _:
                raise InvalidClassifiedColorError(color)

    async def say_direction(self, direction: Direction) -> None:
        """
        Say direction.

        Play audio file given by :py:class:`~ozobot.linefollower.datatypes.Direction` such as `Direction.RIGHT`.

        :param color: Direction to say

        :raises InvalidDirectionError: If the parameter is not a known classified color.
        :See also: :py:meth:`say_color`, :py:meth:`say_number`, :py:meth:`play_audio`

        .. code-block:: python

            from ozobot.linefollower import Direction

            # say "left"
            await robot.say_direction(Direction.LEFT)

            # can't handle groupped directions, so this would fail
            # await robot.say_direction(Direction.LEFT | Direction.STRAIGHT)
        """

        match direction:
            case Direction.LEFT:
                return await self._driver.play_audio_asset("01040102")
            case Direction.RIGHT:
                return await self._driver.play_audio_asset("01040104")
            case Direction.STRAIGHT:
                return await self._driver.play_audio_asset("01040101")
            case Direction.BACKWARD:
                return await self._driver.play_audio_asset("01040108")
            case _:
                raise InvalidDirectionError(direction)
                typing.assert_never(direction)

    async def set_led(self, mask: LEDMask, color: Color) -> None:
        """
        Set LED color.

        Change color of LEDs selected by :py:class:`~ozobot.linefollower.datatypes.LEDMask`. The function accepts both
        :py:class:`~ozobot.linefollower.datatypes.RawColor` and :py:class:`~ozobot.linefollower.datatypes.ClassifiedColor`.

        :param mask: Mask defining which LEDs will be affected
        :param color: Either :py:class:`~ozobot.linefollower.datatypes.RawColor` or :py:class:`~ozobot.linefollower.datatypes.ClassifiedColor` defining the new LED color.

        .. note::
            Set the color to :py:data:`~ozobot.linefollower.datatypes.ClassifiedColor.BLACK` to turn the selected LED off.

        .. code-block:: python

            from ozobot.linefollower import LEDMask, RawColor, ClassifiedColor

            # set the TOP to red
            await robot.set_led(LEDMask.TOP, ClassifiedColor.RED)

            # set the LEFT and RIGHT by RGB value
            await robot.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, RawColor(0, 0.4, 0))

            # turn off ALL
            await robot.set_led(LEDMask.ALL_ROBOT, ClassifiedColor.BLACK)
        """
        logger.debug("Setting LED", mask=mask, color=color)
        if isinstance(color, RawColor):
            raw_color = color
        elif isinstance(color, ClassifiedColor):
            raw_color = color.to_raw_color()

        red = raw_color.red
        green = raw_color.green
        blue = raw_color.blue

        await self._driver.set_led(mask, red, green, blue)

    async def follow_line(self, direction: Direction) -> Direction:
        """
        Follow line until the next intersection.

        Direction in which to follow the line must be given. If there is no line in the given direction, the robot does not move.

        While the robot follows the line, color codes are not interpreted, therefore no action is taken when reading the color code. The robot
        stops on the first intersection or line end. A subsequent call to this function can be made to pick a direction on the intersection.

        Line following speed can be changed by calling :py:meth:`.data.line_following_speed.write`.

        Detected color codes and intersections are available through the virtual memory :py:attr:`.data.intersection` and :py:attr:`.data.color_code`.


        :param direction: Direction to take when the line following starts
        :raises ValueError: If zero or more than one flag is passed as the direction
        :returns: Union of directions forming the final intersection the robot stopped at

        :See also: :py:meth:`face_line_direction`

        .. note::
            Exactly one flag needs to be passed to the `direction` parameter. For example `Direction.LEFT` is valid,
            while `Direction.LEFT | Direction.RIGHT` is not.


        .. code-block:: python

            # turn right on the current intersection, follow the line until the next intersection and collect all color codes on the line segment
            async with robot.data.color_code.watch() as codes_iterator:
                intersection = await robot.follow_line(Direction.RIGHT)

            codes = [code async for code in codes_iterator]
        """
        logger.debug("Following line", direction=direction)
        async with self.data.intersection.watch() as intersections:
            await self._driver.line_navigation(direction, follow=True)
            intersection_sample = await anext(intersections)

        return intersection_sample.value

    async def face_line_direction(self, direction: Direction) -> None:
        """
        Reorient to the given direction on a line.

        If the robot was previously following a line (see :py:meth:`follow_line`), calling this rotates the robot to face the given direction relative to the current direction. When the direction is
        not valid (e.g., :py:obj:`Direction.LEFT` is given on a straight line) or if the robot was not previously following a line, this is no-op.

        The call can be made on intersections, on an end of the line or on a straight line when the previous line following was cancelled. This method is semantically similar to :py:meth:`follow_line`, but it does not snap to the line
        when the robot was not previously following a line and it does not start the actual line following process, it just reorients the robot.

        :param direction: Direction of a line to orient to
        :raises ValueError: If zero or more than one flag is passed as the direction
        :See also: :py:meth:`follow_line`

        .. note::
            Exactly one flag needs to be passed to the `direction` parameter. For example `Direction.LEFT` is valid,
            while `Direction.LEFT | Direction.RIGHT` is not.

        .. code-block:: python

            # make the robot rotate right on the current intersection, but do not start line following
            await robot.reorient_to_line(Direction.RIGHT)
        """

        logger.debug("Facing line direction", direTction=direction)
        await self._driver.line_navigation(direction, follow=False)
