import functools
import logging
import typing

_TUnbound = typing.TypeVar("_TUnbound")
_PUnbound = typing.ParamSpec("_PUnbound")

_logger = logging.getLogger(__name__)


def log_errors(func: typing.Callable[_PUnbound, _TUnbound]) -> typing.Callable[_PUnbound, _TUnbound]:
    if func is None:
        raise Exception("Deceorator does not support arguments, remove parentheses")

    def _inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _logger.warning("Caught error in a callback: cbk=%s, error=%s", func.__name__, e)

    return functools.update_wrapper(_inner, func)
