from unittest.mock import AsyncMock, Mock, patch

import pytest
from ozobot.evo.api.handle import EvoHandle, SyncEvoHandle


def test_evo_handle_creation() -> None:
    handle = EvoHandle(address="test_addr", id="test_id", name="test_name")

    assert handle.address == "test_addr"
    assert handle.id == "test_id"
    assert handle.name == "test_name"


async def test_evo_handle_context_manager() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.evo.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = EvoHandle(name="test")

        async with handle as _:
            mock_driver_class.open.assert_called_once_with(address=None, id=None, name="test")
            mock_driver.__aenter__.assert_awaited_once()
            mock_driver.__aexit__.assert_not_called()

        mock_driver.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_evo_handle_context_manager_exception() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.evo.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = EvoHandle(name="test")

        try:
            async with handle:
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_driver.__aexit__.assert_called_once()


def test_sync_evo_handle_creation() -> None:
    handle = SyncEvoHandle(address="test_addr", id="test_id", name="test_name")

    assert handle.address == "test_addr"
    assert handle.id == "test_id"
    assert handle.name == "test_name"


def test_sync_evo_handle_context_manager() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.evo.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = SyncEvoHandle(name="test")

        with handle as _:
            mock_driver_class.open.assert_called_once_with(address=None, id=None, name="test")
            mock_driver.__aenter__.assert_awaited_once()
            mock_driver.__aexit__.assert_not_called()

        mock_driver.__aexit__.assert_awaited_once()


def test_sync_evo_handle_context_manager_exception() -> None:
    mock_driver = AsyncMock()

    with patch("ozobot.evo.api.handle.get_driver") as mock_get_driver:
        mock_driver_class = Mock()
        mock_driver_class.open.return_value = mock_driver
        mock_get_driver.return_value = mock_driver_class

        handle = SyncEvoHandle(name="test")

        try:
            with handle as _:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Verify exit was called
        assert handle._exit_stack is not None
