import pytest
from ozobot.ari.protocol import base, notification, request, response, serialization, types
from ozobot.ari.protocol.methods import REQUEST_METHODS
from ozobot.ari.protocol.serialization import deserialize
from pydantic.type_adapter import TypeAdapter

# n-tuple of messages to verify (element 0), with its expected deserialized form (element 1)
#     and originating request (element 2) in case of responses and notifications (needed to dispatch the type)
messages: tuple[tuple[base.Message, str, type[base.Request] | None], ...] = (
    (
        base.Cancellation(id=1, code=0, message="test reason"),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/cancellation","code":0,"message":"test reason"}',
        None,
    ),
    (
        request.MoveStraightRequest(id=1, params=request.MoveStraightRequestParams(distance=1, speed=2)),
        '{"id":1,"jsonrpc":"2.0","method":"MoveStraight","params":{"distance":1.0,"speed":2.0}}',
        None,
    ),
    (
        response.MoveStraightResponse(id=1, result=response.MoveStraightResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.MoveStraightRequest,
    ),
    (
        notification.MotionNotification(
            id=1, result=notification.MotionNotificationBody(max_speed=1, overshot_distance=2, overshot_time=3)
        ),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/notification","result":{"maxSpeed":1.0,"overshotDistance":2.0,"overshotTime":3}}',
        request.MoveStraightRequest,
    ),
    (
        request.RotateRequest(id=1, params=request.RotateRequestParams(angle=90, speed=0.5)),
        '{"id":1,"jsonrpc":"2.0","method":"Rotate","params":{"angle":90.0,"speed":0.5}}',
        None,
    ),
    (
        response.RotateResponse(id=1, result=response.RotateResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.RotateRequest,
    ),
    (
        request.VelocityRequest(
            id=1, params=request.VelocityRequestParams(expiration=60, linear_speed=0.5, rotation_speed=0.2)
        ),
        '{"id":1,"jsonrpc":"2.0","method":"Velocity","params":{"expiration":60,"linearSpeed":0.5,"rotationSpeed":0.2}}',
        None,
    ),
    (
        response.VelocityResponse(id=1, result=response.VelocityResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.VelocityRequest,
    ),
    (
        request.LineNavigationRequest(
            id=1,
            params=request.LineNavigationRequestParams(direction="Straight", follow="Follow", detect_color_codes=True),
        ),
        '{"id":1,"jsonrpc":"2.0","method":"LineNavigation","params":{"direction":"Straight","follow":"Follow","detectColorCodes":true}}',
        None,
    ),
    (
        response.LineNavigationResponse(id=1, result=response.LineNavigationResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"success"}}',
        request.LineNavigationRequest,
    ),
    (
        notification.LineNavigationNotification(
            id=1,
            result=notification.LineNavigationColorNotificationBody(
                color_code=["red", "green", "red"],
            ),
        ),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/notification","result":{"color_code": ["red", "green", "red"]}}',
        request.LineNavigationRequest,
    ),
    (
        notification.LineNavigationNotification(
            id=1,
            result=types.Intersection(backward=True, right=True),
        ),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/notification","result":{"Backward": true, "Right": true}}',
        request.LineNavigationRequest,
    ),
    (
        request.SetLEDRequest(
            id=1,
            params=request.SetLEDRequestParams(
                lights=types.Lights(back=True),
                color=types.Color(red=255, green=255, blue=255, name="custom"),
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","method":"SetLED","params":{"lights":{"back":true},"color":{"red":255,"green":255,"blue":255}}}',
        None,
    ),
    (
        response.SetLEDResponse(id=1, result=response.SetLEDResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.SetLEDRequest,
    ),
    (
        request.PlayToneRequest(
            id=1, params=request.PlayToneRequestParams(frequency=440, duration=1000, volume=50, sampling_rate=44100)
        ),
        '{"id":1,"jsonrpc":"2.0","method":"PlayTone","params":{"frequency":440,"duration":1000,"volume":50,"samplingRate":44100}}',
        None,
    ),
    (
        response.PlayToneResponse(id=1, result=response.PlayToneResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.PlayToneRequest,
    ),
    (
        request.PlaySoundRequest(id=1, params=request.PlaySoundRequestParams(name="sound-name", loop=True, volume=1)),
        '{"id":1,"jsonrpc":"2.0","method":"PlaySound","params":{"name":"sound-name","loop":true,"volume":1}}',
        None,
    ),
    (
        response.PlaySoundResponse(id=1, result=response.PlaySoundResponseBody(type="success")),
        '{"id":1,"jsonrpc":"2.0","result":{"type": "success"}}',
        request.PlaySoundRequest,
    ),
    (
        request.TimeOfFlightRequest(id=1, params=request.TimeOfFlightRequestParams(latency=10)),
        '{"id":1,"jsonrpc":"2.0","method":"TimeOfFlight","params":{"latency":10}}',
        None,
    ),
    (
        notification.TimeOfFlightNotification(
            id=1,
            result=notification.TimeOfFlightNotificationBody(
                distance=1.0, deviation=2.0, ambient_rate=3.0, signal_rate=4.0, active_count=5, timestamp=6
            ),
        ),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/notification","result":{"distance":1.0,"deviation":2.0,"ambientRate":3.0,"signalRate":4.0,"activeCount":5,"timestamp":6}}',
        request.TimeOfFlightRequest,
    ),
)


def _get_type_adapter(message: base.Message, request_type: type[base.Request] | None) -> TypeAdapter[base.Message]:
    # we would normally have the context from sending the request, but we don't have that in the test
    if request_type:
        method = REQUEST_METHODS[request_type]  # type: ignore[index]
        return TypeAdapter[base.Message](method.response | method.notification)  # type: ignore[operator]
    else:
        return TypeAdapter[base.Message](type(message))


@pytest.mark.parametrize(
    "message,request_type",
    [(m[0], m[2]) for m in messages],
    ids=[m[0].__class__.__name__ for m in messages],
)
def test_serialization_identity(message: base.Message, request_type: type[base.Request] | None) -> None:
    adapter = _get_type_adapter(message, request_type)
    assert deserialize(serialization.serialize(message), adapter) == message


@pytest.mark.parametrize(
    "message,serialized,request_type",
    messages,
    ids=[m[0].__class__.__name__ for m in messages],
)
def test_deserialization(message: base.Message, serialized: str, request_type: type[base.Request]) -> None:
    adapter = _get_type_adapter(message, request_type)
    assert deserialize(serialized, adapter) == message
