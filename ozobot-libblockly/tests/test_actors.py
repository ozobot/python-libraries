from unittest.mock import AsyncMock, patch

import pydantic
import pytest
from ozobot.libblockly.actors.camera import CameraWebDriver
from ozobot.libblockly.actors.llm import LLMWebDriver
from ozobot.linefollower.datatypes import Direction, NamedColor

_RPC_COROUTINE_MODULE_PATH = "ozobot.linefollower.driver.web.driver._rpcCoroutine"


@patch(_RPC_COROUTINE_MODULE_PATH, new_callable=AsyncMock)
async def test_grab_image(rpc_mock: AsyncMock) -> None:
    rpc_mock.return_value = "data:image/png;base64,abc"

    image = await CameraWebDriver("camera").grab_image()

    assert image == "data:image/png;base64,abc"
    rpc_mock.assert_awaited_once_with("camera", "grabImage", ())


@patch(_RPC_COROUTINE_MODULE_PATH, new_callable=AsyncMock)
async def test_grab_image_invalid_response(rpc_mock: AsyncMock) -> None:
    rpc_mock.return_value = None

    with pytest.raises(pydantic.ValidationError):
        await CameraWebDriver("camera").grab_image()


@pytest.mark.parametrize(
    ("_type", "rpc_type", "rpc_response", "expected"),
    [
        (str, "string", "hello", "hello"),
        (int, "number", 3.0, 3),
        (float, "number", 1.5, 1.5),
        (bool, "boolean", True, True),
        (NamedColor, "surfaceColor", "red", NamedColor.RED),
        (Direction, "direction", "left", Direction.LEFT),
    ],
)
@patch(_RPC_COROUTINE_MODULE_PATH, new_callable=AsyncMock)
async def test_prompt_llm(
    rpc_mock: AsyncMock, _type: type, rpc_type: str, rpc_response: object, expected: object
) -> None:
    rpc_mock.return_value = rpc_response

    result = await LLMWebDriver("llm").prompt_llm(_type, "prompt", ["image"])

    assert result == expected
    rpc_mock.assert_awaited_once_with("llm", "prompt_llm", (["prompt"], ["image"], rpc_type))
