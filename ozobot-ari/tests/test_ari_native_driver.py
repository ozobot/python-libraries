import asyncio
import contextlib
import math
import typing
from unittest.mock import ANY, Mock, PropertyMock, patch

import pytest
from ozobot.ari.driver.native import AriNativeDriver
from ozobot.ari.protocol import memread, memwrite, methods, notification, request, response, types
from ozobot.linefollower.datatypes import (
    ColorCode,
    Direction,
    LEDMask,
    NamedColor,
    Sample,
    SampleWithoutTimestamp,
)


def _create_query(response=None, notifications=None):
    query_mock = Mock()
    evt = asyncio.Event()

    class _MockExecutor:
        @contextlib.asynccontextmanager
        async def execute(self, query, *args, **kwargs):
            query_mock(query._request, query._method)

            async def _resp():
                if notifications:
                    await evt.wait()
                if response:
                    result = response
                else:
                    result = Mock(type="finished")

                return Mock(result=result)

            async def _notifications():
                for n in notifications:
                    yield n

                evt.set()

            ret = Mock()
            type(ret).response = PropertyMock(side_effect=lambda: _resp())
            ret.notifications = _notifications() if notifications else None
            yield ret

    return _MockExecutor(), query_mock


@patch("ozobot.ari.driver.sys.platform", "linux")
def test_import_native() -> None:
    from ozobot.ari.driver import get_driver

    assert issubclass(get_driver(), AriNativeDriver)


async def test_open_ble() -> None:
    async def _get_rk_mock(*args, out_queue, **kwargs):
        await out_queue.put("anvil.abcdefgh")

    async def _blocking_receive_str():
        await asyncio.Future()
        yield

    channel_mock_obj = Mock()
    channel_mock_obj.receive_str = _blocking_receive_str
    channel_mock_obj.send = Mock()

    with patch("ozobot.ari.driver.native._get_routing_key_from_ble", side_effect=_get_rk_mock) as routing_key_mock:
        with patch("ozobot.ari.driver.native._create_webrtc_channel", return_value=channel_mock_obj) as channel_mock:
            async with AriNativeDriver.open(address="11:22:33:44:55:66", id="1234", name="EVO-ABCDEF") as driver:
                assert isinstance(driver, AriNativeDriver)
                routing_key_mock.assert_called_with(
                    address="11:22:33:44:55:66", id="1234", name="EVO-ABCDEF", out_queue=ANY
                )
                channel_mock.assert_called_once_with("anvil.abcdefgh")


async def test_open_connection_key() -> None:
    async def _blocking_receive_str():
        await asyncio.Future()
        yield

    channel_mock_obj = Mock()
    channel_mock_obj.receive_str = _blocking_receive_str
    channel_mock_obj.send = Mock()

    with patch("ozobot.ari.driver.native._create_webrtc_channel", return_value=channel_mock_obj) as channel_mock:
        async with AriNativeDriver.open(connection_key="1234abcd") as driver:
            assert isinstance(driver, AriNativeDriver)
            channel_mock.assert_called_once_with("anvil.1234abcd")


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        (
            "move",
            "MoveStraight",
            [200, 100],
            (
                request.MoveStraightRequest(id=0, params=request.MoveStraightRequestParams(distance=0.2, speed=0.1)),
                methods.MOVE_STRAIGHT,
            ),
        ),
        (
            "rotate",
            "Rotate",
            [90, 10],
            (
                request.RotateRequest(id=0, params=request.RotateRequestParams(angle=90, speed=10)),
                methods.ROTATE,
            ),
        ),
        (
            "velocity",
            "Velocity",
            [100, 10, 3000],
            (
                request.VelocityRequest(
                    id=0,
                    params=request.VelocityRequestParams(
                        linear_speed=0.1, rotation_speed=math.radians(10), expiration=3
                    ),
                ),
                methods.VELOCITY,
            ),
        ),
        (
            "play_tone",
            "PlayTone",
            [1, 2000],
            (
                request.PlayToneRequest(id=0, params=request.PlayToneRequestParams(frequency=1, duration=2)),
                methods.PLAY_TONE,
            ),
        ),
        (
            "play_audio_asset",
            "ExecuteFile",
            ["happy"],
            (
                request.PlaySoundRequest(id=0, params=request.PlaySoundRequestParams(name="happy", loop=False)),
                methods.PLAY_SOUND,
            ),
        ),
        (
            "user_io_print",
            "UserIoPrint",
            ["Hello World"],
            (
                request.UserIoPrintRequest(id=0, params=request.UserIoPrintRequestParams(message="Hello World")),
                methods.USER_IO_PRINT,
            ),
        ),
        (
            "user_io_alert",
            "UserIoAlert",
            ["Alert Message"],
            (
                request.UserIoAlertRequest(
                    id=0, params=request.UserIoAlertRequestParams(message="Alert Message", cancellable=False)
                ),
                methods.USER_IO_ALERT,
            ),
        ),
    ],
)
async def test_command_with_response(
    function_name: str, command_name: str, command_parameters: list[typing.Any], rpc_parameters: dict[str, typing.Any]
) -> None:
    executor_mock, query_mock = _create_query()
    driver = AriNativeDriver(executor_mock)

    function = getattr(driver, function_name)
    await function(*command_parameters)
    query_mock.assert_called_once_with(*rpc_parameters)


