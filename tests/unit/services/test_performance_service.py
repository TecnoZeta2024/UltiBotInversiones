import pytest
from unittest.mock import AsyncMock, MagicMock # Usar AsyncMock para métodos async
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional

from src.services.performance_service import PerformanceService
from src.adapters.persistence_service import SupabasePersistenceService
from src.services.strategy_service import StrategyService
from src.api.v1.models.performance_models import OperatingMode, StrategyPerformanceData
from src.shared.data_types import Trade, TradeOrderDetails, OrderType, OrderStatus, OrderCategory, PositionStatus
from src.core.domain_models.trade_models import TradeMode, TradeSide # Importar TradeMode y TradeSide
from src.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig, BaseStrategyType, ScalpingParameters, DayTradingParameters,
    GridTradingParameters, Timeframe
) # Para mock de strategy_config


from decimal import Decimal # Importar Decimal

def create_mock_trade_order_details(
    order_id_internal: Optional[UUID] = None,
    order_category: OrderCategory = OrderCategory.ENTRY,
    order_type: OrderType = OrderType.MARKET,
    status: OrderStatus = OrderStatus.FILLED,
    requested_quantity: Decimal = Decimal("0.01"),
    executed_quantity: Decimal = Decimal("0.01"),
    executed_price: Decimal = Decimal("100.0"),
    timestamp: Optional[datetime] = None,
    **kwargs
) -> TradeOrderDetails:
    """Helper function to create a valid TradeOrderDetails instance."""
    if order_id_internal is None:
        order_id_internal = uuid4()
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return TradeOrderDetails(
        orderId_internal=order_id_internal,
        orderCategory=order_category,
        type=order_type.value,
        status=status.value,
        requestedQuantity=requested_quantity,
        executedQuantity=executed_quantity,
        executedPrice=executed_price,
        timestamp=timestamp,
        **kwargs
    )


USER_ID = uuid4()

@pytest.fixture
def mock_persistence_service():
    mock = AsyncMock(spec=SupabasePersistenceService)
    # Configurar el método get_trades_with_filters que es el que realmente usa PerformanceService
    mock.get_trades_with_filters = AsyncMock(return_value=[])
    return mock

@pytest.fixture
def mock_strategy_service():
    service = AsyncMock(spec=StrategyService)
    # Configurar un comportamiento por defecto para get_strategy_config
    default_strategy_config = TradingStrategyConfig(
        id=str(uuid4()), # id es Optional[str]
        user_id=str(USER_ID), # user_id es str
        config_name="Estrategia por Defecto",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=60,
            leverage=1.0
        ),
        is_active_paper_mode=True,
        is_active_real_mode=False,
        description="Descripción por defecto",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        applicability_rules=None,
        ai_analysis_profile_id=None,
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=None,
        updated_at=None
    )
    service.get_strategy_config.return_value = default_strategy_config
    return service

@pytest.fixture
def performance_service(mock_persistence_service, mock_strategy_service):
    return PerformanceService(
        persistence_service=mock_persistence_service,
        strategy_service=mock_strategy_service
    )

@pytest.mark.asyncio
async def test_get_all_strategies_performance_no_trades(performance_service, mock_persistence_service):
    """
    Test case when there are no trades for the user.
    """
    mock_persistence_service.get_trades_with_filters.return_value = []
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID)
    
    assert result == []
    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="", status="closed")

@pytest.mark.asyncio
async def test_get_all_strategies_performance_no_closed_trades(performance_service, mock_persistence_service):
    """
    Test case when there are trades, but none are closed.
    """
    trade1_id = uuid4()
    strategy1_id = uuid4()
    open_trade = Trade(
        id=trade1_id,
        user_id=USER_ID,
        mode=TradeMode.PAPER,
        symbol="BTCUSDT",
        side=TradeSide.BUY,
        entryOrder=create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        exitOrders=[], # No exit orders for open trades
        positionStatus=PositionStatus.OPEN,
        strategyId=strategy1_id,
        # Campos obligatorios o con default_factory se manejarán. Opcionales sin default se ponen a None.
        pnl_usd=None,
        pnl_percentage=None,
        opportunityId=None,
        aiAnalysisConfidence=None,
        closingReason=None,
        ocoOrderListId=None,
        takeProfitPrice=None,
        trailingStopActivationPrice=None,
        trailingStopCallbackRate=None,
        currentStopPrice_tsl=None,
        opened_at=datetime.now(timezone.utc),
        closed_at=None, # Explícitamente None para trades abiertos
        # created_at y updated_at tienen default_factory
        # exitOrders tiene default_factory
    )
    mock_persistence_service.get_trades_with_filters.return_value = [open_trade]
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID)
    
    assert result == []
    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="", status="closed")

