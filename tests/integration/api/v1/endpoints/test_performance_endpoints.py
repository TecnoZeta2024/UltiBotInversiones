import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from ultibot_backend.main import app # Importar la app FastAPI
from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.api.v1.models.performance_models import StrategyPerformanceData, OperatingMode
from shared.data_types import Trade
from ultibot_backend.core.domain_models.trade_models import PositionStatus, TradeOrderDetails, OrderCategory, OrderType, OrderStatus
from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType, ScalpingParameters, DayTradingParameters, Timeframe
from uuid import UUID
from ultibot_backend.app_config import settings
from decimal import Decimal # Necesario para TradeOrderDetails

from ultibot_backend.dependencies import get_performance_service
# No necesitamos importar PerformanceService o SupabasePersistenceService aquí,
# ya que la inyección se manejará a través de dependencies.py y conftest.py

@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_no_data(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies when no performance data is available.
    """
    # Configurar el mock de persistencia para que no devuelva trades
    mock_persistence_service_integration.get_trades_with_filters.return_value = []
    
    response = client.get("/api/v1/performance/strategies")
    
    assert response.status_code == 200
    assert response.json() == []
    mock_persistence_service_integration.get_trades_with_filters.assert_called_once_with(user_id=str(settings.FIXED_USER_ID), trading_mode="", status=PositionStatus.CLOSED.value)


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_with_data(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies with some performance data.
    """
    strategy_id = uuid4()
    trade_id = uuid4()

    closed_trade = Trade(
        id=trade_id,
        user_id=settings.FIXED_USER_ID, # user_id en Trade es UUID
        mode="paper",
        symbol="BTCUSDT",
        side="BUY",
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.LIMIT.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("0.002")),
            executedQuantity=float(Decimal("0.002")),
            executedPrice=float(Decimal("50000.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("50000.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("0.002")) * float(Decimal("50000.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        strategyId=strategy_id,
        pnl_usd=100.0,
        pnl_percentage=0.1,
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, closingReason="Test",
        ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
        trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    mock_persistence_service_integration.get_trades_with_filters.return_value = [closed_trade]

    strategy_config = TradingStrategyConfig(
        id=str(strategy_id),
        user_id=str(settings.FIXED_USER_ID), # user_id en TradingStrategyConfig es str
        config_name="Integration Test Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=3600, # Default value
            leverage=1 # Default value
        ),
        is_active_paper_mode=True,
        is_active_real_mode=False,
        description="Strategy for integration test",
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_service_integration.get_strategy_config.return_value = strategy_config

    response = client.get("/api/v1/performance/strategies?mode=paper")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    perf_data = data[0]
    assert perf_data["strategyId"] == str(strategy_id)
    assert perf_data["strategyName"] == "Integration Test Strategy"
    assert perf_data["mode"] == "paper"
    assert perf_data["totalOperations"] == 1
    assert perf_data["totalPnl"] == 100.0
    assert perf_data["win_rate"] == 100.0

    mock_persistence_service_integration.get_trades_with_filters.assert_called_once_with(user_id=str(settings.FIXED_USER_ID), trading_mode="paper", status=PositionStatus.CLOSED.value)
    mock_strategy_service_integration.get_strategy_config.assert_called_once_with(str(strategy_id), str(settings.FIXED_USER_ID))


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_filter_real_mode(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies filtering by 'real' mode.
    """
    strategy_id_real = uuid4()
    trade_id_real = uuid4()

    real_trade = Trade(
        id=trade_id_real,
        user_id=settings.FIXED_USER_ID, # user_id en Trade es UUID
        mode="real", # Crucial para este test
        symbol="ETHUSDT",
        side="SELL",
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.LIMIT.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("0.1")),
            executedQuantity=float(Decimal("0.1")),
            executedPrice=float(Decimal("2000.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("2000.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("0.1")) * float(Decimal("2000.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        strategyId=strategy_id_real,
        pnl_usd=250.0,
        pnl_percentage=0.25,
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, closingReason="Real Test",
        ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
        trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    # Mock para que solo devuelva el trade real cuando se filtra por 'real'
    mock_persistence_service_integration.get_trades_with_filters.return_value = [real_trade]

    strategy_config_real = TradingStrategyConfig(
        id=str(strategy_id_real),
        user_id=str(settings.FIXED_USER_ID), # user_id en TradingStrategyConfig es str
        config_name="Real Mode Strategy",
        base_strategy_type=BaseStrategyType.DAY_TRADING,
        parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_HOUR],
            rsi_period=14, # Default value
            rsi_overbought=70, # Default value
            rsi_oversold=30, # Default value
            macd_fast_period=12, # Default value
            macd_slow_period=26, # Default value
            macd_signal_period=9, # Default value
            exit_timeframes=[Timeframe.FOUR_HOURS] # Default value
        ),
        is_active_paper_mode=False, # No activo en paper
        is_active_real_mode=True,   # Activo en real
        description="Strategy for real mode integration test",
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_service_integration.get_strategy_config.return_value = strategy_config_real

    response = client.get("/api/v1/performance/strategies?mode=real")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    perf_data = data[0]
    assert perf_data["strategyId"] == str(strategy_id_real)
    assert perf_data["strategyName"] == "Real Mode Strategy"
    assert perf_data["mode"] == "real"
    assert perf_data["totalOperations"] == 1
    assert perf_data["totalPnl"] == 250.0
    assert perf_data["win_rate"] == 100.0

    mock_persistence_service_integration.get_trades_with_filters.assert_called_once_with(user_id=str(settings.FIXED_USER_ID), trading_mode="real", status=PositionStatus.CLOSED.value)
    mock_strategy_service_integration.get_strategy_config.assert_called_once_with(str(strategy_id_real), str(settings.FIXED_USER_ID))


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_multiple_strategies(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies with multiple strategies and modes.
    """
    strategy_id_1 = uuid4()
    strategy_id_2 = uuid4()
    trade_id_1 = uuid4()
    trade_id_2 = uuid4()
    trade_id_3 = uuid4()

    # Definir los parámetros comunes directamente en la creación de Trade
    trade1_strat1_paper = Trade(
        id=trade_id_1,
        user_id=settings.FIXED_USER_ID,
        mode="paper",
        symbol="BTCUSDT",
        side="BUY",
        strategyId=strategy_id_1,
        pnl_usd=50.0,
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("1.0")),
            executedQuantity=float(Decimal("1.0")),
            executedPrice=float(Decimal("1.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("1.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("1.0")) * float(Decimal("1.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        opened_at=datetime.now(timezone.utc), 
        closed_at=datetime.now(timezone.utc),
        pnl_percentage=0.1, 
        opportunityId=None, 
        aiAnalysisConfidence=None,
        closingReason="Test", 
        ocoOrderListId=None, 
        takeProfitPrice=None,
        trailingStopActivationPrice=None, 
        trailingStopCallbackRate=None, 
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    trade2_strat1_paper = Trade(
        id=trade_id_2,
        user_id=settings.FIXED_USER_ID,
        mode="paper",
        symbol="ETHUSDT",
        side="SELL",
        strategyId=strategy_id_1,
        pnl_usd=-10.0,
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("1.0")),
            executedQuantity=float(Decimal("1.0")),
            executedPrice=float(Decimal("1.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("1.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("1.0")) * float(Decimal("1.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        opened_at=datetime.now(timezone.utc), 
        closed_at=datetime.now(timezone.utc),
        pnl_percentage=0.1, 
        opportunityId=None, 
        aiAnalysisConfidence=None,
        closingReason="Test", 
        ocoOrderListId=None, 
        takeProfitPrice=None,
        trailingStopActivationPrice=None, 
        trailingStopCallbackRate=None, 
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    trade3_strat2_real = Trade(
        id=trade_id_3,
        user_id=settings.FIXED_USER_ID,
        mode="real",
        symbol="ADAUSDT",
        side="BUY",
        strategyId=strategy_id_2,
        pnl_usd=75.0,
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("1.0")),
            executedQuantity=float(Decimal("1.0")),
            executedPrice=float(Decimal("1.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("1.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("1.0")) * float(Decimal("1.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        opened_at=datetime.now(timezone.utc), 
        closed_at=datetime.now(timezone.utc),
        pnl_percentage=0.1, 
        opportunityId=None, 
        aiAnalysisConfidence=None,
        closingReason="Test", 
        ocoOrderListId=None, 
        takeProfitPrice=None,
        trailingStopActivationPrice=None, 
        trailingStopCallbackRate=None, 
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    
    mock_persistence_service_integration.get_trades_with_filters.return_value = [
        trade1_strat1_paper, trade2_strat1_paper, trade3_strat2_real
    ]

    config_strat1 = TradingStrategyConfig(
        id=str(strategy_id_1), user_id=str(settings.FIXED_USER_ID), config_name="Multi Strat Paper",
        base_strategy_type=BaseStrategyType.SCALPING, parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=3600, # Default value
            leverage=1 # Default value
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description="Paper multi test", version=1,
        applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None, parent_config_id=None,
        performance_metrics=None, market_condition_filters=None, activation_schedule=None,
        depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    config_strat2 = TradingStrategyConfig(
        id=str(strategy_id_2), user_id=str(settings.FIXED_USER_ID), config_name="Multi Strat Real",
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_HOUR],
            rsi_period=14, # Default value
            rsi_overbought=70, # Default value
            rsi_oversold=30, # Default value
            macd_fast_period=12, # Default value
            macd_slow_period=26, # Default value
            macd_signal_period=9, # Default value
            exit_timeframes=[Timeframe.FOUR_HOURS] # Default value
        ),
        is_active_paper_mode=False, is_active_real_mode=True, description="Real multi test", version=1,
        applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None, parent_config_id=None,
        performance_metrics=None, market_condition_filters=None, activation_schedule=None,
        depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )

    async def side_effect_get_strategy_config(strat_id_str, user_id_str):
        if UUID(strat_id_str) == strategy_id_1:
            return config_strat1
        elif UUID(strat_id_str) == strategy_id_2:
            return config_strat2
        return None
    mock_strategy_service_integration.get_strategy_config.side_effect = side_effect_get_strategy_config
    
    response = client.get("/api/v1/performance/strategies") # Sin parámetro 'mode'
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Debería devolver datos para ambas estrategias/modos

    perf_strat1 = next(p for p in data_all if p["strategyId"] == str(strategy_id_1))
    perf_strat2 = next(p for p in data_all if p["strategyId"] == str(strategy_id_2))

    assert perf_strat1["strategyName"] == "Multi Strat Paper"
    assert perf_strat1["mode"] == "paper"
    assert perf_strat1["totalOperations"] == 2
    assert perf_strat1["totalPnl"] == 40.0 # 50 - 10
    assert perf_strat1["win_rate"] == 50.0

    assert perf_strat2["strategyName"] == "Multi Strat Real"
    assert perf_strat2["mode"] == "real"
    assert perf_strat2["totalOperations"] == 1
    assert perf_strat2["totalPnl"] == 75.0
    assert perf_strat2["win_rate"] == 100.0
    
    mock_persistence_service_integration.get_trades_with_filters.assert_called_with(user_id=str(settings.FIXED_USER_ID), trading_mode="", status=PositionStatus.CLOSED.value)
    assert mock_strategy_service_integration.get_strategy_config.call_count == 2 # Una vez por cada estrategia


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_strategy_not_found(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies when a strategy config is not found for a trade's strategyId.
    """
    unknown_strategy_id = uuid4()
    trade_id = uuid4()

    trade_with_unknown_strategy = Trade(
        id=trade_id,
        user_id=settings.FIXED_USER_ID, # user_id en Trade es UUID
        mode="paper",
        symbol="LINKUSDT",
        side="BUY",
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.LIMIT.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("3.0")),
            executedQuantity=float(Decimal("3.0")),
            executedPrice=float(Decimal("10.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("10.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("3.0")) * float(Decimal("10.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        strategyId=unknown_strategy_id, # Este ID no tendrá una config asociada
        pnl_usd=30.0,
        pnl_percentage=0.03,
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, closingReason="Test Unknown",
        ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
        trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    mock_persistence_service_integration.get_trades_with_filters.return_value = [trade_with_unknown_strategy]
    
    # Simular que get_strategy_config devuelve None para este ID
    mock_strategy_service_integration.get_strategy_config.return_value = None

    response = client.get("/api/v1/performance/strategies?mode=paper")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    
    perf_data = data[0]
    assert perf_data["strategyId"] == str(unknown_strategy_id)
    assert perf_data["strategyName"] == "Estrategia Desconocida" # Comportamiento esperado
    assert perf_data["mode"] == "paper"
    assert perf_data["totalOperations"] == 1
    assert perf_data["totalPnl"] == 30.0
    assert perf_data["win_rate"] == 100.0

    mock_persistence_service_integration.get_trades_with_filters.assert_called_once_with(user_id=str(settings.FIXED_USER_ID), trading_mode="paper", status=PositionStatus.CLOSED.value)
    mock_strategy_service_integration.get_strategy_config.assert_called_once_with(str(unknown_strategy_id), str(settings.FIXED_USER_ID))


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_invalid_mode_parameter(client):
    """
    Test GET /api/v1/performance/strategies with an invalid 'mode' query parameter.
    FastAPI should return a 422 Unprocessable Entity error.
    """
    response = client.get("/api/v1/performance/strategies?mode=invalid_mode")
    
    assert response.status_code == 422 # Unprocessable Entity
    data = response.json()
    assert "detail" in data
    # Verificar que el detalle del error menciona el parámetro 'mode' y el valor inválido
    assert any(
        err["type"] == "enum" and err["loc"] == ["query", "mode"] and "invalid_mode" in err["msg"]
        for err in data["detail"]
    )


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_no_mode_filter(client, mock_persistence_service_integration, mock_strategy_service_integration):
    """
    Test GET /api/v1/performance/strategies without the 'mode' query parameter.
    It should return performance data for all modes.
    """
    strategy_id_paper = uuid4()
    strategy_id_real = uuid4()
    trade_paper_id = uuid4()
    trade_real_id = uuid4()

    # Definir los parámetros comunes directamente en la creación de Trade
    paper_trade = Trade(
        id=trade_paper_id,
        user_id=settings.FIXED_USER_ID,
        mode="paper",
        symbol="XRPUSDT",
        side="BUY",
        strategyId=strategy_id_paper,
        pnl_usd=60.0,
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("1.0")),
            executedQuantity=float(Decimal("1.0")),
            executedPrice=float(Decimal("1.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("1.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("1.0")) * float(Decimal("1.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        opened_at=datetime.now(timezone.utc), 
        closed_at=datetime.now(timezone.utc),
        pnl_percentage=0.1, 
        opportunityId=None, 
        aiAnalysisConfidence=None,
        closingReason="Test No Filter", 
        ocoOrderListId=None, 
        takeProfitPrice=None,
        trailingStopActivationPrice=None, 
        trailingStopCallbackRate=None, 
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    real_trade = Trade(
        id=trade_real_id,
        user_id=settings.FIXED_USER_ID,
        mode="real",
        symbol="DOTUSDT",
        side="SELL",
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type=OrderType.MARKET.value,
            status=OrderStatus.FILLED.value,
            requestedQuantity=float(Decimal("1.0")),
            executedQuantity=float(Decimal("1.0")),
            executedPrice=float(Decimal("1.0")),
            timestamp=datetime.now(timezone.utc),
            requestedPrice=float(Decimal("1.0")),
            orderId_exchange=str(uuid4()),
            clientOrderId_exchange=str(uuid4()),
            cumulativeQuoteQty=float(Decimal("1.0")) * float(Decimal("1.0")),
            commissions=[],
            commission=0.0,
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={},
            ocoOrderListId=None
        ),
        positionStatus=PositionStatus.CLOSED.value,
        opened_at=datetime.now(timezone.utc), 
        closed_at=datetime.now(timezone.utc),
        pnl_percentage=0.1, 
        opportunityId=None, 
        aiAnalysisConfidence=None,
        closingReason="Test No Filter", 
        ocoOrderListId=None, 
        takeProfitPrice=None,
        trailingStopActivationPrice=None, 
        trailingStopCallbackRate=None, 
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[]
    )
    
    # Mock para devolver ambos trades cuando no hay filtro de modo
    mock_persistence_service_integration.get_trades_with_filters.return_value = [paper_trade, real_trade]

    config_paper = TradingStrategyConfig(
        id=str(strategy_id_paper), user_id=str(settings.FIXED_USER_ID), config_name="NoFilter Paper Strat",
        base_strategy_type=BaseStrategyType.SCALPING, parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=3600, # Default value
            leverage=1 # Default value
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description="Paper no filter", version=1,
        applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None, parent_config_id=None,
        performance_metrics=None, market_condition_filters=None, activation_schedule=None,
        depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    config_real = TradingStrategyConfig(
        id=str(strategy_id_real), user_id=str(settings.FIXED_USER_ID), config_name="NoFilter Real Strat",
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_HOUR],
            rsi_period=14, # Default value
            rsi_overbought=70, # Default value
            rsi_oversold=30, # Default value
            macd_fast_period=12, # Default value
            macd_slow_period=26, # Default value
            macd_signal_period=9, # Default value
            exit_timeframes=[Timeframe.FOUR_HOURS] # Default value
        ),
        is_active_paper_mode=False, is_active_real_mode=True, description="Real no filter", version=1,
        applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None, parent_config_id=None,
        performance_metrics=None, market_condition_filters=None, activation_schedule=None,
        depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )

    async def side_effect_get_strategy_config(strat_id_str, user_id_str):
        if UUID(strat_id_str) == strategy_id_paper:
            return config_paper
        elif UUID(strat_id_str) == strategy_id_real:
            return config_real
        return None
    mock_strategy_service_integration.get_strategy_config.side_effect = side_effect_get_strategy_config
    
    response = client.get("/api/v1/performance/strategies") # Sin parámetro 'mode'
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Debería devolver datos para ambas estrategias/modos

    perf_paper = next(p for p in data if p["strategyId"] == str(strategy_id_paper))
    perf_real = next(p for p in data if p["strategyId"] == str(strategy_id_real))

    assert perf_paper["strategyName"] == "NoFilter Paper Strat"
    assert perf_paper["mode"] == "paper"
    assert perf_paper["totalPnl"] == 60.0

    assert perf_real["strategyName"] == "NoFilter Real Strat"
    assert perf_real["mode"] == "real"
    assert perf_real["totalPnl"] == 90.0
    
    mock_persistence_service_integration.get_trades_with_filters.assert_called_once_with(user_id=str(settings.FIXED_USER_ID), trading_mode="", status=PositionStatus.CLOSED.value)
    # Se debe llamar a get_strategy_config para cada estrategia
    assert mock_strategy_service_integration.get_strategy_config.call_count == 2
