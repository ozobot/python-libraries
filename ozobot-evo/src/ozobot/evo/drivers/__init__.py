from .driver import Driver as DriverCls, LEDMask
from .native import NativeDriver

__all__ = ["Driver", "LEDMask"]

Driver: type[DriverCls] = NativeDriver
