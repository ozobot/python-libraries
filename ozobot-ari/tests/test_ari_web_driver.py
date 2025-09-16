from unittest.mock import patch

from ozobot.ari.driver.web import AriWebDriver


@patch("ozobot.ari.driver.sys.platform", "emscripten")
def test_import_web() -> None:
    from ozobot.ari.driver import get_driver

    assert issubclass(get_driver(), AriWebDriver)
