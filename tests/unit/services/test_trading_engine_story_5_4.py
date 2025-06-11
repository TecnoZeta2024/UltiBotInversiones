"""
Unit tests for Story 5.4 - TradingEngineService active strategy processing functionality.

Tests the new methods added for processing opportunities with active strategies:
- process_opportunity_with_active_strategies()
- _filter_applicable_strategies()
- _is_strategy_applicable_to_opportunity()
- _consolidate_and_execute_decisions()
- _execute_decision_by_mode()
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.ultibot_backend.services.trading_engine_service import TradingEngine, TradingDecision
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestrator
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    ApplicabilityRules,
)
from src.ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    InitialSignal,
    SourceType,
    Direction,
)
from src.ultibot_backend.core.domain_models.trade_models import (
    Trade,
    TradeOrderDetails,
    TradeMode,
    TradeSide,
    PositionStatus,
    OrderType, # Added for TradeOrderDetails
    OrderStatus, # Added for TradeOrderDetails
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    RealTradingSettings,
    ConfidenceThresholds,
)


@pytest.fixture
def mock_strategy_service():
    return AsyncMock(spec=StrategyService)


@pytest.fixture
def mock_config_service():
    return AsyncMock(spec=ConfigService)


@pytest.fixture
def mock_ai_orchestrator():
    return AsyncMock(spec=AIOrchestrator)


@pytest.fixture
def trading_engine(mock_strategy_service, mock_config_service, mock_ai_orchestrator):
    return TradingEngine(
        strategy_service=mock_strategy_service,
        configuration_service=mock_config_service,
        ai_orchestrator=mock_ai_orchestrator,
    )


@pytest.fixture
def sample_opportunity():
    return Opportunity(
        id=str(uuid4()),
        user_id=str(uuid4()),
        symbol="BTCUSDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.MCP_SIGNAL,
        source_name="test_mcp",
        source_data=None,
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=50000.0,
            stop_loss_target=49000.0,
            take_profit_target=[51000.0],
            timeframe="5m",
            reasoning_source_structured=None,
            reasoning_source_text="Signal from test MCP",
            confidence_source=0.85,
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
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_strategy():
    return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=str(uuid4()),
        config_name="Test Scalping Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Test strategy for unit tests",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.02,
            stop_loss_percentage=0.01,
            max_holding_time_seconds=3600,
            leverage=1.0, # Added
        ),
        applicability_rules=ApplicabilityRules(
            explicit_pairs=["BTCUSDT", "ETHUSDT"],
            include_all_spot=False,
            dynamic_filter=None, # Added
        ),
        ai_analysis_profile_id=None, # Added
        risk_parameters_override=None, # Added
        version=1,
        parent_config_id=None, # Added
        performance_metrics=None, # Added
        market_condition_filters=None, # Added
        activation_schedule=None, # Added
        depends_on_strategies=None, # Added
        sharing_metadata=None, # Added
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestProcessOpportunityWithActiveStrategies:
    """Test the main orchestration method for Story 5.4."""

    @pytest.mark.asyncio
    async def test_no_active_strategies_rejects_opportunity(
        self, trading_engine, mock_strategy_service, sample_opportunity
    ):
        """Test that opportunity is rejected when no active strategies exist."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Mock: No active strategies
        mock_strategy_service.get_active_strategies.return_value = []
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                sample_opportunity, user_id, mode
            )
            
            assert decisions == []
            mock_strategy_service.get_active_strategies.assert_called_once_with(user_id, mode)
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "no_active_strategies",
                f"No active strategies configured for {mode} mode"
            )

    @pytest.mark.asyncio
    async def test_no_applicable_strategies_rejects_opportunity(
        self, trading_engine, mock_strategy_service, sample_opportunity, sample_strategy
    ):
        """Test that opportunity is rejected when no strategies are applicable."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Strategy exists but not applicable to BTCUSDT
        sample_strategy.applicability_rules.explicit_pairs = ["ETHUSDT"]  # Only ETH
        mock_strategy_service.get_active_strategies.return_value = [sample_strategy]
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                sample_opportunity, user_id, mode
            )
            
            assert decisions == []
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "no_applicable_strategies",
                "No active strategies are applicable to this opportunity"
            )

    @pytest.mark.asyncio
    async def test_successful_processing_with_applicable_strategy(
        self, trading_engine, mock_strategy_service, sample_opportunity, sample_strategy
    ):
        """Test successful processing when strategy is applicable and generates decision."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Mock: Strategy is active and applicable
        mock_strategy_service.get_active_strategies.return_value = [sample_strategy]
        
        # Mock: Strategy evaluation returns execute decision
        mock_decision = TradingDecision(
            decision="execute_trade",
            confidence=0.8,
            reasoning="Test strategy approves",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(sample_strategy.id), # Ensure it's a string
        )
        
        with patch.object(trading_engine, 'evaluate_opportunity_with_strategy', return_value=mock_decision) as mock_eval, \
             patch.object(trading_engine, 'log_trading_decision') as mock_log, \
             patch.object(trading_engine, '_consolidate_and_execute_decisions', return_value=[]) as mock_consolidate:
            
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                sample_opportunity, user_id, mode
            )
            
            assert len(decisions) == 1
            assert decisions[0] == mock_decision
            mock_eval.assert_called_once_with(sample_opportunity, sample_strategy, mode)
            mock_log.assert_called_once_with(mock_decision)
            mock_consolidate.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_strategy_evaluation_error_gracefully(
        self, trading_engine, mock_strategy_service, sample_opportunity, sample_strategy
    ):
        """Test that individual strategy errors don't stop processing of other strategies."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Two strategies: one will fail, one will succeed
        strategy2 = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=user_id,
            config_name="Working Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            description="This one works",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.015,
                stop_loss_percentage=0.008,
                max_holding_time_seconds=1800, # Added example
                leverage=1.0, # Added
            ),
            applicability_rules=ApplicabilityRules(
                explicit_pairs=["BTCUSDT"],
                include_all_spot=False,
                dynamic_filter=None, # Added
            ),
            ai_analysis_profile_id=None, # Added
            risk_parameters_override=None, # Added
            version=1,
            parent_config_id=None, # Added
            performance_metrics=None, # Added
            market_condition_filters=None, # Added
            activation_schedule=None, # Added
            depends_on_strategies=None, # Added
            sharing_metadata=None, # Added
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        mock_strategy_service.get_active_strategies.return_value = [sample_strategy, strategy2]
        
        # Mock: First strategy fails, second succeeds
        successful_decision = TradingDecision(
            decision="execute_trade",
            confidence=0.75,
            reasoning="Second strategy works",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(strategy2.id), # Ensure it's a string
        )
        
        def mock_evaluate_side_effect(opp, strat, mode):
            if strat.id == sample_strategy.id:
                raise Exception("Strategy evaluation failed")
            return successful_decision
        
        with patch.object(trading_engine, 'evaluate_opportunity_with_strategy', side_effect=mock_evaluate_side_effect) as mock_eval, \
             patch.object(trading_engine, 'log_trading_decision') as mock_log, \
             patch.object(trading_engine, '_consolidate_and_execute_decisions', return_value=[]) as mock_consolidate:
            
            decisions = await trading_engine.process_opportunity_with_active_strategies(
                sample_opportunity, user_id, mode
            )
            
            # Should have one successful decision despite one failure
            assert len(decisions) == 1
            assert decisions[0] == successful_decision
            assert mock_eval.call_count == 2  # Both strategies attempted
            mock_log.assert_called_once_with(successful_decision)


class TestFilterApplicableStrategies:
    """Test strategy filtering based on applicability rules."""

    @pytest.mark.asyncio
    async def test_filters_explicit_pairs_correctly(self, trading_engine, sample_opportunity):
        """Test filtering based on explicit_pairs in applicability rules."""
        # Strategy 1: Applicable to BTCUSDT
        strategy1 = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=str(uuid4()),
            config_name="BTC Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.02,
                stop_loss_percentage=0.01,
                max_holding_time_seconds=3600, # Added example
                leverage=1.0, # Added
            ),
            applicability_rules=ApplicabilityRules(
                explicit_pairs=["BTCUSDT", "ETHUSDT"],
                include_all_spot=False,
                dynamic_filter=None, # Added
            ),
            description="BTC Strategy for testing", # Added example
            ai_analysis_profile_id=None, # Added
            risk_parameters_override=None, # Added
            version=1,
            parent_config_id=None, # Added
            performance_metrics=None, # Added
            market_condition_filters=None, # Added
            activation_schedule=None, # Added
            depends_on_strategies=None, # Added
            sharing_metadata=None, # Added
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        # Strategy 2: Not applicable to BTCUSDT
        strategy2 = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=str(uuid4()),
            config_name="ETH Only Strategy",
            base_strategy_type=BaseStrategyType.DAY_TRADING, # Changed for variety
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters={ # Using DayTradingParameters as an example
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "macd_fast_period": 12,
                "macd_slow_period": 26,
                "macd_signal_period": 9,
                "entry_timeframes": ["5m"],
            },
            applicability_rules=ApplicabilityRules(
                explicit_pairs=["ETHUSDT"],
                include_all_spot=False,
                dynamic_filter=None, # Added
            ),
            description="ETH Only Strategy for testing", # Added example
            ai_analysis_profile_id=None, # Added
            risk_parameters_override=None, # Added
            version=1,
            parent_config_id=None, # Added
            performance_metrics=None, # Added
            market_condition_filters=None, # Added
            activation_schedule=None, # Added
            depends_on_strategies=None, # Added
            sharing_metadata=None, # Added
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        strategies = [strategy1, strategy2]
        sample_opportunity.symbol = "BTCUSDT"
        
        applicable = await trading_engine._filter_applicable_strategies(sample_opportunity, strategies)
        
        assert len(applicable) == 1
        assert applicable[0].id == strategy1.id

    @pytest.mark.asyncio
    async def test_include_all_spot_applies_to_all(self, trading_engine, sample_opportunity):
        """Test that include_all_spot=True makes strategy applicable to any symbol."""
        strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=str(uuid4()),
            config_name="All Spot Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.02,
                stop_loss_percentage=0.01,
                max_holding_time_seconds=3600, # Added example
                leverage=1.0, # Added
            ),
            applicability_rules=ApplicabilityRules(
                explicit_pairs=None,
                include_all_spot=True,
                dynamic_filter=None, # Added
            ),
            description="All Spot Strategy for testing", # Added example
            ai_analysis_profile_id=None, # Added
            risk_parameters_override=None, # Added
            version=1,
            parent_config_id=None, # Added
            performance_metrics=None, # Added
            market_condition_filters=None, # Added
            activation_schedule=None, # Added
            depends_on_strategies=None, # Added
            sharing_metadata=None, # Added
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        sample_opportunity.symbol = "ADAUSDT"  # Different symbol
        
        applicable = await trading_engine._filter_applicable_strategies(sample_opportunity, [strategy])
        
        assert len(applicable) == 1
        assert applicable[0].id == strategy.id

    @pytest.mark.asyncio
    async def test_no_applicability_rules_applies_to_all(self, trading_engine, sample_opportunity):
        """Test that strategies without applicability rules apply to all opportunities."""
        strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=str(uuid4()),
            config_name="Universal Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=ScalpingParameters(
                profit_target_percentage=0.02,
                stop_loss_percentage=0.01,
                max_holding_time_seconds=3600, # Added example
                leverage=1.0, # Added
            ),
            applicability_rules=None,  # No rules
            description="Universal Strategy for testing", # Added example
            ai_analysis_profile_id=None, # Added
            risk_parameters_override=None, # Added
            version=1,
            parent_config_id=None, # Added
            performance_metrics=None, # Added
            market_condition_filters=None, # Added
            activation_schedule=None, # Added
            depends_on_strategies=None, # Added
            sharing_metadata=None, # Added
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        applicable = await trading_engine._filter_applicable_strategies(sample_opportunity, [strategy])
        
        assert len(applicable) == 1
        assert applicable[0].id == strategy.id


class TestConsolidateAndExecuteDecisions:
    """Test decision consolidation and execution logic."""

    @pytest.mark.asyncio
    async def test_no_execution_decisions_rejects_opportunity(
        self, trading_engine, sample_opportunity
    ):
        """Test that opportunity is rejected when no strategies recommend execution."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Decisions that don't recommend execution
        decisions = [
            TradingDecision(
                decision="reject_opportunity",
                confidence=0.3,
                reasoning="Low confidence",
                opportunity_id=sample_opportunity.id,
                strategy_id=str(uuid4()),
            ),
            TradingDecision(
                decision="requires_investigation",
                confidence=0.5,
                reasoning="Needs more analysis",
                opportunity_id=sample_opportunity.id,
                strategy_id=str(uuid4()),
            ),
        ]
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            trades = await trading_engine._consolidate_and_execute_decisions(
                decisions, sample_opportunity, mode, user_id
            )
            
            assert trades == []
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "no_execution_signals",
                "No active strategies generated execution signals"
            )

    @pytest.mark.asyncio
    async def test_low_confidence_execution_decision_rejected(
        self, trading_engine, mock_strategy_service, sample_opportunity, sample_strategy
    ):
        """Test that execution decisions below confidence threshold are rejected."""
        user_id = str(uuid4())
        mode = "paper"
        
        # Decision with low confidence
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.4,  # Below typical threshold
            reasoning="Low confidence execution",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(sample_strategy.id), # Ensure it's a string
        )
        
        # Mock strategy service calls
        mock_strategy_service.get_strategy_config.return_value = sample_strategy
        mock_strategy_service.get_effective_confidence_thresholds_for_strategy.return_value = ConfidenceThresholds(
            paper_trading=0.6,  # Higher than decision confidence
            real_trading=0.8,
        )
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            trades = await trading_engine._consolidate_and_execute_decisions(
                [decision], sample_opportunity, mode, user_id
            )
            
            assert trades == []
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.REJECTED_BY_AI,
                "confidence_too_low",
                "All strategy decisions below confidence threshold"
            )

    @pytest.mark.asyncio
    async def test_successful_paper_trade_execution(
        self, trading_engine, mock_strategy_service, sample_opportunity, sample_strategy
    ):
        """Test successful execution of paper trade."""
        user_id = str(uuid4())
        mode = "paper"
        
        # High confidence decision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.8,
            reasoning="High confidence execution",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(sample_strategy.id), # Ensure it's a string
        )
        
        # Mock strategy service calls
        mock_strategy_service.get_strategy_config.return_value = sample_strategy
        mock_strategy_service.get_effective_confidence_thresholds_for_strategy.return_value = ConfidenceThresholds(
            paper_trading=0.6,  # Lower than decision confidence
            real_trading=0.8,
        )
        
        # Mock trade creation
        assert sample_strategy.id is not None
        mock_trade = Trade(
            id=str(uuid4()),
            user_id=user_id,
            mode=TradeMode.PAPER,
            symbol="BTCUSDT",
            side=TradeSide.BUY,
            strategy_id=str(sample_strategy.id),
            opportunity_id=sample_opportunity.id,
            ai_analysis_confidence=0.8, # Added example
            strategy_execution_instance_id=None, # Added
            position_status=PositionStatus.PENDING_ENTRY_CONDITIONS,
            entry_order=TradeOrderDetails( 
                order_id_internal=str(uuid4()),
                order_id_exchange=None,
                client_order_id_exchange=None,
                type=OrderType.MARKET,
                status=OrderStatus.NEW,
                exchange_status_raw=None,
                rejection_reason_code=None,
                rejection_reason_message=None,
                requested_price=None,
                stop_price=None,
                executed_price=None,
                slippage_amount=None,
                slippage_percentage=None,
                requested_quantity=1.0,
                executed_quantity=None,
                cumulative_quote_qty=None,
                commissions=None,
                timestamp=datetime.now(timezone.utc),
                submitted_at=None,
                last_update_timestamp=None,
                fill_timestamp=None,
                trailing_stop_activation_price=None,
                trailing_stop_callback_rate=None,
                current_stop_price_tsl=None,
                oco_group_id_exchange=None
            ),
            exit_orders=None, 
            initial_risk_quote_amount=None, # Added
            initial_reward_to_risk_ratio=None, # Added
            risk_reward_adjustments=None, # Added
            current_risk_quote_amount=None, # Added
            current_reward_to_risk_ratio=None, # Added
            pnl=None, # Added
            pnl_percentage=None, # Added
            closing_reason=None, # Added
            market_context_snapshots=None, # Added
            external_event_or_analysis_link=None, # Added
            backtest_details=None, # Added
            ai_influence_details=None, # Added
            notes=None, # Added
            created_at=datetime.now(timezone.utc),
            opened_at=None, # Added
            closed_at=None, # Added
            updated_at=datetime.now(timezone.utc) # Added
        )
        
        with patch.object(trading_engine, 'create_trade_from_decision', return_value=mock_trade) as mock_create, \
             patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            
            trades = await trading_engine._consolidate_and_execute_decisions(
                [decision], sample_opportunity, mode, user_id
            )
            
            assert len(trades) == 1
            assert trades[0] == mock_trade
            mock_create.assert_called_once_with(decision, sample_opportunity, sample_strategy)
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.CONVERTED_TO_TRADE_PAPER,
                "trades_executed",
                "Executed 1 paper trades"
            )


