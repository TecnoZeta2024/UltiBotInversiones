"""
Pruebas de integración para los endpoints de reportes de trading.
"""

import pytest
import pytest_asyncio
import asyncpg
from uuid import UUID
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from fastapi.testclient import TestClient

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

# User ID fijo para las pruebas
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest_asyncio.fixture
async def setup_trades(db_session: asyncpg.Connection):
    """
    Inserta un conjunto de trades de prueba en la base de datos transaccional
    antes de cada test que use esta fixture. La transacción se revierte
    automáticamente por la fixture db_session.
    """
    sample_trades = [
        {
            "id": "test-trade-1", "user_id": str(FIXED_USER_ID), "symbol": "BTCUSDT", "mode": "paper",
            "position_status": "closed", "data": '{"pnl_usd": 150.0}',
            "created_at": datetime.now(timezone.utc) - timedelta(days=5), "updated_at": datetime.now(timezone.utc) - timedelta(days=4),
            "closed_at": datetime.now(timezone.utc) - timedelta(days=4)
        },
        {
            "id": "test-trade-2", "user_id": str(FIXED_USER_ID), "symbol": "ETHUSDT", "mode": "paper",
            "position_status": "closed", "data": '{"pnl_usd": -75.0}',
            "created_at": datetime.now(timezone.utc) - timedelta(days=3), "updated_at": datetime.now(timezone.utc) - timedelta(days=2),
            "closed_at": datetime.now(timezone.utc) - timedelta(days=2)
        },
        {
            "id": "test-trade-3", "user_id": str(FIXED_USER_ID), "symbol": "ADAUSDT", "mode": "paper",
            "position_status": "closed", "data": '{"pnl_usd": 25.0}',
            "created_at": datetime.now(timezone.utc) - timedelta(days=1), "updated_at": datetime.now(timezone.utc) - timedelta(hours=12),
            "closed_at": datetime.now(timezone.utc) - timedelta(hours=12)
        }
    ]

    for trade in sample_trades:
        await db_session.execute(
            """
            INSERT INTO trades (id, user_id, symbol, mode, position_status, data, created_at, updated_at, closed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            trade["id"], trade["user_id"], trade["symbol"], trade["mode"],
            trade["position_status"], trade["data"], trade["created_at"],
            trade["updated_at"], trade["closed_at"]
        )
    yield

@pytest.mark.usefixtures("setup_trades")
class TestPaperTradingHistoryEndpoint:
    """Pruebas para el endpoint GET /trades/history/paper."""

    def test_get_paper_trading_history_success(self, client: TestClient):
        response = client.get(f"/api/v1/trades/history/paper?user_id={FIXED_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert data["total_count"] == 3
        assert isinstance(data["trades"], list)

    def test_get_paper_trading_history_with_symbol_filter(self, client: TestClient):
        params = {"symbol": "BTCUSDT", "user_id": str(FIXED_USER_ID)}
        response = client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"

@pytest.mark.usefixtures("setup_trades")
class TestPaperTradingPerformanceEndpoint:
    """Pruebas para el endpoint GET /portfolio/paper/performance_summary."""

    def test_get_paper_trading_performance_success(self, client: TestClient):
        response = client.get(f"/api/v1/portfolio/paper/performance_summary?user_id={FIXED_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        expected_fields = ["total_trades", "winning_trades", "losing_trades", "win_rate", "total_pnl"]
        for field in expected_fields:
            assert field in data
        assert data["total_trades"] == 3
        assert data["winning_trades"] == 2
        assert data["losing_trades"] == 1
        assert data["total_pnl"] == pytest.approx(100.0)

    def test_get_paper_trading_performance_no_trades(self, client: TestClient):
        start_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        params = {"start_date": start_date, "user_id": str(FIXED_USER_ID)}
        response = client.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
        assert data["total_pnl"] == 0.0
