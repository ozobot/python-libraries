import asyncio
import io
import json
import typing

import pytest
from ozobot.ble.datatypes import DeviceDescription
from ozobot.cli.app import app
from ozobot.cli.output.json import JsonFormatter
from ozobot.cli.output.table import TableFormatter
from typer.testing import CliRunner

runner = CliRunner()


def _desc(
    *,
    address: str = "11:22:33:44:55:66",
    name: str | None = "EVO-123456",
    rssi: int | None = -54,
    product: typing.Literal["evo", "ari"] | None = "evo",
    version: tuple[int, int, int] | None = (1, 2, 3),
    device_id: str | None = "00112233445566778899AABBCCDDEEFF",
) -> DeviceDescription:
    return DeviceDescription(
        name=name,
        address=address,
        id=device_id,
        rssi=rssi,
        version=version,
        product=product,
    )


def _make_async_iter(items: list[DeviceDescription]):
    class _Iter:
        def __init__(self):
            self._idx = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self._idx >= len(items):
                raise StopAsyncIteration
            item = items[self._idx]
            self._idx += 1
            return item, object()

    return _Iter()


def _patch_scan_with_items(monkeypatch, items: list[DeviceDescription]):
    iter_factory = lambda: _make_async_iter(items)

    def cm_factory():
        class _CM:
            async def __aenter__(self):
                return iter_factory()

            async def __aexit__(self, exc_type, exc, tb):
                return None

        return _CM()

    monkeypatch.setattr("ozobot.cli.commands_scan.scan_devices", cm_factory)


def test_table_formatter_emit():
    buf = io.StringIO()
    fmt = TableFormatter(buf)

    async def run():
        async with fmt:
            await fmt.emit(_desc())

    asyncio.run(run())
    out = buf.getvalue()
    assert "NAME" in out
    assert "EVO-123456" in out
    assert "11:22:33:44:55:66" in out
    assert "evo" in out
    assert "1.2.3" in out
    assert "-54 dBm" in out


def test_table_formatter_handles_missing_fields():
    buf = io.StringIO()
    fmt = TableFormatter(buf)

    async def run():
        async with fmt:
            await fmt.emit(
                _desc(
                    name=None,
                    rssi=None,
                    product=None,
                    version=None,
                    device_id=None,
                )
            )

    asyncio.run(run())
    out = buf.getvalue()
    assert "-" in out
    assert "None" not in out
    assert "0.0.0" not in out


def test_json_formatter_omits_version_when_none():
    buf = io.StringIO()
    fmt = JsonFormatter(buf)

    async def run():
        async with fmt:
            await fmt.emit(_desc(version=None))

    asyncio.run(run())
    parsed = json.loads(buf.getvalue())
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert "version" not in parsed[0]


def test_json_formatter_emits_valid_array():
    buf = io.StringIO()
    fmt = JsonFormatter(buf)

    async def run():
        async with fmt:
            await fmt.emit(_desc())
            await fmt.emit(
                _desc(
                    address="AA:BB:CC:DD:EE:FF",
                    name="EVO-ABCDEF",
                    rssi=-71,
                )
            )

    asyncio.run(run())
    parsed = json.loads(buf.getvalue())
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    assert parsed[0]["address"] == "11:22:33:44:55:66"
    assert parsed[0]["version"] == "1.2.3"
    assert parsed[1]["address"] == "AA:BB:CC:DD:EE:FF"
    assert parsed[1]["rssi"] == -71


def test_json_formatter_closes_on_exception():
    buf = io.StringIO()
    fmt = JsonFormatter(buf)

    async def run():
        async with fmt:
            await fmt.emit(_desc())
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        asyncio.run(run())

    parsed = json.loads(buf.getvalue())
    assert isinstance(parsed, list)
    assert len(parsed) == 1


def test_json_formatter_empty():
    buf = io.StringIO()
    fmt = JsonFormatter(buf)

    async def run():
        async with fmt:
            pass

    asyncio.run(run())
    parsed = json.loads(buf.getvalue())
    assert parsed == []


def test_scan_emits_devices_with_timeout(monkeypatch):
    _patch_scan_with_items(
        monkeypatch,
        [_desc(), _desc(address="AA:BB:CC:DD:EE:FF", name="EVO-OTHER")],
    )
    result = runner.invoke(app, ["scan", "--timeout", "5", "--refresh", "10"])
    assert result.exit_code == 0
    assert "EVO-123456" in result.stdout
    assert "EVO-OTHER" in result.stdout


