"""
Integration tests for Story 5.4 - Complete flow from opportunity to trade execution.

Tests the full integration between TradingEngineService, StrategyService, and related components
for the active strategy-based opportunity processing workflow.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestrator
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService

from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ApplicabilityRules,
)
from src.ultibot_backend.core.domain_models.trade_models import Trade
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
    RealTradingSettings,
)


@pytest.fixture
def user_id():
    return str(uuid4())


@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)


@pytest.fixture
def strategy_service(mock_persistence_service):
    return StrategyService(mock_persistence_service)


@pytest.fixture
def config_service(mock_persistence_service):
    from src.ultibot_backend.services.config_service import ConfigService
    return ConfigService(mock_persistence_service)


@pytest.fixture
def ai_orchestrator():
    return AsyncMock(spec=AIOrchestrator)


@pytest.fixture
def trading_engine(strategy_service, config_service, ai_orchestrator):
    from src.ultibot_backend.services.trading_engine_service import TradingEngine
    return TradingEngine(
        strategy_service=strategy_service,
        configuration_service=config_service,
        ai_orchestrator=ai_orchestrator,
    )


@pytest.fixture
def btc_opportunity(user_id):
    """Sample BTC opportunity for testing."""
    from src.ultibot_backend.core.domain_models.opportunity_models import (
        Opportunity,
        OpportunityStatus,
        InitialSignal,
        OpportunitySourceType,
        AIAnalysis,
        SuggestedAction,
    )
    return Opportunity(
        id=str(uuid4()),
        user_id=user_id,
        symbol="BTCUSDT",
        detected_at=datetime.now(timezone.utc),
        source_type=OpportunitySourceType.MCP_SIGNAL,
        source_name="test_mcp_btc",
        initial_signal=InitialSignal(
            direction_sought="buy",
            entry_price_target=50000.0,
            stop_loss_target=49000.0,
            take_profit_target=[51000.0, 52000.0],
            timeframe="15m",
            confidence_source=0.85,
            reasoning_source_text="Strong bullish signal detected",
        ),
        status=OpportunityStatus.NEW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def eth_opportunity(user_id):
    """Sample ETH opportunity for testing."""
    from src.ultibot_backend.core.domain_models.opportunity_models import (
        Opportunity,
        OpportunityStatus,
        InitialSignal,
        OpportunitySourceType,
        AIAnalysis,
        SuggestedAction,
    )
    return Opportunity(
        id=str(uuid4()),
        user_id=user_id,
        symbol="ETHUSDT",
        detected_at=datetime.now(timezone.utc),
        source_type=OpportunitySourceType.INTERNAL_INDICATOR_ALGO,
        source_name="rsi_oversold_detector",
        initial_signal=InitialSignal(
            direction_sought="sell",
            entry_price_target=3000.0,
            stop_loss_target=3100.0,
            take_profit_target=[2900.0],
            timeframe="1h",
            confidence_source=0.75,
            reasoning_source_text="RSI oversold, potential reversal",
        ),
        status=OpportunityStatus.NEW,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def scalping_strategy_btc(user_id):
    """BTC-specific scalping strategy."""
    return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=user_id,
        config_name="BTC Scalping Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="High-frequency BTC scalping with tight SL/TP",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.015,  # 1.5%
            stop_loss_percentage=0.008,      # 0.8%
            max_holding_time_seconds=1800,   # 30 minutes
            leverage=1.0,
        ),
        applicability_rules=ApplicabilityRules(
            explicit_pairs=["BTCUSDT"],
            include_all_spot=False,
        ),
        ai_analysis_profile_id=None,  # No AI for this strategy
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def day_trading_strategy_multi(user_id):
    """Multi-pair day trading strategy with AI."""
    return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=user_id,
        config_name="AI Day Trading Multi-Pair",
        base_strategy_type=BaseStrategyType.DAY_TRADING,
        description="AI-enhanced day trading for major pairs",
        is_active_paper_mode=True,
        is_active_real_mode=True,
        parameters=DayTradingParameters(
            rsi_period=14,
            rsi_overbought=75,
            rsi_oversold=25,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            entry_timeframes=["1h", "4h"],
            exit_timeframes=["15m", "1h"],
        ),
        applicability_rules=ApplicabilityRules(
            explicit_pairs=["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            include_all_spot=False,
        ),
        ai_analysis_profile_id="ai_profile_1",  # Uses AI
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def ai_strategy_config():
    """AI strategy configuration for testing."""
    return AIStrategyConfiguration(
        id="ai_profile_1",
        name="Conservative Day Trading AI",
        gemini_prompt_template="Analyze this {symbol} opportunity for day trading. Market data: {market_data}. Strategy: {strategy_params}",
        tools_available_to_gemini=["price_history", "volume_analysis", "technical_indicators"],
        confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.65,
            real_trading=0.80,
        ),
        max_context_window_tokens=8000,
    )


@pytest.fixture
def user_configuration(user_id, ai_strategy_config):
    """Complete user configuration for testing."""
    return UserConfiguration(
        user_id=user_id,
        paper_trading_active=True,
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=1,
            daily_capital_risked_usd=200.0,
            last_daily_reset=datetime.now(timezone.utc),
        ),
        ai_strategy_configurations=[ai_strategy_config],
        ai_analysis_confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.60,
            real_trading=0.75,
        ),
    )


class TestCompleteOpportunityProcessingFlow:
    """Integration tests for complete opportunity processing workflow."""

    @pytest.mark.asyncio
    async def test_single_strategy_paper_trade_execution_flow(
        self,
        trading_engine,
        mock_persistence_service,
        btc_opportunity,
        scalping_strategy_btc,
        user_configuration,
        user_id,
    ):
        """Test complete flow: opportunity → single applicable strategy → paper trade execution."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            OpportunityStatus,
        )
        mode = "paper"
        
        # Mock database responses
        active_strategies_data = [
            self._strategy_to_db_format(scalping_strategy_btc)
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        
        # Mock get_strategy_config calls
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        # Mock trade creation (no actual DB persistence needed for this test)
        mock_persistence_service.upsert_trade = AsyncMock()
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status:
            # Execute the complete flow
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                btc_opportunity, user_id, mode
            )
            
            # Verify results
            assert len(decisions) == 1
            decision = decisions[0]
            
            # Verify decision details
            assert decision.decision == "execute_trade"
            assert decision.strategy_id == scalping_strategy_btc.id
            assert decision.opportunity_id == btc_opportunity.id
            assert decision.confidence > 0.5  # Autonomous scalping should have decent confidence
            assert "scalping" in decision.reasoning.lower()
            
            # Verify opportunity status was updated correctly
            mock_update_status.assert_called_with(
                btc_opportunity,
                OpportunityStatus.CONVERTED_TO_TRADE_PAPER,
                "trades_executed",
                "Executed 1 paper trades"
            )

    @pytest.mark.asyncio
    async def test_multiple_strategies_with_ai_integration_flow(
        self,
        trading_engine,
        mock_persistence_service,
        btc_opportunity,
        scalping_strategy_btc,
        day_trading_strategy_multi,
        user_configuration,
        ai_orchestrator,
        user_id,
    ):
        """Test flow with multiple strategies where one uses AI analysis."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            SuggestedAction,
        )
        mode = "paper"
        
        # Mock active strategies (both apply to BTCUSDT)
        active_strategies_data = [
            self._strategy_to_db_format(scalping_strategy_btc),
            self._strategy_to_db_format(day_trading_strategy_multi),
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        # Mock AI analysis for day trading strategy
        ai_analysis_result = AsyncMock()
        ai_analysis_result.calculated_confidence = 0.78
        ai_analysis_result.suggested_action = SuggestedAction.BUY
        ai_analysis_result.reasoning_ai = "AI confirms bullish momentum with strong volume"
        ai_analysis_result.recommended_trade_params = {
            "entry_price": 50100.0,
            "stop_loss": 49200.0,
            "take_profit": [51500.0, 52000.0],
            "position_size_percentage": 2.5,
        }
        ai_analysis_result.ai_warnings = []
        ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_analysis_result
        
        # Mock update methods
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status, \
             patch.object(trading_engine, '_update_opportunity_with_ai_analysis') as mock_update_ai:
            
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                btc_opportunity, user_id, mode
            )
            
            # Should have 2 decisions (one from each strategy)
            assert len(decisions) == 2
            
            # Find decisions by strategy type
            scalping_decision = next(d for d in decisions if "scalping" in d.reasoning.lower())
            ai_decision = next(d for d in decisions if d.ai_analysis_used)
            
            # Verify scalping decision (autonomous)
            assert scalping_decision.decision == "execute_trade"
            assert not scalping_decision.ai_analysis_used
            assert scalping_decision.strategy_id == scalping_strategy_btc.id
            
            # Verify AI-enhanced decision
            assert ai_decision.decision == "execute_trade"
            assert ai_decision.ai_analysis_used
            assert ai_decision.strategy_id == day_trading_strategy_multi.id
            assert ai_decision.confidence == 0.78
            assert "AI confirms" in ai_decision.reasoning
            
            # Verify AI was called
            ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_applicable_strategies_rejection_flow(
        self,
        trading_engine,
        mock_persistence_service,
        eth_opportunity,  # ETH opportunity
        scalping_strategy_btc,  # BTC-only strategy
        user_configuration,
        user_id,
    ):
        """Test flow where active strategies exist but none are applicable."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            OpportunityStatus,
        )
        mode = "paper"
        
        # Mock BTC-only strategy as active
        active_strategies_data = [
            self._strategy_to_db_format(scalping_strategy_btc)
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                eth_opportunity, user_id, mode  # ETH opportunity with BTC-only strategy
            )
            
            # Should have no decisions
            assert len(decisions) == 0
            
            # Verify opportunity was rejected due to no applicable strategies
            mock_update_status.assert_called_with(
                eth_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "no_applicable_strategies",
                "No active strategies are applicable to this opportunity"
            )

    @pytest.mark.asyncio
    async def test_confidence_threshold_rejection_flow(
        self,
        trading_engine,
        mock_persistence_service,
        btc_opportunity,
        day_trading_strategy_multi,
        user_configuration,
        ai_orchestrator,
        user_id,
    ):
        """Test flow where AI analysis confidence is below threshold."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            OpportunityStatus,
            SuggestedAction,
        )
        mode = "real"  # Real mode has higher confidence threshold
        
        # Mock active strategy
        active_strategies_data = [
            self._strategy_to_db_format(day_trading_strategy_multi)
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        # Mock low-confidence AI analysis
        ai_analysis_result = AsyncMock()
        ai_analysis_result.calculated_confidence = 0.65  # Below real mode threshold (0.80)
        ai_analysis_result.suggested_action = SuggestedAction.BUY
        ai_analysis_result.reasoning_ai = "Weak bullish signal, uncertain market conditions"
        ai_analysis_result.recommended_trade_params = None
        ai_analysis_result.ai_warnings = ["Low confidence due to market volatility"]
        ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_analysis_result
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                btc_opportunity, user_id, mode
            )
            
            # Should have one decision but no trades executed
            assert len(decisions) == 1
            decision = decisions[0]
            assert decision.confidence == 0.65
            
            # Verify opportunity was rejected due to low confidence
            mock_update_status.assert_called_with(
                btc_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "confidence_too_low",
                "All strategy decisions below confidence threshold"
            )

    @pytest.mark.asyncio
    async def test_real_mode_confirmation_required_flow(
        self,
        trading_engine,
        mock_persistence_service,
        btc_opportunity,
        scalping_strategy_btc,
        user_configuration,
        user_id,
    ):
        """Test flow where real mode requires user confirmation."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            OpportunityStatus,
        )
        mode = "real"
        
        # Modify strategy to be active in real mode
        scalping_strategy_btc.is_active_real_mode = True
        
        # Mock active strategy
        active_strategies_data = [
            self._strategy_to_db_format(scalping_strategy_btc)
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                btc_opportunity, user_id, mode
            )
            
            # Should have decisions but no immediate trade execution
            assert len(decisions) == 1
            decision = decisions[0]
            assert decision.decision == "execute_trade"
            
            # Verify opportunity is pending user confirmation
            mock_update_status.assert_called_with(
                btc_opportunity,
                OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
                "awaiting_user_confirmation",
                f"Real trade requires user confirmation for strategy {scalping_strategy_btc.config_name}"
            )

    @pytest.mark.asyncio
    async def test_strategy_evaluation_error_resilience_flow(
        self,
        trading_engine,
        mock_persistence_service,
        btc_opportunity,
        scalping_strategy_btc,
        day_trading_strategy_multi,
        user_configuration,
        ai_orchestrator,
        user_id,
    ):
        """Test that individual strategy errors don't break the entire flow."""
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            OpportunityStatus,
        )
        mode = "paper"
        
        # Mock both strategies as active
        active_strategies_data = [
            self._strategy_to_db_format(scalping_strategy_btc),
            self._strategy_to_db_format(day_trading_strategy_multi),
        ]
        mock_persistence_service.execute_query.return_value = active_strategies_data
        mock_persistence_service.get_user_configuration.return_value = user_configuration
        
        # Mock AI orchestrator to fail for the AI strategy
        ai_orchestrator.analyze_opportunity_with_strategy_context_async.side_effect = Exception("AI service unavailable")
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update_status:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                btc_opportunity, user_id, mode
            )
            
            # Should still have one successful decision from scalping strategy
            assert len(decisions) == 1
            decision = decisions[0]
            assert decision.strategy_id == scalping_strategy_btc.id
            assert not decision.ai_analysis_used
            
            # Verify successful execution despite one strategy failing
            mock_update_status.assert_called_with(
                btc_opportunity,
                OpportunityStatus.CONVERTED_TO_TRADE_PAPER,
                "trades_executed",
                "Executed 1 paper trades"
            )

    def _strategy_to_db_format(self, strategy: TradingStrategyConfig) -> dict:
        """Convert strategy to database format for mocking."""
        return {
            "id": strategy.id,
            "user_id": strategy.user_id,
            "config_name": strategy.config_name,
            "base_strategy_type": strategy.base_strategy_type.value,
            "description": strategy.description,
            "is_active_paper_mode": strategy.is_active_paper_mode,
            "is_active_real_mode": strategy.is_active_real_mode,
            "parameters": strategy.parameters.dict() if hasattr(strategy.parameters, 'dict') else strategy.parameters,
            "applicability_rules": strategy.applicability_rules.dict() if strategy.applicability_rules else None,
            "ai_analysis_profile_id": strategy.ai_analysis_profile_id,
            "risk_parameters_override": None,
            "version": strategy.version,
            "parent_config_id": strategy.parent_config_id,
            "performance_metrics": None,
            "market_condition_filters": None,
            "activation_schedule": None,
            "depends_on_strategies": None,
            "sharing_metadata": None,
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at,
        }


