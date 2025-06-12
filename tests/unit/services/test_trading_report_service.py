"""
Pruebas unitarias para TradingReportService.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from uuid import UUID

from ultibot_backend.services.trading_report_service import TradingReportService
from ultibot_backend.core.exceptions import ReportError
from shared.data_types import Trade, PerformanceMetrics, TradeOrderDetails # Eliminar Order, OrderSide, OrderType, OrderStatus


@pytest.fixture
def mock_persistence_service():
    """Mock del servicio de persistencia."""
    return AsyncMock()

@pytest.fixture
def trading_report_service(mock_persistence_service):
    """Instancia del servicio de reportes con dependencias mockeadas."""
    return TradingReportService(mock_persistence_service)

@pytest.fixture
def sample_trade_data():
    """Datos de ejemplo para trades, como objetos Trade."""
    raw_data = [
        {
            "id": UUID("123e4567-e89b-12d3-a456-426614174001"),
            "user_id": UUID("123e4567-e89b-12d3-a456-426614174000"),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "mode": "paper",
            "positionStatus": "closed",
            "opened_at": datetime(2024, 1, 1, 10, 0, 0),
            "closed_at": datetime(2024, 1, 1, 12, 0, 0),
            "pnl_usd": 150.0,
            "pnl_percentage": 5.0,
            "closingReason": "TAKE_PROFIT",
            "entryOrder": TradeOrderDetails(
                orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef01"),
                type="market",
                status="filled",
                requestedQuantity=0.005,
                executedQuantity=0.005,
                executedPrice=50000.0,
                timestamp=datetime(2024, 1, 1, 10, 0, 0),
                exchangeOrderId=None,
                commission=None,
                commissionAsset=None,
                rawResponse=None
            ),
            "exitOrders": [
                TradeOrderDetails(
                    orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef02"),
                    type="market",
                    status="filled",
                    requestedQuantity=0.005,
                    executedQuantity=0.005,
                    executedPrice=53000.0,
                    timestamp=datetime(2024, 1, 1, 12, 0, 0),
                    exchangeOrderId=None,
                    commission=None,
                    commissionAsset=None,
                    rawResponse=None
                )
            ],
            "takeProfitPrice": 53000.0,
            "trailingStopActivationPrice": 49500.0,
            "trailingStopCallbackRate": 0.005,
            "currentStopPrice_tsl": 49500.0,
            "riskRewardAdjustments": []
        },
        {
            "id": UUID("123e4567-e89b-12d3-a456-426614174002"),
            "user_id": UUID("123e4567-e89b-12d3-a456-426614174000"),
            "symbol": "ETHUSDT",
            "side": "BUY",
            "mode": "paper",
            "positionStatus": "closed",
            "opened_at": datetime(2024, 1, 2, 14, 0, 0),
            "closed_at": datetime(2024, 1, 2, 16, 0, 0),
            "pnl_usd": -50.0,
            "pnl_percentage": -2.5,
            "closingReason": "STOP_LOSS",
            "entryOrder": TradeOrderDetails(
                orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef03"),
                type="market",
                status="filled",
                requestedQuantity=0.5,
                executedQuantity=0.5,
                executedPrice=2000.0,
                timestamp=datetime(2024, 1, 2, 14, 0, 0),
                exchangeOrderId=None,
                commission=None,
                commissionAsset=None,
                rawResponse=None
            ),
            "exitOrders": [
                TradeOrderDetails(
                    orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef04"),
                    type="market",
                    status="filled",
                    requestedQuantity=0.5,
                    executedQuantity=0.5,
                    executedPrice=1950.0,
                    timestamp=datetime(2024, 1, 2, 16, 0, 0),
                    exchangeOrderId=None,
                    commission=None,
                    commissionAsset=None,
                    rawResponse=None
                )
            ],
            "takeProfitPrice": 2050.0,
            "trailingStopActivationPrice": 1980.0,
            "trailingStopCallbackRate": 0.005,
            "currentStopPrice_tsl": 1980.0,
            "riskRewardAdjustments": []
        },
        {
            "id": UUID("123e4567-e89b-12d3-a456-426614174003"),
            "user_id": UUID("123e4567-e89b-12d3-a456-426614174000"),
            "symbol": "ADAUSDT",
            "side": "BUY",
            "mode": "paper",
            "positionStatus": "closed",
            "opened_at": datetime(2024, 1, 3, 9, 0, 0),
            "closed_at": datetime(2024, 1, 3, 11, 0, 0),
            "pnl_usd": 25.0,
            "pnl_percentage": 1.25,
            "closingReason": "MANUAL",
            "entryOrder": TradeOrderDetails(
                orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef05"),
                type="market",
                status="filled",
                requestedQuantity=1000.0,
                executedQuantity=1000.0,
                executedPrice=0.5,
                timestamp=datetime(2024, 1, 3, 9, 0, 0),
                exchangeOrderId=None,
                commission=None,
                commissionAsset=None,
                rawResponse=None
            ),
            "exitOrders": [
                TradeOrderDetails(
                    orderId_internal=UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef06"),
                    type="market",
                    status="filled",
                    requestedQuantity=1000.0,
                    executedQuantity=1000.0,
                    executedPrice=0.525,
                    timestamp=datetime(2024, 1, 3, 11, 0, 0),
                    exchangeOrderId=None,
                    commission=None,
                    commissionAsset=None,
                    rawResponse=None
                )
            ],
            "takeProfitPrice": 0.55,
            "trailingStopActivationPrice": 0.49,
            "trailingStopCallbackRate": 0.005,
            "currentStopPrice_tsl": 0.49,
            "riskRewardAdjustments": []
        }
    ]
    return [Trade(**data) for data in raw_data]


class TestTradingReportService:
    """Pruebas para TradingReportService."""

    @pytest.mark.asyncio
    async def test_get_closed_trades_success(self, trading_report_service, mock_persistence_service, sample_trade_data):
        """Prueba obtener trades cerrados exitosamente."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.return_value = sample_trade_data
        
        # Act
        result = await trading_report_service.get_closed_trades(user_id, mode="paper")
        
        # Assert
        assert len(result) == 3
        assert all(isinstance(trade, Trade) for trade in result)
        assert result[0].symbol == "BTCUSDT"
        assert result[1].symbol == "ETHUSDT"
        assert result[2].symbol == "ADAUSDT"
        
        # Verificar que se llamó al persistence service con los parámetros correctos
        mock_persistence_service.get_closed_trades.assert_called_once()
        call_args = mock_persistence_service.get_closed_trades.call_args
        assert call_args[0][0]["user_id"] == str(user_id)
        assert call_args[0][0]["mode"] == "paper"
        assert call_args[0][0]["positionStatus"] == "closed"

    @pytest.mark.asyncio
    async def test_get_closed_trades_with_filters(self, trading_report_service, mock_persistence_service, sample_trade_data):
        """Prueba obtener trades cerrados con filtros aplicados."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Filtrar solo trades de BTCUSDT
        btc_trade_data = [trade for trade in sample_trade_data if trade["symbol"] == "BTCUSDT"]
        mock_persistence_service.get_closed_trades.return_value = btc_trade_data
        
        # Act
        result = await trading_report_service.get_closed_trades(
            user_id, 
            mode="paper", 
            symbol="BTCUSDT",
            start_date=start_date,
            end_date=end_date,
            limit=50,
            offset=0
        )
        
        # Assert
        assert len(result) == 1
        assert result[0].symbol == "BTCUSDT"
        
        # Verificar los filtros aplicados
        call_args = mock_persistence_service.get_closed_trades.call_args
        filters = call_args[0][0]
        assert filters["symbol"] == "BTCUSDT"
        assert call_args[0][1] == start_date  # start_date
        assert call_args[0][2] == end_date    # end_date
        assert call_args[0][3] == 50          # limit
        assert call_args[0][4] == 0           # offset

    @pytest.mark.asyncio
    async def test_get_closed_trades_empty_result(self, trading_report_service, mock_persistence_service):
        """Prueba cuando no hay trades cerrados."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.return_value = []
        
        # Act
        result = await trading_report_service.get_closed_trades(user_id, mode="paper")
        
        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_closed_trades_error_handling(self, trading_report_service, mock_persistence_service):
        """Prueba manejo de errores al obtener trades cerrados."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(ReportError) as exc_info:
            await trading_report_service.get_closed_trades(user_id, mode="paper")
        
        assert "Error al obtener historial de trades" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_success(self, trading_report_service, mock_persistence_service, sample_trade_data):
        """Prueba cálculo de métricas de rendimiento exitoso."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.return_value = sample_trade_data
        
        # Act
        result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")
        
        # Assert
        assert isinstance(result, PerformanceMetrics)
        assert result.total_trades == 3
        assert result.winning_trades == 2  # trades con PnL > 0
        assert result.losing_trades == 1   # trades con PnL < 0
        assert result.win_rate == 66.67  # 2/3 * 100, redondeado
        assert result.total_pnl == 125.0  # 150 + (-50) + 25
        assert result.avg_pnl_per_trade == 41.67  # 125/3, redondeado
        assert result.best_trade_pnl == 150.0
        assert result.worst_trade_pnl == -50.0
        assert result.best_trade_symbol == "BTCUSDT"
        assert result.worst_trade_symbol == "ETHUSDT"
        assert result.total_volume_traded > 0

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_no_trades(self, trading_report_service, mock_persistence_service):
        """Prueba cálculo de métricas cuando no hay trades."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.return_value = []
        
        # Act
        result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")
        
        # Assert
        assert isinstance(result, PerformanceMetrics)
        assert result.total_trades == 0
        assert result.winning_trades == 0
        assert result.losing_trades == 0
        assert result.win_rate == 0.0
        assert result.total_pnl == 0.0
        assert result.avg_pnl_per_trade == 0.0
        assert result.best_trade_pnl == 0.0
        assert result.worst_trade_pnl == 0.0
        assert result.best_trade_symbol is None
        assert result.worst_trade_symbol is None
        assert result.total_volume_traded == 0.0

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_with_filters(self, trading_report_service, mock_persistence_service, sample_trade_data):
        """Prueba cálculo de métricas con filtros específicos."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        # Filtrar trades por fechas (solo los primeros 2)
        filtered_data = sample_trade_data[:2]  # BTCUSDT y ETHUSDT
        mock_persistence_service.get_closed_trades.return_value = filtered_data
        
        # Act
        result = await trading_report_service.calculate_performance_metrics(
            user_id, 
            mode="paper",
            start_date=start_date,
            end_date=end_date
        )
        
        # Assert
        assert result.total_trades == 2
        assert result.winning_trades == 1  # Solo BTCUSDT ganó
        assert result.losing_trades == 1   # ETHUSDT perdió
        assert result.win_rate == 50.0    # 1/2 * 100
        assert result.total_pnl == 100.0  # 150 + (-50)
        assert result.period_start == start_date
        assert result.period_end == end_date

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_only_winning_trades(self, trading_report_service, mock_persistence_service):
        """Prueba métricas con solo trades ganadores."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        winning_trade_data = [
            {
                "id": "trade-win-1",
                "user_id": "user-123",
                "symbol": "BTCUSDT",
                "pnl_usd": 100.0,
                "opened_at": datetime(2024, 1, 1),
                "closed_at": datetime(2024, 1, 1),
                "entryOrder": {
                    "executedQuantity": 0.001,
                    "executedPrice": 50000.0
                }
            },
            {
                "id": "trade-win-2",
                "user_id": "user-123",
                "symbol": "ETHUSDT",
                "pnl_usd": 75.0,
                "opened_at": datetime(2024, 1, 2),
                "closed_at": datetime(2024, 1, 2),
                "entryOrder": {
                    "executedQuantity": 0.1,
                    "executedPrice": 2000.0
                }
            }
        ]
        mock_persistence_service.get_closed_trades.return_value = winning_trade_data
        
        # Act
        result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")
        
        # Assert
        assert result.total_trades == 2
        assert result.winning_trades == 2
        assert result.losing_trades == 0
        assert result.win_rate == 100.0
        assert result.total_pnl == 175.0
        assert result.best_trade_pnl == 100.0
        assert result.worst_trade_pnl == 75.0

    @pytest.mark.asyncio
    async def test_calculate_performance_metrics_error_handling(self, trading_report_service, mock_persistence_service):
        """Prueba manejo de errores al calcular métricas."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_persistence_service.get_closed_trades.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(ReportError) as exc_info:
            await trading_report_service.calculate_performance_metrics(user_id, mode="paper")
        
        assert "Error al calcular métricas de rendimiento" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_win_rate_calculation_with_zero_pnl_trades(self, trading_report_service, mock_persistence_service):
        """Prueba que el win rate excluye trades con PnL = 0."""
        # Arrange
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mixed_trade_data = [
            {
                "id": "trade-1",
                "user_id": "user-123",
                "symbol": "BTCUSDT",
                "pnl_usd": 100.0,  # Ganador
                "opened_at": datetime(2024, 1, 1),
                "closed_at": datetime(2024, 1, 1),
                "entryOrder": {"executedQuantity": 0.001, "executedPrice": 50000.0}
            },
            {
                "id": "trade-2",
                "user_id": "user-123",
                "symbol": "ETHUSDT",
                "pnl_usd": 0.0,    # Sin ganancia ni pérdida (debe excluirse del win rate)
                "opened_at": datetime(2024, 1, 2),
                "closed_at": datetime(2024, 1, 2),
                "entryOrder": {"executedQuantity": 0.1, "executedPrice": 2000.0}
            },
            {
                "id": "trade-3",
                "user_id": "user-123",
                "symbol": "ADAUSDT",
                "pnl_usd": -50.0,  # Perdedor
                "opened_at": datetime(2024, 1, 3),
                "closed_at": datetime(2024, 1, 3),
                "entryOrder": {"executedQuantity": 1000.0, "executedPrice": 0.5}
            }
        ]
        mock_persistence_service.get_closed_trades.return_value = mixed_trade_data
        
        # Act
        result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")
        
        # Assert
        assert result.total_trades == 3
        assert result.winning_trades == 1  # Solo 1 con PnL > 0
        assert result.losing_trades == 1   # Solo 1 con PnL < 0
        # Win rate debe ser 50% (1 ganador / 2 trades no-cero)
        assert result.win_rate == 50.0
        assert result.total_pnl == 50.0  # 100 + 0 + (-50)
