import contextlib
import typing
from unittest.mock import ANY, Mock, patch, sentinel

import pytest
from ozobot.evo.drivers import LEDMask
from ozobot.evo.drivers.native import NativeDriver
from ozobot.evo.protocol import Types


def _get_async_control():
    return Mock(
        get_next_request_id=Mock(return_value=sentinel.request_id),
    )


def _create_command(
    *,
    response: dict[str, typing.Any],
    events: list[dict[str, typing.Any]] | None = None,
):
    if events:

        async def _evts():
            for e in events or []:
                yield Mock(**e)

        @contextlib.asynccontextmanager
        async def _resp():
            yield Mock(**response), _evts()
    else:

        async def _resp():
            return Mock(**response)

    return _resp()


@patch("ozobot.evo.drivers.sys.platform", "linux")
def test_import_native() -> None:
    from ozobot.evo.drivers import get_driver

    assert issubclass(get_driver(), NativeDriver)


async def test_open() -> None:
    with patch("ozobot.evo.drivers.native.open_client") as open_client_mock:
        async with NativeDriver.open(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF") as driver:
            assert isinstance(driver, NativeDriver)
            open_client_mock.assert_called_with(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF")


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        ("move", "MoveStraight", [0.2, 0.1], [0.2, 0.1]),
        ("rotate", "Rotate", [0.1, 0.2], [0.1, 0.2]),
        ("velocity", "Velocity", [0.1, 0.2, 3], [0.1, 0.2, 3]),
        ("play_tone", "PlayTone", [1, 2, 3], [1, 2, 3]),
        ("execute_file", "ExecuteFile", ["/path/to/file"], ["/path/to/file"]),
        (
            "line_navigation",
            "LineNavigation",
            ["left", False],
            [Types.IntersectionDirection.Left, Types.LineNavigationAction.DoNotFollow],
        ),
    ],
)
@patch("ozobot.evo.protocol.AsyncControl.get_next_request_id", lambda _: sentinel.request_id)
async def test_command_with_events(
    function_name: str, command_name: str, command_parameters: list[typing.Any], rpc_parameters: list[typing.Any]
) -> None:
    with patch(f"ozobot.evo.protocol.AsyncControl.{command_name}") as cmd_mock:
        driver = NativeDriver(Mock())

        cmd_mock.return_value = _create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
            events=[
                {"executionState": Types.ExecutionStateEnum.Running},
                {"executionState": Types.ExecutionStateEnum.FinishedNormal},
            ],
        )

        function = getattr(driver, function_name)
        await function(*command_parameters)
        cmd_mock.assert_called_once_with(sentinel.request_id, *rpc_parameters)


@pytest.mark.parametrize(
    ["command_direction", "rpc_direction"],
    [
        (LEDMask.FRONT_CENTER, Types.LEDsMask.front_center),
        (LEDMask.FRONT_LEFT_CENTER, Types.LEDsMask.front_left_center),
        (LEDMask.FRONT_RIGHT_CENTER, Types.LEDsMask.front_right_center),
        (LEDMask.FRONT_RIGHT, Types.LEDsMask.front_right),
        (LEDMask.FRONT_LEFT, Types.LEDsMask.front_left),
        (LEDMask.TOP, Types.LEDsMask.top),
        (
            LEDMask.FRONT_CENTER | LEDMask.FRONT_RIGHT,
            Types.LEDsMask.front_center | Types.LEDsMask.front_right,
        ),
    ],
)
async def test_set_led(command_direction: LEDMask, rpc_direction: Types.LEDsMask) -> None:
    with patch("ozobot.evo.protocol.AsyncControl.SetLED") as cmd_mock:
        driver = NativeDriver(Mock())

        cmd_mock.return_value = _create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
        )

        await driver.set_led(command_direction, 0, 100, 200)
        cmd_mock.assert_called_once_with(rpc_direction, 0, 100, 200, 255)


async def test_follow_speed() -> None:
    with patch("ozobot.evo.protocol.AsyncControl.MemWrite") as cmd_mock:
        driver = NativeDriver(Mock())

        cmd_mock.return_value = _create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
        )

        await driver.follow_speed(0.1)
        cmd_mock.assert_called_once_with(ANY, ANY, Types.S8_24(0.1).serialize())
