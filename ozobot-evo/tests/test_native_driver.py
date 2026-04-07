import asyncio
import contextlib
import math
import typing
from unittest.mock import AsyncMock, Mock, patch, sentinel

import pytest
from ozobot.evo.driver.native import (
    EvoNativeDriver,
    NativeDataAccessRead,
    NativeDataAccessReadWrite,
    NativeDataWatcher,
)
from ozobot.evo.protocol import Types, VirtualMemory
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample, SampleWithoutTimestamp


def _create_command(
    *,
    response: dict[str, typing.Any],
    events: list[dict[str, typing.Any]] | None = None,
):
    async def _evts():
        for e in events or []:
            yield Mock(**e)

    @contextlib.asynccontextmanager
    async def _resp():
        yield Mock(**response), _evts()

    return _resp()


@patch("ozobot.evo.driver.sys.platform", "linux")
def test_import_native() -> None:
    from ozobot.evo.driver import get_driver

    with pytest.raises(NotImplementedError):
        _ = get_driver()

    # assert issubclass(get_driver(), EvoNativeDriver)


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        ("move", "MoveStraight", [200, 100], [0.2, 0.1]),
        ("rotate", "Rotate", [90, 10], [math.pi / 2, math.radians(10)]),
        ("velocity", "Velocity", [100, 10, 3], [0.1, math.radians(10), 3]),
        ("play_tone", "PlayTone", [1, 2], [1, 2, 100]),
        ("play_audio_asset", "ExecuteFile", ["01010100"], ["/system/audio/01010100.wav"]),
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
        get_next_request_id=lambda: 1,
    )
    driver = EvoNativeDriver(control, Mock())

    function = getattr(driver, function_name)
    await function(*command_parameters)
    cmd_mock.assert_called_once_with(1, *rpc_parameters)


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
    driver = EvoNativeDriver(control, memory)

    await driver.line_navigation(Direction.LEFT, False)
    cmd_mock.assert_called_once_with(
        sentinel.request_id, Types.IntersectionDirection.Left, Types.LineNavigationAction.DoNotFollow
    )
    memory.intersection_queue.write.assert_called_once_with(SampleWithoutTimestamp(Direction.LEFT | Direction.STRAIGHT))


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
    cmd_mock = Mock(
        return_value=_create_command(
            response={"callStatus": Types.CallStatus.CallSuccess},
        )
    )
    control = Mock(SetLED=cmd_mock)
    driver = EvoNativeDriver(control, Mock())

    await driver.set_led(command_direction, 0, 0.1, 0.2)
    cmd_mock.assert_called_once_with(rpc_direction, 0, 25, 51, 255)


@pytest.mark.parametrize(
    ["function_name", "command_name", "command_parameters", "rpc_parameters"],
    [
        ("move", "MoveStraight", [200, 100], [0.2, 0.1]),
        ("rotate", "Rotate", [90, 10], [math.pi / 2, math.radians(10)]),
        ("velocity", "Velocity", [100, 10, 3], [0.1, math.radians(10), 3]),
        ("play_tone", "PlayTone", [1, 2], [1, 2, 100]),
        ("play_audio_asset", "ExecuteFile", ["01010100"], ["/system/audio/01010100.wav"]),
        (
            "line_navigation",
            "LineNavigation",
            [Direction.LEFT, False],
            [Types.IntersectionDirection.Left, Types.LineNavigationAction.DoNotFollow],
        ),
    ],
)
async def test_cancellation(
    function_name: str, command_name: str, command_parameters: list[typing.Any], rpc_parameters: list[typing.Any]
) -> None:
    @contextlib.asynccontextmanager
    async def _resp():
        async def _evts():
            raise asyncio.CancelledError("test case: cancellation")
            yield None

        yield (
            AsyncMock(side_effect=asyncio.CancelledError("test case: cancellation")),
            _evts(),
        )

    cmd_mock = Mock(
        return_value=_resp(),
    )
    stop_mock = Mock(
        return_value=_resp(),
    )

    control = Mock(
        **{command_name: cmd_mock, "StopExecution": stop_mock},
        get_next_request_id=lambda: sentinel.request_id,
    )
    driver = EvoNativeDriver(control, Mock())

    function = getattr(driver, function_name)
    with pytest.raises(asyncio.CancelledError):
        await function(*command_parameters)

    cmd_mock.assert_called_once_with(sentinel.request_id, *rpc_parameters)
    stop_mock.assert_called_once_with(sentinel.request_id)


async def test_native_data_access_read() -> None:
    cmd_mock = Mock(
        return_value=_create_command(
            response={
                "callStatus": Types.CallStatus.CallSuccess,
                "data": Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize(),
            },
        )
    )

    control = AsyncMock(MemRead=cmd_mock)
    property = Mock(type=Types.Battery)
    da = NativeDataAccessRead(control, property, lambda v: v.voltage)

    ret = await da.read()
    assert ret == 1

    cmd_mock.assert_called_once_with(property.address, property.size)


async def test_native_data_access_write() -> None:
    cmd_mock = Mock(
        return_value=_create_command(
            response={
                "callStatus": Types.CallStatus.CallSuccess,
            },
        )
    )

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
            yield Types.Battery(voltage=10, remainingPower=2, fields=0, timestamp=1)
            yield Types.Battery(voltage=20, remainingPower=2, fields=0, timestamp=2)

        yield _iter()

    cmd_mock = Mock(
        return_value=_create_command(
            response={
                "callStatus": Types.CallStatus.CallSuccess,
                "data": Types.Battery(voltage=1, remainingPower=2, fields=0, timestamp=0).serialize(),
            },
        )
    )
    control = AsyncMock(
        MemRead=cmd_mock,
    )
    property = Mock(type=Types.Battery)
    watcher = Mock(watch=_watch)
    da = NativeDataWatcher(control, property, watcher, lambda v: Sample(v.voltage, v.timestamp))

    # test watching
    async with da.watch() as container:
        it = aiter(container)
        samples = [await anext(it) for _ in range(2)]

        assert all([isinstance(s, Sample) for s in samples])
        values = [s.value for s in samples]
        assert values == [10, 20]

    # test reading
    ret = await da.read()
    assert ret == Sample(1, 0)

    cmd_mock.assert_called_once_with(property.address, property.size)
