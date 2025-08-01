from av.error import NotImplementedError
import asyncio
import contextlib
import datetime
import typing
from unittest.mock import ANY, AsyncMock, Mock, patch, sentinel

import pytest
from ozobot.ari.driver.native import NativeDriver
from ozobot.ari.protocol import request, types, methods
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample


def _create_query():
    query_mock = Mock()

    class _MockQuery:
        def __init__(self, *args, **kwargs):
            query_mock(*args, **kwargs)

        @contextlib.asynccontextmanager
        async def execute(self, *args, **kwargs):
            async def _coro():
                return Mock(result=Mock(type="finished"))

            yield Mock(
                response=_coro(),
            )

    return _MockQuery, query_mock


@patch("ozobot.ari.driver.sys.platform", "linux")
def test_import_native() -> None:
    from ozobot.ari.driver import get_driver

    assert issubclass(get_driver(), NativeDriver)


async def test_open_ble() -> None:
    with patch("ozobot.ari.driver.native._get_routing_key_from_ble", return_value="anvil.abcdefgh") as routing_key_mock:
        with patch("ozobot.ari.driver.native._create_webrtc_channel") as channel_mock:
            async with NativeDriver.open(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF") as driver:
                assert isinstance(driver, NativeDriver)
                routing_key_mock.assert_called_with(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF")
                channel_mock.assert_called_once_with("anvil.abcdefgh")


async def test_open_connection_key() -> None:
    with patch("ozobot.ari.driver.native._create_webrtc_channel") as channel_mock:
        async with NativeDriver.open(connection_key="1234abcd") as driver:
            assert isinstance(driver, NativeDriver)
            channel_mock.assert_called_once_with("anvil.1234abcd")


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        (
            "move",
            "MoveStraight",
            [0.2, 0.1],
            (
                request.MoveStraightRequest(id=0, params=request.MoveStraightRequestParams(distance=0.2, speed=0.1)),
                methods.MOVE_STRAIGHT,
            ),
        ),
        (
            "rotate",
            "Rotate",
            [0.1, 0.2],
            (request.RotateRequest(id=0, params=request.RotateRequestParams(angle=0.1, speed=0.2)), methods.ROTATE),
        ),
        (
            "velocity",
            "Velocity",
            [0.1, 0.2, 3000],
            (
                request.VelocityRequest(
                    id=0, params=request.VelocityRequestParams(linear_speed=0.1, rotation_speed=0.2, expiration=3)
                ),
                methods.VELOCITY,
            ),
        ),
        (
            "play_tone",
            "PlayTone",
            [1, 2000, 3],
            (
                request.PlayToneRequest(id=0, params=request.PlayToneRequestParams(frequency=1, duration=2, volume=3)),
                methods.PLAY_TONE,
            ),
        ),
        (
            "play_audio",
            "ExecuteFile",
            ["happy"],
            (
                request.PlaySoundRequest(
                    id=0, params=request.PlaySoundRequestParams(name="happy", loop=False, volume=1)
                ),
                methods.PLAY_SOUND,
            ),
        ),
    ],
)
async def test_command_with_response(
    function_name: str, command_name: str, command_parameters: list[typing.Any], rpc_parameters: dict[str, typing.Any]
) -> None:
    query_cls, query_cls_mock = _create_query()
    with patch("ozobot.ari.driver.native.Query", query_cls):
        driver = NativeDriver(Mock())

        function = getattr(driver, function_name)
        await function(*command_parameters)
        query_cls_mock.assert_called_once_with(*rpc_parameters)


