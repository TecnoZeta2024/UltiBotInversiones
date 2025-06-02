"""Tests for strategies configured to operate without AI.

Tests for AC 4: Strategies should operate autonomously when AI is not configured.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.ultibot_backend.services.trading_engine_service import (
    TradingEngine,
    TradingDecision,
)
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    GridTradingParameters,
)
from src.ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    SourceType,
    Direction,
    InitialSignal,
)


@pytest.fixture
def mock_strategy_service_no_ai():
    """Create mock strategy service configured for no AI usage."""
    service = Mock()
    service.strategy_requires_ai_analysis = AsyncMock(return_value=False)
    service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    service.get_ai_configuration_for_strategy = AsyncMock(return_value=None)
    service.get_effective_confidence_thresholds_for_strategy = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_configuration_service():
    """Create mock configuration service."""
    return Mock()


@pytest.fixture
def mock_ai_orchestrator():
    """Create mock AI orchestrator that should not be called."""
    orchestrator = Mock()
    orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock()
    return orchestrator


@pytest.fixture
def trading_engine_no_ai(mock_strategy_service_no_ai, mock_configuration_service, mock_ai_orchestrator):
    """Create trading engine for testing autonomous strategies."""
    return TradingEngine(
        strategy_service=mock_strategy_service_no_ai,
        configuration_service=mock_configuration_service,
        ai_orchestrator=mock_ai_orchestrator,
    )


@pytest.fixture
def sample_opportunity():
    """Create sample opportunity for testing."""
    return Opportunity(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        symbol="BTC/USDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.INTERNAL_INDICATOR_ALGO,
        source_name="Technical_Analysis_Bot",
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=45000.0,
            stop_loss_target=44000.0,
            take_profit_target=[46000.0, 47000.0],
            timeframe="1h",
            confidence_source=0.8,
            reasoning_source_text="Strong technical indicators suggest upward movement",
        ),
        status=OpportunityStatus.NEW,
    )


class TestAutonomousScalpingStrategy:
    """Test autonomous scalping strategy without AI."""
    
    @pytest.fixture
    def autonomous_scalping_strategy(self):
        """Create scalping strategy without AI configuration."""
        return TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Pure Autonomous Scalping",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Fast scalping strategy based on technical analysis only",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.008,  # 0.8% profit target
                stop_loss_percentage=0.004,     # 0.4% stop loss
                max_holding_time_seconds=180,   # 3 minutes max
                leverage=2.0,
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_scalping_evaluation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        autonomous_scalping_strategy,
        mock_ai_orchestrator,
    ):
        """Test that scalping strategy evaluates opportunities autonomously."""
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            autonomous_scalping_strategy,
            mode="paper",
        )
        
        # Verify autonomous decision
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.ai_analysis_profile_id is None
        assert decision.strategy_id == autonomous_scalping_strategy.id
        assert decision.opportunity_id == sample_opportunity.id
        
        # Verify decision is based on strategy parameters
        assert decision.decision in ["execute_trade", "reject_opportunity"]
        if decision.decision == "execute_trade":
            assert decision.confidence > 0
            assert "scalping" in decision.reasoning.lower()
            assert decision.recommended_trade_params is not None
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_scalping_autonomous_trade_parameters(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        autonomous_scalping_strategy,
    ):
        """Test that autonomous scalping generates appropriate trade parameters."""
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            autonomous_scalping_strategy,
            mode="paper",
        )
        
        if decision.decision == "execute_trade":
            params = decision.recommended_trade_params
            assert params is not None
            
            # Check that parameters align with strategy configuration
            entry_price = params.get("entry_price")
            stop_loss = params.get("stop_loss")
            take_profit = params.get("take_profit")
            
            assert entry_price is not None
            assert stop_loss is not None
            assert take_profit is not None
            
            # Verify risk/reward ratios match strategy parameters
            if entry_price and stop_loss:
                risk_percentage = abs(entry_price - stop_loss) / entry_price
                assert risk_percentage <= 0.005  # Should be around 0.4% based on strategy


class TestAutonomousDayTradingStrategy:
    """Test autonomous day trading strategy without AI."""
    
    @pytest.fixture
    def autonomous_day_trading_strategy(self):
        """Create day trading strategy without AI configuration."""
        return TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Technical Analysis Day Trading",
            base_strategy_type=BaseStrategyType.DAY_TRADING,
            description="Day trading based on RSI and MACD indicators",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=DayTradingParameters(
                rsi_period=14,
                rsi_overbought=75,
                rsi_oversold=25,
                macd_fast_period=12,
                macd_slow_period=26,
                macd_signal_period=9,
                entry_timeframes=["15m", "1h"],
                exit_timeframes=["1h", "4h"],
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_day_trading_evaluation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        autonomous_day_trading_strategy,
        mock_ai_orchestrator,
    ):
        """Test that day trading strategy evaluates opportunities autonomously."""
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            autonomous_day_trading_strategy,
            mode="paper",
        )
        
        # Verify autonomous decision
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.ai_analysis_profile_id is None
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify decision reasoning mentions day trading
        if decision.decision == "execute_trade":
            assert "day trading" in decision.reasoning.lower()


class TestAutonomousArbitrageStrategy:
    """Test autonomous arbitrage strategy without AI."""
    
    @pytest.fixture
    def autonomous_arbitrage_strategy(self):
        """Create arbitrage strategy without AI configuration."""
        return TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Cross-Exchange Arbitrage",
            base_strategy_type=BaseStrategyType.ARBITRAGE_SIMPLE,
            description="Simple arbitrage between exchanges",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ArbitrageSimpleParameters(
                price_difference_percentage_threshold=0.002,  # 0.2% minimum spread
                min_trade_volume_quote=100.0,
                exchange_a_credential_label="binance_main",
                exchange_b_credential_label="coinbase_pro",
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
    
    @pytest.mark.asyncio
    async def test_autonomous_arbitrage_evaluation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        autonomous_arbitrage_strategy,
        mock_ai_orchestrator,
    ):
        """Test that arbitrage strategy evaluates opportunities autonomously."""
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            autonomous_arbitrage_strategy,
            mode="paper",
        )
        
        # Verify autonomous decision
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.ai_analysis_profile_id is None
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify decision reasoning mentions arbitrage
        if decision.decision == "execute_trade":
            assert "arbitrage" in decision.reasoning.lower()


class TestUnknownStrategyType:
    """Test handling of unknown strategy types without AI."""
    
    @pytest.fixture
    def unknown_strategy_type(self):
        """Create strategy with unknown type."""
        return TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Custom Strategy",
            base_strategy_type="CUSTOM_UNKNOWN_TYPE",  # Unknown type
            description="Custom strategy type for testing",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters={"custom_param": "value"},
            ai_analysis_profile_id=None,  # No AI configured
        )
    
    @pytest.mark.asyncio
    async def test_unknown_strategy_type_autonomous_evaluation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        unknown_strategy_type,
        mock_ai_orchestrator,
    ):
        """Test that unknown strategy types require investigation."""
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            unknown_strategy_type,
            mode="paper",
        )
        
        # Verify autonomous decision
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.decision == "requires_investigation"
        assert "manual evaluation" in decision.reasoning.lower()
        assert len(decision.warnings) > 0
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()


class TestStrategyServiceIntegration:
    """Test integration with strategy service for autonomous strategies."""
    
    @pytest.mark.asyncio
    async def test_strategy_service_autonomous_validation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        mock_strategy_service_no_ai,
    ):
        """Test that strategy service correctly identifies autonomous strategies."""
        # Create strategy without AI
        strategy = TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Test Autonomous Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Test strategy",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.01,
                stop_loss_percentage=0.005,
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
        
        # Execute evaluation
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            strategy,
            mode="paper",
        )
        
        # Verify strategy service methods were called correctly
        mock_strategy_service_no_ai.strategy_requires_ai_analysis.assert_called_once_with(strategy)
        
        # Verify AI configuration methods were not called
        mock_strategy_service_no_ai.get_ai_configuration_for_strategy.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_strategy_logging_for_autonomous_decisions(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        caplog,
    ):
        """Test that autonomous strategy decisions are properly logged."""
        strategy = TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Logged Autonomous Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Strategy for testing logging",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.01,
                stop_loss_percentage=0.005,
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
        
        # Execute evaluation
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            strategy,
            mode="paper",
        )
        
        # Verify autonomous evaluation was logged
        assert "autonomous evaluation" in caplog.text.lower()
        assert decision.strategy_id in caplog.text
        assert decision.opportunity_id in caplog.text
        
        # Verify no AI-related logging occurred
        assert "ai analysis" not in caplog.text.lower()
        assert "ai profile" not in caplog.text.lower()


class TestPerformanceConsiderations:
    """Test performance aspects of autonomous strategies."""
    
    @pytest.mark.asyncio
    async def test_autonomous_evaluation_performance(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        mock_ai_orchestrator,
    ):
        """Test that autonomous evaluation is fast and doesn't call AI services."""
        strategy = TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Performance Test Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Strategy for performance testing",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.01,
                stop_loss_percentage=0.005,
            ),
            ai_analysis_profile_id=None,  # No AI configured
        )
        
        import time
        start_time = time.time()
        
        # Execute evaluation
        decision = await trading_engine_no_ai.evaluate_opportunity_with_strategy(
            sample_opportunity,
            strategy,
            mode="paper",
        )
        
        end_time = time.time()
        evaluation_time = end_time - start_time
        
        # Verify evaluation was fast (should be sub-second for autonomous strategies)
        assert evaluation_time < 1.0  # Less than 1 second
        
        # Verify no AI service calls were made
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify decision was made
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
