import abc


class OzobotUnitError(Exception, abc.ABC): ...


class IncompatiblePhysicalDomainError(OzobotUnitError):
    def __init__(self, actual: str, expected: str):
        super().__init__(f"Incompatible physical domain: {actual} is not compatible with {expected}")
