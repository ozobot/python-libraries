class BLEError(Exception): ...


class DeviceNotFoundError(BLEError): ...


class DeviceDescriptionError(BLEError):
    def __init__(self, reason: str):
        super().__init__(f"Device description does not match the expected one: {reason}")


class NoFilterSpecifiedError(BLEError):
    def __init__(self):
        super().__init__("No BLE filter given")
