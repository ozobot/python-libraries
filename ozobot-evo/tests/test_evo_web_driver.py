import typing
from unittest.mock import patch

import pytest
from ozobot.evo.driver.web import EvoWebDriver


@patch("ozobot.evo.driver.sys.platform", "emscripten")
def test_import_web() -> None:
    from ozobot.evo.driver import get_driver

    assert issubclass(get_driver(), EvoWebDriver)


@pytest.mark.parametrize(
    ["method_name", "method_args", "method_result", "rpc_name", "rpc_args", "rpc_result"],
    (
        (
            "play_audio",
            ("happy",),
            None,
            "playAudio",
            ("01010100",),
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
    with patch("ozobot.web.driver._rpcCoroutine") as mock_coro:
        mock_coro.return_value = rpc_result
        driver = EvoWebDriver(robot_name)
        method = getattr(driver, method_name)
        result = await method(*method_args)
        assert result == method_result

        mock_coro.assert_awaited_once_with(robot_name, rpc_name, rpc_args)
