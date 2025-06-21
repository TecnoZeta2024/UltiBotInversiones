"""
Pruebas unitarias para TradingReportService.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from ultibot_backend.services.trading_report_service import TradingReportService
from ultibot_backend.core.exceptions import ReportError
from ultibot_backend.core.domain_models.trade_models import (
    Trade,
    TradeOrderDetails,
    OrderCategory,
    OrderType,
    OrderStatus,
    TradeSide,
)
from shared.data_types import PerformanceMetrics


@pytest.fixture
def mock_session_factory():
    """
    Fixture para mockear la session_factory que devuelve un context manager asíncrono.
    Esto simula el comportamiento de `async with session_factory() as session:`.
    """
    mock_session = AsyncMock()
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None  # Necesario para el context manager
    return mock_factory, mock_session


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
            rawResponse=None, ocoOrderListId=None
        )
        exit_order = TradeOrderDetails(
            orderId_internal=uuid4(), type=OrderType.MARKET, status=OrderStatus.FILLED,
            requestedQuantity=Decimal("1"), executedQuantity=Decimal("1"),
            executedPrice=Decimal(str(100 + pnl)), orderCategory=OrderCategory.TAKE_PROFIT,
            timestamp=datetime.utcnow(),
            orderId_exchange=None, clientOrderId_exchange=None, requestedPrice=None,
            cumulativeQuoteQty=None, commissions=[], commission=None,
            commissionAsset=None, submittedAt=None, fillTimestamp=None,
            rawResponse=None, ocoOrderListId=None
        )
        
        return Trade(
            id=uuid4(),
            user_id=user_id,
            symbol=symbol,
            side=TradeSide.BUY,
            mode="paper",
            positionStatus="closed",
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


@patch('ultibot_backend.services.trading_report_service.SupabasePersistenceService')
@pytest.mark.asyncio
async def test_get_closed_trades_success(mock_persistence_service_class, mock_session_factory, sample_trade_data):
    """Prueba obtener trades cerrados exitosamente."""
    # Arrange
    mock_factory, mock_session = mock_session_factory
    mock_persistence_instance = AsyncMock()
    mock_persistence_service_class.return_value = mock_persistence_instance
    mock_persistence_instance.get_closed_trades.return_value = sample_trade_data
    
    service = TradingReportService(session_factory=mock_factory)
    user_id = sample_trade_data[0].user_id

    # Act
    result = await service.get_closed_trades(user_id, mode="paper")

    # Assert
    mock_factory.assert_called_once()
    mock_persistence_service_class.assert_called_once_with(mock_session)
    mock_persistence_instance.get_closed_trades.assert_called_once_with(
        user_id=user_id, mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert len(result) == 3
    assert result[0].symbol == "BTCUSDT"


@patch('ultibot_backend.services.trading_report_service.SupabasePersistenceService')
@pytest.mark.asyncio
async def test_calculate_performance_metrics_success(mock_persistence_service_class, mock_session_factory, sample_trade_data):
    """Prueba cálculo de métricas de rendimiento exitoso."""
    # Arrange
    mock_factory, mock_session = mock_session_factory
    mock_persistence_instance = AsyncMock()
    mock_persistence_service_class.return_value = mock_persistence_instance
    mock_persistence_instance.get_closed_trades.return_value = sample_trade_data
    
    service = TradingReportService(session_factory=mock_factory)
    user_id = sample_trade_data[0].user_id

    # Act
    result = await service.calculate_performance_metrics(user_id, mode="paper")

    # Assert
    mock_factory.assert_called_once()
    mock_persistence_service_class.assert_called_once_with(mock_session)
    mock_persistence_instance.get_closed_trades.assert_called_once_with(
        user_id=user_id, mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert isinstance(result, PerformanceMetrics)
    assert result.total_trades == 3
    assert result.winning_trades == 2
    assert result.losing_trades == 1
    assert result.win_rate == pytest.approx(Decimal("66.67"), rel=Decimal("1e-2"))
    assert result.total_pnl == Decimal("125.0")


@patch('ultibot_backend.services.trading_report_service.SupabasePersistenceService')
@pytest.mark.asyncio
async def test_calculate_performance_metrics_no_trades(mock_persistence_service_class, mock_session_factory):
    """Prueba cálculo de métricas cuando no hay trades."""
    # Arrange
    mock_factory, mock_session = mock_session_factory
    mock_persistence_instance = AsyncMock()
    mock_persistence_service_class.return_value = mock_persistence_instance
    mock_persistence_instance.get_closed_trades.return_value = []
    
    service = TradingReportService(session_factory=mock_factory)
    user_id = uuid4()

    # Act
    result = await service.calculate_performance_metrics(user_id, mode="paper")

    # Assert
    mock_factory.assert_called_once()
    mock_persistence_service_class.assert_called_once_with(mock_session)
    mock_persistence_instance.get_closed_trades.assert_called_once_with(
        user_id=user_id, mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert result.total_trades == 0
    assert result.total_pnl == Decimal("0.0")


@patch('ultibot_backend.services.trading_report_service.SupabasePersistenceService')
@pytest.mark.asyncio
async def test_get_closed_trades_error_handling(mock_persistence_service_class, mock_session_factory):
    """Prueba manejo de errores al obtener trades cerrados."""
    # Arrange
    mock_factory, mock_session = mock_session_factory
    mock_persistence_instance = AsyncMock()
    mock_persistence_service_class.return_value = mock_persistence_instance
    mock_persistence_instance.get_closed_trades.side_effect = Exception("Database connection failed")
    
    service = TradingReportService(session_factory=mock_factory)
    user_id = uuid4()

    # Act & Assert
    with pytest.raises(ReportError) as exc_info:
        await service.get_closed_trades(user_id, mode="paper")
    
    mock_factory.assert_called_once()
    mock_persistence_service_class.assert_called_once_with(mock_session)
    mock_persistence_instance.get_closed_trades.assert_called_once_with(
        user_id=user_id, mode='paper', symbol=None, start_date=None, end_date=None
    )
    assert "Error al obtener historial de trades" in str(exc_info.value)
