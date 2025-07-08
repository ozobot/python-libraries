from ozobot.common.exceptions import OzobotError


class BLEError(OzobotError):
    """Base BLE error"""


class DeviceNotFoundError(BLEError):
    def __init__(self):
        super().__init__("No device matching given filters found")


class DeviceDescriptionError(BLEError):
    def __init__(self, reason: str):
        super().__init__(f"Device description does not match the expected one: {reason}")


class NoFilterSpecifiedError(BLEError):
    def __init__(self):
        super().__init__("No BLE filter given")
