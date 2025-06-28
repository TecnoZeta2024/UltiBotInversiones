import pytest
import sys
sys.path.insert(0, 'src')
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from services.trading_engine_service import TradingEngine, TradingDecision
from services.ai_orchestrator_service import AIAnalysisResult
from core.domain_models.trading_strategy_models import (
    TradingStrategyConfig, BaseStrategyType, ScalpingParameters
)
from core.domain_models.user_configuration_models import (
    UserConfiguration, AIStrategyConfiguration, ConfidenceThresholds
)
from core.domain_models.opportunity_models import (
    Opportunity, OpportunityStatus, SourceType, Direction, InitialSignal, SuggestedAction, RecommendedTradeParams
)
from shared.data_types import PortfolioSnapshot, PortfolioSummary

from tests.conftest import FIXED_USER_ID

@pytest.fixture
def sample_strategy_id() -> uuid.UUID:
    """Provides a consistent strategy ID for tests."""
    return uuid.uuid4()

@pytest.fixture
def sample_opportunity(sample_strategy_id: uuid.UUID) -> Opportunity:
    """
    Provides a fully-formed Opportunity object, ensuring all fields are present.
    """
    now = datetime.now(timezone.utc)
    return Opportunity(
        id=str(uuid.uuid4()),
        user_id=str(FIXED_USER_ID),
        strategy_id=sample_strategy_id,
        exchange="binance",
        symbol="BTCUSDT",
        detected_at=now,
        source_type=SourceType.INTERNAL_INDICATOR_ALGO,
        source_name="test_indicator",
        source_data=None,
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=Decimal("30000"),
            stop_loss_target=Decimal("29500"),
            take_profit_target=[Decimal("30500")],
            timeframe=None,
            reasoning_source_structured=None,
            reasoning_source_text=None,
            confidence_source=None
        ),
        system_calculated_priority_score=None,
        last_priority_calculation_at=None,
        status=OpportunityStatus.NEW,
        status_reason_code=None,
        status_reason_text=None,
        ai_analysis=None,
        investigation_details=None,
        user_feedback=None,
        linked_trade_ids=None,
        expires_at=None,
        expiration_logic=None,
        post_trade_feedback=None,
        post_facto_simulation_results=None,
        created_at=now,
        updated_at=now
    )

@pytest.fixture
def scalping_strategy_with_ai(sample_strategy_id: uuid.UUID) -> TradingStrategyConfig:
    """Provides a fully-formed TradingStrategyConfig that requires AI analysis."""
    return TradingStrategyConfig(
        id=str(sample_strategy_id),
        user_id=str(FIXED_USER_ID),
        config_name="AI Scalping Test",
        base_strategy_type=BaseStrategyType.SCALPING,
        description=None,
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=None,
            leverage=None
        ),
        allowed_symbols=["BTCUSDT"],
        excluded_symbols=None,
        applicability_rules=None,
        ai_analysis_profile_id="ai-profile-scalping",
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None
    )

@pytest.fixture
def autonomous_scalping_strategy(sample_strategy_id: uuid.UUID) -> TradingStrategyConfig:
    """Provides a fully-formed TradingStrategyConfig that operates autonomously."""
    return TradingStrategyConfig(
        id=str(sample_strategy_id),
        user_id=str(FIXED_USER_ID),
        config_name="Autonomous Scalping Test",
        base_strategy_type=BaseStrategyType.SCALPING,
        description=None,
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=None,
            leverage=None
        ),
        allowed_symbols=["BTCUSDT"],
        excluded_symbols=None,
        applicability_rules=None,
        ai_analysis_profile_id=None,  # No AI profile means autonomous
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None
    )

@pytest.fixture
def ai_config_scalping() -> AIStrategyConfiguration:
    """Provides a fully-formed AIStrategyConfiguration."""
    return AIStrategyConfiguration(
        id="ai-profile-scalping",
        name="Scalping AI Profile",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        total_pnl=Decimal("0.0"),
        number_of_trades=0,
        applies_to_strategies=None,
        applies_to_pairs=None,
        gemini_prompt_template=None,
        tools_available_to_gemini=None,
        output_parser_config=None,
        indicator_weights=None,
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.60, real_trading=0.80),
        max_context_window_tokens=None
    )