@pytest.mark.asyncio
async def test_get_all_strategies_performance_with_closed_trades(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test case with a single closed trade.
    """
    strategy1_id = uuid4()
    trade1_id = uuid4()

    closed_trade = Trade(
        id=trade1_id,
        user_id=USER_ID,
        mode=TradeMode.PAPER,
        symbol="BTCUSDT",
        side=TradeSide.BUY,
        entryOrder=create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        exitOrders=[
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        positionStatus=PositionStatus.CLOSED,
        strategyId=strategy1_id,
        pnl_usd=Decimal("10.0"), 
        pnl_percentage=Decimal("0.01"),
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        # Opcionales a None
        opportunityId=None,
        aiAnalysisConfidence=None,
        closingReason="Test Close",
        ocoOrderListId=None,
        takeProfitPrice=None,
        trailingStopActivationPrice=None,
        trailingStopCallbackRate=None,
        currentStopPrice_tsl=None,
    )
    mock_persistence_service.get_trades_with_filters.return_value = [closed_trade]
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy1_id),
        user_id=str(USER_ID),
        config_name="Test Strategy 1",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=60,
            leverage=1.0
        ),
        is_active_paper_mode=True,
        is_active_real_mode=False,
        description="Test strategy description",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        applicability_rules=None,
        ai_analysis_profile_id=None,
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=None,
        updated_at=None
    )
    mock_strategy_service.get_strategy_config.return_value = mock_strategy_config
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)
    
    assert len(result) == 1
    perf_data = result[0]

    assert perf_data.strategyId == strategy1_id
    assert perf_data.strategyName == "Test Strategy 1"
    assert perf_data.mode == OperatingMode.PAPER
    assert perf_data.totalOperations == 1
    assert perf_data.totalPnl == 10.0
    assert perf_data.win_rate == 100.0
    
    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="paper", status="closed")
    mock_strategy_service.get_strategy_config.assert_called_once_with(str(strategy1_id), str(USER_ID))

@pytest.mark.asyncio
async def test_get_all_strategies_performance_multiple_trades_mixed_pnl(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test with multiple trades for a strategy, mixed P&L.
    """
    strategy1_id = uuid4()
    trade1_id, trade2_id, trade3_id = uuid4(), uuid4(), uuid4()

    common_trade_params = {
        "user_id": USER_ID, "mode": TradeMode.PAPER,
        "entryOrder": create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        "exitOrders": [
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        "positionStatus": PositionStatus.CLOSED, "strategyId": strategy1_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": Decimal("0.0"), "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    trade1 = Trade(id=trade1_id, symbol="BTCUSDT", side=TradeSide.BUY, pnl_usd=Decimal("20.0"), **common_trade_params)
    trade2 = Trade(id=trade2_id, symbol="ETHUSDT", side=TradeSide.SELL, pnl_usd=Decimal("-5.0"), **common_trade_params)
    trade3 = Trade(id=trade3_id, symbol="ADAUSDT", side=TradeSide.BUY, pnl_usd=Decimal("15.0"), **common_trade_params)
    
    mock_persistence_service.get_trades_with_filters.return_value = [trade1, trade2, trade3]
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy1_id), user_id=str(USER_ID), config_name="Scalping Pro", 
        base_strategy_type=BaseStrategyType.SCALPING, parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=60,
            leverage=1.0
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description="Scalping strategy",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        applicability_rules=None,
        ai_analysis_profile_id=None,
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=None,
        updated_at=None
    )
    mock_strategy_service.get_strategy_config.return_value = mock_strategy_config
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)
    
    assert len(result) == 1
    perf_data = result[0]
    
    assert perf_data.strategyId == strategy1_id
    assert perf_data.strategyName == "Scalping Pro"
    assert perf_data.mode == OperatingMode.PAPER
    assert perf_data.totalOperations == 3
    assert perf_data.totalPnl == pytest.approx(30.0) # 20 - 5 + 15
    assert perf_data.win_rate == pytest.approx((2/3) * 100)

