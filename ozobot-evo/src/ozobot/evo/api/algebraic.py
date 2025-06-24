from __future__ import annotations

from loguru import logger
from ozobot.common.algebraic import ActorDispatcher
from ozobot.evo.api.core import Evo
from ozobot.evo.api.data_access import DataAccessRead, DataWatcher, FakeDataWatcher
from ozobot.evo.datatypes import BatteryState, Color, ColorCode, Direction, LEDMask
from ozobot.evo.protocol import Types

# Global dispatcher for Evo instances
_evo_dispatcher = ActorDispatcher[Evo]()


def battery() -> DataAccessRead[Types.Battery, BatteryState]:
    return _evo_dispatcher.get_property(Evo, DataAccessRead, "_property_battery")

def color_codes() -> DataWatcher[Types.ColorCode, ColorCode]:
    return _evo_dispatcher.get_property(Evo, DataWatcher, "_watcher_color_codes")

def line_color() -> DataWatcher[Types.LineColor, Color]:
    return _evo_dispatcher.get_property(Evo, DataWatcher, "_watcher_line_color")

def surface_color() -> DataWatcher[Types.SurfaceColor, Color]:
    return _evo_dispatcher.get_property(Evo, DataWatcher, "_watcher_surface_color")

def intersection() -> FakeDataWatcher[Direction]:
    return _evo_dispatcher.get_property(Evo, FakeDataWatcher, "_intersection")

async def move(distance_m: float, speed_mps: float) -> None:
    logger.debug("Moving", distance=distance_m, speed=speed_mps)
    return await _evo_dispatcher.acall(Evo.move, Evo, distance_m, speed_mps)

async def rotate(angle_deg: float, angular_speed_degps: float) -> None:
    logger.debug("Rotating", angle=angle_deg, anglle_speed=angular_speed_degps)
    return await _evo_dispatcher.acall(Evo, Evo.rotate, angle_deg, angular_speed_degps)

async def set_velocity(linear_mps: float, angular_degps: float, duration_s: float) -> None:
    logger.debug("Setting velocity", linear=linear_mps, angular=angular_degps, duration=duration_s)
    return await _evo_dispatcher.acall(Evo, Evo.set_velocity, linear_mps, angular_degps, duration_s)

async def emit_tone(frequency_hz: int, duration_s: float, volume: int) -> None:
    logger.debug("Emitting tone", frequency=frequency_hz, duration=duration_s, volume=volume)
    return await _evo_dispatcher.acall(Evo, Evo.emit_tone, frequency_hz, duration_s, volume)
async def emit_note(note: str, octave: int, duration_s: float, volume: int) -> None:
    return await _evo_dispatcher.acall(Evo, Evo.emit_note, note, octave, duration_s, volume)

async def play_audio(name: str) -> None:
    await _evo_dispatcher.acall(Evo, Evo.play_audio, filename)

async def set_led(mask: LEDMask, color: Color) -> None:
    logger.debug("Setting LED", mask=mask, color=color)
    await _evo_dispatcher.acall(Evo, Evo.set_led, mask, red, green, blue)

async def follow_line(direction: Direction) -> None:
    logger.debug("Following line", direction=direction)
    await _evo_dispatcher.acall(Evo, Evo.follow_line, direction)

async def align_with_line(direction: Direction) -> None:
    logger.debug("Aligning with line", direTction=direction)
    await _evo_dispatcher.acall(Evo, Evo.align_with_line, direction)

async def set_follow_line_speed(speed_mps: float) -> None:
    logger.debug("Setting line following speed", speed=speed_mps)
    await _evo_dispatcher.acall(Evo, Evo.set_follow_line_speed, speed_mps)