@pytest.mark.parametrize(
    "follow_bool,follow_protocol",
    [(True, "Follow"), (False, "DoNotFollow")],
    ids=lambda x: repr(x),
)
async def test_line_navigation(follow_bool: bool, follow_protocol: typing.Literal["Follow", "DoNotFollow"]) -> None:
    executor_mock, query_mock = _create_query(
        notifications=[
            notification.LineNavigationNotification(id=0, result=types.Intersection(back=True)),
            notification.LineNavigationNotification(
                id=0, result=notification.LineNavigationColorNotificationBody(colors=["Red", "Black", "Blue"])
            ),
        ]
    )
    driver = AriNativeDriver(executor_mock)

    async with driver.memory.intersection.watch() as intersection_it, driver.memory.color_code.watch() as cc_it:
        await driver.line_navigation(Direction.LEFT, follow_bool)

        assert await anext(aiter(intersection_it)) == SampleWithoutTimestamp(Direction.BACKWARD)
        assert await anext(aiter(cc_it)) == SampleWithoutTimestamp(
            ColorCode(colors=(NamedColor.RED, NamedColor.BLACK, NamedColor.BLUE)),
        )

    query_mock.assert_called_once_with(
        request.LineNavigationRequest(
            id=0,
            params=request.LineNavigationRequestParams(
                direction="Left", follow=follow_protocol, detect_color_codes=True
            ),
        ),
        methods.LINE_NAVIGATION,
    )


async def test_request_id_counter() -> None:
    executor_mock, query_mock = _create_query()
    driver = AriNativeDriver(executor_mock)
    await driver.move(0, 0)
    await driver.move(1, 1)

    assert query_mock.call_args_list[0].args[0].id == 0
    assert query_mock.call_args_list[1].args[0].id == 1


@pytest.mark.parametrize(
    ["command_lights", "rpc_lights"],
    [
        (LEDMask.FRONT_CENTER, types.Lights(frontCenter=True)),
        (LEDMask.FRONT_LEFT_CENTER, types.Lights(frontLeftCenter=True)),
        (LEDMask.FRONT_RIGHT_CENTER, types.Lights(frontRightCenter=True)),
        (LEDMask.FRONT_RIGHT, types.Lights(frontRight=True)),
        (LEDMask.FRONT_LEFT, types.Lights(frontLeft=True)),
        (LEDMask.TOP, types.Lights(top=True)),
        (
            LEDMask.FRONT_CENTER | LEDMask.FRONT_RIGHT,
            types.Lights(frontCenter=True, frontRight=True),
        ),
    ],
)
async def test_set_led(command_lights: LEDMask, rpc_lights: types.Lights) -> None:
    executor_mock, query_mock = _create_query()
    driver = AriNativeDriver(executor_mock)

    await driver.set_led(command_lights, 0.1, 0.2, 0.3)

    query_mock.assert_called_once_with(
        request.SetLEDRequest(
            id=0,
            params=request.SetLEDRequestParams(
                lights=rpc_lights,
                color=types.Color(red=25, green=51, blue=76),
            ),
        ),
        methods.SET_LED,
    )


