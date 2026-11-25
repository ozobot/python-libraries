import importlib
import sys
import types

import pytest

_DEVICE_MODULES = {
    "Ari": "ozobot.ari",
    "Evo": "ozobot.evo",
    "Ora": "ozobot.ora.driver.web",
}


def _import_devices_without(monkeypatch: pytest.MonkeyPatch, *missing: str) -> types.ModuleType:
    # a `None` entry in sys.modules makes any import of that module raise ModuleNotFoundError
    for name in missing:
        monkeypatch.setitem(sys.modules, _DEVICE_MODULES[name], None)

    monkeypatch.delitem(sys.modules, "ozobot.actors.devices", raising=False)
    return importlib.import_module("ozobot.actors.devices")


def test_all_devices_available(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = _import_devices_without(monkeypatch)

    assert {name for _, name in devices.compatible_devices} == {"Ari", "Evo", "Ora"}


@pytest.mark.parametrize("missing", list(_DEVICE_MODULES))
def test_single_device_missing(monkeypatch: pytest.MonkeyPatch, missing: str) -> None:
    devices = _import_devices_without(monkeypatch, missing)

    assert {name for _, name in devices.compatible_devices} == set(_DEVICE_MODULES) - {missing}


def test_no_devices_available(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = _import_devices_without(monkeypatch, *_DEVICE_MODULES)

    assert devices.compatible_devices == set()
