from __future__ import annotations

import asyncio
import sys
import typing

P = typing.ParamSpec("P")
R = typing.TypeVar("R")


def run(
    coro_factory: typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, R]],
    *args: typing.Any,
    **kwargs: typing.Any,
) -> R:
    try:
        return asyncio.run(coro_factory(*args, **kwargs))
    except KeyboardInterrupt:
        sys.exit(130)
