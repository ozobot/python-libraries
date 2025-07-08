class BleError(Exception): ...


class NoFilterSpecifiedError(BleError):
    def __init__(self):
        super().__init__("No BLE filter given")
