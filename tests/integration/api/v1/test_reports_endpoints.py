import pytest
from httpx import AsyncClient
from uuid import UUID
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession

from ultibot_backend.main import app
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.dependencies import get_persistence_service
from ultibot_backend.core.domain_models.trade_models import Trade

# User ID fijo para las pruebas
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture para un cliente de prueba asíncrono de FastAPI.
    Sobrescribe la dependencia de persistencia para usar la sesión de BD del test.
    """
    persistence_service_override = SupabasePersistenceService(db_session=db_session)

    def override_get_persistence_service():
        return persistence_service_override

    app.dependency_overrides[get_persistence_service] = override_get_persistence_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture(scope="function", autouse=True)
async def setup_test_trades(db_session: AsyncSession):
    """
    Configura trades de prueba en la base de datos usando la sesión del test.
    El rollback de la sesión se encargará de la limpieza.
    """
    sample_trades_data = [
        {
            "id": "a1b2c3d4-e5f6-7788-9900-aabbccddeeff",
            "user_id": str(FIXED_USER_ID),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "mode": "paper",
            "position_status": "closed",
            "opened_at": datetime.now(timezone.utc) - timedelta(days=5),
            "closed_at": datetime.now(timezone.utc) - timedelta(days=4),
            "pnl_usd": 150.0,
            "pnl_percentage": 5.0,
            "closing_reason": "TAKE_PROFIT",
            "entry_order_data": {"id": "entry-1", "price": 50000.0, "quantity": 0.005},
            "exit_orders_data": [{"id": "exit-1", "price": 53000.0, "quantity": 0.005}]
        },
        {
            "id": "b2c3d4e5-f6a7-8899-0011-bbccddeeff00",
            "user_id": str(FIXED_USER_ID),
            "symbol": "ETHUSDT",
            "side": "BUY",
            "mode": "paper",
            "position_status": "closed",
            "opened_at": datetime.now(timezone.utc) - timedelta(days=3),
            "closed_at": datetime.now(timezone.utc) - timedelta(days=2),
            "pnl_usd": -75.0,
            "pnl_percentage": -3.75,
            "closing_reason": "STOP_LOSS",
            "entry_order_data": {"id": "entry-2", "price": 2000.0, "quantity": 1.0},
            "exit_orders_data": [{"id": "exit-2", "price": 1925.0, "quantity": 1.0}]
        },
        {
            "id": "c3d4e5f6-a7b8-9900-1122-ccddeeff0011",
            "user_id": str(FIXED_USER_ID),
            "symbol": "ADAUSDT",
            "side": "BUY",
            "mode": "paper",
            "position_status": "closed",
            "opened_at": datetime.now(timezone.utc) - timedelta(days=1),
            "closed_at": datetime.now(timezone.utc) - timedelta(hours=12),
            "pnl_usd": 25.0,
            "pnl_percentage": 2.5,
            "closing_reason": "MANUAL",
            "entry_order_data": {"id": "entry-3", "price": 0.5, "quantity": 2000.0},
            "exit_orders_data": [{"id": "exit-3", "price": 0.5125, "quantity": 2000.0}]
        }
    ]
    
    persistence_service = SupabasePersistenceService(db_session=db_session)
    for trade_data in sample_trades_data:
        # Convertir a un diccionario que el upsert_trade pueda manejar
        await persistence_service.upsert_trade(trade_data)

    yield


class TestPaperTradingHistoryEndpoint:
    @pytest.mark.asyncio
    async def test_get_paper_trading_history_success(self, client: AsyncClient):
        response = await client.get("/api/v1/trades/history/paper")
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert "total_count" in data
        assert "has_more" in data
        trades = data["trades"]
        assert isinstance(trades, list)
        assert len(trades) == 3
        assert trades[0]["symbol"] == "ADAUSDT" # El más reciente primero

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_symbol_filter(self, client: AsyncClient):
        params = {"symbol": "BTCUSDT"}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_date_filters(self, client: AsyncClient):
        start_date = (datetime.now(timezone.utc) - timedelta(days=3.5)).isoformat()
        end_date = (datetime.now(timezone.utc) - timedelta(days=1.5)).isoformat()
        params = {"start_date": start_date, "end_date": end_date}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "ETHUSDT"

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_pagination(self, client: AsyncClient):
        params = {"limit": 2, "offset": 1}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 2
        assert data["trades"][0]["symbol"] == "ETHUSDT"
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_invalid_params(self, client: AsyncClient):
        params = {"limit": -1}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 422


class TestPaperTradingPerformanceEndpoint:
    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_success(self, client: AsyncClient):
        response = await client.get("/api/v1/portfolio/paper/performance_summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 3
        assert data["winning_trades"] == 2
        assert data["losing_trades"] == 1
        assert pytest.approx(data["win_rate"]) == 66.67
        assert pytest.approx(data["total_pnl"]) == 100.0

    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_no_trades(self, client: AsyncClient):
        start_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        params = {"start_date": start_date}
        response = await client.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
        assert data["total_pnl"] == 0.0


class TestRealTradingEndpoints:
    @pytest.mark.asyncio
    async def test_get_real_trading_history_success(self, client: AsyncClient):
        response = await client.get("/api/v1/trades/history/real")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 0 # No real trades were created in setup

    @pytest.mark.asyncio
    async def test_get_real_trading_performance_success(self, client: AsyncClient):
        response = await client.get("/api/v1/portfolio/real/performance_summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
