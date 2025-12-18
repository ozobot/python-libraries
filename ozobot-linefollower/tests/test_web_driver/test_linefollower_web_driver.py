import math
import typing
from unittest.mock import call, patch

import pytest
from ozobot.linefollower.datatypes import Colors, Direction, LEDMask
from ozobot.linefollower.driver.web import LineFollowerWebDriver

_RPC_COROUTINE_MODULE_PATH = "ozobot.linefollower.driver.web.driver._rpcCoroutine"


@pytest.mark.parametrize(
    ["method_name", "method_args", "method_result", "rpc_name", "rpc_args", "rpc_result"],
    (
        (
            "move",
            (100, 200),
            None,
            "move",
            (0.1, 0.2),
            None,
        ),
        (
            "rotate",
            (90, 10),
            None,
            "rotate",
            (math.pi / 2, math.radians(10)),
            None,
        ),
        (
            "velocity",
            (100, 90, 1000),
            None,
            "velocity",
            (0.1, math.pi / 2, 1000),
            None,
        ),
        (
            "play_tone",
            (440, 500, 50),
            None,
            "playTone",
            (440, 500),
            None,
        ),
        (
            "set_led",
            (LEDMask.TOP | LEDMask.FRONT_LEFT, 255, 128, 0),
            None,
            "setLed",
            ({"top": True, "front_left": True}, 255, 128, 0),
            None,
        ),
        (
            "line_navigation",
            (Direction.STRAIGHT, True),
            None,
            "lineNavigation",
            ("Straight", True),
            None,
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
    with patch(_RPC_COROUTINE_MODULE_PATH) as mock_coro:
        mock_coro.return_value = rpc_result
        driver = LineFollowerWebDriver(robot_name)
        method = getattr(driver, method_name)
        result = await method(*method_args)
        assert result == method_result

        mock_coro.assert_awaited_once_with(robot_name, rpc_name, rpc_args)


async def test_mem_read():
    robot_name = "robot1"
    with patch(_RPC_COROUTINE_MODULE_PATH) as mock_coro:
        mock_coro.return_value = 0.5
        driver = LineFollowerWebDriver(robot_name)

        speed = await driver.memory.line_following_speed.read()
        assert speed == 500

        mock_coro.assert_awaited_once_with(robot_name, "memory.lineFollowingSpeed.read", tuple())


async def test_mem_write():
    robot_name = "robot1"
    with patch(_RPC_COROUTINE_MODULE_PATH) as mock_coro:
        mock_coro.return_value = None
        driver = LineFollowerWebDriver(robot_name)

        await driver.memory.line_following_speed.write(500)

        mock_coro.assert_awaited_once_with(robot_name, "memory.lineFollowingSpeed.write", (0.5,))


async def test_mem_watch_structure() -> None:
    robot_name = "robot1"
    num_data = 3

    responses_flat = [
        {"value": "Red", "timestamp": 1},
        {"value": "Black", "timestamp": 2},
        {"value": "Blue", "timestamp": 3},
    ]

    rpc_responses = [
        [responses_flat[0], responses_flat[1]],
        [
            responses_flat[2],
        ],
    ]
    with patch(_RPC_COROUTINE_MODULE_PATH, side_effect=rpc_responses) as mock_coro:
        driver = LineFollowerWebDriver(robot_name)

        async with driver.memory.line_color.watch() as it:
            samples = [await anext(it) for _ in range(num_data)]
            data = [sample.value for sample in samples]
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
            "memory.lineColor.wait",
        )

        mock_coro.assert_has_calls(
            [
                call(*call_args_prefix, (None,)),
                call(*call_args_prefix, ({"value": responses_flat[1]},)),
            ]
        )


async def test_mem_watch_simple_type() -> None:
    robot_name = "robot1"
    num_data = 3

    responses_flat = [
        {"timestamp": 0, "value": 0.1},
        {"timestamp": 0, "value": 0.2},
        {"timestamp": 0, "value": 0.3},
    ]

    rpc_responses = [
        [responses_flat[0], responses_flat[1]],
        [
            responses_flat[2],
        ],
    ]
    with patch(_RPC_COROUTINE_MODULE_PATH, side_effect=rpc_responses) as mock_coro:
        driver = LineFollowerWebDriver(robot_name)

        async with driver.memory.line_following_speed.watch() as it:
            samples = [await anext(it) for _ in range(num_data)]
            data = [sample.value for sample in samples]
        assert len(data) == num_data
        assert data == [100, 200, 300]

        # we expect the calls to contain the property name in the first call
        # and the property name plus previous value in the consequent calls
        call_args_prefix = (
            robot_name,
            "memory.lineFollowingSpeed.wait",
        )

        mock_coro.assert_has_calls(
            [
                call(*call_args_prefix, (None,)),
                call(*call_args_prefix, ({"value": responses_flat[1]},)),
            ]
        )
