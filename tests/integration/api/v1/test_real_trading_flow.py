"""
Tests de integración para el flujo de trading, validando la interacción
entre la API, el motor de trading y los adaptadores de servicios externos.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal

from ultibot_backend.main import app
from ultibot_backend.core.domain_models.trading import Order, OrderSide, OrderType, OrderStatus
from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.dependencies import get_trading_engine_service

@pytest.mark.asyncio
async def test_real_trading_market_order_flow():
    """
    Valida el flujo completo de una orden de mercado.
    1. Cliente envía request a la API.
    2. API invoca al TradingEngine.
    3. TradingEngine ejecuta la lógica de la orden.
    4. Se retorna una respuesta exitosa.
    """
    symbol = "BTCUSDT"
    quantity = Decimal("0.01")
    price = Decimal("50000.0")

    # Mock del TradingEngine completo
    mock_trading_engine = AsyncMock(spec=TradingEngine)
    mock_trading_engine.execute_order.return_value = Order(
        id=uuid4(),  # Corregido: Pasar UUID directamente
        symbol=symbol,
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=quantity,
        price=price,
        status=OrderStatus.FILLED
    )

    # Sobrescribir la dependencia en la app de FastAPI usando la función proveedora como clave
    app.dependency_overrides[get_trading_engine_service] = lambda: mock_trading_engine

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/trading/order",
            json={
                "symbol": symbol,
                "side": "BUY",
                "quantity": str(quantity),
                "price": str(price),
                "order_type": "MARKET",
                "trading_mode": "real",
                "strategy_id": None
            }
        )

    # Verificaciones
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["symbol"] == symbol
    assert response_data["status"] == "FILLED"
    assert response_data["side"] == "BUY"

    # Verificar que se llamó al método del engine con los argumentos correctos
    mock_trading_engine.execute_order.assert_called_once()
    call_args = mock_trading_engine.execute_order.call_args[1]
    assert call_args['symbol'] == symbol
    assert call_args['quantity'] == quantity
    assert call_args['user_id'] is not None

    # Limpiar la sobrescritura de dependencias para no afectar otros tests
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_trading_api_rejects_invalid_order_type():
    """
    Verifica que la API rechaza una orden con un tipo de orden inválido.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/trading/order",
            json={
                "symbol": "ETHUSDT",
                "side": "SELL",
                "quantity": "0.1",
                "price": "2500.0",
                "order_type": "INVALID_TYPE", # Tipo inválido
                "trading_mode": "paper",
                "strategy_id": None
            }
        )
    
    assert response.status_code == 422  # Unprocessable Entity
