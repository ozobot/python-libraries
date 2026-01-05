from ozobot.linefollower.api.data_access import DataReadConstant
from ozobot.linefollower.datatypes import RobotGeometry

geometry = DataReadConstant(
    lambda: RobotGeometry(
        ticks_per_meter=22281.69,
        wheel_track=0.0315,
        wheel_diameter=0.012,
        encoder_ticks_per_wheel_revolution=16 * 2 * 21 * 15 / 12.0,
        max_speed_limit=0.3,
    )
)
