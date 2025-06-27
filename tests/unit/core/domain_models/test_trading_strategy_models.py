
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError
from pydantic import ValidationError
from decimal import Decimal

from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    Timeframe,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
    DynamicFilter,
    ApplicabilityRules,
    RiskParametersOverride,
    PerformanceMetrics,
    MarketConditionFilter,
    ActivationSchedule,
    StrategyDependency,
    SharingMetadata,
    TradingStrategyConfig,
    StrategySpecificParameters
)

# Test Enums
# =================================================================
class TestEnums:
    def test_timeframe_enum(self):
        assert Timeframe.ONE_MINUTE.value == "1m"
        assert Timeframe.ONE_DAY.value == "1d"

    def test_base_strategy_type_enum(self):
        assert BaseStrategyType.SCALPING.value == "SCALPING"
        assert BaseStrategyType.CUSTOM_AI_DRIVEN.value == "CUSTOM_AI_DRIVEN"
        assert BaseStrategyType.UNKNOWN.value == "UNKNOWN"

# Test Pydantic Models (basic instantiation and field types)
# =================================================================
class TestPydanticModels:

    def test_scalping_parameters(self):
        params = ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=300,
            leverage=10.0
        )
        assert params.profit_target_percentage == 0.01
        assert params.stop_loss_percentage == 0.005

    def test_day_trading_parameters_basic(self):
        params = DayTradingParameters(
            entry_timeframes=[Timeframe.FIVE_MINUTES, Timeframe.FIFTEEN_MINUTES]
        )
        assert params.rsi_period == 14
        assert params.entry_timeframes == [Timeframe.FIVE_MINUTES, Timeframe.FIFTEEN_MINUTES]

    def test_day_trading_parameters_validators(self):
        # Test entry_timeframes not empty
        with pytest.raises(ValueError, match="Entry timeframes cannot be empty"):
            DayTradingParameters(entry_timeframes=[])

        # Test invalid timeframe
        with pytest.raises(ValidationError, match="Input should be '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w' or '1M'"):
            DayTradingParameters(entry_timeframes=["invalid_tf"])

        # Test duplicate timeframe
        with pytest.raises(ValueError, match="Duplicate timeframe found"):
            DayTradingParameters(entry_timeframes=[Timeframe.ONE_HOUR, Timeframe.ONE_HOUR])

        # Test slow_period_must_be_greater_than_fast
        with pytest.raises(ValueError, match="MACD slow period must be greater than fast period"):
            DayTradingParameters(macd_fast_period=20, macd_slow_period=10, entry_timeframes=[Timeframe.ONE_HOUR])

        # Test overbought_must_be_greater_than_oversold
        with pytest.raises(ValidationError, match="Input should be greater than or equal to 50"):
            DayTradingParameters(rsi_oversold=50, rsi_overbought=40, entry_timeframes=[Timeframe.ONE_HOUR])

    def test_arbitrage_simple_parameters(self):
        params = ArbitrageSimpleParameters(
            price_difference_percentage_threshold=0.001,
            exchange_a_credential_label="binance_a",
            exchange_b_credential_label="binance_b"
        )
        assert params.price_difference_percentage_threshold == 0.001

    def test_custom_ai_driven_parameters(self):
        params = CustomAIDrivenParameters(
            primary_objective_prompt="Optimize for profit",
            max_tokens_for_response=500
        )
        assert params.primary_objective_prompt == "Optimize for profit"

    def test_mcp_signal_follower_parameters(self):
        params = MCPSignalFollowerParameters(
            mcp_source_config_id="mcp_config_1",
            allowed_signal_types=["buy_signal", "sell_signal"]
        )
        assert params.mcp_source_config_id == "mcp_config_1"

    def test_grid_trading_parameters(self):
        params = GridTradingParameters(
            grid_upper_price=100.0,
            grid_lower_price=90.0,
            grid_levels=10,
            profit_per_grid=0.001
        )
        assert params.grid_upper_price == 100.0

    def test_grid_trading_parameters_validator(self):
        with pytest.raises(ValidationError) as excinfo:
            GridTradingParameters(grid_upper_price=90.0, grid_lower_price=100.0, grid_levels=10, profit_per_grid=0.001)
        assert "Grid upper price must be greater than lower price" in str(excinfo.value)

    def test_dca_investing_parameters(self):
        params = DCAInvestingParameters(
            investment_amount=100.0,
            investment_interval_hours=24
        )
        assert params.investment_amount == 100.0

    def test_dynamic_filter(self):
        df = DynamicFilter(
            min_daily_volatility_percentage=0.01,
            max_daily_volatility_percentage=0.05
        )
        assert df.min_daily_volatility_percentage == 0.01

    def test_dynamic_filter_validator(self):
        with pytest.raises(ValueError, match="Max daily volatility must be greater than min daily volatility"):
            DynamicFilter(min_daily_volatility_percentage=0.05, max_daily_volatility_percentage=0.01)

    def test_applicability_rules(self):
        ar = ApplicabilityRules(include_all_spot=True)
        assert ar.include_all_spot is True

    def test_risk_parameters_override(self):
        rpo = RiskParametersOverride(
            per_trade_capital_risk_percentage=0.01,
            max_concurrent_trades_for_this_strategy=5
        )
        assert rpo.per_trade_capital_risk_percentage == 0.01

    def test_performance_metrics(self):
        pm = PerformanceMetrics(
            total_trades_executed=100,
            winning_trades=60,
            losing_trades=40
        )
        assert pm.total_trades_executed == 100

    def test_performance_metrics_validators(self):
        with pytest.raises(ValueError, match="Winning trades cannot exceed total trades"):
            PerformanceMetrics(total_trades_executed=10, winning_trades=15)
        with pytest.raises(ValueError, match="Sum of winning and losing trades cannot exceed total trades"):
            PerformanceMetrics(total_trades_executed=10, winning_trades=5, losing_trades=6)

    def test_market_condition_filter(self):
        mcf = MarketConditionFilter(
            filter_type="volatility",
            condition="greater_than",
            threshold_value=0.02,
            action_on_trigger="pause_strategy"
        )
        assert mcf.filter_type == "volatility"

    def test_activation_schedule(self):
        schedule = ActivationSchedule(cron_expression="0 0 * * *", time_zone="America/New_York")
        assert schedule.cron_expression == "0 0 * * *"

    def test_strategy_dependency(self):
        dep = StrategyDependency(
            strategy_config_id=str(uuid4()),
            required_status_for_activation="active"
        )
        assert isinstance(dep.strategy_config_id, str)

    def test_sharing_metadata(self):
        meta = SharingMetadata(
            is_template=True,
            author_user_id=str(uuid4())
        )
        assert meta.is_template is True

