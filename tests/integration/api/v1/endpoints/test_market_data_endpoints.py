import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from typing import Tuple
from fastapi import FastAPI
from dependencies import get_market_data_service

# Marcar todos los tests de este módulo como tests de integración
pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_get_tickers_success(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market/tickers responde correctamente con datos mockeados.
    """
    http_client, app = client
    # 1. Mockear el servicio de datos de mercado
    mock_service = AsyncMock()
    mock_service.get_market_data_rest.return_value = {
        "BTC/USDT": {"price": "50000.00", "change": "1.5", "volume": "1000"},
        "ETH/USDT": {"price": "4000.00", "change": "-0.5", "volume": "5000"}
    }
    
    # Sobrescribir la dependencia en la app
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    # 2. Hacer la llamada a la API
    response = await http_client.get("/api/v1/market/tickers?symbols=BTC/USDT,ETH/USDT")
    
    # 3. Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Find the BTC/USDT ticker in the list
    btc_ticker = next((item for item in data if item["symbol"] == "BTC/USDT"), None)
    assert btc_ticker is not None
    assert btc_ticker["price"] == "50000.00"
    
    # 4. Verificar que el mock fue llamado
    mock_service.get_market_data_rest.assert_awaited_once_with(['BTC/USDT', 'ETH/USDT'])
    
    # Limpiar el override para no afectar otros tests
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_ticker_24hr_success(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market-data/ticker/24hr/{symbol} responde correctamente con datos mockeados.
    """
    http_client, app = client
    # 1. Mockear el servicio de datos de mercado
    mock_service = AsyncMock()
    mock_service.get_ticker_24hr.return_value = {
        "symbol": "BTCUSDT",
        "priceChange": "100.00",
        "priceChangePercent": "0.20",
        "weightedAvgPrice": "50000.00",
        "lastPrice": "50100.00",
        "lastQty": "0.001",
        "openPrice": "50000.00",
        "highPrice": "50200.00",
        "lowPrice": "49900.00",
        "volume": "1000.00",
        "quoteVolume": "50100000.00",
        "openTime": 1678886400000,
        "closeTime": 1678972799999,
        "firstId": 12345,
        "lastId": 67890,
        "count": 500
    }
    
    # Sobrescribir la dependencia en la app
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    # 2. Hacer la llamada a la API
    response = await http_client.get("/api/v1/market/ticker/24hr/BTCUSDT")
    
    # 3. Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTCUSDT"
    assert data["lastPrice"] == "50100.00"
    assert data["volume"] == "1000.00"
    
    # 4. Verificar que el mock fue llamado
    mock_service.get_ticker_24hr.assert_awaited_once_with("BTCUSDT")
    
    # Limpiar el override para no afectar otros tests
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_klines_success(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market/klines responde correctamente con datos mockeados.
    """
    http_client, app = client
    # 1. Mockear el servicio
    mock_service = AsyncMock()
    mock_klines = [
        {"timestamp": 1672531200000, "open": "49000", "high": "49500", "low": "48500", "close": "49200", "volume": "100"},
        {"timestamp": 1672534800000, "open": "49200", "high": "49800", "low": "49100", "close": "49700", "volume": "120"}
    ]
    # Ensure the mock is awaitable
    mock_service.get_candlestick_data = AsyncMock(return_value=mock_klines)
    
    # Sobrescribir la dependencia
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    # 2. Hacer la llamada
    response = await http_client.get("/api/v1/market/klines?symbol=BTCUSDT&interval=1h&limit=2")
    
    # 3. Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["close"] == "49200"
    
    # 4. Verificar que el mock fue llamado
    mock_service.get_candlestick_data.assert_awaited_once_with(
        symbol="BTCUSDT", 
        interval="1h", 
        limit=2,
        start_time=None,
        end_time=None
    )
    
    # Limpiar el override
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_tickers_service_error(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market/tickers maneja errores del servicio de datos de mercado.
    """
    http_client, app = client
    mock_service = AsyncMock()
    mock_service.get_market_data_rest.side_effect = Exception("Service unavailable")
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    response = await http_client.get("/api/v1/market/tickers?symbols=BTC/USDT")
    
    assert response.status_code == 500
    assert "Service unavailable" in response.json()["detail"]
    mock_service.get_market_data_rest.assert_awaited_once_with(['BTC/USDT'])
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_ticker_24hr_invalid_symbol(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market-data/ticker/24hr/{symbol} maneja un símbolo inválido.
    """
    http_client, app = client
    # No mockeamos el servicio aquí para probar la validación de la ruta
    
    response = await http_client.get("/api/v1/market/ticker/24hr/INVALID_SYMBOL")
    
    assert response.status_code == 422 # Unprocessable Entity (FastAPI validation error)
    assert "value is not a valid enumeration member" in response.json()["detail"][0]["msg"]
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_ticker_24hr_service_error(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market-data/ticker/24hr/{symbol} maneja errores del servicio.
    """
    http_client, app = client
    mock_service = AsyncMock()
    mock_service.get_ticker_24hr.side_effect = Exception("External API error")
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    response = await http_client.get("/api/v1/market/ticker/24hr/BTCUSDT")
    
    assert response.status_code == 500
    assert "External API error" in response.json()["detail"]
    mock_service.get_ticker_24hr.assert_awaited_once_with("BTCUSDT")
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_klines_invalid_interval(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market/klines maneja un intervalo inválido.
    """
    http_client, app = client
    
    response = await http_client.get("/api/v1/market/klines?symbol=BTCUSDT&interval=INVALID&limit=1")
    
    assert response.status_code == 422
    assert "value is not a valid enumeration member" in response.json()["detail"][0]["msg"]
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_klines_service_error(client: Tuple[AsyncClient, FastAPI]):
    """
    Prueba que el endpoint /market/klines maneja errores del servicio.
    """
    http_client, app = client
    mock_service = AsyncMock()
    mock_service.get_candlestick_data.side_effect = Exception("Data retrieval failed")
    app.dependency_overrides[get_market_data_service] = lambda: mock_service
    
    response = await http_client.get("/api/v1/market/klines?symbol=BTCUSDT&interval=1h&limit=1")
    
    assert response.status_code == 500
    assert "Data retrieval failed" in response.json()["detail"]
    mock_service.get_candlestick_data.assert_awaited_once()
    app.dependency_overrides.clear()