class TestExecuteDecisionByMode:
    """Test mode-specific trade execution logic."""

    @pytest.mark.asyncio
    async def test_paper_mode_creates_trade_directly(
        self, trading_engine, sample_opportunity, sample_strategy
    ):
        """Test that paper mode creates trades directly without confirmation."""
        user_id = str(uuid4())
        mode = "paper"
        
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.8,
            reasoning="Paper trade execution",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(sample_strategy.id), # Ensure it's a string
        )
        
        assert sample_strategy.id is not None
        mock_trade = Trade(
            id=str(uuid4()),
            user_id=user_id,
            mode=TradeMode.PAPER,
            symbol="BTCUSDT",
            side=TradeSide.BUY,
            strategy_id=str(sample_strategy.id),
            opportunity_id=sample_opportunity.id, 
            ai_analysis_confidence=0.8, 
            strategy_execution_instance_id=None, 
            position_status=PositionStatus.PENDING_ENTRY_CONDITIONS, 
            entry_order=TradeOrderDetails( 
                order_id_internal=str(uuid4()),
                order_id_exchange=None,
                client_order_id_exchange=None,
                type=OrderType.MARKET,
                status=OrderStatus.NEW,
                exchange_status_raw=None,
                rejection_reason_code=None,
                rejection_reason_message=None,
                requested_price=None,
                stop_price=None,
                executed_price=None,
                slippage_amount=None,
                slippage_percentage=None,
                requested_quantity=1.0,
                executed_quantity=None,
                cumulative_quote_qty=None,
                commissions=None,
                timestamp=datetime.now(timezone.utc),
                submitted_at=None,
                last_update_timestamp=None,
                fill_timestamp=None,
                trailing_stop_activation_price=None,
                trailing_stop_callback_rate=None,
                current_stop_price_tsl=None,
                oco_group_id_exchange=None
            ),
            exit_orders=None, 
            initial_risk_quote_amount=None, # Added
            initial_reward_to_risk_ratio=None, # Added
            risk_reward_adjustments=None, # Added
            current_risk_quote_amount=None, # Added
            current_reward_to_risk_ratio=None, # Added
            pnl=None, # Added
            pnl_percentage=None, # Added
            closing_reason=None, # Added
            market_context_snapshots=None, # Added
            external_event_or_analysis_link=None, # Added
            backtest_details=None, # Added
            ai_influence_details=None, # Added
            notes=None, # Added
            created_at=datetime.now(timezone.utc),
            opened_at=None, # Added
            closed_at=None, # Added
            updated_at=datetime.now(timezone.utc) # Added
        )
        
        with patch.object(trading_engine, 'create_trade_from_decision', return_value=mock_trade) as mock_create:
            result = await trading_engine._execute_decision_by_mode(
                decision, sample_opportunity, sample_strategy, mode, user_id
            )
            
            assert result == mock_trade
            mock_create.assert_called_once_with(decision, sample_opportunity, sample_strategy)

    @pytest.mark.asyncio
    async def test_real_mode_requires_confirmation_by_default(
        self, trading_engine, mock_config_service, sample_opportunity, sample_strategy
    ):
        """Test that real mode requires user confirmation by default."""
        user_id = str(uuid4())
        mode = "real"
        
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.85,
            reasoning="Real trade execution",
            opportunity_id=sample_opportunity.id,
            strategy_id=str(sample_strategy.id), # Ensure it's a string
        )
        
        # Mock user configuration
        mock_user_config = UserConfiguration(
            id=str(uuid4()), # Added
            user_id=user_id,
            telegram_chat_id=None, # Added
            notification_preferences=None, # Added
            enable_telegram_notifications=True, # Added
            default_paper_trading_capital=10000.0, # Added
            paper_trading_active=True, # Added
            watchlists=None, # Added
            favorite_pairs=None, # Added
            risk_profile=None, # Added
            risk_profile_settings=None, # Added
            real_trading_settings=RealTradingSettings(
                real_trading_mode_active=True,
                # max_real_trades=10, # This field seems to have been removed or renamed
                real_trades_executed_count=2,
                # daily_capital_risked_usd=500.0, # This field seems to have been removed or renamed
                # last_daily_reset=datetime.now(timezone.utc), # This field seems to have been removed or renamed
                max_concurrent_operations=5, # Added example
                daily_loss_limit_absolute=100.0, # Added example
                daily_profit_target_absolute=200.0, # Added example
                asset_specific_stop_loss=None, # Added
                auto_pause_trading_conditions=None, # Added
            ),
            ai_strategy_configurations=None, # Added
            ai_analysis_confidence_thresholds=None, # Added
            mcp_server_preferences=None, # Added
            selected_theme=None, # Added
            dashboard_layout_profiles=None, # Added
            active_dashboard_layout_profile_id=None, # Added
            dashboard_layout_config=None, # Added
            cloud_sync_preferences=None, # Added
            created_at=datetime.now(timezone.utc), # Added
            updated_at=datetime.now(timezone.utc) # Added
        )
        mock_config_service.get_user_configuration.return_value = mock_user_config
        
        with patch.object(trading_engine, '_update_opportunity_status') as mock_update:
            result = await trading_engine._execute_decision_by_mode(
                decision, sample_opportunity, sample_strategy, mode, user_id
            )
            
            assert result is None  # No trade created, awaiting confirmation
            mock_update.assert_called_once_with(
                sample_opportunity,
                OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
                "awaiting_user_confirmation",
                f"Real trade requires user confirmation for strategy {sample_strategy.config_name}"
            )


