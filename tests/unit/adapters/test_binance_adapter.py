import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
import pytest_asyncio # Importar pytest_asyncio

from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
from shared.data_types import AssetBalance

@pytest_asyncio.fixture # Usar pytest_asyncio.fixture
async def binance_adapter():
    """Fixture para crear una instancia de BinanceAdapter y asegurar su cierre."""
    adapter = BinanceAdapter()
    yield adapter
    await adapter.close()

@pytest.mark.asyncio
async def test_get_account_info_success(binance_adapter: BinanceAdapter):
    """Prueba get_account_info con una respuesta exitosa de la API."""
    mock_response_data = {
        "makerCommission": 15,
        "takerCommission": 15,
        "buyerCommission": 0,
        "sellerCommission": 0,
        "canTrade": True,
        "canWithdraw": True,
        "canDeposit": True,
        "updateTime": 1234567890000,
        "accountType": "SPOT",
        "balances": [
            {"asset": "BTC", "free": "1.0", "locked": "0.5"},
            {"asset": "USDT", "free": "1000", "locked": "0"}
        ],
        "permissions": ["SPOT"]
    }

    # Mockear _make_request para que devuelva la respuesta simulada
    binance_adapter._make_request = AsyncMock(return_value=mock_response_data)

    api_key = "test_key"
    api_secret = "test_secret"
    
    account_info = await binance_adapter.get_account_info(api_key, api_secret)

    assert account_info == mock_response_data
    binance_adapter._make_request.assert_called_once_with(
        "GET", "/api/v3/account", api_key, api_secret, signed=True
    )

@pytest.mark.asyncio
async def test_get_account_info_api_error(binance_adapter: BinanceAdapter):
    """Prueba get_account_info cuando la API devuelve un error."""
    # Mockear _make_request para que lance BinanceAPIError
    binance_adapter._make_request = AsyncMock(
        side_effect=BinanceAPIError("API Error", status_code=500, response_data={"msg": "Server error", "code": -1000})
    )

    api_key = "test_key"
    api_secret = "test_secret"

    with pytest.raises(BinanceAPIError) as excinfo:
        await binance_adapter.get_account_info(api_key, api_secret)
    
    assert excinfo.value.status_code == 500
    assert excinfo.value.response_data == {"msg": "Server error", "code": -1000}

@pytest.mark.asyncio
async def test_get_spot_balances_success(binance_adapter: BinanceAdapter):
    """Prueba get_spot_balances con una respuesta exitosa."""
    mock_account_info_data = {
        "balances": [
            {"asset": "BTC", "free": "1.00000000", "locked": "0.50000000"},
            {"asset": "USDT", "free": "1000.00000000", "locked": "0.00000000"},
            {"asset": "ETH", "free": "0.00000000", "locked": "0.00000000"} # Balance cero
        ]
    }
    # Mockear get_account_info
    binance_adapter.get_account_info = AsyncMock(return_value=mock_account_info_data)

    api_key = "test_key"
    api_secret = "test_secret"

    balances = await binance_adapter.get_spot_balances(api_key, api_secret)

    assert len(balances) == 2 # ETH no debería estar porque su total es 0
    
    btc_balance = next(b for b in balances if b.asset == "BTC")
    usdt_balance = next(b for b in balances if b.asset == "USDT")

    assert btc_balance.asset == "BTC"
    assert btc_balance.free == 1.0
    assert btc_balance.locked == 0.5
    assert btc_balance.total == 1.5

    assert usdt_balance.asset == "USDT"
    assert usdt_balance.free == 1000.0
    assert usdt_balance.locked == 0.0
    assert usdt_balance.total == 1000.0
    
    binance_adapter.get_account_info.assert_called_once_with(api_key, api_secret)

@pytest.mark.asyncio
async def test_get_spot_balances_parsing_error(binance_adapter: BinanceAdapter):
    """Prueba get_spot_balances cuando hay un error al parsear un balance."""
    mock_account_info_data = {
        "balances": [
            {"asset": "BTC", "free": "1.0", "locked": "0.5"},
            {"asset": "XYZ", "free": "invalid_value", "locked": "0.1"} # Valor inválido
        ]
    }
    binance_adapter.get_account_info = AsyncMock(return_value=mock_account_info_data)
    
    # Mockear print para capturar la advertencia
    with patch('builtins.print') as mock_print:
        balances = await binance_adapter.get_spot_balances("key", "secret")
        assert len(balances) == 1
        assert balances[0].asset == "BTC"
        mock_print.assert_called_with("Advertencia: No se pudo parsear el balance para el activo XYZ: could not convert string to float: 'invalid_value'")

