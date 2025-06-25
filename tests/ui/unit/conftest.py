import pytest
from unittest.mock import AsyncMock, MagicMock
from PySide6.QtWidgets import QApplication
import asyncio
from qasync import QEventLoop

from ultibot_ui.services.api_client import UltiBotAPIClient

# Fixture para el QApplication, necesario para PySide6 en tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

# Fixture para el bucle de eventos de asyncio, con scope de sesión para pytest-asyncio
@pytest.fixture(scope="session")
def event_loop(qapp):
    # Asegurarse de que el bucle de eventos de asyncio esté configurado para qasync
    loop = QEventLoop(qapp)
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# Mock para UltiBotAPIClient
@pytest.fixture
def mock_api_client():
    mock_client = MagicMock(spec=UltiBotAPIClient)
    mock_client.base_url = "http://mock-api.com"
    mock_client.create_order = AsyncMock(return_value={"id": "mock_order_id"})
    mock_client.get_latest_price = AsyncMock(side_effect=[
        {"symbol": "BTCUSDT", "price": 50000.0, "timestamp": "2025-01-01T10:00:00Z"},
        {"symbol": "BTCUSDT", "price": 50001.0, "timestamp": "2025-01-01T10:00:01Z"},
        {"symbol": "BTCUSDT", "price": 50002.0, "timestamp": "2025-01-01T10:00:02Z"},
        {"symbol": "BTCUSDT", "price": 50003.0, "timestamp": "2025-01-01T10:00:03Z"},
        {"symbol": "BTCUSDT", "price": 50004.0, "timestamp": "2025-01-01T10:00:04Z"},
        {"symbol": "BTCUSDT", "price": 50005.0, "timestamp": "2025-01-01T10:00:05Z"},
    ])
    return mock_client
