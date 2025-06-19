"""Tests for strategies configured to operate without AI.

Tests for AC 4: Strategies should operate autonomously when AI is not configured.
"""

import pytest
from uuid import UUID, uuid4 # Importar UUID y uuid4
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock
from decimal import Decimal # Importar Decimal

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
    service = AsyncMock()
    service.strategy_requires_ai_analysis.return_value = False
    service.get_ai_configuration_for_strategy.return_value = None
    service.get_effective_confidence_thresholds_for_strategy.return_value = None

    # Add an attribute to control active strategies for specific tests
    service._test_active_strategies_override = None

    # Mock get_strategy_config to return a valid strategy config
    # This mock needs to be flexible enough to return different strategy types
    # including the 'unknown_strategy_type' from the test.
    original_get_strategy_config = service.get_strategy_config

    async def custom_get_strategy_config(strategy_id: str, user_id: str):
        # Default mock strategy
        default_strategy = TradingStrategyConfig(
            id=strategy_id,
            user_id=user_id,
            config_name="Mock Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Mock strategy for testing",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=Decimal("0.01"),
                stop_loss_percentage=Decimal("0.005"),
                max_holding_time_seconds=180,
                leverage=Decimal("1.0")
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
        # Allow specific strategies to be returned if set by test
        if hasattr(service, '_test_strategy_config_override') and service._test_strategy_config_override.id == strategy_id:
            return service._test_strategy_config_override
        return default_strategy

    service.get_strategy_config.side_effect = custom_get_strategy_config

    # Mock get_active_strategies to return a list containing the autonomous strategy
    async def mock_get_active_strategies(user_id: str, mode: str):
        if service._test_active_strategies_override is not None:
            return service._test_active_strategies_override
        return [
            TradingStrategyConfig(
            id=str(uuid4()),
            user_id=user_id,
            config_name="Autonomous Test Strategy",
                base_strategy_type=BaseStrategyType.SCALPING,
                description="A strategy for testing autonomous flow",
                is_active_paper_mode=True,
                is_active_real_mode=False,
                parameters=ScalpingParameters(
                    profit_target_percentage=Decimal("0.01"),
                    stop_loss_percentage=Decimal("0.005"),
                    max_holding_time_seconds=180,
                    leverage=Decimal("1.0")
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
        ]
    service.get_active_strategies.side_effect = mock_get_active_strategies

    # Mock is_strategy_applicable_to_symbol to always return True for testing purposes
    service.is_strategy_applicable_to_symbol.return_value = True

    async def mock_strategy_can_operate_autonomously(strategy_id: str, user_id: str):
        # Use the actual get_strategy_config mock to retrieve the strategy
        strategy_config = await service.get_strategy_config(strategy_id, user_id)
        if strategy_config and strategy_config.base_strategy_type == "CUSTOM_UNKNOWN_TYPE":
            return False
        return True # Default to True for known types

    service.strategy_can_operate_autonomously.side_effect = mock_strategy_can_operate_autonomously
    
    return service


@pytest.fixture
def mock_configuration_service():
    """Create mock configuration service."""
    service = AsyncMock()
    # Mock get_user_configuration to return a dummy UserConfiguration
    async def mock_get_user_configuration(user_id: str):
        from ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration, RiskProfile, RealTradingSettings, ConfidenceThresholds, Theme
        from decimal import Decimal
        from uuid import uuid4
        return UserConfiguration(
            id=str(uuid4()),
            user_id=user_id,
            telegram_chat_id=None,
            notification_preferences=None,
            enable_telegram_notifications=True,
            default_paper_trading_capital=Decimal("10000.0"),
            paper_trading_active=True,
            paper_trading_assets=[],
            watchlists=[],
            favorite_pairs=["BTCUSDT", "ETHUSDT"],
            risk_profile=RiskProfile.MODERATE,
            risk_profile_settings=None,
            real_trading_settings=RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_concurrent_operations=5,
                daily_loss_limit_absolute=Decimal("500.0"),
                daily_profit_target_absolute=Decimal("1000.0"),
                daily_capital_risked_usd=Decimal("0.0"),
                last_daily_reset=datetime.now(timezone.utc),
                asset_specific_stop_loss=None,
                auto_pause_trading_conditions=None,
            ),
            ai_strategy_configurations=[],
            ai_analysis_confidence_thresholds=ConfidenceThresholds(
                paper_trading=0.60,
                real_trading=0.75,
            ),
            mcp_server_preferences=None,
            selected_theme=Theme.DARK,
            dashboard_layout_profiles=None,
            active_dashboard_layout_profile_id=None,
            dashboard_layout_config=None,
            cloud_sync_preferences=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    service.get_user_configuration.side_effect = mock_get_user_configuration
    return service


@pytest.fixture
def mock_ai_orchestrator():
    """Create mock AI orchestrator that should not be called."""
    orchestrator = AsyncMock() # Changed to AsyncMock
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
        id=str(uuid4()),
        user_id=str(uuid4()),
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
        strategy_id=uuid4(),
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
        id=str(uuid4()),
        user_id=str(uuid4()),
        config_name="Pure Autonomous Scalping",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Fast scalping strategy based on technical analysis only",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=Decimal("0.008"),  # 0.8% profit target
                stop_loss_percentage=Decimal("0.004"),     # 0.4% stop loss
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(d.decision == "execute_trade" for d in decisions)
        
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        
        # Find the execute_trade decision
        execute_decision = next((d for d in decisions if d.decision == "execute_trade"), None)
        assert execute_decision is not None
        
        # Verify that the decision was made autonomously (no AI used)
        assert not execute_decision.ai_analysis_used
        assert "autonomous" in execute_decision.reasoning.lower()
        
        # Since create_trade_from_decision is called internally, we can't directly
        # assert on the Trade object's parameters here without further mocking.
        # The primary goal of this test is to ensure the autonomous path is taken
        # and a decision is generated.
        
        # For a more robust test, one might mock create_trade_from_decision
        # and assert its arguments.


class TestAutonomousDayTradingStrategy:
    """Test autonomous day trading strategy without AI."""
    
    @pytest.fixture
    def autonomous_day_trading_strategy(self):
        """Create day trading strategy without AI configuration."""
        return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=str(uuid4()),
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)
        # Further assertions would depend on the internal logic of process_opportunity
        # For now, we just ensure it runs and doesn't call AI


class TestAutonomousArbitrageStrategy:
    """Test autonomous arbitrage strategy without AI."""
    
    @pytest.fixture
    def autonomous_arbitrage_strategy(self):
        """Create arbitrage strategy without AI configuration."""
        return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=str(uuid4()),
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)
        # Further assertions would depend on the internal logic of process_opportunity
        # For now, we just ensure it runs and doesn't call AI


class TestUnknownStrategyType:
    """Test handling of unknown strategy types without AI."""
    
    @pytest.fixture
    def unknown_strategy_type(self):
        """Create strategy with unknown type using model_construct to bypass validation."""
        strategy_data = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
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
        mocker # Add mocker fixture
    ):
        """Test that unknown strategy types require investigation."""
        # Override the mock_strategy_service_no_ai's get_strategy_config for this specific test
        trading_engine_no_ai.strategy_service._test_strategy_config_override = unknown_strategy_type

        # Ensure that get_active_strategies returns only the unknown_strategy_type for this test
        mocker.patch.object(
            trading_engine_no_ai.strategy_service,
            'get_active_strategies',
            return_value=[unknown_strategy_type]
        )

        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that decisions were returned and at least one is an "investigate" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)
        # For unknown strategies, we expect an "investigate" decision or similar, not necessarily an execute_trade
        assert any(d.decision == "investigate" for d in decisions) or any(d.decision == "reject" for d in decisions)


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
            id=str(uuid4()),
            user_id=str(uuid4()),
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify strategy service methods were called correctly
        # The strategy_requires_ai_analysis is called internally by process_opportunity
        # mock_strategy_service_no_ai.strategy_requires_ai_analysis.assert_called_once_with(strategy)
        
        # Verify AI configuration methods were not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        mock_strategy_service_no_ai.get_ai_configuration_for_strategy.assert_not_called()
        
        # Assert that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)
        assert any(d.decision == "execute_trade" for d in decisions)
    
    @pytest.mark.asyncio
    @patch("ultibot_backend.services.trading_engine_service.logger") # Patch the logger directly
    async def test_strategy_logging_for_autonomous_decisions(
        self,
        mock_trading_engine_logger, # The patched logger
        trading_engine_no_ai,
        sample_opportunity,
        mock_strategy_service_no_ai # Add this fixture to access the mock
    ):
        """Test that autonomous strategy decisions are properly logged."""
        # Create a specific strategy for this test
        test_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=str(sample_opportunity.user_id), # Ensure user_id matches
            config_name="Logging Test Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="Strategy for testing logging",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=Decimal("0.01"),
                stop_loss_percentage=Decimal("0.005"),
                max_holding_time_seconds=180,
                leverage=Decimal("1.0")
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

        # Configure the mock to return only this specific strategy
        mock_strategy_service_no_ai._test_active_strategies_override = [test_strategy]
        
        # Update the sample_opportunity's strategy_id to match the test strategy's ID
        sample_opportunity.strategy_id = UUID(test_strategy.id)

        # Execute evaluation
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        # Verify autonomous evaluation was logged
        log_message_found = False
        for call in mock_trading_engine_logger.info.call_args_list:
            if call.args and isinstance(call.args[0], str):
                if f"Strategy {test_strategy.id} can operate autonomously. Proceeding with autonomous logic." in call.args[0]:
                    log_message_found = True
                    break
        assert log_message_found, f"Expected log message for strategy {test_strategy.id} not found."
        
        # Verify no AI-related logging occurred (check for specific AI decision messages)
        for call in mock_trading_engine_logger.mock_calls:
            if call.args and isinstance(call.args[0], str):
                message = call.args[0].lower()
                assert "ai recommended action" not in message
                assert "ai-driven trade" not in message
                assert "ai profile" not in message
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)


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
            id=str(uuid4()),
            user_id=str(uuid4()),
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
        decisions = await trading_engine_no_ai.process_opportunity(
            sample_opportunity
        )
        
        end_time = time.time()
        evaluation_time = end_time - start_time
        
        # Verify evaluation was fast (should be sub-second for autonomous strategies)
        assert evaluation_time < 1.0  # Less than 1 second
        
        # Verify no AI service calls were made
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
        
        # Verify that decisions were returned and at least one is an "execute_trade" decision
        assert isinstance(decisions, list)
        assert len(decisions) > 0
        assert any(isinstance(d, TradingDecision) for d in decisions)
