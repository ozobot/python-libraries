import asyncio
import time

from ozobot.ari import SyncAriHandle
from ozobot.evo import SyncEvoHandle
from ozobot.linefollower import Color, Colors, Direction, LEDMask

name = "Ari_1"
# name = "Evo_1"
handle = SyncAriHandle(name=name) if name.startswith("Ari") else SyncEvoHandle(name=name)


def main():
    with handle.connect() as r:
        # motion(r)
        # line(r)
        # led(r)
        # sound(r)
        io(r)
        # sensors(r)


def motion(r):
    r.move(100, 50)
    r.rotate(180, 90)
    r.set_velocity(50, 0, 2)


def sound(r):
    r.play_audio("happy")
    r.emit_note("A", 4, 1, 1)
    time.sleep(0.5)
    r.emit_tone(440, 1, 1)
    time.sleep(0.5)
    r.emit_midi(69, 1, 1)


def led(r):
    r.set_led(LEDMask.TOP | LEDMask.FRONT_CENTER, Colors.RED)
    r.set_led(LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT, Colors.BLUE)


def io(r):
    r.user_io_print("Hello world!")
    import time

    time.sleep(0.5)
    r.user_io_alert("Confirm this", cancellable=False)

    try:
        r.user_io_alert("Cancel this", cancellable=True)
    except asyncio.CancelledError:
        pass
    else:
        raise Exception("Cancellation expected")

    selections = [
        (int, [1, 2, 3]),
        (float, [1.0, 2.0, 3.0]),
        (str, ("one", "two", "three")),
        (Color, (Colors.RED, Colors.BLUE, Colors.GREEN)),
        (Direction, (Direction.LEFT, Direction.RIGHT)),
    ]

    for t, v in selections:
        x = r.user_io_prompt("Select", t, v, cancellable=False)
        print("Selected ", x, type(x))


def line(r):
    s1 = r.follow_line(Direction.STRAIGHT)
    print(s1)
    s2 = r.align_with_line(Direction.RIGHT)
    print(s2)
    s3 = r.align_with_line(Direction.LEFT)
    print(s3)

    s = r.data.line_color.read()
    print(s.value)


def read_sensors(r, sensors):
    for name in sensors:
        if hasattr(r.data, name):
            sensor = getattr(r.data, name)

            if hasattr(sensor, "read"):
                val = sensor.read()
                print(f"read {name}: {val.value} @ {val.timestamp}")
            else:
                print(f"skipping read for {name}")
        else:
            print(f"Skipping {name} - not present")


def read_write_sensors(r, sensors):
    for name in sensors:
        if hasattr(r.data, name):
            sensor = getattr(r.data, name)
            val = sensor.read()
            print(f"read {name}: {val}")
            sensor.write(val)
            print(f"written {name}: {val}")
        else:
            print(f"Skipping {name} - not present")


def sensors(r):
    read_sensorlist = [
        "surface_color",
        "proximity_left_front",
        "proximity_right_front",
        "proximity_right_rear",
        "proximity_left_rear",
        "time_of_flight",
    ]

    # read_sensorlist += [
    #     "ir_message_left_front",
    #     "ir_message_right_front",
    #     "ir_message_left_rear",
    #     "ir_message_right_rear",
    # ]

    read_sensors(r, read_sensorlist)
    read_write_sensors(r, ["line_following_speed"])


main()
