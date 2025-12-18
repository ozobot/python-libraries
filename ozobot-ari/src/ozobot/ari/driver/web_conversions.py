from ozobot.ari.webprotocol.types import TimeOfFlightResponse
from ozobot.linefollower.datatypes import TimeOfFlight


def time_of_flight_from_web(time_of_flight: TimeOfFlightResponse) -> TimeOfFlight:
    return TimeOfFlight(
        distance=time_of_flight.distance * 1000,
        deviation=time_of_flight.deviation * 1000,
    )