@pytest.mark.asyncio
@patch('src.ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_make_request_get_success(MockAsyncClient):
    """Prueba _make_request para un GET exitoso."""
    # Necesitamos una nueva instancia de adapter para que use el MockAsyncClient
    adapter = BinanceAdapter()
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "success"}
    
    # Configurar el mock del cliente para que su método get devuelva el mock_response
    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.aclose = AsyncMock() # Asegurar que aclose sea awaitable

    api_key = "test_key"
    api_secret = "test_secret" # No usado en GET no firmado, pero requerido por la firma del método
    endpoint = "/api/v3/time"
    
    result = await adapter._make_request("GET", endpoint, api_key, api_secret, signed=False)

    assert result == {"data": "success"}
    mock_client_instance.get.assert_called_once_with(endpoint, params={}, headers={"X-MBX-APIKEY": api_key})


@pytest.mark.asyncio
@patch('src.ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_make_request_retry_on_5xx_then_success(MockAsyncClient):
    """Prueba que _make_request reintenta en error 5xx y luego tiene éxito."""
    adapter = BinanceAdapter()

    mock_error_response = MagicMock(spec=httpx.Response)
    mock_error_response.status_code = 500
    mock_error_response.text = '{"msg":"Server error","code":-1000}'
    mock_error_response.json.return_value = {"msg":"Server error","code":-1000}
    
    mock_success_response = MagicMock(spec=httpx.Response)
    mock_success_response.status_code = 200
    mock_success_response.json.return_value = {"data": "success_after_retry"}

    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(side_effect=[
        httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_error_response),
        mock_success_response
    ])
    mock_client_instance.aclose = AsyncMock() # Asegurar que aclose sea awaitable
    
    # Mockear asyncio.sleep para que no espere realmente
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        result = await adapter._make_request("GET", "/api/v3/ping", "key", "secret", signed=False)
        assert result == {"data": "success_after_retry"}
        assert mock_client_instance.get.call_count == 2
        mock_sleep.assert_called_once_with(adapter.RETRY_DELAY_SECONDS)

@pytest.mark.asyncio
@patch('src.ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_make_request_fail_after_retries_on_5xx(MockAsyncClient):
    """Prueba que _make_request falla después de todos los reintentos en error 5xx."""
    adapter = BinanceAdapter()

    mock_error_response = MagicMock(spec=httpx.Response)
    mock_error_response.status_code = 502
    mock_error_response.text = '{"msg":"Bad Gateway","code":-1002}'
    mock_error_response.json.return_value = {"msg":"Bad Gateway","code":-1002}

    mock_client_instance = MockAsyncClient.return_value
    # Configurar para que siempre falle con HTTPStatusError
    mock_client_instance.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("Server Error", request=MagicMock(), response=mock_error_response)
    )
    mock_client_instance.aclose = AsyncMock() # Asegurar que aclose sea awaitable

    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(BinanceAPIError) as excinfo:
            await adapter._make_request("GET", "/api/v3/ping", "key", "secret", signed=False)
        
        assert excinfo.value.status_code == 502
        assert mock_client_instance.get.call_count == adapter.RETRY_ATTEMPTS
        assert mock_sleep.call_count == adapter.RETRY_ATTEMPTS - 1

@pytest.mark.asyncio
@patch('src.ultibot_backend.adapters.binance_adapter.httpx.AsyncClient')
async def test_make_request_client_error_no_retry(MockAsyncClient):
    """Prueba que _make_request no reintenta en errores de cliente (4xx)."""
    adapter = BinanceAdapter()
    
    mock_error_response = MagicMock(spec=httpx.Response)
    mock_error_response.status_code = 400
    mock_error_response.text = '{"msg":"Bad Request","code":-1102}'
    mock_error_response.json.return_value = {"msg":"Bad Request","code":-1102}

    mock_client_instance = MockAsyncClient.return_value
    mock_client_instance.get = AsyncMock(
        side_effect=httpx.HTTPStatusError("Client Error", request=MagicMock(), response=mock_error_response)
    )
    mock_client_instance.aclose = AsyncMock() # Asegurar que aclose sea awaitable
    
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        with pytest.raises(BinanceAPIError) as excinfo:
            await adapter._make_request("GET", "/api/v3/order", "key", "secret", params={"symbol": "BTCUSDT"}, signed=True)
        
        assert excinfo.value.status_code == 400
        assert mock_client_instance.get.call_count == 1 # Solo un intento
        mock_sleep.assert_not_called() # No se debe llamar a sleep