@pytest.mark.parametrize(
    "follow_bool,follow_protocol",
    [(True, "Follow"), (False, "DoNotFollow")],
    ids=lambda x: repr(x),
)
@patch(
    "ozobot.evo.driver.native.datetime", Mock(datetime=Mock(now=Mock(return_value=datetime.datetime.fromtimestamp(0))))
)
async def test_line_navigation(follow_bool: bool, follow_protocol: str) -> None:
    query_cls, query_cls_mock = _create_query()
    with patch("ozobot.ari.driver.native.Query", query_cls):
        driver = NativeDriver(Mock())

        await driver.line_navigation(Direction.LEFT, follow_bool)

        query_cls_mock.assert_called_once_with(
            request.LineNavigationRequest(
                id=0,
                params=request.LineNavigationRequestParams(
                    direction="Left", follow=follow_protocol, detect_color_codes=True
                ),
            ),
            methods.LINE_NAVIGATION,
        )

    # TODO: test intersecion and color code reading
    # memory.intersection_queue.write.assert_called_once_with(Sample(Direction.LEFT | Direction.STRAIGHT, 0))


async def test_request_id_counter() -> None:
    query_cls, query_cls_mock = _create_query()
    with patch("ozobot.ari.driver.native.Query", query_cls):
        driver = NativeDriver(Mock())
        await driver.move(0, 0)
        await driver.move(1, 1)

        assert query_cls_mock.call_args_list[0].args[0].id == 0
        assert query_cls_mock.call_args_list[1].args[0].id == 1


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
    query_cls, query_cls_mock = _create_query()
    with patch("ozobot.ari.driver.native.Query", query_cls):
        driver = NativeDriver(Mock())

        await driver.set_led(command_lights, 10, 20, 30)

        query_cls_mock.assert_called_once_with(
            request.SetLEDRequest(
                id=0,
                params=request.SetLEDRequestParams(
                    lights=rpc_lights,
                    color=types.Color(red=10, green=20, blue=30),
                ),
            ),
            methods.SET_LED,
        )


async def test_follow_speed() -> None:
    raise NotImplementedError("no vmem support yet")
    # cmd_mock = AsyncMock(
    #     return_value=_create_command(
    #         response={"callStatus": Types.CallStatus.CallSuccess},
    #     )
    # )
    # control = Mock(MemWrite=cmd_mock)
    # memory = NativeMemoryRegions(control, (Mock(),) * 3)
    # driver = NativeDriver(control, memory)

    # await driver.follow_speed(0.1)
    # cmd_mock.assert_called_once_with(ANY, ANY, Types.S8_24(0.1).serialize())


async def test_native_data_access_read() -> None:
    raise NotImplementedError("no vmem support yet")
    # cmd_mock = AsyncMock(
    #     return_value=Mock(data=Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize())
    # )
    # control = AsyncMock(MemRead=cmd_mock)
    # property = Mock(type=Types.Battery)
    # da = NativeDataAccessRead(control, property, lambda v: v.voltage)

    # ret = await da.read()
    # assert isinstance(ret, Sample)
    # assert ret.data == 1

    # cmd_mock.assert_called_once_with(property.address, property.size)


async def test_native_data_watcher() -> None:
    raise NotImplementedError("no vmem support yet")
    # @contextlib.asynccontextmanager
    # async def _watch() -> typing.AsyncIterator[Types.Battery]:
    #     async def _iter():
    #         yield Types.Battery(voltage=10, remainingPower=2, fields=0, timestamp=0)
    #         yield Types.Battery(voltage=20, remainingPower=2, fields=0, timestamp=0)

    #     yield _iter()

    # cmd_mock = AsyncMock(
    #     return_value=Mock(data=Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize())
    # )
    # control = AsyncMock(
    #     MemRead=cmd_mock,
    # )
    # property = Mock(type=Types.Battery)
    # watcher = Mock(watch=_watch)
    # da = NativeDataWatcher(control, property, watcher, lambda v: v.voltage)

    # # test watching
    # async with da.watch() as it:
    #     samples = [await anext(it) for _ in range(2)]

    #     assert all([isinstance(s, Sample) for s in samples])
    #     values = [s.data for s in samples]
    #     assert values == [10, 20]

    # # test reading
    # ret = await da.read()
    # assert isinstance(ret, Sample)
    # assert ret.data == 1

    # cmd_mock.assert_called_once_with(property.address, property.size)
