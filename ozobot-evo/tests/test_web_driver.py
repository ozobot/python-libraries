from unittest.mock import patch

from ozobot.evo.driver.web import WebDriver


@patch("ozobot.evo.driver.sys.platform", "emscripten")
def test_import_web() -> None:
    from ozobot.evo.driver import get_driver

    assert issubclass(get_driver(), WebDriver)
