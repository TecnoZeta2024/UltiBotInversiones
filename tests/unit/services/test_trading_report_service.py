"""
Pruebas unitarias para TradingReportService.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from src.services.trading_report_service import TradingReportService
from src.core.exceptions import ReportError
from src.core.domain_models.trade_models import (
    Trade,
    TradeOrderDetails,
    OrderCategory,
    OrderType,
    OrderStatus,
    TradeSide,
    TradeMode,
    PositionStatus,
)
from src.shared.data_types import PerformanceMetrics
from src.adapters.persistence_service import SupabasePersistenceService


@pytest.fixture
def trading_report_service(mock_persistence_service: SupabasePersistenceService) -> TradingReportService:
    """
    Fixture que proporciona una instancia de TradingReportService con un 
    servicio de persistencia mockeado inyectado.
    """
    return TradingReportService(persistence_service=mock_persistence_service)


@pytest.fixture
def sample_trade_data():
    """Datos de ejemplo para trades, como objetos Trade de Pydantic."""
    user_id = uuid4()
    
    def create_trade_object(pnl, symbol):
        entry_order = TradeOrderDetails(
            orderId_internal=uuid4(), type=OrderType.MARKET, status=OrderStatus.FILLED,
            requestedQuantity=Decimal("1"), executedQuantity=Decimal("1"),
            executedPrice=Decimal("100"), orderCategory=OrderCategory.ENTRY,
            timestamp=datetime.utcnow(),
            orderId_exchange=None, clientOrderId_exchange=None, requestedPrice=None,
            cumulativeQuoteQty=None, commissions=[], commission=None,
            commissionAsset=None, submittedAt=None, fillTimestamp=None,
            rawResponse=None, ocoOrderListId=None,
            price=None, stopPrice=None, timeInForce=None
        )
        exit_order = TradeOrderDetails(
            orderId_internal=uuid4(), type=OrderType.MARKET, status=OrderStatus.FILLED,
            requestedQuantity=Decimal("1"), executedQuantity=Decimal("1"),
            executedPrice=Decimal(str(100 + pnl)), orderCategory=OrderCategory.TAKE_PROFIT,
            timestamp=datetime.utcnow(),
            orderId_exchange=None, clientOrderId_exchange=None, requestedPrice=None,
            cumulativeQuoteQty=None, commissions=[], commission=None,
            commissionAsset=None, submittedAt=None, fillTimestamp=None,
            rawResponse=None, ocoOrderListId=None,
            price=None, stopPrice=None, timeInForce=None
        )
        
        return Trade(
            id=uuid4(),
            user_id=user_id,
            symbol=symbol,
            side=TradeSide.BUY,
            mode=TradeMode.PAPER,
            positionStatus=PositionStatus.CLOSED,
            opened_at=datetime.utcnow(),
            closed_at=datetime.utcnow(),
            pnl_usd=Decimal(str(pnl)),
            pnl_percentage=Decimal(str(pnl / 1000)),
            closingReason="TAKE_PROFIT" if pnl > 0 else "STOP_LOSS",
            entryOrder=entry_order,
            exitOrders=[exit_order],
            strategyId=uuid4(),
            opportunityId=uuid4(),
            aiAnalysisConfidence=Decimal("0.8"),
            ocoOrderListId=None,
            takeProfitPrice=None,
            trailingStopActivationPrice=None,
            trailingStopCallbackRate=None,
            currentStopPrice_tsl=None,
            riskRewardAdjustments=[]
        )

    return [
        create_trade_object(150.0, "BTCUSDT"),
        create_trade_object(-50.0, "ETHUSDT"),
        create_trade_object(25.0, "ADAUSDT"),
    ]


@pytest.mark.asyncio
async def test_get_closed_trades_success(
    trading_report_service: TradingReportService, 
    mock_persistence_service: AsyncMock, 
    sample_trade_data: list[Trade]
):
    """Prueba obtener trades cerrados exitosamente."""
    # Arrange
    mock_persistence_service.get_closed_trades.return_value = sample_trade_data
    user_id = sample_trade_data[0].user_id

    # Act
    result = await trading_report_service.get_closed_trades(user_id, mode="paper")

    # Assert
    mock_persistence_service.get_closed_trades.assert_called_once_with(
        user_id=str(user_id), mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert len(result) == 3
    assert result[0].symbol == "BTCUSDT"


@pytest.mark.asyncio
async def test_calculate_performance_metrics_success(
    trading_report_service: TradingReportService, 
    mock_persistence_service: AsyncMock, 
    sample_trade_data: list[Trade]
):
    """Prueba cálculo de métricas de rendimiento exitoso."""
    # Arrange
    mock_persistence_service.get_closed_trades.return_value = sample_trade_data
    user_id = sample_trade_data[0].user_id

    # Act
    result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")

    # Assert
    # La llamada a `calculate_performance_metrics` invoca internamente a `get_closed_trades`,
    # que a su vez llama a `persistence_service.get_closed_trades`.
    # Verificamos la llamada al método del mock de persistencia.
    # Notar que `limit` y `offset` no se pasan al servicio de persistencia.
    mock_persistence_service.get_closed_trades.assert_called_once_with(
        user_id=str(user_id), mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert isinstance(result, PerformanceMetrics)
    assert result.total_trades == 3
    assert result.winning_trades == 2
    assert result.losing_trades == 1
    assert result.win_rate == pytest.approx(Decimal("66.67"), rel=Decimal("1e-2"))
    assert result.total_pnl == Decimal("125.0")


@pytest.mark.asyncio
async def test_calculate_performance_metrics_no_trades(
    trading_report_service: TradingReportService, 
    mock_persistence_service: AsyncMock
):
    """Prueba cálculo de métricas cuando no hay trades."""
    # Arrange
    mock_persistence_service.get_closed_trades.return_value = []
    user_id = uuid4()

    # Act
    result = await trading_report_service.calculate_performance_metrics(user_id, mode="paper")

    # Assert
    # La llamada a `calculate_performance_metrics` invoca internamente a `get_closed_trades`,
    # que a su vez llama a `persistence_service.get_closed_trades`.
    # Verificamos la llamada al método del mock de persistencia.
    mock_persistence_service.get_closed_trades.assert_called_once_with(
        user_id=str(user_id), mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert result.total_trades == 0
    assert result.total_pnl == Decimal("0.0")


@pytest.mark.asyncio
async def test_get_closed_trades_error_handling(
    trading_report_service: TradingReportService, 
    mock_persistence_service: AsyncMock
):
    """Prueba manejo de errores al obtener trades cerrados."""
    # Arrange
    mock_persistence_service.get_closed_trades.side_effect = Exception("Database connection failed")
    user_id = uuid4()

    # Act & Assert
    with pytest.raises(ReportError, match="Error al obtener historial de trades: Database connection failed"):
        await trading_report_service.get_closed_trades(user_id, mode="paper")
    
    mock_persistence_service.get_closed_trades.assert_called_once_with(
        user_id=str(user_id), mode='paper', symbol=None, start_date=None, end_date=None
    )
