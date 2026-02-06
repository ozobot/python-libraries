from unittest.mock import AsyncMock, Mock, patch

import pytest
from ozobot.ari.api.handle import AriHandle, SyncAriHandle


def test_ari_handle_creation() -> None:
    handle = AriHandle(address="test_addr", id="test_id", name="test_name", connection_key="test_key")

    assert handle.address == "test_addr"
    assert handle.id == "test_id"
    assert handle.name == "test_name"
    assert handle.connection_key == "test_key"


def test_ari_handle_readonly_properties() -> None:
    handle = AriHandle(connection_key="test_key")

    with pytest.raises(AttributeError):
        handle.connection_key = "new_key"  # type: ignore[misc]


async def test_ari_handle_context_manager() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.ari.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = AriHandle(name="test", connection_key="key")

        async with handle as _:
            mock_driver_class.open.assert_called_once_with(address=None, id=None, name="test", connection_key="key")
            mock_driver.__aenter__.assert_awaited_once()
            mock_driver.__aexit__.assert_not_called()

        mock_driver.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_ari_handle_context_manager_exception() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.ari.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = AriHandle(name="test")

        try:
            async with handle:
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_driver.__aexit__.assert_called_once()


def test_sync_ari_handle_creation() -> None:
    handle = SyncAriHandle(address="test_addr", id="test_id", name="test_name", connection_key="test_key")

    assert handle.address == "test_addr"
    assert handle.id == "test_id"
    assert handle.name == "test_name"
    assert handle.connection_key == "test_key"


def test_sync_ari_handle_readonly_properties() -> None:
    handle = SyncAriHandle(connection_key="test_key")

    with pytest.raises(AttributeError):
        handle.connection_key = "new_key"  # type: ignore[misc]


def test_sync_ari_handle_context_manager() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.ari.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = SyncAriHandle(name="test", connection_key="key")

        with handle as _:
            mock_driver_class.open.assert_called_once_with(address=None, id=None, name="test", connection_key="key")
            mock_driver.__aenter__.assert_awaited_once()
            mock_driver.__aexit__.assert_not_called()

        mock_driver.__aexit__.assert_awaited_once()


def test_sync_ari_handle_context_manager_exception() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.ari.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = SyncAriHandle(name="test")

        try:
            with handle as _:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify exit was called
        assert handle._exit_stack is not None
