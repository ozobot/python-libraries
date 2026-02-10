from __future__ import annotations

from ozobot.common.sync import as_sync
from ozobot.linefollower.datatypes import Color, ColorCode, Direction, LEDMask, NamedColor, TAudio, TNote
from ozobot.linefollower.driver.interface import ReadableRegion, ReadableWritableRegion

from .core import LineFollower


class SyncDataAccessRead[T]:
    def __init__(self, reader: ReadableRegion[T]) -> None:
        self._reader = reader

    @as_sync
    async def read(self) -> T:
        return await self._reader.read()


class SyncDataAccessReadWrite[T](SyncDataAccessRead[T]):
    def __init__(self, reader: ReadableWritableRegion[T]) -> None:
        super().__init__(reader)
        self._writer = reader

    @as_sync
    async def write(self, data: T) -> None:
        await self._writer.write(data)


class SyncMemoryRegions:
    def __init__(self, linefollower: LineFollower) -> None:
        self.line_following_speed = SyncDataAccessReadWrite(linefollower.data.line_following_speed)
        """
        Line following speed in mm/s.
        """

        self.line_color = SyncDataAccessRead(linefollower.data.line_color)
        """
        Line color detected.

        Classified color detected by the line sensor. Gives `None` if the color cannot be classified.
        """

        self.surface_color = SyncDataAccessRead(linefollower.data.surface_color)
        """
        Surface color detected.

        Classified color detected by the surface sensor. Gives `None` if the color cannot be classified.
        """


