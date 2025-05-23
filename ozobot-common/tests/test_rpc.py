import contextlib
import typing

import pytest

from ozobot.common.rpc import RpcCall, RpcCallReentryError


@contextlib.asynccontextmanager
async def _generator() -> typing.AsyncIterator[tuple[str, typing.AsyncIterator[int]]]:
    async def _gen() -> typing.AsyncIterator[int]:
        yield 1
        yield 2
        yield 3

    yield "response", _gen()


async def test_rpc_call_await():
    rpc = RpcCall(_generator())
    ret = await rpc
    assert ret == "response"


async def test_rpc_iterate_cm():
    rpc = RpcCall(_generator())
    async with rpc as (resp, events):
        values = [await anext(events) for _ in range(3)]

        with pytest.raises(StopAsyncIteration):
            await anext(events)

    assert resp == "response"
    assert values == [1, 2, 3]


async def test_rpc_iterate_exhaust():
    rpc = RpcCall(_generator())
    async with rpc as (resp, events):
        values = [await anext(events) for _ in range(3)]

    assert resp == "response"
    assert values == [1, 2, 3]


async def test_rpc_prevent_reentry():
    rpc = RpcCall(_generator())
    await rpc

    with pytest.raises(RpcCallReentryError):
        await rpc

    with pytest.raises(RpcCallReentryError):
        async with rpc:
            ...
