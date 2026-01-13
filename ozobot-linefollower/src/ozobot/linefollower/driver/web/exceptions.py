from ozobot.common.exceptions import OzobotError
from ozobot.linefollower.datatypes import Color


class WebDriverError(OzobotError): ...

class InvalidWebRobotSelectorError(WebDriverError):
    """Invalid robot selector is used for the web driver."""

    def __init__(self, selector_name: str) -> None:
        super().__init__(f"Web driver cannot select robots by their {selector_name}")


class MissingRobotSelectorError(WebDriverError):
    """Required robot selector parameter is missing."""

    def __init__(self, selector_name: str) -> None:
        super().__init__(f"Cannot select robot, selector parameter missing: {selector_name}")


class InvalidColorCodeError(WebDriverError):
    """Unsupported color code is encountered."""

    def __init__(self, color: Color | None) -> None:
        super().__init__(f"Unsupported color code color: {color}")
