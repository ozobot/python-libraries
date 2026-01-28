import sys
import typing

if typing.TYPE_CHECKING:
    from ozobot.ari.driver.native import AriNativeDriver
    from ozobot.ari.driver.web import AriWebDriver

    type AriDriver = AriWebDriver | AriNativeDriver
else:
    type AriDriver = typing.Any


def get_driver() -> type[AriDriver]:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        from ozobot.ari.driver.web import AriWebDriver

        return AriWebDriver
    else:
        raise NotImplementedError("Ari native driver is not yet implemented")
        from ozobot.ari.driver.native import AriNativeDriver

        return AriNativeDriver
