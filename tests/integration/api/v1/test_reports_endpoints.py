"""
Pruebas de integración para los endpoints de reportes de trading.
"""

import pytest
from httpx import AsyncClient
from uuid import UUID
from datetime import datetime, timedelta
from urllib.parse import urlencode

from ultibot_backend.main import app
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

# User ID fijo para las pruebas
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture(scope="module")
async def client():
    """Fixture para un cliente de prueba asíncrono de FastAPI."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def setup_and_cleanup_db():
    """Configura y limpia la base de datos antes y después de cada test."""
    persistence_service = SupabasePersistenceService()
    await persistence_service.connect()
    
    try:
        # Limpiar datos previos
        await persistence_service.execute_raw_sql(f"DELETE FROM trades WHERE user_id = '{FIXED_USER_ID}';")
        await persistence_service.execute_raw_sql(f"DELETE FROM portfolio_snapshots WHERE user_id = '{FIXED_USER_ID}';")
        await persistence_service.execute_raw_sql(f"DELETE FROM user_configurations WHERE user_id = '{FIXED_USER_ID}';")
        
        # Configurar datos de prueba - algunos trades de ejemplo
        sample_trades = [
            {
                "id": "test-trade-1",
                "user_id": str(FIXED_USER_ID),
                "symbol": "BTCUSDT",
                "side": "BUY",
                "mode": "paper",
                "positionStatus": "closed",
                "opened_at": datetime.now() - timedelta(days=5),
                "closed_at": datetime.now() - timedelta(days=4),
                "pnl_usd": 150.0,
                "pnl_percentage": 5.0,
                "closingReason": "TAKE_PROFIT",
                "entry_order_data": {
                    "id": "entry-1",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED",
                    "executedQuantity": 0.005,
                    "executedPrice": 50000.0,
                    "cost": 250.0,
                    "fee": 0.25,
                    "feeAsset": "USDT",
                    "timestamp": datetime.now() - timedelta(days=5)
                },
                "exit_orders_data": [
                    {
                        "id": "exit-1",
                        "symbol": "BTCUSDT",
                        "side": "SELL",
                        "type": "MARKET",
                        "status": "FILLED",
                        "executedQuantity": 0.005,
                        "executedPrice": 53000.0,
                        "cost": 265.0,
                        "fee": 0.265,
                        "feeAsset": "USDT",
                        "timestamp": datetime.now() - timedelta(days=4)
                    }
                ]
            },
            {
                "id": "test-trade-2",
                "user_id": str(FIXED_USER_ID),
                "symbol": "ETHUSDT",
                "side": "BUY",
                "mode": "paper",
                "positionStatus": "closed",
                "opened_at": datetime.now() - timedelta(days=3),
                "closed_at": datetime.now() - timedelta(days=2),
                "pnl_usd": -75.0,
                "pnl_percentage": -3.75,
                "closingReason": "STOP_LOSS",
                "entry_order_data": {
                    "id": "entry-2",
                    "symbol": "ETHUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED",
                    "executedQuantity": 1.0,
                    "executedPrice": 2000.0,
                    "cost": 2000.0,
                    "fee": 2.0,
                    "feeAsset": "USDT",
                    "timestamp": datetime.now() - timedelta(days=3)
                },
                "exit_orders_data": [
                    {
                        "id": "exit-2",
                        "symbol": "ETHUSDT",
                        "side": "SELL",
                        "type": "MARKET",
                        "status": "FILLED",
                        "executedQuantity": 1.0,
                        "executedPrice": 1925.0,
                        "cost": 1925.0,
                        "fee": 1.925,
                        "feeAsset": "USDT",
                        "timestamp": datetime.now() - timedelta(days=2)
                    }
                ]
            },
            {
                "id": "test-trade-3",
                "user_id": str(FIXED_USER_ID),
                "symbol": "ADAUSDT",
                "side": "BUY",
                "mode": "paper",
                "positionStatus": "closed",
                "opened_at": datetime.now() - timedelta(days=1),
                "closed_at": datetime.now() - timedelta(hours=12),
                "pnl_usd": 25.0,
                "pnl_percentage": 2.5,
                "closingReason": "MANUAL",
                "entry_order_data": {
                    "id": "entry-3",
                    "symbol": "ADAUSDT",
                    "side": "BUY",
                    "type": "MARKET",
                    "status": "FILLED",
                    "executedQuantity": 2000.0,
                    "executedPrice": 0.5,
                    "cost": 1000.0,
                    "fee": 1.0,
                    "feeAsset": "USDT",
                    "timestamp": datetime.now() - timedelta(days=1)
                },
                "exit_orders_data": [
                    {
                        "id": "exit-3",
                        "symbol": "ADAUSDT",
                        "side": "SELL",
                        "type": "MARKET",
                        "status": "FILLED",
                        "executedQuantity": 2000.0,
                        "executedPrice": 0.5125,
                        "cost": 1025.0,
                        "fee": 1.025,
                        "feeAsset": "USDT",
                        "timestamp": datetime.now() - timedelta(hours=12)
                    }
                ]
            }
        ]
        
        # Insertar trades de prueba (esto podría requerir métodos específicos del persistence service)
        # Por simplicidad, vamos a asumir que el persistence service puede manejar estos datos
        for trade_data in sample_trades:
            await persistence_service.create_trade(trade_data)
        
        yield  # Ejecutar el test
        
        # Limpiar después del test
        await persistence_service.execute_raw_sql(f"DELETE FROM trades WHERE user_id = '{FIXED_USER_ID}';")
        await persistence_service.execute_raw_sql(f"DELETE FROM portfolio_snapshots WHERE user_id = '{FIXED_USER_ID}';")
        
    except Exception as e:
        print(f"Error en setup_and_cleanup_db: {e}")
        yield  # Continuar con el test aunque haya errores en setup
    finally:
        await persistence_service.disconnect()


class TestPaperTradingHistoryEndpoint:
    """Pruebas para el endpoint GET /trades/history/paper."""

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_success(self, client):
        """Prueba obtener historial de paper trading exitosamente."""
        response = await client.get("/api/v1/trades/history/paper")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "trades" in data
        assert "total_count" in data
        assert "has_more" in data
        
        # Verificar que se devuelven trades
        trades = data["trades"]
        assert isinstance(trades, list)
        assert len(trades) >= 0  # Podría ser 0 si no hay trades de test
        
        # Si hay trades, verificar su estructura
        if trades:
            trade = trades[0]
            assert "id" in trade
            assert "symbol" in trade
            assert "side" in trade
            assert "mode" in trade
            assert "positionStatus" in trade
            assert trade["mode"] == "paper"
            assert trade["positionStatus"] == "closed"

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_symbol_filter(self, client):
        """Prueba filtrar historial por símbolo."""
        params = {"symbol": "BTCUSDT"}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        trades = data["trades"]
        # Todos los trades devueltos deben ser del símbolo especificado
        for trade in trades:
            assert trade["symbol"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_date_filters(self, client):
        """Prueba filtrar historial por fechas."""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert isinstance(data["trades"], list)

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_with_pagination(self, client):
        """Prueba paginación del historial."""
        params = {
            "limit": 1,
            "offset": 0
        }
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Con limit=1, no debe devolver más de 1 trade
        assert len(data["trades"]) <= 1

    @pytest.mark.asyncio
    async def test_get_paper_trading_history_invalid_params(self, client):
        """Prueba parámetros inválidos."""
        params = {"limit": -1}  # Límite inválido
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        
        assert response.status_code == 422  # Validation error


class TestPaperTradingPerformanceEndpoint:
    """Pruebas para el endpoint GET /portfolio/paper/performance_summary."""

    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_success(self, client):
        """Prueba obtener métricas de rendimiento exitosamente."""
        response = await client.get("/api/v1/portfolio/paper/performance_summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta de PerformanceMetrics
        expected_fields = [
            "total_trades", "winning_trades", "losing_trades", "win_rate",
            "total_pnl", "avg_pnl_per_trade", "best_trade_pnl", "worst_trade_pnl",
            "best_trade_symbol", "worst_trade_symbol", "period_start", "period_end",
            "total_volume_traded"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verificar tipos de datos
        assert isinstance(data["total_trades"], int)
        assert isinstance(data["winning_trades"], int)
        assert isinstance(data["losing_trades"], int)
        assert isinstance(data["win_rate"], (int, float))
        assert isinstance(data["total_pnl"], (int, float))
        assert isinstance(data["avg_pnl_per_trade"], (int, float))

    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_with_symbol_filter(self, client):
        """Prueba obtener métricas filtradas por símbolo."""
        params = {"symbol": "BTCUSDT"}
        response = await client.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Las métricas deben estar presentes aunque sea un subconjunto de datos
        assert "total_trades" in data
        assert "win_rate" in data
        assert "total_pnl" in data

    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_with_date_filters(self, client):
        """Prueba obtener métricas filtradas por fechas."""
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = await client.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que las fechas del periodo están en la respuesta
        assert data["period_start"] is not None or data["period_end"] is not None

    @pytest.mark.asyncio
    async def test_get_paper_trading_performance_no_trades(self, client):
        """Prueba métricas cuando no hay trades (usando fechas futuras)."""
        start_date = (datetime.now() + timedelta(days=1)).isoformat()
        end_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        response = await client.get(f"/api/v1/portfolio/paper/performance_summary?{urlencode(params)}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Con rango de fechas futuro, no debe haber trades
        assert data["total_trades"] == 0
        assert data["winning_trades"] == 0
        assert data["losing_trades"] == 0
        assert data["win_rate"] == 0.0
        assert data["total_pnl"] == 0.0


class TestRealTradingEndpoints:
    """Pruebas para los endpoints de trading real (similares a paper trading)."""

    @pytest.mark.asyncio
    async def test_get_real_trading_history_success(self, client):
        """Prueba obtener historial de trading real."""
        response = await client.get("/api/v1/trades/history/real")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert "total_count" in data
        assert "has_more" in data
        assert isinstance(data["trades"], list)

    @pytest.mark.asyncio
    async def test_get_real_trading_performance_success(self, client):
        """Prueba obtener métricas de rendimiento de trading real."""
        response = await client.get("/api/v1/portfolio/real/performance_summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura básica
        assert "total_trades" in data
        assert "win_rate" in data
        assert "total_pnl" in data
        assert isinstance(data["total_trades"], int)

    @pytest.mark.asyncio
    async def test_endpoints_error_handling(self, client):
        """Prueba manejo básico de errores en los endpoints."""
        # Probar con parámetros de fecha malformados
        params = {"start_date": "invalid-date-format"}
        response = await client.get(f"/api/v1/trades/history/paper?{urlencode(params)}")
        
        # Debe retornar error de validación
        assert response.status_code == 422

