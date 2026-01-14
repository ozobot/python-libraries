from ozobot.linefollower.api.data_access import DataReadConstant
from ozobot.linefollower.datatypes import RobotGeometry

geometry = DataReadConstant(
    lambda: RobotGeometry(
        ticks_per_mm=22.28169,
        wheel_track_mm=31.5,
        wheel_diameter_mm=12,
        encoder_ticks_per_wheel_revolution=16 * 2 * 21 * 15 / 12.0,
        max_speed_limit_mmps=300,
    )
)