async def test_native_data_access_read() -> None:
    executor_mock, query_mock = _create_query(response=memread.MemReadResponseLinearVelocity(velocity=1.23))
    driver = AriNativeDriver(executor_mock)

    assert await driver.memory.line_following_speed.read() == 1230

    query_mock.assert_called_with(
        memread.MemReadRequest(
            id=0,
            params=memread.MemReadRequestParams(
                segment="lineFollowingSpeed",
            ),
        ),
        methods.MEM_READ,
    )


async def test_native_data_access_write() -> None:
    executor_mock, query_mock = _create_query()
    driver = AriNativeDriver(executor_mock)

    await driver.memory.line_following_speed.write(1230)

    query_mock.assert_called_with(
        memwrite.MemWriteRequest(
            id=0,
            params=memwrite.MemWriteRequestLineFollowingSpeedParams(
                segment="lineFollowingSpeed",
                value=1.23,
            ),
        ),
        methods.MEM_WRITE,
    )


@pytest.mark.parametrize(
    ["prompt_type", "options", "protocol_options", "response_body", "expected_result"],
    [
        (
            str,
            ["option1", "option2"],
            ["option1", "option2"],
            response.UserIoPromptStringResponseBody(value="option1"),
            "option1",
        ),
        (
            int,
            [1, 2, 3],
            [1, 2, 3],
            response.UserIoPromptNumberResponseBody(value=2),
            2,
        ),
        (
            float,
            [1.5, 2.5, 3.5],
            [1.5, 2.5, 3.5],
            response.UserIoPromptNumberResponseBody(value=2.5),
            2.5,
        ),
        (
            bool,
            [True, False],
            [True, False],
            response.UserIoPromptBooleanResponseBody(value=True),
            True,
        ),
        (
            NamedColor,
            [NamedColor.RED, NamedColor.GREEN],
            ["Red", "Green"],
            response.UserIoPromptSurfaceColorResponseBody(value="Red"),
            NamedColor.RED,
        ),
        (
            Direction,
            [Direction.LEFT, Direction.RIGHT],
            ["Left", "Right"],
            response.UserIoPromptDirectionResponseBody(value="Left"),
            Direction.LEFT,
        ),
    ],
)
async def test_user_io_prompt(
    prompt_type: type,
    options: list[typing.Any],
    protocol_options: list[typing.Any],
    response_body: typing.Any,
    expected_result: typing.Any,
) -> None:
    executor_mock, query_mock = _create_query(response=response_body)
    driver = AriNativeDriver(executor_mock)

    result = await driver.user_io_prompt("Choose an option", prompt_type, options)
    assert result == expected_result

    # Determine expected type name
    type_name: typing.Any
    if prompt_type == str:
        type_name = "string"
    elif prompt_type in (int, float):
        type_name = "number"
    elif prompt_type == bool:
        type_name = "boolean"
    elif prompt_type == NamedColor:
        type_name = "surfaceColor"
    elif prompt_type == Direction:
        type_name = "direction"

    query_mock.assert_called_once_with(
        request.UserIoPromptRequest(
            id=0,
            params=request.UserIoPromptRequestParams(
                message="Choose an option", type=type_name, options=protocol_options, cancellable=False
            ),
        ),
        methods.USER_IO_PROMPT,
    )


async def test_native_data_access_watch() -> None:
    executor_mock, query_mock = _create_query(
        notifications=[
            memread.WatchNotification(
                id=0, notification=memread.MemReadResponseLineColor(color="Red", light_source=True, timestamp=0)
            ),
            memread.WatchNotification(
                id=0, notification=memread.MemReadResponseLineColor(color="Blue", light_source=True, timestamp=1)
            ),
            memread.WatchNotification(
                id=0, notification=memread.MemReadResponseLineColor(color="Green", light_source=True, timestamp=2)
            ),
        ],
    )
    driver = AriNativeDriver(executor_mock)

    async with driver.memory.line_color.watch() as container:
        it = aiter(container)
        notifications = [await anext(it) for _ in range(3)]

    assert notifications == [
        Sample(NamedColor.RED, 0),
        Sample(NamedColor.BLUE, 1),
        Sample(NamedColor.GREEN, 2),
    ]

    query_mock.assert_called_with(
        memread.WatchRequest(
            id=0,
            params=memread.MemReadRequestParams(
                segment="lineColor",
            ),
        ),
        methods.WATCH,
    )