@pytest.mark.asyncio
async def test_get_all_strategies_performance_mode_filtering_real(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test mode filtering for 'real' trades.
    """
    strategy_paper_id, strategy_real_id = uuid4(), uuid4()
    trade_paper_id, trade_real_id = uuid4(), uuid4()
    
    common_trade_params_filter_test = {
        "user_id": USER_ID, 
        "entryOrder": create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        "exitOrders": [
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        "positionStatus": PositionStatus.CLOSED,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": Decimal("0.0"), "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    paper_trade = Trade(id=trade_paper_id, mode=TradeMode.PAPER, symbol="BTCUSDT", side=TradeSide.BUY, strategyId=strategy_paper_id, pnl_usd=Decimal("10.0"), **common_trade_params_filter_test)
    real_trade = Trade(id=trade_real_id, mode=TradeMode.REAL, symbol="ETHUSDT", side=TradeSide.SELL, strategyId=strategy_real_id, pnl_usd=Decimal("50.0"), **common_trade_params_filter_test)
    
    mock_persistence_service.get_trades_with_filters.return_value = [real_trade] 
    
    mock_strategy_config_real = TradingStrategyConfig(
        id=str(strategy_real_id), user_id=str(USER_ID), config_name="Real Trader", 
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.FIFTEEN_MINUTES],
            rsi_period=14,
            rsi_overbought=70.0,
            rsi_oversold=30.0,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            exit_timeframes=None
        ),
        is_active_paper_mode=False, is_active_real_mode=True, description="Real trading strategy",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        applicability_rules=None,
        ai_analysis_profile_id=None,
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=None,
        updated_at=None
    )
    
    async def side_effect_get_strategy_config(strat_id_str, user_id_str):
        if UUID(strat_id_str) == strategy_real_id:
            return mock_strategy_config_real
        return None
    mock_strategy_service.get_strategy_config.side_effect = side_effect_get_strategy_config
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.REAL)
    
    assert len(result) == 1
    perf_data = result[0]
    assert perf_data.strategyId == strategy_real_id
    assert perf_data.strategyName == "Real Trader"
    assert perf_data.mode == OperatingMode.REAL
    assert perf_data.totalOperations == 1
    assert perf_data.totalPnl == 50.0
    assert perf_data.totalPnl == 50.0
    assert perf_data.win_rate == 100.0
    
    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="real", status="closed")

@pytest.mark.asyncio
async def test_get_all_strategies_performance_unknown_strategy(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test when a strategyId from a trade does not have a corresponding strategy config.
    """
    strategy_unknown_id = uuid4()
    trade_id = uuid4()

    common_trade_params_unknown_strat = {
        "user_id": USER_ID, "mode": TradeMode.PAPER,
        "entryOrder": create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        "exitOrders": [
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        "positionStatus": PositionStatus.CLOSED, "strategyId": strategy_unknown_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": Decimal("0.0"), "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }
    
    trade = Trade(id=trade_id, symbol="BTCUSDT", side=TradeSide.BUY, pnl_usd=Decimal("10.0"), **common_trade_params_unknown_strat)
    mock_persistence_service.get_trades_with_filters.return_value = [trade]
    
    mock_strategy_service.get_strategy_config.return_value = None # Simula que no se encuentra la estrategia
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)
    
    assert len(result) == 1
    perf_data = result[0]
    assert perf_data.strategyName == "Estrategia Desconocida"
    assert perf_data.strategyId == strategy_unknown_id

@pytest.mark.asyncio
async def test_get_all_strategies_performance_multiple_strategies_different_modes(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test with multiple strategies operating in different modes (paper and real).
    """
    strategy_paper_id = uuid4()
    strategy_real_id = uuid4()
    trade_paper_id = uuid4()
    trade_real_id = uuid4()

    common_trade_params_multi_strat = {
        "user_id": USER_ID, 
        "entryOrder": create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        "exitOrders": [
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        "positionStatus": PositionStatus.CLOSED,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": Decimal("0.0"), "opportunityId": None, "aiAnalysisConfidence": None,
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None,
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    paper_trade = Trade(
        id=trade_paper_id, mode=TradeMode.PAPER, symbol="BTCUSDT", side=TradeSide.BUY,
        strategyId=strategy_paper_id, pnl_usd=Decimal("15.0"), **common_trade_params_multi_strat
    )
    real_trade = Trade(
        id=trade_real_id, mode=TradeMode.REAL, symbol="ETHUSDT", side=TradeSide.SELL,
        strategyId=strategy_real_id, pnl_usd=Decimal("25.0"), **common_trade_params_multi_strat
    )

    # Cuando se llama sin filtro de modo, debe devolver todos los trades
    mock_persistence_service.get_trades_with_filters.return_value = [paper_trade, real_trade]

    mock_strategy_config_paper = TradingStrategyConfig(
        id=str(strategy_paper_id), user_id=str(USER_ID), config_name="Paper Trader Pro",
        base_strategy_type=BaseStrategyType.SCALPING, parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=60,
            leverage=1.0
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description="Paper trading strategy",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_config_real = TradingStrategyConfig(
        id=str(strategy_real_id), user_id=str(USER_ID), config_name="Real Deal Trader",
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_HOUR],
            rsi_period=14,
            rsi_overbought=70.0,
            rsi_oversold=30.0,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            exit_timeframes=None
        ),
        is_active_paper_mode=False, is_active_real_mode=True, description="Real trading strategy",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )

    async def side_effect_get_strategy_config(strat_id_str, user_id_str):
        if UUID(strat_id_str) == strategy_paper_id:
            return mock_strategy_config_paper
        elif UUID(strat_id_str) == strategy_real_id:
            return mock_strategy_config_real
        return None
    mock_strategy_service.get_strategy_config.side_effect = side_effect_get_strategy_config

    result_all_modes = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=None)
    
    assert len(result_all_modes) == 2
    
    paper_perf = next(p for p in result_all_modes if p.strategyId == strategy_paper_id)
    real_perf = next(p for p in result_all_modes if p.strategyId == strategy_real_id)

    assert paper_perf.strategyName == "Paper Trader Pro"
    assert paper_perf.mode == OperatingMode.PAPER
    assert paper_perf.totalPnl == 15.0
    assert paper_perf.totalOperations == 1

    assert real_perf.strategyName == "Real Deal Trader"
    assert real_perf.mode == OperatingMode.REAL
    assert real_perf.totalPnl == 25.0
    assert real_perf.totalOperations == 1
    
    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="", status="closed")
    # Verificar que get_strategy_config fue llamado para ambas estrategias
    assert mock_strategy_service.get_strategy_config.call_count == 2
    mock_strategy_service.get_strategy_config.assert_any_call(str(strategy_paper_id), str(USER_ID))
    mock_strategy_service.get_strategy_config.assert_any_call(str(strategy_real_id), str(USER_ID))

@pytest.mark.asyncio
async def test_get_all_strategies_performance_breakeven_trades(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test with trades that result in zero P&L (break-even).
    """
    strategy_id = uuid4()
    trade1_id, trade2_id = uuid4(), uuid4()

    common_trade_params_breakeven = {
        "user_id": USER_ID, "mode": TradeMode.PAPER,
        "entryOrder": create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        "exitOrders": [
            create_mock_trade_order_details(
                order_category=OrderCategory.TAKE_PROFIT,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50100.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        "positionStatus": PositionStatus.CLOSED, "strategyId": strategy_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": Decimal("0.0"), "opportunityId": None, "aiAnalysisConfidence": None,
        "closingReason": "Break Even", "ocoOrderListId": None, "takeProfitPrice": None,
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    trade1 = Trade(id=trade1_id, symbol="XRPUSDT", side=TradeSide.BUY, pnl_usd=Decimal("0.0"), **common_trade_params_breakeven)
    trade2 = Trade(id=trade2_id, symbol="LTCUSDT", side=TradeSide.SELL, pnl_usd=Decimal("0.0"), **common_trade_params_breakeven)

    mock_persistence_service.get_trades_with_filters.return_value = [trade1, trade2]

    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy_id), user_id=str(USER_ID), config_name="Breakeven Master",
        base_strategy_type=BaseStrategyType.GRID_TRADING, parameters=GridTradingParameters(
            grid_upper_price=100.0,
            grid_lower_price=90.0,
            grid_levels=10,
            profit_per_grid=0.001
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description="Grid strategy for breakeven",
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_service.get_strategy_config.return_value = mock_strategy_config

    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)

    assert len(result) == 1
    perf_data = result[0]

    assert perf_data.strategyId == strategy_id
    assert perf_data.strategyName == "Breakeven Master"
    assert perf_data.totalOperations == 2
    assert perf_data.totalPnl == 0.0
    assert perf_data.win_rate == 0.0 # Break-even trades no cuentan como ganadoras para el win_rate simple

@pytest.mark.asyncio
async def test_get_all_strategies_performance_trade_with_none_strategy_id(
    performance_service, mock_persistence_service, mock_strategy_service
):
    """
    Test that trades with strategyId=None are handled gracefully (e.g., ignored or grouped under a special ID).
    The current implementation groups them under a "None" strategyId key, which then attempts to fetch
    a strategy config for "None", resulting in "Estrategia Desconocida".
    """
    trade_id = uuid4()

    trade_no_strategy = Trade(
        id=trade_id,
        user_id=USER_ID,
        mode=TradeMode.PAPER,
        symbol="SOLUSDT",
        side=TradeSide.BUY,
        entryOrder=create_mock_trade_order_details(
            order_category=OrderCategory.ENTRY,
            requested_quantity=Decimal("0.01"),
            executed_quantity=Decimal("0.01"),
            executed_price=Decimal("50000.0"),
            timestamp=datetime.now(timezone.utc)
        ),
        exitOrders=[
            create_mock_trade_order_details(
                order_category=OrderCategory.MANUAL_CLOSE,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50050.0"),
                timestamp=datetime.now(timezone.utc)
            )
        ],
        positionStatus=PositionStatus.CLOSED,
        strategyId=None, # Explicitly None
        pnl_usd=Decimal("5.0"),
        pnl_percentage=Decimal("0.02"),
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, closingReason="Manual",
        ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
        trailingStopCallbackRate=None, currentStopPrice_tsl=None,
    )
    mock_persistence_service.get_trades_with_filters.return_value = [trade_no_strategy]
    mock_strategy_service.get_strategy_config.return_value = None # Simulate strategy not found for "None"

    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)

    # Si el servicio filtra trades con strategyId=None, el resultado debería ser una lista vacía.
    # Asumiendo que el servicio filtra estos trades.
    assert result == []

    mock_persistence_service.get_trades_with_filters.assert_called_once_with(user_id=str(USER_ID), trading_mode="paper", status="closed")
    # El servicio no debería intentar buscar una estrategia con ID None si los filtra.
    mock_strategy_service.get_strategy_config.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "trades_pnl, expected_win_rate, description",
    [
        ([], 0.0, "No trades, win rate 0%"),
        ([10.0, 20.0], 100.0, "All winning trades, win rate 100%"),
        ([-5.0, -15.0], 0.0, "All losing trades, win rate 0%"),
        ([10.0, -5.0, 0.0], pytest.approx(1/3 * 100), "Mixed with one breakeven, win rate 33.33%"),
        ([0.0, 0.0], 0.0, "All breakeven trades, win rate 0%")
    ]
)
async def test_get_all_strategies_performance_win_rate_edge_cases(
    performance_service, mock_persistence_service, mock_strategy_service,
    trades_pnl, expected_win_rate, description
):
    """
    Test win_rate calculation for edge cases: no trades, all winning, all losing, break-even.
    """
    strategy_id = uuid4()
    
    trades = []
    for i, pnl in enumerate(trades_pnl):
        trade = Trade(
            id=uuid4(), user_id=USER_ID, mode=TradeMode.PAPER, symbol=f"SYM{i}", side=TradeSide.BUY,
            entryOrder=create_mock_trade_order_details(
                order_category=OrderCategory.ENTRY,
                requested_quantity=Decimal("0.01"),
                executed_quantity=Decimal("0.01"),
                executed_price=Decimal("50000.0"),
                timestamp=datetime.now(timezone.utc)
            ),
            exitOrders=[
                create_mock_trade_order_details(
                    order_category=OrderCategory.TAKE_PROFIT if pnl > 0 else OrderCategory.STOP_LOSS,
                    requested_quantity=Decimal("0.01"),
                    executed_quantity=Decimal("0.01"),
                    executed_price=Decimal(str(50000.0 + pnl)), # Ajustar precio de salida para reflejar PnL
                    timestamp=datetime.now(timezone.utc)
                )
            ],
            positionStatus=PositionStatus.CLOSED,
            strategyId=strategy_id, pnl_usd=Decimal(str(pnl)), pnl_percentage=Decimal("0.01") if pnl > 0 else (Decimal("-0.01") if pnl < 0 else Decimal("0.0")),
            opened_at=datetime.now(timezone.utc), closed_at=datetime.now(timezone.utc),
            opportunityId=None, aiAnalysisConfidence=None, closingReason="Test",
            ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
            trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        )
        trades.append(trade)

    mock_persistence_service.get_trades_with_filters.return_value = trades
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy_id), user_id=str(USER_ID), config_name="WinRate Test Strat",
        base_strategy_type=BaseStrategyType.SCALPING, parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=60,
            leverage=1.0
        ),
        is_active_paper_mode=True, is_active_real_mode=False, description=description,
        allowed_symbols=None, # Añadido para SRST-5011
        excluded_symbols=None, # Añadido para SRST-5011
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_service.get_strategy_config.return_value = mock_strategy_config

    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)

    if not trades: # No trades, no performance data
        assert result == []
    else:
        assert len(result) == 1
        perf_data = result[0]
        assert perf_data.strategyId == strategy_id
        assert perf_data.totalOperations == len(trades_pnl)
        assert perf_data.win_rate == expected_win_rate
