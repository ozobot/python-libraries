import math
import typing
from unittest.mock import call, patch

import pytest
from ozobot.linefollower.datatypes import Colors, Direction, LEDMask
from ozobot.web import rpctypes
from ozobot.web.driver import WebDriver


@pytest.mark.parametrize(
    ["method_name", "method_args", "method_result", "rpc_name", "rpc_args", "rpc_result"],
    (
        (
            "move",
            (100, 200),
            None,
            "MoveStraight",
            (0.1, 0.2),
            rpctypes.BaseExecutionStateResponse(execution_state="FinishedNormal"),
        ),
        (
            "rotate",
            (90, 10),
            None,
            "Rotate",
            (math.pi / 2, math.radians(10)),
            rpctypes.BaseExecutionStateResponse(execution_state="FinishedNormal"),
        ),
        (
            "velocity",
            (100, 90, 1000),
            None,
            "Velocity",
            (0.1, math.pi / 2, 1000),
            rpctypes.BaseExecutionStateResponse(execution_state="FinishedNormal"),
        ),
        (
            "play_tone",
            (440, 500, 50),
            None,
            "PlayTone",
            (440, 500),
            rpctypes.BaseExecutionStateResponse(execution_state="FinishedNormal"),
        ),
        ("stop_all", (), None, "StopExecution", (), rpctypes.Base()),
        (
            "set_led",
            (LEDMask.TOP | LEDMask.FRONT_LEFT, 255, 128, 0),
            None,
            "SetLED",
            ({"top": True, "front_left": True}, 255, 128, 0),
            rpctypes.BaseCallStatusResponse(call_status="CallSuccess"),
        ),
    ),
)
async def test_commands(
    method_name: str,
    method_args: tuple[typing.Any],
    method_result: typing.Any,
    rpc_name: str,
    rpc_args: tuple[typing.Any],
    rpc_result: typing.Any,
) -> None:
    robot_name = "robot1"
    with patch("ozobot.web.driver._rpcCoroutine") as mock_coro:
        mock_coro.return_value = rpc_result
        driver = WebDriver(robot_name)
        method = getattr(driver, method_name)
        result = await method(*method_args)
        assert result == method_result

        mock_coro.assert_awaited_once_with(robot_name, rpc_name, rpc_args)


async def test_line_navigation():
    robot_name = "robot1"
    with patch("ozobot.web.driver._rpcCoroutine") as mock_coro:
        mock_coro.return_value = rpctypes.IntersectionResponse(
            execution_state="FinishedNormal",
            intersection={"Forward": True, "Left": False},
        )
        driver = WebDriver(robot_name)

        await driver.line_navigation(Direction.STRAIGHT, follow=True)
        intersection = await driver.memory.intersection.read()
        assert intersection.data == Direction.STRAIGHT | Direction.LEFT

        mock_coro.assert_awaited_once_with(robot_name, "LineNavigation", ("Forward", "Follow"))


async def test_mem_read():
    robot_name = "robot1"
    with patch("ozobot.web.driver._rpcCoroutine") as mock_coro:
        mock_coro.return_value = 0.5
        driver = WebDriver(robot_name)

        speed = await driver.memory.line_following_speed.read()
        assert speed.data == 500

        mock_coro.assert_awaited_once_with(robot_name, "GetValue_wrapper", ("lineNavigationSpeed",))


async def test_mem_write():
    robot_name = "robot1"
    with patch("ozobot.web.driver._rpcCoroutine") as mock_coro:
        mock_coro.return_value = rpctypes.BaseCallStatusResponse(call_status="CallSuccess")
        driver = WebDriver(robot_name)

        await driver.memory.line_following_speed.write(500)

        mock_coro.assert_awaited_once_with(robot_name, "set_lineNavigationSpeed", (0.5,))


async def test_mem_watch_structure() -> None:
    robot_name = "robot1"
    num_data = 3

    responses_flat = [
        {"color": "Red", "timestamp": 1},
        {"color": "Black", "timestamp": 2},
        {"color": "Blue", "timestamp": 3},
    ]

    rpc_responses = [
        [responses_flat[0], responses_flat[1]],
        [
            responses_flat[2],
        ],
    ]
    with patch("ozobot.web.driver._rpcCoroutine", side_effect=rpc_responses) as mock_coro:
        driver = WebDriver(robot_name)

        async with driver.memory.line_color.watch() as it:
            samples = [await anext(it) for _ in range(num_data)]
            data = [sample.data for sample in samples]
        assert len(data) == num_data
        assert data == [
            Colors.RED,
            Colors.BLACK,
            Colors.BLUE,
        ]

        # we expect the calls to contain the property name in the first call
        # and the property name plus previous value in the consequent calls
        call_args_prefix = (
            robot_name,
            "retrieveFromDataStream_wrapper",
        )

        mock_coro.assert_has_calls(
            [
                call(*call_args_prefix, ({"type": "lineColor"},)),
                call(*call_args_prefix, ({"type": "lineColor", "value": responses_flat[1]},)),
            ]
        )


async def test_mem_watch_simple_type() -> None:
    robot_name = "robot1"
    num_data = 3

    responses_flat = [0.1, 0.2, 0.3]

    rpc_responses = [
        [responses_flat[0], responses_flat[1]],
        [
            responses_flat[2],
        ],
    ]
    with patch("ozobot.web.driver._rpcCoroutine", side_effect=rpc_responses) as mock_coro:
        driver = WebDriver(robot_name)

        async with driver.memory.line_following_speed.watch() as it:
            samples = [await anext(it) for _ in range(num_data)]
            data = [sample.data for sample in samples]
        assert len(data) == num_data
        assert data == [100, 200, 300]

        # we expect the calls to contain the property name in the first call
        # and the property name plus previous value in the consequent calls
        call_args_prefix = (
            robot_name,
            "retrieveFromDataStream_wrapper",
        )

        mock_coro.assert_has_calls(
            [
                call(*call_args_prefix, ({"type": "lineNavigationSpeed"},)),
                call(*call_args_prefix, ({"type": "lineNavigationSpeed", "value": responses_flat[1]},)),
            ]
        )
