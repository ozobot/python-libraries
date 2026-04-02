from __future__ import annotations

import typing

from ozobot.common.logging import logger
from ozobot.linefollower.datatypes import (
    Color,
    Direction,
    LEDMask,
    NamedColor,
    RawColor,
    TAudio,
    TNote,
)
from ozobot.linefollower.driver.interface import Driver, VirtualMemoryRegions
from ozobot.linefollower.driver.shared import map_audio_name_to_filename
from ozobot.linefollower.exceptions import (
    AudioFileNotFoundError,
    InvalidDirectionError,
    InvalidNamedColorError,
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
        Move the robot in a straight line.

        Move the robot forward by the given distance at the given speed when the given distance is positive; or move it backwards when the distance is negative.

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

        Rotate the robot counter-clockwise when the angle is positive, or clockwise when the angle is negative.

        :param angle_deg: Angle to rotate counter-clockwise in degrees. If negative, the robot rotates clockwise.
        :param angular_speed_degps: Rotation speed in degrees per second. The sign is ignored.
        :See also: :py:meth:`move`, :py:meth:`set_velocity`

        .. code-block:: python

            # move robot 90deg counter-clockwise and clockwise
            await robot.rotate(90, 45)
            await robot.rotate(-90, 45)
        """

        logger.debug("Rotating", angle=angle_deg, angle_speed=angular_speed_degps)
        await self._driver.rotate(
            angle_deg,
            abs(angular_speed_degps),
        )

    async def set_velocity(self, linear_mmps: float, angular_degps: float, duration_s: float) -> None:
        """
        Move for a specified duration.

        Given linear and angular velocity components, the robot moves at the specified velocity for the given duration, then stops.

        :param linear_mmps: Linear velocity component in millimeters per second
        :param angular_degps: Angular velocity component in degrees per second
        :param duration: Movement duration in seconds, -1 for infinity.
        :See also: :py:meth:`move`, :py:meth:`rotate`

        .. note::
            Although bad practice, the `duration_s` parameter is here for convenience. If you want to follow asyncio idioms, such as `timeouts <https://docs.python.org/3/library/asyncio-task.html#timeouts>` or
            `tasks <https://docs.python.org/3/library/asyncio-task.html#creating-tasks>`_, you can use `duration_s=-1` for an infinite duration.


        .. code-block:: python

            # move straight forward for 2.5 seconds - the convenient way
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

    async def play_tone(self, frequency_hz: int, duration_s: float, volume_percent: int) -> None:
        """
        Play sound defined by frequency.

        Given a frequency and a duration, play the sound.

        :param frequency_hz: Sound frequency in range 0 - 100_000 in Hertz
        :param duration_s: Sound duration in seconds
        :param volume_percent: Sound volume in percent (0 - 100)
        :raises ValueError: when the frequency is out of range

        :See also: :py:meth:`play_note`, :py:meth:`play_midi`

        .. code-block:: python

            # play 440 Hz (A4) for one second at 50% volume
            await robot.play_tone(440, 1, 50)
        """

        if frequency_hz < 0 or frequency_hz > 100_000:
            raise ValueError(f"Frequency out of range: {frequency_hz}")

        logger.debug("Playing tone", frequency=frequency_hz, duration=duration_s, volume=volume_percent)
        await self._driver.play_tone(
            frequency_hz,
            int(duration_s * 1000),
            int(volume_percent),
        )

    async def play_note(self, note: TNote, octave: int, duration_s: float, volume_percent: int) -> None:
        """
        Play sound defined by a note and an octave.

        Given a note, octave and a duration, play the sound.

        :param note: The note represented by a capital letter and a sharp sign, such as A or F#
        :param octave: Sound octave number (0 - 9). Middle C and A 440 Hz are in octave 4
        :param duration_s: Sound duration in seconds
        :param volume_percent: Sound volume in percent (0 - 100)
        :raises ValueError: when the note is invalid
        :raises ValueError: when the octave is out of range
        :See also: :py:meth:`play_tone`, :py:meth:`play_midi`

        .. code-block:: python

            # play A4 (440Hz) for one second at 50% volume
            await robot.play_note("A", 4, 1, 50)
        """

        notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
        note_idx = notes.index(note.upper())

        if note_idx < 0:
            raise ValueError(f"Invalid note: {note_idx}")

        if octave < 0 or octave > 9:
            raise ValueError(f"Invalid octave: {octave}")

        frequency_hz = self._convert_note_to_frequency(octave, note_idx)
        await self.play_tone(
            frequency_hz,
            duration_s,
            volume_percent,
        )

    async def play_midi(self, midi_number: int, duration_s: float, volume_percent: int):
        """
        Play tone defined by its MIDI number.

        Given a MIDI number and a duration, play the sound.

        :param midi_number: Tone MIDI number, 0-127
        :param duration_s: Sound duration in seconds
        :param volume_percent: Sound volume in percent (0 - 100)
        :raises ValueError: when the midi number is out of range
        :See also: :py:meth:`play_tone`, :py:meth:`play_note`

        .. code-block:: python

            # play MIDI 69 (A4, 440Hz) for one second at 50% volume
            await robot.play_midi(69, 1, 50)
        """

        if midi_number < 0 or midi_number > 127:
            raise ValueError(f"Midi number out of range: {midi_number}")

        frequency_hz = LineFollower._convert_key_to_frequency(midi_number, reference=69)
        await self.play_tone(
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

        Play audio file given by name. These files are stored in the robot and cannot be modified. Playing arbitrary audio files is not supported.

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

    def _int_to_number_asset_name(self, number: int) -> str:
        return f"010400{format(abs(number), 'x').rjust(2, '0').upper()}"

    async def say_number(self, number: int | float) -> None:
        """
        Say number.

        Play audio file(s) saying the given number. Only integers from -199 to 199 are supported.

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
        if not (-200 < numint < 200):
            raise ValueError(f"`say_number` only supports range -199 to 199, got {numint}")

        sounds: list[str] = []
        if numint < 0:
            sounds.append("010400FF")  # minus

        if numint == 0:
            sounds.append(self._int_to_number_asset_name(0))
        else:
            numint = abs(numint)
            if numint >= 100:
                sounds.append(self._int_to_number_asset_name(100))
                numint -= 100

            if numint >= 20:
                tens = numint // 10
                sounds.append(self._int_to_number_asset_name(tens * 10))
                numint %= 10

            if numint > 0:
                sounds.append(self._int_to_number_asset_name(numint))

        for sound in sounds:
            await self._driver.play_audio_asset(sound)

    async def say_color(self, color: NamedColor) -> None:
        """
        Say one of named (classified) colors.

        Play audio file given by :py:class:`~ozobot.linefollower.datatypes.NamedColor` such as `NamedColor.BLACK`. Raw colors defined by RGB value are not supported.

        :param color: Classified color to say

        :raises InvalidNamedColorError: If the parameter is not a known color the robot can classify.
        :See also: :py:meth:`say_direction`, :py:meth:`say_number`, :py:meth:`play_audio`

        .. code-block:: python

            from ozobot.linefollower import NamedColor

            # say "red"
            await robot.say_color(NamedColor.RED)
        """

        match color:
            case NamedColor.BLACK:
                return await self._driver.play_audio_asset("01040200")
            case NamedColor.RED:
                return await self._driver.play_audio_asset("01040201")
            case NamedColor.GREEN:
                return await self._driver.play_audio_asset("01040202")
            case NamedColor.BLUE:
                return await self._driver.play_audio_asset("01040204")
            case NamedColor.WHITE:
                return await self._driver.play_audio_asset("01040207")
            case _:
                raise InvalidNamedColorError(color)

    async def say_direction(self, direction: Direction) -> None:
        """
        Say direction.

        Play audio file given by :py:class:`~ozobot.linefollower.datatypes.Direction` such as `Direction.RIGHT`.

        :param color: Direction to say

        :raises InvalidDirectionError: If the parameter is not a valid Direction.
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
        :py:class:`~ozobot.linefollower.datatypes.RawColor` and :py:class:`~ozobot.linefollower.datatypes.NamedColor`.

        :param mask: Mask defining which LEDs will be affected
        :param color: Either :py:class:`~ozobot.linefollower.datatypes.RawColor` or :py:class:`~ozobot.linefollower.datatypes.NamedColor` defining the new LED color.

        .. note::
            Set the color to :py:data:`~ozobot.linefollower.datatypes.NamedColor.BLACK` to turn the selected LED off.

        .. code-block:: python

            from ozobot.linefollower import LEDMask, RawColor, NamedColor

            # set the TOP to red
            await robot.set_led(LEDMask.TOP, NamedColor.RED)

            # set the LEFT and RIGHT by RGB value
            await robot.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, RawColor(0, 0.4, 0))

            # turn off ALL
            await robot.set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
        """
        logger.debug("Setting LED", mask=mask, color=color)
        if isinstance(color, RawColor):
            raw_color = color
        elif isinstance(color, NamedColor):
            raw_color = color.to_raw_color()

        red = raw_color.red
        green = raw_color.green
        blue = raw_color.blue

        await self._driver.set_led(mask, red, green, blue)

    async def follow_line(self, direction: Direction) -> Direction:
        """
        Follow the line until the next intersection.

        Direction in which to follow the line must be given. If there is no line in the given direction, the robot does not move.

        While the robot follows the line, the color codes are not interpreted, therefore no action is taken when reading the color code. The robot
        stops at the first intersection or line end. A subsequent call to this function can be made to pick a direction at the intersection.

        Line-following speed can be changed by calling :py:meth:`.data.line_following_speed.write`.

        Detected color codes and intersections are available through the virtual memory :py:attr:`.data.intersection` and :py:attr:`.data.color_code`.


        :param direction: Direction to take when the line-following starts
        :raises ValueError: If zero or more than one flag is passed as the direction
        :returns: Union of directions forming the final intersection the robot stopped at

        :See also: :py:meth:`face_line_direction`

        .. note::
            Exactly one flag needs to be passed to the `direction` parameter. For example `Direction.LEFT` is valid,
            while `Direction.LEFT | Direction.RIGHT` is not.


        .. code-block:: python

            # turn right at the current intersection, follow the line until the next intersection and collect all color codes on the line segment
            async with robot.data.color_code.watch() as codes_iterator:
                intersection = await robot.follow_line(Direction.RIGHT)

            codes = [code async for code in codes_iterator]
        """
        logger.debug("Following line", direction=direction)
        async with self.data.intersection.watch() as intersections:
            await self._driver.line_navigation(direction, follow=True)
            intersection_sample = await anext(aiter(intersections))

        return intersection_sample.value

    async def face_line_direction(self, direction: Direction) -> None:
        """
        Reorient to the given direction while on a line.

        If the robot was previously following a line (see :py:meth:`follow_line`), calling this rotates the robot to face the given direction relative to the current direction. When the direction is
        not valid (e.g., :py:obj:`Direction.LEFT` is given on a straight line) or if the robot was not previously following a line, this is no-op.

        The call can be made at intersections, at the end of a line, or on a straight line after the previous line-following was cancelled. This method is semantically similar to :py:meth:`follow_line`, but it does not snap to the line
        when the robot was not previously following a line and it does not start the actual line-following process, it just reorients the robot.

        :param direction: Direction of a line to orient to
        :raises ValueError: If zero or more than one flag is passed as the direction
        :See also: :py:meth:`follow_line`

        .. note::
            Exactly one flag needs to be passed to the `direction` parameter. For example `Direction.LEFT` is valid,
            while `Direction.LEFT | Direction.RIGHT` is not.

        .. code-block:: python

            # make the robot rotate right at the current intersection, but do not start line-following
            await robot.face_line_direction(Direction.RIGHT)
        """

        logger.debug("Facing line direction", direction=direction)
        await self._driver.line_navigation(direction, follow=False)
