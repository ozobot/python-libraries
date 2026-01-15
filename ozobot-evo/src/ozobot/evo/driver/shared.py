from ozobot.linefollower.api.data_access import DataReadConstant
from ozobot.linefollower.datatypes import RobotGeometry

geometry = DataReadConstant(
    lambda: RobotGeometry(
        ticks_per_mm=18.851,
        wheel_track_mm=23,
        wheel_diameter_mm=11.82,
        encoder_ticks_per_wheel_revolution=8 * 2 * 21 * 25 / 12,
        max_speed_limit_mmps=300,
    )
)