class SyncLineFollower:
    def __init__(self, linefollower: LineFollower) -> None:
        self._linefollower = linefollower

    @as_sync
    async def move(self, distance_m: float, speed_mps: float) -> None:
        """
        Move the robot straight.

        Move the robot forward by the given distance at the given speed for or positive distance, or backwards for negative distance.

        :param distance_mm: Distance to move in millimeters. If negative, the robot moves backwards.
        :param speed_mmps: Movement speed at millimeters per second. The sign is ignored.
        :See also: :py:meth:`rotate`, :py:meth:`set_velocity`

        .. code-block:: python

            # move robot 200mm forward and backward
            robot.move(200, 50)
            robot.move(-200, 50)
        """
        await self._linefollower.move(distance_m, speed_mps)

    @as_sync
    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        """
        Rotate the robot.

        Rotate the robot counter clockwise when the angle is positive, or clockwise when the angle is negative.

        :param angle_deg: Angle to rotate counter clockwise in degrees. If negative, the robot rotates clockwise.
        :param speed_mmps: Rotation speed in degrees per second. The sign is ignored.
        :See also: :py:meth:`move`, :py:meth:`set_velocity`

        .. code-block:: python

            # move robot 90deg counter clockwise and clockwise
            robot.rotate(90, 45)
            robot.rotate(-90, 45)
        """
        await self._linefollower.rotate(angle_deg, angular_speed_degps)

    @as_sync
    async def set_velocity(self, linear_mps: float, angular_degps: float, duration_s: float) -> None:
        """
        Move with duration.

        Provided linear and angular velocity components, the robot moves at given velocity with a given duration. Robot stops after the duration passes.

        :param linear_mmps: Linear velocity component in millimeters per second
        :param angular_degps: Angular velocity component in degrees per second
        :param duration: Movement duration in seconds.
        :See also: :py:meth:`move`, :py:meth:`rotate`

        .. code-block:: python

            # move for 2.5 seconds
            robot.set_velocity(100, 0, 2.5)
        """
        await self._linefollower.set_velocity(linear_mps, angular_degps, duration_s)

    @as_sync
    async def play_tone(self, frequency_hz: int, duration_s: float, volume_percent: int) -> None:
        """
        Play sound defined by frequency.

        Given a frequency and a duration, play sound.

        :param frequency_hz: Sound frequency in Hertz
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`play_note`, :py:meth:`play_midi`

        .. code-block:: python

            # play 440 Hz (A4) for one second
            robot.play_tone(440, 1, 50)
        """
        await self._linefollower.play_tone(frequency_hz, duration_s, volume_percent)

    @as_sync
    async def play_midi(self, midi_number: int, duration_s: float, volume_percent: int) -> None:
        """
        Play sound defined its midi number.

        Given a midi number and a duration, play sound.

        :param midi_number: Tone midi number
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`play_tone`, :py:meth:`play_note`

        .. code-block:: python

            # play midi 69 (A4, 440Hz) for one second
            robot.play_note(69, 1, 50)
        """
        await self._linefollower.play_midi(midi_number, duration_s, volume_percent)

    @as_sync
    async def play_note(self, note: TNote, octave: int, duration_s: float, volume_percent: int) -> None:
        """
        Play sound defined by note and octave.

        Given a note, octave and a duration, play sound.

        :param note: String containing the note in capital letters with sharp, such as A or F#
        :param octave: Sound octave
        :param duration_s: Sound duration
        :param volume_percent: Sound volume in percent (0 - 100)
        :See also: :py:meth:`play_tone`, :py:meth:`play_midi`

        .. code-block:: python

            # play A4 (440Hz) for one second
            robot.play_note("A", 4, 1, 50)
        """
        await self._linefollower.play_note(note, octave, duration_s, volume_percent)

    @as_sync
    async def play_audio(self, name: TAudio) -> None:
        """
        Play audio file.

        :param name: Audio name

        :raises AudioFileNotFoundError: When the audio file does not exist
        :See also: :py:meth:`say_color`, :py:meth:`say_direction`, :py:meth:`say_number`

        .. code-block:: python

            # play audio file called "happy"
            robot.play_audio("happy")
        """
        await self._linefollower.play_audio(name)

    @as_sync
    async def say_number(self, number: int | float) -> None:
        """
        Say number.

        Play audio file(s) given by number. Only integers from -199 to 199 supported.

        :param number: Number to say

        :raises ValueError: When the number is out of bounds
        :See also: :py:meth:`say_color`, :py:meth:`say_direction`, :py:meth:`play_audio`

        .. code-block:: python

            # say number 95
            robot.say_number(95)

            # say number -15
            robot.say_number(-15)
        """
        await self._linefollower.say_number(number)

    @as_sync
    async def say_color(self, color: NamedColor) -> None:
        """
        Say (classified) color.

        Play audio file given by :py:class:`~ozobot.linefollower.datatypes.NamedColor` such as `NamedColor.BLACK`. Raw colors defined by RGB value are not supported.

        :param color: Classified color to say

        :raises InvalidNamedColorError: If the parameter is not a known classified color.
        :See also: :py:meth:`say_direction`, :py:meth:`say_number`, :py:meth:`play_audio`

        .. code-block:: python

            from ozobot.linefollower import NamedColor

            # say "red"
            robot.say_color(NamedColor.RED)
        """
        await self._linefollower.say_color(color)

    @as_sync
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
            robot.say_direction(Direction.LEFT)

            # can't handle groupped directions, so this would fail
            # robot.say_direction(Direction.LEFT | Direction.STRAIGHT)
        """
        await self._linefollower.say_direction(direction)

    @as_sync
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
            robot.set_led(LEDMask.TOP, NamedColor.RED)

            # set the LEFT and RIGHT by RGB value
            robot.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, RawColor(0, 0.4, 0))

            # turn off ALL
            robot.set_led(LEDMask.ALL_ROBOT, NamedColor.BLACK)
        """
        await self._linefollower.set_led(mask, color)

    @as_sync
    async def follow_line(self, direction: Direction) -> tuple[Direction, list[ColorCode]]:
        """
        Follow line until the next intersection.

        Direction in which to follow the line must be given. If there is no line in the given direction, the robot does not move.

        While the robot follows the line, color codes are not interpreted, therefore no action is taken when reading the color code. The robot
        stops on the first intersection or line end. A subsequent call to this function can be made to pick a direction on the intersection.

        Line following speed can be changed by calling :py:meth:`.data.line_following_speed.write`.

        Returns the intersection where it stopped and a list of detected color codes.


        :param direction: Direction to take when the line following starts
        :raises ValueError: If zero or more than one flag is passed as the direction
        :returns: Union of directions forming the final intersection the robot stopped at, and list of color codes encountered.

        :See also: :py:meth:`face_line_direction`

        .. note::
            Exactly one flag needs to be passed to the `direction` parameter. For example `Direction.LEFT` is valid,
            while `Direction.LEFT | Direction.RIGHT` is not.


        .. code-block:: python

            # turn right on the current intersection, follow the line until the next intersection and collect all color codes on the line segment
            intersection, codes = robot.follow_line(Direction.RIGHT)
        """
        async with self._linefollower.data.color_code.watch() as color_codes:
            intersection = await self._linefollower.follow_line(direction)

        return intersection, [cc.value async for cc in color_codes]

    @as_sync
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
            robot.face_line_direction(Direction.RIGHT)
        """
        await self._linefollower.face_line_direction(direction)