@pytest.mark.asyncio
async def test_ai_workflow_high_confidence_generates_decision(
    trading_engine_fixture: TradingEngine,
    sample_opportunity: Opportunity,
    scalping_strategy_with_ai: TradingStrategyConfig,
    ai_config_scalping: AIStrategyConfiguration,
    mock_user_config: UserConfiguration,
):
    """
    Verify that an opportunity with AI analysis passing the confidence threshold
    results in an affirmative TradingDecision.
    """
    # 1. Setup Mocks
    strategy_service = trading_engine_fixture.strategy_service
    ai_orchestrator = trading_engine_fixture.ai_orchestrator
    persistence_service = trading_engine_fixture.persistence_service
    order_execution_service = trading_engine_fixture.unified_order_execution_service
    config_service = trading_engine_fixture.configuration_service

    # Correctly mock the service calls made by process_opportunity
    strategy_service.get_active_strategies = AsyncMock(return_value=[scalping_strategy_with_ai])
    strategy_service.is_strategy_applicable_to_symbol = AsyncMock(return_value=True)
    strategy_service.strategy_can_operate_autonomously = AsyncMock(return_value=False)
    
    mock_user_config.ai_strategy_configurations = [ai_config_scalping]
    config_service.get_user_configuration = AsyncMock(return_value=mock_user_config)

    ai_result = AIAnalysisResult(
        analysis_id=str(uuid.uuid4()),
        calculated_confidence=0.85,
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="Strong bullish indicators observed.",
        recommended_trade_params=RecommendedTradeParams(
            entry_price=Decimal("30000"),
            stop_loss_price=Decimal("29500"),
            take_profit_levels=[Decimal("30500")],
            trade_size_percentage=None
        ).model_dump()
    )
    ai_orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock(return_value=ai_result)
    persistence_service.update_opportunity_status = AsyncMock()
    persistence_service.upsert_trade = AsyncMock()

    # 2. Execute
    decisions = await trading_engine_fixture.process_opportunity(sample_opportunity)

    # 3. Assertions
    ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
    
    assert len(decisions) == 1
    decision = decisions[0]
    assert isinstance(decision, TradingDecision)
    assert decision.decision == "execute_trade"
    assert decision.confidence == 0.85
    assert decision.ai_analysis_used is True

    persistence_service.update_opportunity_status.assert_called_once()
    call_kwargs = persistence_service.update_opportunity_status.call_args.kwargs
    assert call_kwargs['new_status'] == OpportunityStatus.UNDER_EVALUATION

    order_execution_service.execute_market_order.assert_not_called()
    persistence_service.upsert_trade.assert_not_called()

@pytest.mark.asyncio
async def test_ai_workflow_low_confidence_rejects_opportunity(
    trading_engine_fixture: TradingEngine,
    sample_opportunity: Opportunity,
    scalping_strategy_with_ai: TradingStrategyConfig,
    ai_config_scalping: AIStrategyConfiguration,
    mock_user_config: UserConfiguration,
):
    """
    Verify that an opportunity with AI analysis failing the confidence threshold
    is rejected and does not generate a trade decision.
    """
    # 1. Setup Mocks
    strategy_service = trading_engine_fixture.strategy_service
    ai_orchestrator = trading_engine_fixture.ai_orchestrator
    persistence_service = trading_engine_fixture.persistence_service
    order_execution_service = trading_engine_fixture.unified_order_execution_service
    config_service = trading_engine_fixture.configuration_service

    strategy_service.get_active_strategies = AsyncMock(return_value=[scalping_strategy_with_ai])
    strategy_service.is_strategy_applicable_to_symbol = AsyncMock(return_value=True)
    strategy_service.strategy_can_operate_autonomously = AsyncMock(return_value=False)
    
    mock_user_config.ai_strategy_configurations = [ai_config_scalping]
    config_service.get_user_configuration = AsyncMock(return_value=mock_user_config)

    ai_result = AIAnalysisResult(
        analysis_id=str(uuid.uuid4()),
        calculated_confidence=0.40, # Below the 0.6 threshold
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="Indicators are weak.",
    )
    ai_orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock(return_value=ai_result)
    persistence_service.update_opportunity_status = AsyncMock()

    # 2. Execute
    decisions = await trading_engine_fixture.process_opportunity(sample_opportunity)

    # 3. Assertions
    ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
    
    assert len(decisions) == 0

    persistence_service.update_opportunity_status.assert_called_once()
    call_kwargs = persistence_service.update_opportunity_status.call_args.kwargs
    assert call_kwargs['new_status'] == OpportunityStatus.REJECTED_BY_SYSTEM
    assert call_kwargs['status_reason'] == "All applicable strategies evaluated, but none resulted in a decision to trade."

    order_execution_service.execute_market_order.assert_not_called()

@pytest.mark.asyncio
async def test_autonomous_strategy_generates_decision_without_ai(
    trading_engine_fixture: TradingEngine,
    sample_opportunity: Opportunity,
    autonomous_scalping_strategy: TradingStrategyConfig,
    mock_user_config: UserConfiguration,
):
    """
    Verify that an opportunity for an autonomous strategy bypasses AI analysis
    and directly generates a TradingDecision.
    """
    # 1. Setup Mocks
    strategy_service = trading_engine_fixture.strategy_service
    ai_orchestrator = trading_engine_fixture.ai_orchestrator
    persistence_service = trading_engine_fixture.persistence_service
    order_execution_service = trading_engine_fixture.unified_order_execution_service
    config_service = trading_engine_fixture.configuration_service

    strategy_service.get_active_strategies = AsyncMock(return_value=[autonomous_scalping_strategy])
    strategy_service.is_strategy_applicable_to_symbol = AsyncMock(return_value=True)
    strategy_service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    config_service.get_user_configuration = AsyncMock(return_value=mock_user_config)
    
    ai_orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock()
    persistence_service.update_opportunity_status = AsyncMock()
    persistence_service.upsert_trade = AsyncMock()

    # 2. Execute
    decisions = await trading_engine_fixture.process_opportunity(sample_opportunity)

    # 3. Assertions
    ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
    
    assert len(decisions) == 1
    decision = decisions[0]
    assert isinstance(decision, TradingDecision)
    assert decision.decision == "execute_trade"
    assert decision.ai_analysis_used is False

    persistence_service.update_opportunity_status.assert_called_once()
    call_kwargs = persistence_service.update_opportunity_status.call_args.kwargs
    assert call_kwargs['new_status'] == OpportunityStatus.UNDER_EVALUATION

    order_execution_service.execute_market_order.assert_not_called()
    persistence_service.upsert_trade.assert_not_called()
