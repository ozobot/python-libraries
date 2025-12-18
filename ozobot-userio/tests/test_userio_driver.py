import typing
from unittest.mock import patch

import pytest
from ozobot.linefollower.datatypes import Color, Colors, Direction
from ozobot.linefollower.driver.web import Rpc, rpctypes
from ozobot.userio.web import UserIoWebDriverComponent

_RPC_COROUTINE_MODULE_PATH = "ozobot.linefollower.driver.web.driver._rpcCoroutine"


@pytest.mark.parametrize(
    ["method_name", "method_args", "method_result", "rpc_name", "rpc_args", "rpc_result"],
    (
        (
            "print",
            {"message": "hello world!"},
            None,
            "userIoPrint",
            ("hello world!",),
            rpctypes.ValidatedBool(root=True),
        ),
        (
            "alert",
            {"message": "hello world!", "cancellable": True},
            None,
            "userIoAlert",
            ("hello world!", True),
            rpctypes.ValidatedBool(root=True),
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
        rpc = Rpc(robot_name)
        driver = UserIoWebDriverComponent(rpc)
        method = getattr(driver, method_name)
        result = await method(**method_args)
        assert result == method_result

        mock_coro.assert_awaited_once_with(robot_name, rpc_name, rpc_args)


@pytest.mark.parametrize(
    ["method_type", "method_options", "method_result", "rpc_type", "rpc_options", "rpc_response"],
    (
        (
            int,
            (
                1,
                2,
                3,
            ),
            1,
            "number",
            [1, 2, 3],
            1,
        ),
        (
            bool,
            (
                True,
                False,
            ),
            True,
            "boolean",
            [True, False],
            True,
        ),
        (
            bool,
            (
                True,
                False,
            ),
            False,
            "boolean",
            [True, False],
            False,
        ),
        (
            float,
            (
                0.1,
                0.2,
                0.3,
            ),
            0.1,
            "number",
            [0.1, 0.2, 0.3],
            0.1,
        ),
        (
            str,
            (
                "A",
                "B",
                "C",
            ),
            "B",
            "string",
            ["A", "B", "C"],
            "B",
        ),
        (
            Color,
            (
                Colors.BLACK,
                Colors.BLUE,
                Colors.RED,
            ),
            Colors.BLUE,
            "color",
            [
                "Black",
                "Blue",
                "Red",
            ],
            "Blue",
        ),
        (
            Direction,
            (
                Direction.LEFT,
                Direction.RIGHT,
            ),
            Direction.RIGHT,
            "direction",
            ["Left", "Right"],
            "Right",
        ),
    ),
)
async def test_user_io_prompt(
    method_type: type[typing.Any],
    method_options: list[typing.Any],
    method_result: typing.Any,
    rpc_type: str,
    rpc_options: list[typing.Any],
    rpc_response: typing.Any,
) -> None:
    robot_name = "robot1"
    message = "Hello world!"
    with patch(_RPC_COROUTINE_MODULE_PATH) as mock_coro:
        mock_coro.return_value = rpc_response
        rpc = Rpc(robot_name)
        driver = UserIoWebDriverComponent(rpc)

        result = await driver.prompt(message, method_type, method_options, cancellable=False)
        assert result == method_result

        mock_coro.assert_awaited_once_with(robot_name, "userIoPrompt", (message, rpc_type, rpc_options, False))
