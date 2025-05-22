import sys

from .driver import Driver as Driver, LEDMask
from .native import NativeDriver
from .web import WebDriver

__all__ = ["get_driver", "LEDMask"]


def get_driver() -> type[Driver]:
    if sys.platform == "emscripten":
        return WebDriver
    else:
        return NativeDriver
