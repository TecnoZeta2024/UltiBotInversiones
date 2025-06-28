
import pytest
from datetime import datetime
from uuid import uuid4
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
    ApplicabilityRules,
    DynamicFilter,
    RiskParametersOverride,
    PerformanceMetrics,
    MarketConditionFilter,
    ActivationSchedule,
    StrategyDependency,
    SharingMetadata,
    TradingStrategyConfig,
)
from pydantic import ValidationError

# Test Timeframe Enum
def test_timeframe_enum():
    assert Timeframe.ONE_MINUTE == "1m"
    assert Timeframe.ONE_MONTH == "1M"

# Test BaseStrategyType Enum
def test_base_strategy_type_enum():
    assert BaseStrategyType.SCALPING == "SCALPING"
    assert BaseStrategyType.UNKNOWN == "UNKNOWN"

# Test ScalpingParameters
def test_scalping_parameters_valid():
    params = ScalpingParameters(
        profit_target_percentage=0.01,
        stop_loss_percentage=0.005,
        max_holding_time_seconds=300,
        leverage=10.0
    )
    assert params.profit_target_percentage == 0.01

def test_scalping_parameters_invalid_profit_target():
    with pytest.raises(ValidationError):
        ScalpingParameters(profit_target_percentage=1.5, stop_loss_percentage=0.005)

# Test DayTradingParameters
def test_day_trading_parameters_valid():
    params = DayTradingParameters(
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        entry_timeframes=[Timeframe.FIVE_MINUTES, Timeframe.FIFTEEN_MINUTES],
        exit_timeframes=[Timeframe.ONE_HOUR]
    )
    assert params.rsi_period == 14

def test_day_trading_parameters_invalid_timeframes():
    with pytest.raises(ValidationError):
        DayTradingParameters(
            entry_timeframes=["invalid_timeframe"],
            exit_timeframes=[]
        )
    with pytest.raises(ValidationError):
        DayTradingParameters(
            entry_timeframes=[Timeframe.FIVE_MINUTES, Timeframe.FIVE_MINUTES]
        )

def test_day_trading_parameters_invalid_macd_periods():
    with pytest.raises(ValidationError):
        DayTradingParameters(
            macd_fast_period=20,
            macd_slow_period=10,
            entry_timeframes=[Timeframe.FIVE_MINUTES]
        )

def test_day_trading_parameters_invalid_rsi_thresholds():
    with pytest.raises(ValidationError):
        DayTradingParameters(
            rsi_overbought=50,
            rsi_oversold=60,
            entry_timeframes=[Timeframe.FIVE_MINUTES]
        )

# Test ArbitrageSimpleParameters
def test_arbitrage_simple_parameters_valid():
    params = ArbitrageSimpleParameters(
        price_difference_percentage_threshold=0.001,
        min_trade_volume_quote=100.0,
        exchange_a_credential_label="binance_api",
        exchange_b_credential_label="kraken_api"
    )
    assert params.price_difference_percentage_threshold == 0.001

# Test CustomAIDrivenParameters
def test_custom_ai_driven_parameters_valid():
    params = CustomAIDrivenParameters(
        primary_objective_prompt="Analyze market for bullish signals.",
        max_tokens_for_response=500
    )
    assert params.primary_objective_prompt == "Analyze market for bullish signals."

# Test MCPSignalFollowerParameters
def test_mcp_signal_follower_parameters_valid():
    params = MCPSignalFollowerParameters(
        mcp_source_config_id="mcp_config_123",
        allowed_signal_types=["buy", "sell"]
    )
    assert params.mcp_source_config_id == "mcp_config_123"

# Test GridTradingParameters
def test_grid_trading_parameters_valid():
    params = GridTradingParameters(
        grid_upper_price=100.0,
        grid_lower_price=90.0,
        grid_levels=10,
        profit_per_grid=0.001
    )
    assert params.grid_levels == 10

def test_grid_trading_parameters_invalid_prices():
    with pytest.raises(ValidationError):
        GridTradingParameters(
            grid_upper_price=90.0,
            grid_lower_price=100.0,
            grid_levels=10,
            profit_per_grid=0.001
        )

# Test DCAInvestingParameters
def test_dca_investing_parameters_valid():
    params = DCAInvestingParameters(
        investment_amount=100.0,
        investment_interval_hours=24,
        max_total_investment=1000.0
    )
    assert params.investment_amount == 100.0

# Test DynamicFilter
def test_dynamic_filter_valid():
    df = DynamicFilter(
        min_daily_volatility_percentage=0.01,
        max_daily_volatility_percentage=0.05
    )
    assert df.min_daily_volatility_percentage == 0.01

def test_dynamic_filter_invalid_volatility():
    with pytest.raises(ValidationError):
        DynamicFilter(
            min_daily_volatility_percentage=0.05,
            max_daily_volatility_percentage=0.01
        )

# Test ApplicabilityRules
def test_applicability_rules_valid():
    ar = ApplicabilityRules(
        include_all_spot=True,
        dynamic_filter=DynamicFilter(min_market_cap_usd=1000000.0)
    )
    assert ar.include_all_spot is True

