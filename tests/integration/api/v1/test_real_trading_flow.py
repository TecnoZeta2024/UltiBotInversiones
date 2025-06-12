"""
Tests de integración para el flujo de trading real, validando la interacción
entre la API, el motor de trading y los adaptadores de servicios externos.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

# Asumiendo que la app de FastAPI se puede importar para testing
from ultibot_backend.main import app
from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.domain_models.trading import Order, Portfolio

@pytest.mark.asyncio
async def test_real_trading_market_order_flow():
    """
    Valida el flujo completo de una orden de mercado en modo 'real'.
    1.  Cliente envía request a la API.
    2.  API invoca al TradingEngine.
    3.  TradingEngine usa el IBinanceAdapter para ejecutar la orden.
    4.  Se actualiza el portafolio en la base de datos.
    5.  Se retorna una respuesta exitosa.
    """
    user_id = "test_user_real_flow"
    symbol = "BTCUSDT"
    quantity = 0.01

    # Mock del adaptador de Binance
    mock_binance_adapter = AsyncMock()
    mock_binance_adapter.execute_order.return_value = Order(
        id="real_order_123",
        user_id=user_id,
        symbol=symbol,
        side="BUY",
        order_type="MARKET",
        quantity=quantity,
        price=50000.0,
        status="FILLED"
    )

    # Mock del repositorio de base de datos
    mock_repo = AsyncMock()
    mock_repo.get_portfolio.return_value = Portfolio(user_id=user_id, available_balance_usdt=10000.0)
    
    # Inyectar mocks en el contenedor de dependencias de la app
    with app.container.binance_adapter.override(mock_binance_adapter), \
         app.container.persistence_adapter.override(mock_repo):

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/trading/market-order",
                json={
                    "user_id": user_id,
                    "symbol": symbol,
                    "side": "BUY",
                    "quantity": quantity,
                    "trading_mode": "real",
                    "api_key": "test_key",  # Requerido por el modelo Pydantic
                    "api_secret": "test_secret" # Requerido por el modelo Pydantic
                }
            )

    # Verificaciones
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["order_id"] == "real_order_123"
    assert response_data["symbol"] == symbol
    assert response_data["status"] == "FILLED"
    assert response_data["trading_mode"] == "real"

    # Verificar que se llamó al adaptador de Binance
    mock_binance_adapter.execute_order.assert_called_once()
    
    # Verificar que se intentó actualizar el portafolio
    mock_repo.update_portfolio.assert_called_once()

@pytest.mark.asyncio
async def test_get_real_portfolio_snapshot():
    """
    Valida la obtención del snapshot del portafolio en modo 'real'.
    """
    user_id = "test_user_portfolio_real"

    # Mock del adaptador de persistencia
    mock_persistence_adapter = AsyncMock()
    mock_persistence_adapter.get_portfolio.return_value = Portfolio(
        user_id=user_id,
        trading_mode="real",
        available_balance_usdt=5000.0,
        total_assets_value_usd=15000.0,
        total_portfolio_value_usd=20000.0,
        assets=[]
    )

    with app.container.persistence_adapter.override(mock_persistence_adapter):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(f"/api/v1/portfolio/snapshot/{user_id}?trading_mode=real")

    # Verificaciones
    assert response.status_code == 200
    data = response.json()
    assert data["real_trading"]["user_id"] == user_id
    assert data["real_trading"]["total_portfolio_value_usd"] == 20000.0
    
    mock_persistence_adapter.get_portfolio.assert_called_once_with(user_id, "real")

@pytest.mark.asyncio
async def test_real_trading_requires_credentials():
    """
    Verifica que la API rechaza una orden 'real' sin credenciales.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/trading/market-order",
            json={
                "user_id": "some_user",
                "symbol": "ETHUSDT",
                "side": "SELL",
                "quantity": 0.1,
                "trading_mode": "real"
                # Faltan api_key y api_secret
            }
        )
    
    assert response.status_code == 422  # Unprocessable Entity
