import pytest
from ozobot.protocol_common.rpc import RpcCall, RpcCallReentryError


async def _generator() -> int:
    yield 1
    yield 2
    yield 3


async def test_rpc_call_await():
    rpc = RpcCall(_generator())
    ret = await rpc
    assert ret == 1


async def test_rpc_iterate_cm():
    gen = _generator()
    rpc = RpcCall[int, int](gen)
    async with rpc as it:
        values = [await anext(it) for _ in range(2)]

    with pytest.raises(StopAsyncIteration):
        await anext(gen)

    assert values == [1, 2]
    

async def test_rpc_iterate_exhaust():
    rpc = RpcCall[int, int](_generator())
    async with rpc as it:
        values = [await anext(it) for _ in range(3)]

    assert values == [1, 2, 3]
    

async def test_rpc_prevent_reentry():
    rpc = RpcCall[int, int](_generator())
    await rpc

    with pytest.raises(RpcCallReentryError):
        await rpc

    with pytest.raises(RpcCallReentryError):
        async with rpc:
            ...
    
    
