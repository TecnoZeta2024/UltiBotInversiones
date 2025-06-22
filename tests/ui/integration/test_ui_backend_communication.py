import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from typing import AsyncGenerator, Generator

import httpx
from httpx import RequestError

from src.ultibot_backend.main import app
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.workers import StrategiesWorker

@pytest.fixture(scope="module")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Asegura que todos los tests en el módulo usen el mismo event loop."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture
async def api_client_fixture() -> AsyncGenerator[UltiBotAPIClient, None]:
    """
    Fixture que proporciona una instancia del cliente de API configurada
    para apuntar al backend de prueba en memoria.
    """
    base_url = "http://testserver"
    async with httpx.AsyncClient(app=app, base_url=base_url) as test_httpx_client:
        api_client = UltiBotAPIClient(base_url=base_url)
        api_client._client = test_httpx_client
        yield api_client
        # El cliente se cierra automáticamente por el context manager 'async with'

@pytest.mark.asyncio
async def test_successful_connection_and_data_fetch(api_client_fixture: UltiBotAPIClient):
    """
    Test 'happy path': Verifica que el worker puede conectarse y obtener datos
    del backend simulado a través del cliente de API.
    """
    # Arrange: Creamos un worker con el cliente de API configurado
    # Este worker usa datos mock, pero la prueba valida la capa de comunicación.
    worker = StrategiesWorker(api_client=api_client_fixture)
    
    # Act: Ejecutamos la corutina del worker directamente para el test
    # (No necesitamos QThread aquí)
    strategies = await worker._fetch_strategies(api_client_fixture)
    
    # Assert: Verificamos que se recibieron los datos esperados
    assert isinstance(strategies, list)
    assert len(strategies) > 0
    assert "name" in strategies[0]
    assert strategies[0]['name'] == 'Momentum Breakout'

@pytest.mark.asyncio
@patch('httpx.AsyncClient.request', new_callable=AsyncMock)
async def test_connection_failure_and_recovery(mock_request: AsyncMock, api_client_fixture: UltiBotAPIClient):
    """
    Test de resiliencia: Simula un fallo de conexión inicial y verifica
    que el cliente se recupera y obtiene los datos gracias a `tenacity`.
    """
    # Arrange: Configurar el mock para que falle la primera vez y funcione la segunda.
    mock_request.side_effect = [
        RequestError("Connection refused", request=httpx.Request("GET", "/")),
        httpx.Response(
            status_code=200,
            json=[{'id': 'trade_123', 'symbol': 'BTC/USDT', 'status': 'open'}],
            request=httpx.Request("GET", "/")  # Añadir el objeto request a la respuesta
        )
    ]
    
    # Act: Llamamos a un método del cliente que usa _make_request.
    # Gracias al decorador @retry, debería fallar, reintentar y luego tener éxito.
    result = await api_client_fixture.get_trades(trading_mode="paper")

    # Assert
    assert result is not None
    assert isinstance(result, list)
    assert result[0]['symbol'] == 'BTC/USDT'
    
    # Verificar que se llamó dos veces (fallo + éxito)
    assert mock_request.call_count == 2
