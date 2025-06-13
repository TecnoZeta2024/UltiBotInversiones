import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4, UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from ultibot_backend.main import app
from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.dependencies import get_performance_service, get_strategy_service
from ultibot_backend.core.domain_models.trade_models import Trade, PositionStatus, TradeOrderDetails
from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType
from ultibot_backend.app_config import settings

FIXED_TEST_USER_ID = settings.FIXED_USER_ID

def create_valid_entry_order_data(order_id: str = "order1") -> dict:
    """Factory para crear datos de TradeOrderDetails válidos."""
    return {
        "id": order_id,
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "status": "FILLED",
        "executedQuantity": 1.0,
        "executedPrice": 50000.0,
        "cost": 50000.0,
        "fee": 50.0,
        "feeAsset": "USDT",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@pytest.fixture
def mock_strategy_service():
    return AsyncMock(spec=StrategyService)

@pytest.fixture
def mock_performance_service():
    """Mock del PerformanceService con métodos correctos según el endpoint real."""
    mock = AsyncMock(spec=PerformanceService)
    # ✅ CORREGIDO: Usar el nombre del método que realmente llama el endpoint
    mock.get_all_strategies_performance = AsyncMock()
    mock.get_trade_performance_metrics = AsyncMock()
    return mock

@pytest.fixture
async def client(mock_performance_service: AsyncMock, mock_strategy_service: AsyncMock):
    """Cliente de prueba asíncrono con dependencias mockeadas."""
    
    def override_get_performance():
        return mock_performance_service
        
    def override_get_strategy():
        return mock_strategy_service

    app.dependency_overrides[get_performance_service] = override_get_performance
    app.dependency_overrides[get_strategy_service] = override_get_strategy

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_strategies_performance_no_data(client: AsyncClient, mock_performance_service: AsyncMock):
    """Test del endpoint /strategies sin datos."""
    # ✅ CORREGIDO: Usar el método correcto que llama el endpoint
    mock_performance_service.get_all_strategies_performance.return_value = []
    
    response = await client.get("/api/v1/performance/strategies")
    
    assert response.status_code == 200
    assert response.json() == []
    # ✅ CORREGIDO: Verificar llamada con parámetros correctos según el endpoint
    mock_performance_service.get_all_strategies_performance.assert_called_once_with(
        user_id=str(FIXED_TEST_USER_ID), 
        mode_filter=None
    )

@pytest.mark.asyncio
async def test_get_strategies_performance_with_data(client: AsyncClient, mock_performance_service: AsyncMock):
    """Test del endpoint /strategies con datos."""
    strategy_id = uuid4()
    
    performance_data = [
        {
            "strategyId": str(strategy_id),
            "strategyName": "Test Strategy",
            "mode": "paper",
            "totalOperations": 1,
            "totalPnl": 100.0,
            "win_rate": 100.0,
        }
    ]
    # ✅ CORREGIDO: Usar el método correcto
    mock_performance_service.get_all_strategies_performance.return_value = performance_data

    response = await client.get("/api/v1/performance/strategies?mode=paper")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["strategyId"] == str(strategy_id)
    assert data[0]["totalPnl"] == 100.0
    
    # ✅ CORREGIDO: Verificar llamada con mode_filter correcto
    mock_performance_service.get_all_strategies_performance.assert_called_once_with(
        user_id=str(FIXED_TEST_USER_ID), 
        mode_filter="paper"  # El endpoint pasa el OperatingMode.value
    )

@pytest.mark.asyncio
async def test_get_strategies_performance_invalid_mode(client: AsyncClient):
    """Test con modo inválido que debe retornar 422."""
    response = await client.get("/api/v1/performance/strategies?mode=invalid_mode")
    assert response.status_code == 422
