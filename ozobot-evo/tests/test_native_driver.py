import contextlib
import typing
from unittest.mock import AsyncMock, Mock, patch, sentinel

import pytest
from ozobot.evo.driver.native import (
    NativeDataAccessRead,
    NativeDataAccessReadWrite,
    NativeDataWatcher,
    NativeDriver,
)
from ozobot.evo.protocol import Types, VirtualMemory
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample


def _get_async_control():
    return Mock(
        get_next_request_id=Mock(return_value=sentinel.request_id),
    )


def _create_command(
    *,
    response: dict[str, typing.Any],
    events: list[dict[str, typing.Any]] | None = None,
):
    if events:

        async def _evts():
            for e in events or []:
                yield Mock(**e)

        @contextlib.asynccontextmanager
        async def _resp():
            yield Mock(**response), _evts()
    else:

        async def _resp():
            return Mock(**response)

    return _resp()


@patch("ozobot.evo.driver.sys.platform", "linux")
def test_import_native() -> None:
    from ozobot.evo.driver import get_driver

    assert issubclass(get_driver(), NativeDriver)


async def test_open() -> None:
    with (
        patch("ozobot.evo.driver.native.open_client") as open_client_mock,
        patch("ozobot.evo.driver.native.create_memory_regions_structure"),
    ):
        async with NativeDriver.open(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF") as driver:
            assert isinstance(driver, NativeDriver)
            open_client_mock.assert_called_with(address="11:22:33:44:55:66", id_prefix="1234", name="EVO-ABCDEF")


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        ("move", "MoveStraight", [0.2, 0.1], [0.2, 0.1]),
        ("rotate", "Rotate", [0.1, 0.2], [0.1, 0.2]),
        ("velocity", "Velocity", [0.1, 0.2, 3], [0.1, 0.2, 3]),
        ("play_tone", "PlayTone", [1, 2, 3], [1, 2, 3]),
        ("play_audio", "ExecuteFile", ["happy"], ["/system/audio/01010100.wav"]),
    ],
)
async def test_command_with_events(
    function_name: str, command_name: str, command_parameters: list[typing.Any], rpc_parameters: list[typing.Any]
) -> None:
    cmd_mock = Mock(
        return_value=_create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
            events=[
                {"executionState": Types.ExecutionStateEnum.Running},
                {"executionState": Types.ExecutionStateEnum.FinishedNormal},
            ],
        )
    )

    control = Mock(
        **{command_name: cmd_mock},
        get_next_request_id=lambda: sentinel.request_id,
    )
    driver = NativeDriver(control, Mock())

    function = getattr(driver, function_name)
    await function(*command_parameters)
    cmd_mock.assert_called_once_with(sentinel.request_id, *rpc_parameters)


@patch("ozobot.linefollower.datatypes.Sample.now", lambda d: Sample(d, 0))
async def test_line_navigation() -> None:
    cmd_mock = Mock(
        return_value=_create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
            events=[
                {"executionState": Types.ExecutionStateEnum.Running},
                {
                    "executionState": Types.ExecutionStateEnum.FinishedNormal,
                    "intersection": Types.IntersectionBitmap.Straight | Types.IntersectionBitmap.Left,
                },
            ],
        )
    )
    control = Mock(
        LineNavigation=cmd_mock,
        get_next_request_id=lambda: sentinel.request_id,
    )
    memory = AsyncMock()
    driver = NativeDriver(control, memory)

    await driver.line_navigation(Direction.LEFT, False)
    cmd_mock.assert_called_once_with(
        sentinel.request_id, Types.IntersectionDirection.Left, Types.LineNavigationAction.DoNotFollow
    )
    memory.intersection_queue.write.assert_called_once_with(Sample(Direction.LEFT | Direction.STRAIGHT, 0))


@pytest.mark.parametrize(
    ["command_direction", "rpc_direction"],
    [
        (LEDMask.FRONT_CENTER, Types.LEDsMask.front_center),
        (LEDMask.FRONT_LEFT_CENTER, Types.LEDsMask.front_left_center),
        (LEDMask.FRONT_RIGHT_CENTER, Types.LEDsMask.front_right_center),
        (LEDMask.FRONT_RIGHT, Types.LEDsMask.front_right),
        (LEDMask.FRONT_LEFT, Types.LEDsMask.front_left),
        (LEDMask.TOP, Types.LEDsMask.top),
        (
            LEDMask.FRONT_CENTER | LEDMask.FRONT_RIGHT,
            Types.LEDsMask.front_center | Types.LEDsMask.front_right,
        ),
    ],
)
async def test_set_led(command_direction: LEDMask, rpc_direction: Types.LEDsMask) -> None:
    cmd_mock = AsyncMock(
        return_value=_create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
        )
    )
    control = Mock(SetLED=cmd_mock)
    driver = NativeDriver(control, Mock())

    await driver.set_led(command_direction, 0, 100, 200)
    cmd_mock.assert_called_once_with(rpc_direction, 0, 100, 200, 255)


async def test_native_data_access_read() -> None:
    cmd_mock = AsyncMock(
        return_value=Mock(data=Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize())
    )
    control = AsyncMock(MemRead=cmd_mock)
    property = Mock(type=Types.Battery)
    da = NativeDataAccessRead(control, property, lambda v: v.voltage)

    ret = await da.read()
    assert isinstance(ret, Sample)
    assert ret.data == 1

    cmd_mock.assert_called_once_with(property.address, property.size)


async def test_native_data_access_write() -> None:
    cmd_mock = AsyncMock()
    control = AsyncMock(MemWrite=cmd_mock)
    property = VirtualMemory.lineNavigationSpeed
    da = NativeDataAccessReadWrite(
        control,
        property,
        lambda s8_24: float(s8_24),
        lambda fl: Types.S8_24(fl),
    )

    await da.write(1.23)
    cmd_mock.assert_called_once_with(property.address, property.size, Types.S8_24(1.23).serialize())


async def test_native_data_watcher() -> None:
    @contextlib.asynccontextmanager
    async def _watch() -> typing.AsyncIterator[Types.Battery]:
        async def _iter():
            yield Types.Battery(voltage=10, remainingPower=2, fields=0, timestamp=0)
            yield Types.Battery(voltage=20, remainingPower=2, fields=0, timestamp=0)

        yield _iter()

    cmd_mock = AsyncMock(
        return_value=Mock(data=Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize())
    )
    control = AsyncMock(
        MemRead=cmd_mock,
    )
    property = Mock(type=Types.Battery)
    watcher = Mock(watch=_watch)
    da = NativeDataWatcher(control, property, watcher, lambda v: v.voltage)

    # test watching
    async with da.watch() as it:
        samples = [await anext(it) for _ in range(2)]

        assert all([isinstance(s, Sample) for s in samples])
        values = [s.data for s in samples]
        assert values == [10, 20]

    # test reading
    ret = await da.read()
    assert isinstance(ret, Sample)
    assert ret.data == 1

    cmd_mock.assert_called_once_with(property.address, property.size)
