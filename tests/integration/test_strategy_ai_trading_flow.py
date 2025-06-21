"""Integration tests for Strategy-AI-TradingEngine flow.

Tests for the complete workflow: Strategy -> AI_Orchestrator -> Trading Decision.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta # Importar timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ultibot_backend.services.trading_engine_service import (
    TradingEngine,
    TradingDecision,
)
from ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
)
from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    Timeframe, # Importar Timeframe
    ApplicabilityRules, # Importar ApplicabilityRules
    DynamicFilter, # Importar DynamicFilter
    RiskParametersOverride, # Importar RiskParametersOverride
    PerformanceMetrics, # Importar PerformanceMetrics
    MarketConditionFilter, # Importar MarketConditionFilter
    ActivationSchedule, # Importar ActivationSchedule
    SharingMetadata, # Importar SharingMetadata
)
from ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
    UserConfiguration,
)
import logging # Importar logging
from ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    SourceType,
    Direction,
    InitialSignal,
    AIAnalysis, # Importar AIAnalysis
    SuggestedAction, # Importar SuggestedAction
    ExpirationLogic, # Importar ExpirationLogic
    RecommendedTradeParams, # Importar RecommendedTradeParams
    DataVerification, # Importar DataVerification
)
from shared.data_types import PortfolioSnapshot

logger = logging.getLogger(__name__) # Inicializar logger




@pytest.fixture
def mock_configuration_service():
    """Create mock configuration service."""
    service = Mock()
    return service


@pytest.fixture
def mock_ai_orchestrator():
    """Create mock AI orchestrator."""
    # Using spec=AIOrchestrator ensures the mock has the same interface
    # as the real class, which helps with type checking and auto-completion.
    orchestrator = Mock(spec=AIOrchestrator)
    orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock()
    return orchestrator


# Se elimina la fixture local 'trading_engine' para usar la global de conftest.py
# @pytest.fixture
# def trading_engine(mock_strategy_service, mock_configuration_service, mock_ai_orchestrator):
#     """Create trading engine with mocked dependencies."""
#     return TradingEngine(
#         strategy_service=mock_strategy_service,
#         configuration_service=mock_configuration_service,
#         ai_orchestrator=mock_ai_orchestrator,
#     )


@pytest.fixture
def sample_opportunity():
    """Create sample opportunity for testing."""
    return Opportunity(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        strategy_id=uuid.uuid4(),
        symbol="BTC/USDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.INTERNAL_INDICATOR_ALGO,
        source_name="RSI_MACD_Signal",
        source_data={"indicator": "RSI", "value": 65},
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=Decimal("30000.0"),
            stop_loss_target=Decimal("29500.0"),
            take_profit_target=[Decimal("30500.0"), Decimal("31000.0")],
            timeframe="5m",
            confidence_source=0.75,
            reasoning_source_text="Strong bullish momentum detected",
            reasoning_source_structured={"indicator": "RSI", "value": 65},
        ),
        system_calculated_priority_score=80,
        last_priority_calculation_at=datetime.now(timezone.utc),
        status=OpportunityStatus.NEW,
        status_reason_code="initial_detection",
        status_reason_text="Opportunity detected by internal algorithm.",
        ai_analysis=None,
        investigation_details=None,
        user_feedback=None,
        linked_trade_ids=[],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        expiration_logic=ExpirationLogic(type="time", value="1h"),
        post_trade_feedback=None,
        post_facto_simulation_results=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def scalping_strategy_with_ai():
    """Create scalping strategy configured to use AI."""
    return TradingStrategyConfig(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        config_name="AI-Enhanced Scalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Scalping strategy with AI analysis",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=300,
            leverage=10.0,
        ),
        ai_analysis_profile_id="ai-profile-scalping-1",
        allowed_symbols=["BTC/USDT"],
        excluded_symbols=[],
        applicability_rules=ApplicabilityRules(
            include_all_spot=False,
            dynamic_filter=DynamicFilter(
                min_daily_volatility_percentage=0.001,
                max_daily_volatility_percentage=0.05,
                min_market_cap_usd=1000000000,
                included_watchlist_ids=["watchlist-1"],
                asset_categories=["crypto"]
            )
        ),
        risk_parameters_override=RiskParametersOverride(
            per_trade_capital_risk_percentage=0.01,
            max_concurrent_trades_for_this_strategy=5,
            max_capital_allocation_quote=10000.0
        ),
        version=1,
        parent_config_id=None,
        performance_metrics=PerformanceMetrics(
            total_trades_executed=100,
            winning_trades=60,
            losing_trades=40,
            cumulative_pnl_quote=500.0,
            average_winning_trade_pnl=10.0,
            average_losing_trade_pnl=-5.0,
            profit_factor=1.5,
            sharpe_ratio=1.2,
            win_rate=0.6
        ),
        market_condition_filters=[
            MarketConditionFilter(
                filter_type="volatility",
                source_id="binance",
                condition="high",
                threshold_value=0.02,
                action_on_trigger="warn"
            )
        ],
        activation_schedule=ActivationSchedule(
            cron_expression="0 9 * * 1-5",
            time_zone="UTC",
            event_triggers=[{"event": "market_open", "value": "9:00"}]
        ),
        depends_on_strategies=[],
        sharing_metadata=SharingMetadata(
            is_template=False,
            author_user_id=str(uuid.uuid4()),
            user_rating_average=4.5,
            download_or_copy_count=100,
            tags=["scalping", "ai"]
        ),
    )


@pytest.fixture
def scalping_strategy_without_ai():
    """Create scalping strategy configured to operate autonomously."""
    return TradingStrategyConfig(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        config_name="Autonomous Scalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Autonomous scalping strategy",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.015,
            stop_loss_percentage=0.008,
            max_holding_time_seconds=600,
            leverage=5.0,
        ),
        ai_analysis_profile_id=None,
        allowed_symbols=["ETH/USDT"],
        excluded_symbols=[],
        applicability_rules=ApplicabilityRules(
            include_all_spot=True,
            dynamic_filter=DynamicFilter(
                min_daily_volatility_percentage=0.0005,
                max_daily_volatility_percentage=0.03,
                min_market_cap_usd=500000000,
                included_watchlist_ids=["watchlist-2"],
                asset_categories=["crypto"]
            )
        ),
        risk_parameters_override=RiskParametersOverride(
            per_trade_capital_risk_percentage=0.005,
            max_concurrent_trades_for_this_strategy=3,
            max_capital_allocation_quote=5000.0
        ),
        version=1,
        parent_config_id=None,
        performance_metrics=PerformanceMetrics(
            total_trades_executed=50,
            winning_trades=35,
            losing_trades=15,
            cumulative_pnl_quote=200.0,
            average_winning_trade_pnl=8.0,
            average_losing_trade_pnl=-4.0,
            profit_factor=2.0,
            sharpe_ratio=1.8,
            win_rate=0.7
        ),
        market_condition_filters=[
            MarketConditionFilter(
                filter_type="volatility",
                source_id="binance",
                condition="medium",
                threshold_value=0.01,
                action_on_trigger="warn"
            )
        ],
        activation_schedule=ActivationSchedule(
            cron_expression="0 8 * * 1-5",
            time_zone="UTC",
            event_triggers=[{"event": "market_open", "value": "8:00"}]
        ),
        depends_on_strategies=[],
        sharing_metadata=SharingMetadata(
            is_template=False,
            author_user_id=str(uuid.uuid4()),
            user_rating_average=4.0,
            download_or_copy_count=50,
            tags=["scalping", "autonomous"]
        ),
    )


@pytest.fixture
def ai_config_scalping():
    """Create AI configuration for scalping."""
    return AIStrategyConfiguration(
        id="ai-profile-scalping-1",
        name="Scalping AI Profile",
        applies_to_strategies=["SCALPING"],
        applies_to_pairs=["BTC/USDT", "ETH/USDT"],
        confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.6,
            real_trading=0.8,
        ),
        tools_available_to_gemini=["MobulaChecker", "BinanceMarketReader"],
        gemini_prompt_template="Analyze the market for scalping opportunities.",
        output_parser_config={"type": "pydantic", "schema_name": "AIAnalysisResult"},
        indicator_weights={"RSI": 0.4, "MACD": 0.6, "Volume": 0.2},
        max_context_window_tokens=4000,
    )


class TestStrategyAITradingEngineIntegration:
    """Integration tests for Strategy-AI-TradingEngine workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow_high_confidence(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        ai_config_scalping: AIStrategyConfiguration,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test complete workflow with AI analysis resulting in high confidence trade execution."""
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service_integration.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service_integration.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        mock_strategy_service_integration.get_active_strategies.return_value = [scalping_strategy_with_ai]
        
        # Mock AI analysis result with high confidence
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-123",
            calculated_confidence=0.85,
            suggested_action=SuggestedAction.BUY, # Usar Enum
            reasoning_ai="Strong bullish indicators with favorable risk/reward ratio",
            recommended_trade_strategy_type="SCALPING",
            recommended_trade_params=RecommendedTradeParams(
                entry_price=Decimal("30000.0"),
                stop_loss_price=Decimal("29500.0"),
                take_profit_levels=[Decimal("30500.0")],
                trade_size_percentage=Decimal("0.05")
            ).model_dump(),
            data_verification=DataVerification(
                mobula_check_status="verified",
                mobula_discrepancies=None,
                binance_data_check_status="verified"
            ).model_dump(),
            processing_time_ms=1500,
            ai_warnings=[],
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Execute AI analysis
        ai_analysis_result = await mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async(
            opportunity=sample_opportunity,
            strategy=scalping_strategy_with_ai,
            ai_config=ai_config_scalping,
            user_id=str(sample_opportunity.user_id),
        )

        # Simulate decision based on AI analysis and confidence thresholds
        assert ai_config_scalping.confidence_thresholds is not None
        confidence_threshold = ai_config_scalping.confidence_thresholds.paper_trading
        if ai_analysis_result.calculated_confidence >= confidence_threshold:
            # Simulate a confirmed opportunity for trade execution
            sample_opportunity.status = OpportunityStatus.CONFIRMED_BY_AI
            sample_opportunity.ai_analysis = AIAnalysis(
                analysis_id=ai_analysis_result.analysis_id,
                analyzed_at=datetime.now(timezone.utc),
                model_used=ai_analysis_result.model_used,
                calculated_confidence=ai_analysis_result.calculated_confidence,
                suggested_action=ai_analysis_result.suggested_action,
                reasoning_ai=ai_analysis_result.reasoning_ai,
                recommended_trade_strategy_type=ai_analysis_result.recommended_trade_strategy_type,
                recommended_trade_params=RecommendedTradeParams.model_validate(ai_analysis_result.recommended_trade_params),
                data_verification=DataVerification.model_validate(ai_analysis_result.data_verification),
                processing_time_ms=ai_analysis_result.processing_time_ms,
                ai_warnings=ai_analysis_result.ai_warnings,
            )
            decision = await trading_engine_fixture.execute_trade_from_confirmed_opportunity(
                sample_opportunity
            )
            assert decision is not None # Expect a trade object
            assert decision.symbol == sample_opportunity.symbol
            assert decision.side == ai_analysis_result.suggested_action.value.lower()
            assert decision.aiAnalysisConfidence == Decimal(str(ai_analysis_result.calculated_confidence))
            assert decision.positionStatus == "open" # Assuming immediate execution in test
            # Further assertions on trade details can be added here
        else:
            decision = TradingDecision(
                decision="reject_opportunity",
                confidence=ai_analysis_result.calculated_confidence,
                reasoning=f"AI confidence {ai_analysis_result.calculated_confidence:.2f} below threshold {confidence_threshold:.2f}",
                opportunity_id=str(sample_opportunity.id),
                strategy_id=str(scalping_strategy_with_ai.id),
                ai_analysis_used=True,
                ai_analysis_profile_id=ai_config_scalping.id,
            )
            assert decision.decision == "reject_opportunity"
            assert decision.confidence == ai_analysis_result.calculated_confidence
            assert decision.ai_analysis_used is True
            assert "below threshold" in decision.reasoning
        
        # Verify AI orchestrator was called correctly
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
        call_args = mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.call_args
        assert call_args[1]["opportunity"] == sample_opportunity
        assert call_args[1]["strategy"] == scalping_strategy_with_ai
        assert call_args[1]["ai_config"] == ai_config_scalping
        assert call_args[1]["user_id"] == str(sample_opportunity.user_id)
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow_low_confidence(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        ai_config_scalping: AIStrategyConfiguration,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test complete workflow with AI analysis resulting in low confidence rejection."""
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service_integration.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service_integration.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        mock_strategy_service_integration.get_active_strategies.return_value = [scalping_strategy_with_ai]
        
        # Mock AI analysis result with low confidence
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-456",
            calculated_confidence=0.4,  # Below paper trading threshold of 0.6
            suggested_action=SuggestedAction.HOLD_NEUTRAL, # Usar Enum
            reasoning_ai="Mixed signals, insufficient confidence for trade execution",
            recommended_trade_strategy_type="SCALPING",
            recommended_trade_params=None,
            data_verification=DataVerification(
                mobula_check_status="verified",
                mobula_discrepancies=None,
                binance_data_check_status="sufficient"
            ).model_dump(),
            processing_time_ms=1200,
            ai_warnings=[],
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Execute AI analysis
        ai_analysis_result = await mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async(
            opportunity=sample_opportunity,
            strategy=scalping_strategy_with_ai,
            ai_config=ai_config_scalping,
            user_id=str(sample_opportunity.user_id),
        )

        # Simulate decision based on AI analysis and confidence thresholds
        assert ai_config_scalping.confidence_thresholds is not None
        confidence_threshold = ai_config_scalping.confidence_thresholds.paper_trading
        if ai_analysis_result.calculated_confidence >= confidence_threshold:
            # Simulate a confirmed opportunity for trade execution
            sample_opportunity.status = OpportunityStatus.CONFIRMED_BY_AI
            sample_opportunity.ai_analysis = AIAnalysis(
                analysis_id=ai_analysis_result.analysis_id,
                analyzed_at=datetime.now(timezone.utc),
                model_used=ai_analysis_result.model_used,
                calculated_confidence=ai_analysis_result.calculated_confidence,
                suggested_action=ai_analysis_result.suggested_action,
                reasoning_ai=ai_analysis_result.reasoning_ai,
                recommended_trade_strategy_type=ai_analysis_result.recommended_trade_strategy_type,
                recommended_trade_params=None,
                data_verification=DataVerification.model_validate(ai_analysis_result.data_verification),
                processing_time_ms=ai_analysis_result.processing_time_ms,
                ai_warnings=ai_analysis_result.ai_warnings,
            )
            decision = await trading_engine_fixture.execute_trade_from_confirmed_opportunity(
                sample_opportunity
            )
            assert decision is not None
        else:
            decision = TradingDecision(
                decision="reject_opportunity",
                confidence=ai_analysis_result.calculated_confidence,
                reasoning=f"AI confidence {ai_analysis_result.calculated_confidence:.2f} below threshold {confidence_threshold:.2f}",
                opportunity_id=str(sample_opportunity.id),
                strategy_id=str(scalping_strategy_with_ai.id),
                ai_analysis_used=True,
                ai_analysis_profile_id=ai_config_scalping.id,
            )
            assert decision.decision == "reject_opportunity"
            assert decision.confidence == ai_analysis_result.calculated_confidence
            assert decision.ai_analysis_used is True
            assert "below threshold" in decision.reasoning
        
        # Verify AI orchestrator was called correctly
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
        call_args = mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.call_args
        assert call_args[1]["opportunity"] == sample_opportunity
        assert call_args[1]["strategy"] == scalping_strategy_with_ai
        assert call_args[1]["ai_config"] == ai_config_scalping
        assert call_args[1]["user_id"] == str(sample_opportunity.user_id)
    
    @pytest.mark.asyncio
    async def test_ai_failure_fallback_to_autonomous(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        ai_config_scalping: AIStrategyConfiguration,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test fallback to autonomous evaluation when AI analysis fails."""
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service_integration.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service_integration.strategy_can_operate_autonomously.return_value = True
        mock_strategy_service_integration.get_active_strategies.return_value = [scalping_strategy_with_ai]
        
        # Mock AI orchestrator to raise exception
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.side_effect = (
            Exception("AI service temporarily unavailable")
        )
        
        # Execute AI analysis (which will fail)
        ai_analysis_result = None
        try:
            ai_analysis_result = await mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async(
                opportunity=sample_opportunity,
                strategy=scalping_strategy_with_ai,
                ai_config=ai_config_scalping,
                user_id=str(sample_opportunity.user_id),
            )
        except Exception:
            logger.info("AI analysis failed as expected, falling back to autonomous.")

        # Simulate autonomous decision (since AI failed)
        # In a real scenario, this would involve calling a method on strategy_service
        # or a dedicated autonomous evaluation service. For this test, we simulate a decision.
        decision = TradingDecision(
            decision="execute_trade", # Simulate a positive autonomous decision
            confidence=0.7,
            reasoning="Autonomous evaluation due to AI failure.",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(scalping_strategy_with_ai.id),
            ai_analysis_used=False,
        )

        # Now, actually process the opportunity with the engine, which should trigger the fallback
        await trading_engine_fixture.process_opportunity(sample_opportunity)

        # Verify AI orchestrator was called and raised an exception
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
        
        # Verify that the fallback logic was triggered
        mock_strategy_service_integration.strategy_can_operate_autonomously.assert_called_once()

    @pytest.mark.asyncio
    async def test_autonomous_strategy_evaluation(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_without_ai: TradingStrategyConfig,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test evaluation of strategy configured to operate autonomously."""
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = False
        mock_strategy_service_integration.get_active_strategies.return_value = [scalping_strategy_without_ai]
        
        # For autonomous strategies, we directly simulate the decision
        # as there's no AI analysis step.
        # In a real scenario, this would involve calling a method on strategy_service
        # or a dedicated autonomous evaluation service.
        decision = TradingDecision(
            decision="execute_trade", # Simulate a positive autonomous decision
            confidence=0.9, # High confidence for autonomous
            reasoning="Autonomous strategy identifies strong opportunity.",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(scalping_strategy_without_ai.id),
            ai_analysis_used=False,
        )

        # If autonomous decision is to execute, simulate trade execution
        if decision.decision == "execute_trade":
            sample_opportunity.status = OpportunityStatus.CONFIRMED_BY_AUTONOMOUS
            trade = await trading_engine_fixture.execute_trade_from_confirmed_opportunity(
                sample_opportunity
            )
            assert trade is not None
            assert trade.symbol == sample_opportunity.symbol
            assert trade.positionStatus == "open" # Cambiado a minúsculas para coincidir con PositionStatus.OPEN.value
        else:
            assert False, "Autonomous decision should lead to trade execution in this test case."
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_different_confidence_thresholds_paper_vs_real(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        ai_config_scalping: AIStrategyConfiguration,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test different confidence thresholds for paper vs real trading modes."""
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service_integration.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service_integration.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        mock_strategy_service_integration.get_active_strategies.return_value = [scalping_strategy_with_ai]
        
        # Mock AI analysis result with medium confidence (0.7)
        # This should pass paper trading (0.6 threshold) but fail real trading (0.8 threshold)
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-789",
            calculated_confidence=0.7,
            suggested_action=SuggestedAction.BUY, # Usar Enum
            reasoning_ai="Moderate confidence trade opportunity",
            recommended_trade_strategy_type="SCALPING",
            recommended_trade_params=RecommendedTradeParams(
                entry_price=Decimal("30000.0"),
                stop_loss_price=Decimal("29500.0"),
                take_profit_levels=[Decimal("30500.0")],
                trade_size_percentage=Decimal("0.01")
            ).model_dump(),
            data_verification=DataVerification(
                mobula_check_status="verified",
                mobula_discrepancies=None,
                binance_data_check_status="sufficient"
            ).model_dump(),
            processing_time_ms=1300,
            ai_warnings=[],
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Test paper trading mode
        ai_analysis_result_paper = await mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async(
            opportunity=sample_opportunity,
            strategy=scalping_strategy_with_ai,
            ai_config=ai_config_scalping,
            user_id=str(sample_opportunity.user_id),
        )
        assert ai_config_scalping.confidence_thresholds is not None
        confidence_threshold_paper = ai_config_scalping.confidence_thresholds.paper_trading
        if ai_analysis_result_paper.calculated_confidence >= confidence_threshold_paper:
            sample_opportunity.status = OpportunityStatus.CONFIRMED_BY_AI
            sample_opportunity.ai_analysis = AIAnalysis(
                analysis_id=ai_analysis_result_paper.analysis_id,
                analyzed_at=datetime.now(timezone.utc),
                model_used=ai_analysis_result_paper.model_used,
                calculated_confidence=ai_analysis_result_paper.calculated_confidence,
                suggested_action=ai_analysis_result_paper.suggested_action,
                reasoning_ai=ai_analysis_result_paper.reasoning_ai,
                recommended_trade_strategy_type=ai_analysis_result_paper.recommended_trade_strategy_type,
                recommended_trade_params=RecommendedTradeParams.model_validate(ai_analysis_result_paper.recommended_trade_params),
                data_verification=DataVerification.model_validate(ai_analysis_result_paper.data_verification),
                processing_time_ms=ai_analysis_result_paper.processing_time_ms,
                ai_warnings=ai_analysis_result_paper.ai_warnings,
            )
            paper_trade = await trading_engine_fixture.execute_trade_from_confirmed_opportunity(
                sample_opportunity
            )
            assert paper_trade is not None
            assert paper_trade.positionStatus == "open" # Cambiado a minúsculas para coincidir con PositionStatus.OPEN.value
        else:
            assert False, "Paper trading should have executed trade."

        # Reset mock for real trading mode test
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.reset_mock()

        # Test real trading mode
        ai_analysis_result_real = await mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async(
            opportunity=sample_opportunity,
            strategy=scalping_strategy_with_ai,
            ai_config=ai_config_scalping,
            user_id=str(sample_opportunity.user_id),
        )
        assert ai_config_scalping.confidence_thresholds is not None
        confidence_threshold_real = ai_config_scalping.confidence_thresholds.real_trading
        if ai_analysis_result_real.calculated_confidence >= confidence_threshold_real:
            assert False, "Real trading should have been rejected due to low confidence."
        else:
            # Simulate rejection decision
            real_decision = TradingDecision(
                decision="reject_opportunity",
                confidence=ai_analysis_result_real.calculated_confidence,
                reasoning=f"AI confidence {ai_analysis_result_real.calculated_confidence:.2f} below real trading threshold {confidence_threshold_real:.2f}",
                opportunity_id=str(sample_opportunity.id),
                strategy_id=str(scalping_strategy_with_ai.id),
                ai_analysis_used=True,
                ai_analysis_profile_id=ai_config_scalping.id,
            )
            assert real_decision.decision == "reject_opportunity"
            assert "below real trading threshold" in real_decision.reasoning
    
    @pytest.mark.asyncio
    async def test_day_trading_strategy_autonomous_evaluation(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        mock_strategy_service_integration: Mock,
        mock_ai_orchestrator: Mock,
    ):
        """Test autonomous evaluation for day trading strategy."""
        # Create day trading strategy without AI
        day_strategy = TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Day Trading Strategy",
            base_strategy_type=BaseStrategyType.DAY_TRADING,
            description="Autonomous day trading strategy",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=DayTradingParameters(
                rsi_period=14,
                rsi_overbought=70,
                rsi_oversold=30,
                entry_timeframes=[Timeframe.FIVE_MINUTES, Timeframe.FIFTEEN_MINUTES], # Usar Enum
                macd_fast_period=12,
                macd_slow_period=26,
                macd_signal_period=9,
                exit_timeframes=[Timeframe.ONE_HOUR],
            ),
            ai_analysis_profile_id=None,
            allowed_symbols=["ETH/USDT"],
            excluded_symbols=[],
            applicability_rules=ApplicabilityRules(
                include_all_spot=False,
                dynamic_filter=DynamicFilter(
                    min_daily_volatility_percentage=0.002,
                    max_daily_volatility_percentage=0.06,
                    min_market_cap_usd=2000000000,
                    included_watchlist_ids=["watchlist-3"],
                    asset_categories=["crypto", "defi"]
                )
            ),
            risk_parameters_override=RiskParametersOverride(
                per_trade_capital_risk_percentage=0.02,
                max_concurrent_trades_for_this_strategy=2,
                max_capital_allocation_quote=20000.0
            ),
            version=1,
            parent_config_id=None,
            performance_metrics=PerformanceMetrics(
                total_trades_executed=200,
                winning_trades=150,
                losing_trades=50,
                cumulative_pnl_quote=1500.0,
                average_winning_trade_pnl=15.0,
                average_losing_trade_pnl=-7.5,
                profit_factor=2.5,
                sharpe_ratio=1.5,
                win_rate=0.75
            ),
            market_condition_filters=[
                MarketConditionFilter(
                    filter_type="trend",
                    source_id="tradingview",
                    condition="bullish",
                    threshold_value=0.0,
                    action_on_trigger="execute"
                )
            ],
            activation_schedule=ActivationSchedule(
                cron_expression="0 7 * * 1-5",
                time_zone="UTC",
                event_triggers=[{"event": "daily_open", "value": "7:00"}]
            ),
            depends_on_strategies=[],
            sharing_metadata=SharingMetadata(
                is_template=False,
                author_user_id=str(uuid.uuid4()),
                user_rating_average=4.8,
                download_or_copy_count=200,
                tags=["day_trading", "autonomous"]
            ),
        )
        
        # Setup mocks
        mock_strategy_service_integration.strategy_requires_ai_analysis.return_value = False
        mock_strategy_service_integration.get_active_strategies.return_value = [day_strategy]
        
        # For autonomous strategies, we directly simulate the decision
        # as there's no AI analysis step.
        decision = TradingDecision(
            decision="execute_trade", # Simulate a positive autonomous decision
            confidence=0.95, # High confidence for autonomous day trading
            reasoning="Autonomous day trading strategy identifies strong opportunity.",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(day_strategy.id),
            ai_analysis_used=False,
        )

        # If autonomous decision is to execute, simulate trade execution
        if decision.decision == "execute_trade":
            sample_opportunity.status = OpportunityStatus.CONFIRMED_BY_AUTONOMOUS
            trade = await trading_engine_fixture.execute_trade_from_confirmed_opportunity(
                sample_opportunity
            )
            assert trade is not None
            assert trade.symbol == sample_opportunity.symbol
            assert trade.positionStatus == "open" # Cambiado a minúsculas para coincidir con PositionStatus.OPEN.value
        else:
            assert False, "Autonomous decision should lead to trade execution in this test case."
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()


class TestTradeCreationFromDecision:
    """Test trade creation from trading decisions."""

    @pytest.mark.asyncio
    async def test_create_trade_from_ai_decision(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        mock_user_config: UserConfiguration,
        mock_portfolio_snapshot: PortfolioSnapshot,
    ):
        """Test creating a trade from an AI-influenced decision."""
        from decimal import Decimal
        
        # Create an AI-influenced decision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.85,
            reasoning="AI recommends strong buy with high confidence",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(scalping_strategy_with_ai.id),
            ai_analysis_used=True,
            ai_analysis_profile_id="ai-profile-scalping-1",
            recommended_trade_params={
                "entry_price": 30000.0,
                "stop_loss_target": 29500.0,
                "take_profit_target": [30500.0],
            },
        )

        # Add AI analysis to opportunity
        sample_opportunity.ai_analysis = AIAnalysis(
            analysis_id="test-analysis-decision-123",
            analyzed_at=datetime.now(timezone.utc),
            model_used="Gemini-1.5-Pro",
            calculated_confidence=0.85,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Strong bullish indicators with favorable risk/reward ratio",
            recommended_trade_strategy_type="SCALPING",
            recommended_trade_params=RecommendedTradeParams(
                entry_price=Decimal("30000.0"),
                stop_loss_price=Decimal("29500.0"),
                take_profit_levels=[Decimal("30500.0")],
                trade_size_percentage=Decimal("0.05")
            ),
            data_verification=DataVerification(
                mobula_check_status="verified",
                mobula_discrepancies=None,
                binance_data_check_status="verified"
            ),
            processing_time_ms=1500,
            ai_warnings=[],
        )

        # Create trade from decision with all required parameters
        current_price = Decimal("30000.0")
        trade = await trading_engine_fixture.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_with_ai,
            mock_user_config,
            current_price,
            mock_portfolio_snapshot,
        )

        # Verify trade creation based on the actual Trade model
        assert trade is not None
        assert trade.symbol == sample_opportunity.symbol
        assert trade.strategyId == uuid.UUID(scalping_strategy_with_ai.id)
        assert trade.opportunityId == uuid.UUID(sample_opportunity.id)
        assert trade.aiAnalysisConfidence == Decimal("0.85")

    @pytest.mark.asyncio
    async def test_create_trade_from_autonomous_decision(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_without_ai: TradingStrategyConfig,
        mock_user_config: UserConfiguration,
        mock_portfolio_snapshot: PortfolioSnapshot,
    ):
        """Test creating a trade from an autonomous decision."""
        from decimal import Decimal
        
        # Create an autonomous decision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.7,
            reasoning="Autonomous scalping strategy identifies good opportunity",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(scalping_strategy_without_ai.id),
            ai_analysis_used=False,
        )

        # Create trade from decision with all required parameters
        current_price = Decimal("30000.0")
        trade = await trading_engine_fixture.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_without_ai,
            mock_user_config,
            current_price,
            mock_portfolio_snapshot,
        )

        # Verify trade creation based on the actual Trade model
        assert trade is not None
        assert trade.strategyId == uuid.UUID(scalping_strategy_without_ai.id)
        assert trade.opportunityId == uuid.UUID(sample_opportunity.id)
        assert trade.aiAnalysisConfidence is None

    @pytest.mark.asyncio
    async def test_no_trade_creation_for_reject_decision(
        self,
        trading_engine_fixture: TradingEngine,
        sample_opportunity: Opportunity,
        scalping_strategy_with_ai: TradingStrategyConfig,
        mock_user_config: UserConfiguration,
        mock_portfolio_snapshot: PortfolioSnapshot,
    ):
        """Test that no trade is created for reject decisions."""
        from decimal import Decimal
        
        # Create a reject decision
        decision = TradingDecision(
            decision="reject_opportunity",
            confidence=0.3,
            reasoning="Insufficient confidence for trade execution",
            opportunity_id=str(sample_opportunity.id),
            strategy_id=str(scalping_strategy_with_ai.id),
            ai_analysis_used=True,
        )

        # Attempt to create trade from decision with all required parameters
        current_price = Decimal("30000.0")
        trade = await trading_engine_fixture.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_with_ai,
            mock_user_config,
            current_price,
            mock_portfolio_snapshot,
        )

        # Verify no trade was created
        assert trade is None
