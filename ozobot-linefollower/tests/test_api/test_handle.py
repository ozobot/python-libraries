import pytest
from ozobot.linefollower.api.handle import BaseHandle


def test_base_handle_creation() -> None:
    handle = BaseHandle(address="test_addr", id="test_id", name="test_name")

    assert handle.address == "test_addr"
    assert handle.id == "test_id"
    assert handle.name == "test_name"


def test_base_handle_readonly_properties() -> None:
    handle = BaseHandle(address="test_addr", id="test_id", name="test_name")

    with pytest.raises(AttributeError):
        handle.address = "new_addr"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        handle.id = "new_id"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        handle.name = "new_name"  # type: ignore[misc]
