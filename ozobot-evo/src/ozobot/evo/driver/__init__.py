import sys
import typing

if typing.TYPE_CHECKING:
    from ozobot.evo.driver.native import EvoNativeDriver
    from ozobot.evo.driver.web import EvoWebDriver

    type EvoDriver = EvoWebDriver | EvoNativeDriver
else:
    type EvoDriver = typing.Any


def get_driver() -> type[EvoDriver]:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        from ozobot.evo.driver.web import EvoWebDriver

        return EvoWebDriver
    else:
        from ozobot.evo.driver.native import EvoNativeDriver

        return EvoNativeDriver