# Test RiskParametersOverride
def test_risk_parameters_override_valid():
    rpo = RiskParametersOverride(
        per_trade_capital_risk_percentage=0.01,
        max_concurrent_trades_for_this_strategy=5
    )
    assert rpo.per_trade_capital_risk_percentage == 0.01

# Test PerformanceMetrics
def test_performance_metrics_valid():
    pm = PerformanceMetrics(
        total_trades_executed=100,
        winning_trades=60,
        losing_trades=40,
        win_rate=0.6,
        cumulative_pnl_quote=1000.0,
        last_calculated_at=datetime.now()
    )
    assert pm.total_trades_executed == 100

def test_performance_metrics_invalid_trades():
    with pytest.raises(ValidationError):
        PerformanceMetrics(total_trades_executed=10, winning_trades=12)
    with pytest.raises(ValidationError):
        PerformanceMetrics(total_trades_executed=10, winning_trades=5, losing_trades=6)

# Test MarketConditionFilter
def test_market_condition_filter_valid():
    mcf = MarketConditionFilter(
        filter_type="volatility",
        condition="greater_than",
        threshold_value=0.02,
        action_on_trigger="pause_strategy"
    )
    assert mcf.filter_type == "volatility"

# Test ActivationSchedule
def test_activation_schedule_valid():
    acs = ActivationSchedule(
        cron_expression="0 0 * * *",
        time_zone="America/New_York"
    )
    assert acs.cron_expression == "0 0 * * *"

# Test StrategyDependency
def test_strategy_dependency_valid():
    sd = StrategyDependency(
        strategy_config_id=str(uuid4()),
        required_status_for_activation="active"
    )
    assert isinstance(sd.strategy_config_id, str)

# Test SharingMetadata
def test_sharing_metadata_valid():
    sm = SharingMetadata(
        is_template=True,
        author_user_id=str(uuid4()),
        user_rating_average=4.5
    )
    assert sm.is_template is True

# Test TradingStrategyConfig
def test_trading_strategy_config_valid_scalping():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="My Scalping Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(
            profit_target_percentage=0.008,
            stop_loss_percentage=0.003
        )
    )
    assert config.config_name == "My Scalping Strategy"
    assert isinstance(config.parameters, ScalpingParameters)

def test_trading_strategy_config_valid_day_trading():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="My Day Trading Strategy",
        base_strategy_type=BaseStrategyType.DAY_TRADING,
        parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.FIFTEEN_MINUTES],
            rsi_period=14
        )
    )
    assert config.base_strategy_type == BaseStrategyType.DAY_TRADING
    assert isinstance(config.parameters, DayTradingParameters)

def test_trading_strategy_config_invalid_parameters_type():
    with pytest.raises(ValidationError):
        TradingStrategyConfig(
            user_id=str(uuid4()),
            config_name="Invalid Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=DayTradingParameters(entry_timeframes=[Timeframe.FIVE_MINUTES]) # Wrong parameters type
        )

def test_trading_strategy_config_missing_required_fields():
    with pytest.raises(ValidationError):
        TradingStrategyConfig(
            user_id=str(uuid4()),
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
        )

def test_trading_strategy_config_config_name_validation():
    with pytest.raises(ValidationError):
        TradingStrategyConfig(
            user_id=str(uuid4()),
            config_name="",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
        )
    with pytest.raises(ValidationError):
        TradingStrategyConfig(
            user_id=str(uuid4()),
            config_name="   ",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
        )

def test_trading_strategy_config_unknown_strategy_type_with_dict_parameters():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Unknown Strategy",
        base_strategy_type=BaseStrategyType.UNKNOWN,
        parameters={"some_key": "some_value", "another_key": 123}
    )
    assert config.base_strategy_type == BaseStrategyType.UNKNOWN
    assert config.parameters == {"some_key": "some_value", "another_key": 123}

def test_trading_strategy_config_allowed_and_excluded_symbols():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Symbol Specific Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        allowed_symbols=["BTC/USDT", "ETH/USDT"],
        excluded_symbols=["XRP/USDT"]
    )
    assert "BTC/USDT" in config.allowed_symbols
    assert "XRP/USDT" in config.excluded_symbols

def test_trading_strategy_config_risk_parameters_override():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Risk Override Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        risk_parameters_override=RiskParametersOverride(per_trade_capital_risk_percentage=0.02)
    )
    assert config.risk_parameters_override.per_trade_capital_risk_percentage == 0.02

def test_trading_strategy_config_performance_metrics():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Performance Tracked Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        performance_metrics=PerformanceMetrics(total_trades_executed=50, winning_trades=30)
    )
    assert config.performance_metrics.total_trades_executed == 50

def test_trading_strategy_config_activation_schedule():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Scheduled Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        activation_schedule=ActivationSchedule(cron_expression="0 0 * * *")
    )
    assert config.activation_schedule.cron_expression == "0 0 * * *"

def test_trading_strategy_config_sharing_metadata():
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Shared Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        sharing_metadata=SharingMetadata(is_template=True, author_user_id=str(uuid4()))
    )
    assert config.sharing_metadata.is_template is True

def test_trading_strategy_config_timestamps():
    now = datetime.now()
    config = TradingStrategyConfig(
        user_id=str(uuid4()),
        config_name="Timestamped Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
        created_at=now,
        updated_at=now
    )
    assert config.created_at == now
    assert config.updated_at == now
