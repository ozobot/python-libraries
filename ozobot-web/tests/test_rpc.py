import pytest
from ozobot.web.browser import _rpcCoroutine


async def test_rpc_coroutine_fails_on_desktop() -> None:
    with pytest.raises(NotImplementedError):
        _ = await _rpcCoroutine("obj", "fun", [])
