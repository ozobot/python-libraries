from ozobot.linefollower.driver.web import rpctypes


class TimeOfFlightResponse(rpctypes.BaseResponse):
    distance: float
    deviation: float
    timestamp: int
