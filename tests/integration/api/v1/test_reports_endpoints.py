"""
Pruebas de integración para los endpoints de reportes de trading.
"""

import pytest
import pytest_asyncio
import asyncpg
import json # Importar json
from uuid import UUID
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text # Importar text

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

# User ID fijo para las pruebas
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest_asyncio.fixture
async def setup_trades(db_session: AsyncSession, trade_factory):
    """
    Inserta un conjunto de trades de prueba en la base de datos transaccional
    antes de cada test que use esta fixture, utilizando la trade_factory.
    La transacción se revierte automáticamente por la fixture db_session.
    """
    sample_trades_data = [
        trade_factory(id="test-trade-1", symbol="BTCUSDT", pnl_usd=150.0, side="buy"),
        trade_factory(id="test-trade-2", symbol="ETHUSDT", pnl_usd=-75.0, side="sell"),
        trade_factory(id="test-trade-3", symbol="ADAUSDT", pnl_usd=25.0, side="buy")
    ]

    for trade_data in sample_trades_data:
            await db_session.execute(
                text("""
                INSERT INTO trades (id, user_id, symbol, mode, position_status, data, created_at, updated_at, closed_at, side)
                VALUES (:id, :user_id, :symbol, :mode, :position_status, :data, :created_at, :updated_at, :closed_at, :side)
"""),
                trade_data
            )
    await db_session.commit()
    yield

@pytest.mark.usefixtures("setup_trades")
@pytest.mark.asyncio
class TestPaperTradingHistoryEndpoint:
    """Pruebas para el endpoint GET /trades/history/paper."""

    async def test_get_paper_trading_history_success(self, client_with_db: AsyncClient):
        response = await client_with_db.get(f"/api/v1/trades/history/paper?user_id={FIXED_USER_ID}")
        if response.status_code != 200:
            print(f"Error Response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "trades" in data
        assert data["total_count"] == 3
        assert isinstance(data["trades"], list)

    async def test_get_paper_trading_history_with_symbol_filter(self, client_with_db: AsyncClient):
        params = {"symbol": "BTCUSDT", "user_id": str(FIXED_USER_ID)}
        response = await client_with_db.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 1
        assert data["trades"][0]["symbol"] == "BTCUSDT"

@pytest.mark.usefixtures("setup_trades")
@pytest.mark.asyncio
class TestPaperTradingPerformanceEndpoint:
    """Pruebas para el endpoint GET /portfolio/paper/performance_summary."""

    async def test_get_paper_trading_performance_success(self, client_with_db: AsyncClient):
        response = await client_with_db.get(f"/api/v1/portfolio/paper/performance_summary?user_id={FIXED_USER_ID}")
        assert response.status_code == 200
        data = response.json()
        expected_fields = ["total_trades", "winning_trades", "losing_trades", "win_rate", "total_pnl"]
        for field in expected_fields:
            assert field in data
        assert data["total_trades"] == 3
        assert data["winning_trades"] == 2
        assert data["losing_trades"] == 1
        assert float(data["total_pnl"]) == pytest.approx(100.0)

    async def test_get_paper_trading_performance_no_trades(self, client_with_db: AsyncClient):
        start_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        params = {"start_date": start_date, "user_id": str(FIXED_USER_ID)}
        response = await client_with_db.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_trades"] == 0
        assert float(data["total_pnl"]) == 0.0
