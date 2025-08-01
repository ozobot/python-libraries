import sys

from .native import NativeDriver
from .web import WebDriver

__all__ = ["get_driver"]


def get_driver() -> type[NativeDriver]:
    if sys.platform == "emscripten":
        return WebDriver
    else:
        return NativeDriver