class TestDetermineTradeSimpleFromOpportunity:
    """Test trade side determination from opportunity signals."""

    def test_buy_direction_returns_buy(self, trading_engine, sample_opportunity):
        """Test that 'buy' direction_sought returns 'buy' side."""
        sample_opportunity.initial_signal.direction_sought = "buy"
        
        side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
        
        assert side == "buy"

    def test_long_direction_returns_buy(self, trading_engine, sample_opportunity):
        """Test that 'long' direction_sought returns 'buy' side."""
        sample_opportunity.initial_signal.direction_sought = "long"
        
        side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
        
        assert side == "buy"

    def test_sell_direction_returns_sell(self, trading_engine, sample_opportunity):
        """Test that 'sell' direction_sought returns 'sell' side."""
        sample_opportunity.initial_signal.direction_sought = "sell"
        
        side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
        
        assert side == "sell"

    def test_short_direction_returns_sell(self, trading_engine, sample_opportunity):
        """Test that 'short' direction_sought returns 'sell' side."""
        sample_opportunity.initial_signal.direction_sought = "short"
        
        side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
        
        assert side == "sell"

    def test_unknown_direction_defaults_to_buy(self, trading_engine, sample_opportunity):
        """Test that unknown direction defaults to 'buy' with warning."""
        sample_opportunity.initial_signal.direction_sought = "unknown"
        
        with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
            side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
            
            assert side == "buy"
            mock_logger.warning.assert_called_once()

    def test_none_direction_defaults_to_buy(self, trading_engine, sample_opportunity):
        """Test that None direction defaults to 'buy' with warning."""
        sample_opportunity.initial_signal.direction_sought = None
        
        with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
            side = trading_engine._determine_trade_side_from_opportunity(sample_opportunity)
            
            assert side == "buy"
            mock_logger.warning.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
