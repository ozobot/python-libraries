import pytest
from ozobot.ari.protocol import base, memread, memwrite, notification, request, response, serialization, types
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
                colors=["red", "green", "red"],
            ),
        ),
        '{"id":1,"jsonrpc":"com/ozobot/jsonrpc/2.0/notification","result":{"colors": ["red", "green", "red"]}}',
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
    (
        memread.MemReadRequest(id=1, params=memread.MemReadRequestParams(segment="someSegment")),
        '{"id": 1,"jsonrpc":"2.0","params":{"segment":"someSegment"}}',
        None,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseColorSensor(
                red=120,
                green=65,
                blue=200,
                mixed=75,
                color=127,
                has_light_source=True,
                saturation_analog=False,
                saturation_digital=True,
                is_valid=True,
                timestamp=1627849200,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"color","red":120,"green":65,"blue":200,"mixed":75,"color":127,"hasLightSource":true,"saturationAnalog":false,"saturationDigital":true,"isValid":true,"timestamp":1627849200}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLineSensorsCalibration(
                black=[1, 2, 3],
                white=[4, 5, 6],
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"lineSensorsCalibration","black":[1,2,3],"white":[4,5,6]}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLineSensors(
                position=1.0,
                width=2.0,
                under_left=True,
                under_right=False,
                under_all=True,
                active_sensors=[True, False],
                timestamp=123,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"lineSensors","position":1.0,"width":2.0,"underLeft":true,"underRight":false,"underAll":true,"activeSensors":[true,false],"timestamp":123}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLineSensorsRaw(
                sensors=[10, 20, 30],
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"lineSensorsRaw","sensors":[10,20,30]}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponsePickup(
                is_picked_up=True,
                timestamp=456,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"pickup","isPickedUp":true,"timestamp":456}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponsePosition(
                origin_count=5,
                x=1.1,
                y=2.2,
                angle_x=0.3,
                angle_y=0.4,
                timestamp=789,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"position","originCount":5,"x":1.1,"y":2.2,"angleX":0.3,"angleY":0.4,"timestamp":789}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseProximity(
                value=10,
                timestamp=101,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"proximity","value":10,"timestamp":101}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseReadIr(
                message=5,
                intensity=10,
                timestamp=202,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"readIr","message":5,"intensity":10,"timestamp":202}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseSentIr(
                message=6,
                active=False,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"sentIr","message":6,"active":false}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseVersion(
                ir=types.VersionPair(
                    bundled=types.Version(version="1.0", hash="abc"),
                    current=types.Version(version="1.1", hash="def"),
                ),
                sensor=types.VersionPair(
                    bundled=types.Version(version="2.0", hash="ghi"),
                    current=types.Version(version="2.1", hash="jkl"),
                ),
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"version","ir":{"bundled":{"version":"1.0","hash":"abc"},"current":{"version":"1.1","hash":"def"}},"sensor":{"bundled":{"version":"2.0","hash":"ghi"},"current":{"version":"2.1","hash":"jkl"}}}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseWheels(
                count_left=100,
                count_right=200,
                timestamp=303,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"wheels","countLeft":100,"countRight":200,"timestamp":303}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseHardwareState(
                sensor="sensor1",
                ir="ir1",
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"state","sensor":"sensor1","ir":"ir1"}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLog(
                level=2,
                message="log message",
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"log","level":2,"message":"log message"}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponsePickupADC(
                adc=[10, 20, 30],
                timestamp=404,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"pickupADC","adc":[10,20,30],"timestamp":404}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLineColor(
                color="Red",
                light_source=True,
                timestamp=505,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"lineColor","color":"Red","lightSource":true,"timestamp":505}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseSurfaceColor(
                color="Blue",
                counter=7,
                light_source=False,
                timestamp=606,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"surfaceColor","color":"Blue","counter":7,"lightSource":false,"timestamp":606}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseEncoderDACReference(
                reference=[0.1, 0.2, 0.3],
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"encoderDACReference","reference":[0.1,0.2,0.3]}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseEncoderDACReferenceRange(
                ranges=[
                    memread.FloatRange(start=0.0, end=1.0),
                    memread.FloatRange(start=1.0, end=2.0),
                ],
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"encoderDACReferenceRange","ranges":[{"start":0.0,"end":1.0},{"start":1.0,"end":2.0}]}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLinearVelocity(
                velocity=3.14,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"linearVelocity","velocity":3.14}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseEncoderDACReference(
                reference=[0.1, 0.2, 0.3],
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"encoderDACReference","reference":[0.1,0.2,0.3]}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseLinearVelocity(
                velocity=3.14,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"linearVelocity","velocity":3.14}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponseColorSensorCalibration(
                red=memread.FloatRange(start=0.0, end=1.0),
                green=memread.FloatRange(start=1.0, end=2.0),
                blue=memread.FloatRange(start=2.0, end=3.0),
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"colorSensorCalibration","red":{"start":0.0,"end":1.0},"green":{"start":1.0,"end":2.0},"blue":{"start":2.0,"end":3.0}}}',
        memread.MemReadRequest,
    ),
    (
        memread.MemReadResponse(
            id=1,
            result=memread.MemReadResponsePickupThreshold(
                threshold=10,
            ),
        ),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"pickupThreshold","threshold":10}}',
        memread.MemReadRequest,
    ),
    (
        memwrite.MemWriteRequest(
            id=1, params=memwrite.MemWriteRequestIrLeftParams(segment="irLeft", active=True, message=42)
        ),
        '{"id":1,"jsonrpc":"2.0","method":"MemWrite","params":{"segment":"irLeft","active":true,"message":42}}',
        None,
    ),
    (
        memwrite.MemWriteRequest(
            id=1, params=memwrite.MemWriteRequestIrRightParams(segment="irRight", active=False, message=43)
        ),
        '{"id":1,"jsonrpc":"2.0","method":"MemWrite","params":{"segment":"irRight","active":false,"message":43}}',
        None,
    ),
    (
        memwrite.MemWriteRequest(
            id=1, params=memwrite.MemWriteRequestLineFollowingSpeedParams(segment="lineFollowingSpeed", value=1.5)
        ),
        '{"id":1,"jsonrpc":"2.0","method":"MemWrite","params":{"segment":"lineFollowingSpeed","value":1.5}}',
        None,
    ),
    (
        memwrite.MemWriteResponse(id=1, result=memwrite.MemWriteResponseBody(type="finished", success=True)),
        '{"id":1,"jsonrpc":"2.0","result":{"type":"finished","success":true}}',
        memwrite.MemWriteRequest,
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
