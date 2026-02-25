import asyncio
import contextlib
import functools
import typing

_runner = asyncio.Runner()


def _ensure_no_running_loop() -> None:
    loop = None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    if loop:
        raise RuntimeError("the function cannot be called from within a running event loop")


def as_sync[**P, T](func: typing.Callable[P, typing.Awaitable[T]]) -> typing.Callable[P, T]:
    if func is None:
        raise Exception("Deceorator does not support arguments, remove parentheses")

    @functools.wraps(func)
    def _inner(*args, **kwargs):
        _ensure_no_running_loop()
        return _runner.run(func(*args, **kwargs))

    return functools.update_wrapper(_inner, func)


@contextlib.contextmanager
def as_sync_context_manager[T](async_context_manager: contextlib.AbstractAsyncContextManager[T]) -> typing.Iterator[T]:
    _ensure_no_running_loop()
    exit_stack = contextlib.AsyncExitStack()
    try:
        yield _runner.run(exit_stack.enter_async_context(async_context_manager))
    finally:
        _runner.run(exit_stack.aclose())