def test_scan_refresh_throttles_repeat_sightings(monkeypatch):
    d1 = _desc()
    d1_again = _desc(rssi=-60)
    d2 = _desc(address="AA:BB:CC:DD:EE:FF", name="EVO-OTHER")
    _patch_scan_with_items(monkeypatch, [d1, d1_again, d2])

    result = runner.invoke(app, ["scan", "--timeout", "5", "--refresh", "100"])
    assert result.exit_code == 0
    matching = [ln for ln in result.stdout.splitlines() if "11:22:33:44:55:66" in ln]
    assert len(matching) == 1
    assert "EVO-OTHER" in result.stdout


def test_scan_json_with_max_devices_emits_array(monkeypatch):
    d1 = _desc()
    d2 = _desc(address="AA:BB:CC:DD:EE:FF", name="EVO-OTHER")
    d3 = _desc(address="11:11:11:11:11:11", name="EVO-THIRD")
    _patch_scan_with_items(monkeypatch, [d1, d2, d3])

    result = runner.invoke(app, ["scan", "--json", "--max-devices", "2"])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    addresses = {item["address"] for item in parsed}
    assert "11:22:33:44:55:66" in addresses
    assert "AA:BB:CC:DD:EE:FF" in addresses


def test_scan_json_without_timeout_or_max_devices_uses_internal_default(monkeypatch):
    _patch_scan_with_items(monkeypatch, [_desc()])
    result = runner.invoke(app, ["scan", "--json"])
    assert result.exit_code == 0
    stderr = result.stderr or ""
    assert "no stop condition set" in stderr
    assert "max-devices=1" in stderr


def test_scan_json_with_max_devices_no_notice(monkeypatch):
    _patch_scan_with_items(monkeypatch, [_desc()])
    result = runner.invoke(app, ["scan", "--json", "--max-devices", "3"])
    assert result.exit_code == 0
    assert "no stop condition" not in (result.stderr or "")


def test_scan_json_with_timeout_no_notice(monkeypatch):
    _patch_scan_with_items(monkeypatch, [_desc()])
    result = runner.invoke(app, ["scan", "--json", "--timeout", "5"])
    assert result.exit_code == 0
    assert "no stop condition" not in (result.stderr or "")


def test_scan_no_args_runs_human_output(monkeypatch):
    _patch_scan_with_items(
        monkeypatch,
        [_desc(), _desc(address="AA:BB:CC:DD:EE:FF", name="EVO-OTHER")],
    )
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "EVO-123456" in result.stdout
    assert "EVO-OTHER" in result.stdout
    stderr = result.stderr or ""
    assert "no stop condition" in stderr
    assert "Ctrl-C" in stderr


def test_scan_default_refresh_is_infinity(monkeypatch):
    d1 = _desc()
    d1_again = _desc(rssi=-60)
    d2 = _desc(address="AA:BB:CC:DD:EE:FF", name="EVO-OTHER")
    _patch_scan_with_items(monkeypatch, [d1, d1_again, d2])

    result = runner.invoke(app, ["scan", "--timeout", "5"])
    assert result.exit_code == 0
    matching = [ln for ln in result.stdout.splitlines() if "11:22:33:44:55:66" in ln]
    assert len(matching) == 1
    assert "EVO-OTHER" in result.stdout


def test_scan_refresh_zero_reemits_immediately(monkeypatch):
    d1 = _desc()
    d1_again = _desc(rssi=-60)
    _patch_scan_with_items(monkeypatch, [d1, d1_again])

    result = runner.invoke(app, ["scan", "--timeout", "5", "--refresh", "0"])
    assert result.exit_code == 0
    matching = [ln for ln in result.stdout.splitlines() if "11:22:33:44:55:66" in ln]
    assert len(matching) == 2


def test_scan_defaults_printed_to_stderr(monkeypatch):
    _patch_scan_with_items(monkeypatch, [_desc()])
    result = runner.invoke(app, ["scan", "--timeout", "5", "--json"])
    assert result.exit_code == 0
    assert "# defaults" in (result.stderr or "")
    assert "timeout=5" in (result.stderr or "")


def test_scan_filters_unknown_products(monkeypatch):
    known = _desc()
    unknown = _desc(
        address="AA:BB:CC:DD:EE:FF",
        name="NOT-AN-OZOBOT",
        product=None,
        version=None,
    )
    _patch_scan_with_items(monkeypatch, [unknown, known])

    result = runner.invoke(app, ["scan", "--timeout", "5"])
    assert result.exit_code == 0
    assert "NOT-AN-OZOBOT" not in result.stdout
    assert "AA:BB:CC:DD:EE:FF" not in result.stdout
    assert "EVO-123456" in result.stdout
    assert "11:22:33:44:55:66" in result.stdout