# Test TradingStrategyConfig Model
# =================================================================
class TestTradingStrategyConfig:

    @pytest.fixture
    def sample_scalping_params(self):
        return ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005
        )

    @pytest.fixture
    def sample_day_trading_params(self):
        return DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_HOUR]
        )

    def test_trading_strategy_config_creation(self, sample_scalping_params):
        user_id = str(uuid4())
        config = TradingStrategyConfig(
            user_id=user_id,
            config_name="My Scalping Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=sample_scalping_params
        )
        assert isinstance(config.id, str)
        assert len(config.id) > 0 # Ensure ID is not empty
        assert config.user_id == user_id
        assert config.config_name == "My Scalping Strategy"
        assert config.base_strategy_type == BaseStrategyType.SCALPING
        assert config.parameters == sample_scalping_params
        assert config.is_active_paper_mode is False
        assert config.is_active_real_mode is False

    def test_trading_strategy_config_with_day_trading_params(self, sample_day_trading_params):
        user_id = str(uuid4())
        config = TradingStrategyConfig(
            user_id=user_id,
            config_name="My Day Trading Strategy",
            base_strategy_type=BaseStrategyType.DAY_TRADING,
            parameters=sample_day_trading_params
        )
        assert config.base_strategy_type == BaseStrategyType.DAY_TRADING
        assert config.parameters == sample_day_trading_params

    def test_trading_strategy_config_name_validator(self):
        user_id = str(uuid4())
        with pytest.raises(ValueError, match="Configuration name cannot be empty"):
            TradingStrategyConfig(
                user_id=user_id,
                config_name="   ",
                base_strategy_type=BaseStrategyType.SCALPING,
                parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
            )

    def test_trading_strategy_config_parameters_validator_valid(self):
        user_id = str(uuid4())
        # Test with ScalpingParameters
        config = TradingStrategyConfig(
            user_id=user_id,
            config_name="Scalping",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
        )
        assert isinstance(config.parameters, ScalpingParameters)

        # Test with DayTradingParameters
        config = TradingStrategyConfig(
            user_id=user_id,
            config_name="DayTrading",
            base_strategy_type=BaseStrategyType.DAY_TRADING,
            parameters=DayTradingParameters(entry_timeframes=[Timeframe.ONE_HOUR])
        )
        assert isinstance(config.parameters, DayTradingParameters)

        # Test with Dict for UNKNOWN type
        config = TradingStrategyConfig(
            user_id=user_id,
            config_name="Unknown Strategy",
            base_strategy_type=BaseStrategyType.UNKNOWN,
            parameters={"some_key": "some_value"}
        )
        assert isinstance(config.parameters, dict)
        assert config.parameters["some_key"] == "some_value"

        # Test with Dict for UNKNOWN type, but parameters is not a dict
        with pytest.raises(ValidationError, match="Input should be a valid dictionary"):
            TradingStrategyConfig(
                user_id=user_id,
                config_name="Unknown Strategy Invalid",
                base_strategy_type=BaseStrategyType.UNKNOWN,
                parameters="not_a_dict"
            )

    def test_trading_strategy_config_parameters_validator_invalid(self):
        user_id = str(uuid4())
        # Mismatch between strategy type and parameters
        with pytest.raises(ValidationError, match="Parameters for strategy type 'SCALPING' must be an instance of ScalpingParameters or a dictionary"):
            TradingStrategyConfig(
                user_id=user_id,
                config_name="Scalping",
                base_strategy_type=BaseStrategyType.SCALPING,
                parameters=DayTradingParameters(entry_timeframes=[Timeframe.ONE_HOUR]) # Wrong parameters
            )

        # Invalid parameters for the correct type
        with pytest.raises(ValueError, match="Invalid parameters for strategy type"):
            TradingStrategyConfig(
                user_id=user_id,
                config_name="Scalping",
                base_strategy_type=BaseStrategyType.SCALPING,
                parameters={"profit_target_percentage": -0.01, "stop_loss_percentage": 0.005} # Invalid value
            )

