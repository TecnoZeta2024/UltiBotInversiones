import pytest
from unittest.mock import AsyncMock, MagicMock # Usar AsyncMock para métodos async
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.api.v1.models.performance_models import OperatingMode, StrategyPerformanceData
from shared.data_types import Trade # Asegúrate que Trade y PositionStatus estén aquí o importables
from ultibot_backend.core.domain_models.trade_models import PositionStatus
from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType # Para mock de strategy_config


USER_ID = uuid4()

@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_strategy_service():
    service = AsyncMock(spec=StrategyService)
    # Configurar un comportamiento por defecto para get_strategy_config
    default_strategy_config = TradingStrategyConfig(
        id=str(uuid4()), # id es Optional[str]
        user_id=str(USER_ID), # user_id es str
        config_name="Estrategia por Defecto",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters={},
        is_active_paper_mode=True,
        is_active_real_mode=False,
        description="Descripción por defecto",
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
    mock_persistence_service.get_all_trades_for_user.return_value = []
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID)
    
    assert result == []
    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, None)

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
        mode="paper", # mode es str
        symbol="BTCUSDT",
        side="BUY",
        entryOrder=MagicMock(), 
        positionStatus=PositionStatus.OPEN.value, 
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
    mock_persistence_service.get_all_trades_for_user.return_value = [open_trade]
    
    result = await performance_service.get_all_strategies_performance(user_id=USER_ID)
    
    assert result == []
    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, None)

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
        mode="paper", 
        symbol="BTCUSDT",
        side="BUY",
        entryOrder=MagicMock(), 
        positionStatus=PositionStatus.CLOSED.value,
        strategyId=strategy1_id,
        pnl_usd=10.0, 
        pnl_percentage=0.01,
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
    mock_persistence_service.get_all_trades_for_user.return_value = [closed_trade]
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy1_id),
        user_id=str(USER_ID),
        config_name="Test Strategy 1",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters={},
        is_active_paper_mode=True,
        is_active_real_mode=False,
        description="Test strategy description",
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
    
    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, "paper")
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
        "user_id": USER_ID, "mode": "paper", "entryOrder": MagicMock(), 
        "positionStatus": PositionStatus.CLOSED.value, "strategyId": strategy1_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": 0.0, "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    trade1 = Trade(id=trade1_id, symbol="BTCUSDT", side="BUY", pnl_usd=20.0, **common_trade_params)
    trade2 = Trade(id=trade2_id, symbol="ETHUSDT", side="SELL", pnl_usd=-5.0, **common_trade_params)
    trade3 = Trade(id=trade3_id, symbol="ADAUSDT", side="BUY", pnl_usd=15.0, **common_trade_params)
    
    mock_persistence_service.get_all_trades_for_user.return_value = [trade1, trade2, trade3]
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy1_id), user_id=str(USER_ID), config_name="Scalping Pro", 
        base_strategy_type=BaseStrategyType.SCALPING, parameters={}, 
        is_active_paper_mode=True, is_active_real_mode=False, description="Scalping strategy",
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
        "user_id": USER_ID, "entryOrder": MagicMock(), 
        "positionStatus": PositionStatus.CLOSED.value, 
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": 0.0, "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    paper_trade = Trade(id=trade_paper_id, mode="paper", symbol="BTCUSDT", side="BUY", strategyId=strategy_paper_id, pnl_usd=10.0, **common_trade_params_filter_test)
    real_trade = Trade(id=trade_real_id, mode="real", symbol="ETHUSDT", side="SELL", strategyId=strategy_real_id, pnl_usd=50.0, **common_trade_params_filter_test)
    
    mock_persistence_service.get_all_trades_for_user.return_value = [real_trade] 
    
    mock_strategy_config_real = TradingStrategyConfig(
        id=str(strategy_real_id), user_id=str(USER_ID), config_name="Real Trader", 
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters={}, 
        is_active_paper_mode=False, is_active_real_mode=True, description="Real trading strategy",
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
    assert perf_data.win_rate == 100.0
    
    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, "real")

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
        "user_id": USER_ID, "mode": "paper", "entryOrder": MagicMock(), 
        "positionStatus": PositionStatus.CLOSED.value, "strategyId": strategy_unknown_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": 0.0, "opportunityId": None, "aiAnalysisConfidence": None, 
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None, 
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }
    
    trade = Trade(id=trade_id, symbol="BTCUSDT", side="BUY", pnl_usd=10.0, **common_trade_params_unknown_strat)
    mock_persistence_service.get_all_trades_for_user.return_value = [trade]
    
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
        "user_id": USER_ID, "entryOrder": MagicMock(),
        "positionStatus": PositionStatus.CLOSED.value,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": 0.0, "opportunityId": None, "aiAnalysisConfidence": None,
        "closingReason": None, "ocoOrderListId": None, "takeProfitPrice": None,
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    paper_trade = Trade(
        id=trade_paper_id, mode="paper", symbol="BTCUSDT", side="BUY",
        strategyId=strategy_paper_id, pnl_usd=15.0, **common_trade_params_multi_strat
    )
    real_trade = Trade(
        id=trade_real_id, mode="real", symbol="ETHUSDT", side="SELL",
        strategyId=strategy_real_id, pnl_usd=25.0, **common_trade_params_multi_strat
    )

    # Cuando se llama sin filtro de modo, debe devolver todos los trades
    mock_persistence_service.get_all_trades_for_user.return_value = [paper_trade, real_trade]

    mock_strategy_config_paper = TradingStrategyConfig(
        id=str(strategy_paper_id), user_id=str(USER_ID), config_name="Paper Trader Pro",
        base_strategy_type=BaseStrategyType.SCALPING, parameters={},
        is_active_paper_mode=True, is_active_real_mode=False, description="Paper trading strategy",
        version=1, applicability_rules=None, ai_analysis_profile_id=None, risk_parameters_override=None,
        parent_config_id=None, performance_metrics=None, market_condition_filters=None,
        activation_schedule=None, depends_on_strategies=None, sharing_metadata=None, created_at=None, updated_at=None
    )
    mock_strategy_config_real = TradingStrategyConfig(
        id=str(strategy_real_id), user_id=str(USER_ID), config_name="Real Deal Trader",
        base_strategy_type=BaseStrategyType.DAY_TRADING, parameters={},
        is_active_paper_mode=False, is_active_real_mode=True, description="Real trading strategy",
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
    
    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, None)
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
        "user_id": USER_ID, "mode": "paper", "entryOrder": MagicMock(),
        "positionStatus": PositionStatus.CLOSED.value, "strategyId": strategy_id,
        "opened_at": datetime.now(timezone.utc), "closed_at": datetime.now(timezone.utc),
        "pnl_percentage": 0.0, "opportunityId": None, "aiAnalysisConfidence": None,
        "closingReason": "Break Even", "ocoOrderListId": None, "takeProfitPrice": None,
        "trailingStopActivationPrice": None, "trailingStopCallbackRate": None, "currentStopPrice_tsl": None,
    }

    trade1 = Trade(id=trade1_id, symbol="XRPUSDT", side="BUY", pnl_usd=0.0, **common_trade_params_breakeven)
    trade2 = Trade(id=trade2_id, symbol="LTCUSDT", side="SELL", pnl_usd=0.0, **common_trade_params_breakeven)

    mock_persistence_service.get_all_trades_for_user.return_value = [trade1, trade2]

    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy_id), user_id=str(USER_ID), config_name="Breakeven Master",
        base_strategy_type=BaseStrategyType.GRID_TRADING, parameters={},
        is_active_paper_mode=True, is_active_real_mode=False, description="Grid strategy for breakeven",
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
        mode="paper",
        symbol="SOLUSDT",
        side="BUY",
        entryOrder=MagicMock(),
        positionStatus=PositionStatus.CLOSED.value,
        strategyId=None, # Explicitly None
        pnl_usd=5.0,
        pnl_percentage=0.02,
        opened_at=datetime.now(timezone.utc),
        closed_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, closingReason="Manual",
        ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
        trailingStopCallbackRate=None, currentStopPrice_tsl=None,
    )
    mock_persistence_service.get_all_trades_for_user.return_value = [trade_no_strategy]
    mock_strategy_service.get_strategy_config.return_value = None # Simulate strategy not found for "None"

    result = await performance_service.get_all_strategies_performance(user_id=USER_ID, mode_filter=OperatingMode.PAPER)

    # Expect one performance data entry for the "None" strategyId
    assert len(result) == 1
    perf_data = result[0]

    assert perf_data.strategyId is None # The key in the dict was None
    assert perf_data.strategyName == "Estrategia Desconocida" # Default name for unfound strategies
    assert perf_data.totalOperations == 1
    assert perf_data.totalPnl == 5.0
    assert perf_data.win_rate == 100.0

    mock_persistence_service.get_all_trades_for_user.assert_called_once_with(USER_ID, "paper")
    # It will try to fetch a strategy with ID "None"
    mock_strategy_service.get_strategy_config.assert_called_once_with(None, str(USER_ID))

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "trades_pnl, expected_win_rate, description",
    [
        ([], 0.0, "No trades, win rate 0%"),
        ([10.0, 20.0], 100.0, "All winning trades, win rate 100%"),
        ([-5.0, -15.0], 0.0, "All losing trades, win rate 0%"),
        ([10.0, -5.0, 0.0], pytest.approx(1/2 * 100), "Mixed with one breakeven, win rate 50% of non-breakeven"),
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
            id=uuid4(), user_id=USER_ID, mode="paper", symbol=f"SYM{i}", side="BUY",
            entryOrder=MagicMock(), positionStatus=PositionStatus.CLOSED.value,
            strategyId=strategy_id, pnl_usd=pnl, pnl_percentage=0.01 if pnl > 0 else (-0.01 if pnl < 0 else 0.0),
            opened_at=datetime.now(timezone.utc), closed_at=datetime.now(timezone.utc),
            opportunityId=None, aiAnalysisConfidence=None, closingReason="Test",
            ocoOrderListId=None, takeProfitPrice=None, trailingStopActivationPrice=None,
            trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        )
        trades.append(trade)

    mock_persistence_service.get_all_trades_for_user.return_value = trades
    
    mock_strategy_config = TradingStrategyConfig(
        id=str(strategy_id), user_id=str(USER_ID), config_name="WinRate Test Strat",
        base_strategy_type=BaseStrategyType.SCALPING, parameters={},
        is_active_paper_mode=True, is_active_real_mode=False, description=description,
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

