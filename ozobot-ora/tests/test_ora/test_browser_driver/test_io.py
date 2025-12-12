from unittest.mock import patch

from ozobot.ora.datatypes import IoName, IoValue, IoValueType
from ozobot.ora.drivers.browser import OraWebDriver

_CORO_MODULE_PATH = "ozobot.ora.drivers.browser._rpcCoroutine"


async def test_get_analog_inputs():
    inputs = [
        IoName[float](0, IoValueType.ANALOG),
        IoName[float](2, IoValueType.ANALOG),
    ]

    return_value = [
        {"index": 0, "value": 2.1, "type": "analog"},
        {"index": 2, "value": 3.5, "type": "analog"},
    ]

    with patch(_CORO_MODULE_PATH, return_value=return_value) as rpc:
        driver = OraWebDriver()
        values = await driver.get_inputs(inputs)
        rpc.assert_awaited_once_with(
            "ora",
            "readInputs",
            [
                [
                    {"index": 0, "type": "analog"},
                    {"index": 2, "type": "analog"},
                ],
            ],
        )

        assert values == [
            IoValue[float](0, 2.1, IoValueType.ANALOG),
            IoValue[float](2, 3.5, IoValueType.ANALOG),
        ]


async def test_get_digital_inputs():
    inputs = [
        IoName[bool](0, IoValueType.DIGITAL),
        IoName[bool](2, IoValueType.DIGITAL),
    ]

    return_value = [
        {"index": 0, "value": False, "type": "digital"},
        {"index": 2, "value": True, "type": "digital"},
    ]

    with patch(_CORO_MODULE_PATH, return_value=return_value) as rpc:
        driver = OraWebDriver()
        values = await driver.get_inputs(inputs)
        rpc.assert_awaited_once_with(
            "ora",
            "readInputs",
            [
                [
                    {"index": 0, "type": "digital"},
                    {"index": 2, "type": "digital"},
                ],
            ],
        )

        assert values == [
            IoValue[bool](0, False, IoValueType.DIGITAL),
            IoValue[bool](2, True, IoValueType.DIGITAL),
        ]


async def test_wait_for_input_change():
    inputs = [
        IoName[float](0, IoValueType.ANALOG),
        IoName[float](2, IoValueType.ANALOG),
    ]

    return_value = [
        {"index": 0, "value": 2.1, "type": "analog"},
        {"index": 2, "value": 3.5, "type": "analog"},
    ]

    with patch(_CORO_MODULE_PATH, return_value=return_value) as rpc:
        driver = OraWebDriver()
        values = await driver.wait_for_input_change(inputs)
        rpc.assert_awaited_once_with(
            "ora.listener",
            "waitForInputs",
            [
                [
                    {"index": 0, "type": "analog"},
                    {"index": 2, "type": "analog"},
                ],
            ],
        )

        assert values == [
            IoValue[float](0, 2.1, IoValueType.ANALOG),
            IoValue[float](2, 3.5, IoValueType.ANALOG),
        ]


async def test_write_outputs():
    outputs = [
        IoValue[float](0, 1.2, IoValueType.ANALOG),
        IoValue[float](2, 3.4, IoValueType.ANALOG),
    ]

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.write_outputs(outputs)
        rpc.assert_awaited_once_with(
            "ora",
            "writeOutputs",
            [
                [
                    {"index": 0, "type": "analog", "value": 1.2},
                    {"index": 2, "type": "analog", "value": 3.4},
                ],
            ],
        )
