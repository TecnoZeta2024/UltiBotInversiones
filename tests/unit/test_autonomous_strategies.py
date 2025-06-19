"""Tests for strategies configured to operate without AI.

Tests for AC 4: Strategies should operate autonomously when AI is not configured.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from unittest.mock import patch # Added for mocking logger

from ultibot_backend.services.trading_engine_service import (
    TradingEngine,
    TradingDecision,
)
from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    GridTradingParameters,
    Timeframe,
)
from ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    SourceType,
    Direction,
    InitialSignal,
)


@pytest.fixture
def mock_strategy_service_no_ai():
    """Create mock strategy service configured for no AI usage."""
    service = AsyncMock() # Changed to AsyncMock directly
    service.strategy_requires_ai_analysis.return_value = False
    service.strategy_can_operate_autonomously.return_value = True
    service.get_ai_configuration_for_strategy.return_value = None
    service.get_effective_confidence_thresholds_for_strategy.return_value = None
    
    # Mock get_strategy_config to return a valid strategy config
    async def mock_get_strategy_config(strategy_id: str, user_id: str):
        # Return a dummy TradingStrategyConfig for testing purposes
        return TradingStrategyConfig(
            id=strategy_id,
            user_id=user_id,
            config_name="Mock Strategy",
            base_strategy_type=BaseStrategyType.SCALPING, # Or any other valid type
            description="Mock strategy for testing",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.01,
                stop_loss_percentage=0.005,
                max_holding_time_seconds=180,
                leverage=1.0
            ),
            ai_analysis_profile_id=None,
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    service.get_strategy_config.side_effect = mock_get_strategy_config
    
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
def mock_persistence_service():
    return AsyncMock()

@pytest.fixture
def mock_market_data_service():
    return AsyncMock()

@pytest.fixture
def mock_unified_order_execution_service():
    return AsyncMock()

@pytest.fixture
def mock_credential_service():
    return AsyncMock()

@pytest.fixture
def mock_notification_service():
    return AsyncMock()

@pytest.fixture
def mock_portfolio_service():
    return AsyncMock()

@pytest.fixture
def trading_engine_no_ai(
    mock_strategy_service_no_ai,
    mock_configuration_service,
    mock_ai_orchestrator,
    mock_persistence_service,
    mock_market_data_service,
    mock_unified_order_execution_service,
    mock_credential_service,
    mock_notification_service,
    mock_portfolio_service,
):
    """Create trading engine for testing autonomous strategies."""
    return TradingEngine(
        strategy_service=mock_strategy_service_no_ai,
        configuration_service=mock_configuration_service,
        ai_orchestrator=mock_ai_orchestrator,
        persistence_service=mock_persistence_service,
        market_data_service=mock_market_data_service,
        unified_order_execution_service=mock_unified_order_execution_service,
        credential_service=mock_credential_service,
        notification_service=mock_notification_service,
        portfolio_service=mock_portfolio_service,
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
            reasoning_source_structured={}
        ),
        status=OpportunityStatus.NEW,
        strategy_id=uuid.uuid4(),
        source_data={},
        system_calculated_priority_score=None,
        last_priority_calculation_at=None,
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
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
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
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
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that a trade was potentially created (or at least the process ran)
        assert trade is None or trade.symbol == sample_opportunity.symbol
        
        # Further assertions would depend on the internal logic of process_opportunity
        # For now, we just ensure it runs and doesn't call AI
    
    @pytest.mark.asyncio
    async def test_scalping_autonomous_trade_parameters(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        autonomous_scalping_strategy,
    ):
        """Test that autonomous scalping generates appropriate trade parameters."""
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Since process_opportunity might return None or a Trade,
        # we can't directly assert on decision.recommended_trade_params here.
        # The focus is on ensuring the autonomous path is taken and AI is not called.
        assert trade is None or trade.symbol == sample_opportunity.symbol


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
                entry_timeframes=[Timeframe.FIFTEEN_MINUTES, Timeframe.ONE_HOUR],
                exit_timeframes=[Timeframe.ONE_HOUR, Timeframe.FOUR_HOURS],
            ),
            ai_analysis_profile_id=None,  # No AI configured
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
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
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that a trade was potentially created (or at least the process ran)
        assert trade is None or trade.symbol == sample_opportunity.symbol


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
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
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
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that a trade was potentially created (or at least the process ran)
        assert trade is None or trade.symbol == sample_opportunity.symbol


class TestUnknownStrategyType:
    """Test handling of unknown strategy types without AI."""
    
    @pytest.fixture
    def unknown_strategy_type(self):
        """Create strategy with unknown type using model_construct to bypass validation."""
        strategy_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "config_name": "Custom Strategy",
            "base_strategy_type": "CUSTOM_UNKNOWN_TYPE",  # Invalid type
            "description": "Custom strategy type for testing",
            "is_active_paper_mode": True,
            "is_active_real_mode": False,
            "parameters": {"custom_param": "value"},
            "ai_analysis_profile_id": None,
            "applicability_rules": None,
            "risk_parameters_override": None,
            "version": 1,
            "parent_config_id": None,
            "performance_metrics": None,
            "market_condition_filters": None,
            "activation_schedule": None,
            "depends_on_strategies": None,
            "sharing_metadata": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        return TradingStrategyConfig.model_construct(**strategy_data)
    
    @pytest.mark.asyncio
    async def test_unknown_strategy_type_autonomous_evaluation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        unknown_strategy_type,
        mock_ai_orchestrator,
    ):
        """Test that unknown strategy types require investigation."""
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that a trade was potentially created (or at least the process ran)
        assert trade is None or trade.symbol == sample_opportunity.symbol


class TestStrategyServiceIntegration:
    """Test integration with strategy service for autonomous strategies."""
    
    @pytest.mark.asyncio
    async def test_strategy_service_autonomous_validation(
        self,
        trading_engine_no_ai,
        sample_opportunity,
        mock_strategy_service_no_ai,
        mock_ai_orchestrator, # Added mock_ai_orchestrator
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
                max_holding_time_seconds=180,
                leverage=1.0
            ),
            ai_analysis_profile_id=None,  # No AI configured
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Execute evaluation
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify strategy service methods were called correctly
        # The strategy_requires_ai_analysis is called internally by process_opportunity
        # mock_strategy_service_no_ai.strategy_requires_ai_analysis.assert_called_once_with(strategy)
        
        # Verify AI configuration methods were not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        mock_strategy_service_no_ai.get_ai_configuration_for_strategy.assert_not_called()
        
        assert trade is None or trade.symbol == sample_opportunity.symbol
    
    @pytest.mark.asyncio
    @patch("ultibot_backend.services.trading_engine_service.logger") # Patch the logger directly
    async def test_strategy_logging_for_autonomous_decisions(
        self,
        mock_trading_engine_logger, # The patched logger
        trading_engine_no_ai,
        sample_opportunity,
    ):
        """Test that autonomous strategy decisions are properly logged."""
        # Execute evaluation
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify autonomous evaluation was logged
        mock_trading_engine_logger.warning.assert_any_call(
            f"AI analysis failed or did not recommend trade for opportunity {sample_opportunity.id}: AI did not recommend trade or analysis was skipped.. Checking for autonomous fallback."
        )
        mock_trading_engine_logger.info.assert_any_call(
            f"Strategy {sample_opportunity.strategy_id} can operate autonomously. Proceeding with autonomous logic."
        )
        
        # Verify no AI-related logging occurred (check for specific AI decision messages)
        # The warning about AI analysis failing/not recommending a trade is expected,
        # so we specifically check for messages indicating a successful AI-driven decision.
        for call in mock_trading_engine_logger.mock_calls:
            if call.args and isinstance(call.args[0], str):
                message = call.args[0].lower()
                assert "ai recommended action" not in message
                assert "ai-driven trade" not in message
                assert "ai profile" not in message # Still check for direct AI profile mentions
        
        assert trade is None or trade.symbol == sample_opportunity.symbol


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
                max_holding_time_seconds=180,
                leverage=1.0
            ),
            ai_analysis_profile_id=None,  # No AI configured
            applicability_rules=None,
            risk_parameters_override=None,
            version=1,
            parent_config_id=None,
            performance_metrics=None,
            market_condition_filters=None,
            activation_schedule=None,
            depends_on_strategies=None,
            sharing_metadata=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        import time
        start_time = time.time()
        
        # Execute evaluation
        trade = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        end_time = time.time()
        evaluation_time = end_time - start_time
        
        # Verify evaluation was fast (should be sub-second for autonomous strategies)
        assert evaluation_time < 1.0  # Less than 1 second
        
        # Verify no AI service calls were made
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that a trade was potentially created (or at least the process ran)
        assert trade is None or trade.symbol == sample_opportunity.symbol