class TestTradeCreationWithStrategyAssociation:
    """Test that trades are correctly created with strategy association (AC5)."""

    @pytest.mark.asyncio
    async def test_trade_strategy_id_association(
        self,
        trading_engine,
        btc_opportunity,
        scalping_strategy_btc,
    ):
        """Test that created trades have correct strategy_id association."""
        from src.ultibot_backend.services.trading_engine_service import TradingDecision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.8,
            reasoning="Test scalping decision",
            opportunity_id=btc_opportunity.id,
            strategy_id=scalping_strategy_btc.id,
        )
        
        # Mock trade creation
        with patch('uuid.uuid4', return_value=uuid4()), \
             patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
            
            mock_datetime.now.return_value = datetime.now(timezone.utc)
            
            trade = await trading_engine.create_trade_from_decision(
                decision, btc_opportunity, scalping_strategy_btc
            )
            
            # Verify strategy association (AC5)
            assert trade.strategy_id == scalping_strategy_btc.id
            assert trade.opportunity_id == btc_opportunity.id
            assert trade.user_id == scalping_strategy_btc.user_id
            assert scalping_strategy_btc.config_name in trade.notes
            assert scalping_strategy_btc.id in trade.notes

    @pytest.mark.asyncio
    async def test_trade_side_determination(
        self,
        trading_engine,
        btc_opportunity,
        scalping_strategy_btc,
    ):
        """Test that trade side is correctly determined from opportunity signal."""
        from src.ultibot_backend.services.trading_engine_service import TradingDecision
        # Test buy signal
        btc_opportunity.initial_signal.direction_sought = "buy"
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.8,
            reasoning="Buy signal test",
            opportunity_id=btc_opportunity.id,
            strategy_id=scalping_strategy_btc.id,
        )
        
        trade = await trading_engine.create_trade_from_decision(
            decision, btc_opportunity, scalping_strategy_btc
        )
        
        assert trade.side == "buy"
        
        # Test sell signal
        btc_opportunity.initial_signal.direction_sought = "sell"
        trade = await trading_engine.create_trade_from_decision(
            decision, btc_opportunity, scalping_strategy_btc
        )
        
        assert trade.side == "sell"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
