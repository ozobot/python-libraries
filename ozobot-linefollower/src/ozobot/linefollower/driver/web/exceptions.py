from ozobot.common.exceptions import OzobotError


class WebDriverError(OzobotError): ...


class MemoryReadUnsuccessfulError(WebDriverError):
    def __init__(self, name: str, reason: str) -> None:
        super().__init__(f"Could not read virtual memory: '{reason}' on '{name}'")


class InvalidWebRobotSelectorError(WebDriverError):
    def __init__(self, selector_name: str) -> None:
        super().__init__(f"Web driver cannot select robots by their {selector_name}")


class MissingRobotSelectorError(WebDriverError):
    def __init__(self, selector_name: str) -> None:
        super().__init__(f"Cannot select robot, selector parameter missing: {selector_name}")
