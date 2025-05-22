from unittest.mock import patch

from ozobot.evo.drivers.web import WebDriver


@patch("ozobot.evo.drivers.sys.platform", "emscripten")
def test_import_web() -> None:
    from ozobot.evo.drivers import get_driver

    assert issubclass(get_driver(), WebDriver)
