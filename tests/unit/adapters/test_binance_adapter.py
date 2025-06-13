import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
from ultibot_backend.app_config import AppSettings
from ultibot_backend.core.domain_models.trading import Order, OrderSide, OrderType, OrderStatus

# Fixture para una configuración de AppSettings mockeada
@pytest.fixture
def mock_app_settings():
    """Provides a mock AppSettings object for tests."""
    return AppSettings(
        binance_api_key="test_key",
        binance_api_secret="test_secret",
        # Añadir otros campos requeridos por AppSettings con valores dummy
        db_host="localhost",
        db_port=5432,
        db_user="user",
        db_password="password",
        db_name="testdb",
        mobula_api_key="dummy",
        telegram_bot_token="dummy",
        telegram_chat_id="dummy",
        gemini_api_key="dummy",
        credential_encryption_key="a" * 44,
        log_level="INFO",
        supabase_url="http://dummy.url",
        supabase_key="dummy",
        db_pool_min_size=1,
        db_pool_max_size=1,
        fixed_user_id="user123",
        default_paper_trading_capital=10000.0,
        default_real_trading_exchange="binance",
        ai_trading_confidence_threshold=0.75
    )

# Fixture para el adaptador de Binance
@pytest.fixture
def binance_adapter(mock_app_settings):
    """Fixture to create a BinanceAdapter instance."""
    return BinanceAdapter(config=mock_app_settings)

@pytest.mark.asyncio
@patch('ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_get_market_data_success(MockAsyncClient, binance_adapter):
    """Test successful fetching of market data."""
    # Arrange
    mock_response_data = {"symbol": "BTCUSDT", "lastPrice": "50000.0"}
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    
    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    
    binance_adapter._client = mock_client_instance # Sobrescribir el cliente con el mock

    # Act
    result = await binance_adapter.get_market_data("BTCUSDT")

    # Assert
    assert result == mock_response_data
    mock_client_instance.get.assert_called_once_with(
        f"{binance_adapter._base_url}/ticker/24hr", params={"symbol": "BTCUSDT"}
    )

@pytest.mark.asyncio
@patch('ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_get_market_data_http_error(MockAsyncClient, binance_adapter):
    """Test handling of HTTPStatusError when fetching market data."""
    # Arrange
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.json.return_value = {"code": -1121, "msg": "Invalid symbol."}
    
    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )
    )
    binance_adapter._client = mock_client_instance

    # Act & Assert
    with pytest.raises(BinanceAPIError) as excinfo:
        await binance_adapter.get_market_data("INVALIDSYMBOL")
    
    assert excinfo.value.status_code == 404
    assert "Invalid symbol" in excinfo.value.response_data["msg"]

@pytest.mark.asyncio
@patch('ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_get_historical_data_success(MockAsyncClient, binance_adapter):
    """Test successful fetching of historical k-line data."""
    # Arrange
    mock_response_data = [
        [1625097600000, "40000", "42000", "39000", "41000", "1000", 1625183999999]
    ]
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    
    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    binance_adapter._client = mock_client_instance

    # Act
    result = await binance_adapter.get_historical_data("BTCUSDT", "1d", 1)

    # Assert
    assert result == mock_response_data
    mock_client_instance.get.assert_called_once_with(
        f"{binance_adapter._base_url}/klines",
        params={"symbol": "BTCUSDT", "interval": "1d", "limit": 1}
    )

@pytest.mark.asyncio
async def test_close_adapter(binance_adapter):
    """Test that the close method calls aclose on the httpx client."""
    # Arrange
    binance_adapter._client = AsyncMock(spec=httpx.AsyncClient)
    
    # Act
    await binance_adapter.close()
    
    # Assert
    binance_adapter._client.aclose.assert_awaited_once()
