"""Trading Strategy Domain Models.

This module defines the Pydantic models for trading strategy configurations
and strategy-specific parameters.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ValidationError, field_validator


class Timeframe(str, Enum):
    """Enumeration of valid timeframes."""
    
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1M"


class BaseStrategyType(str, Enum):
    """Enumeration of base trading strategy types."""
    
    SCALPING = "SCALPING"
    DAY_TRADING = "DAY_TRADING"
    SWING_TRADING = "SWING_TRADING"
    ARBITRAGE_SIMPLE = "ARBITRAGE_SIMPLE"
    ARBITRAGE_TRIANGULAR = "ARBITRAGE_TRIANGULAR"
    GRID_TRADING = "GRID_TRADING"
    DCA_INVESTING = "DCA_INVESTING"  # Dollar Cost Averaging
    CUSTOM_AI_DRIVEN = "CUSTOM_AI_DRIVEN"
    MCP_SIGNAL_FOLLOWER = "MCP_SIGNAL_FOLLOWER"


class ScalpingParameters(BaseModel):
    """Parameters specific to scalping trading strategy."""
    
    profit_target_percentage: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Target profit percentage per trade (e.g., 0.01 for 1%)"
    )
    stop_loss_percentage: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Stop loss percentage per trade (e.g., 0.005 for 0.5%)"
    )
    max_holding_time_seconds: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum time to hold a position in seconds"
    )
    leverage: Optional[float] = Field(
        None, 
        gt=0, 
        le=100, 
        description="Leverage multiplier (1.0 = no leverage)"
    )


class DayTradingParameters(BaseModel):
    """Parameters specific to day trading strategy."""
    
    rsi_period: Optional[int] = Field(14, gt=0, description="RSI calculation period")
    rsi_overbought: Optional[float] = Field(
        70, 
        ge=50, 
        le=100, 
        description="RSI overbought threshold"
    )
    rsi_oversold: Optional[float] = Field(
        30, 
        ge=0, 
        le=50, 
        description="RSI oversold threshold"
    )
    macd_fast_period: Optional[int] = Field(
        12, 
        gt=0, 
        description="MACD fast EMA period"
    )
    macd_slow_period: Optional[int] = Field(
        26, 
        gt=0, 
        description="MACD slow EMA period"
    )
    macd_signal_period: Optional[int] = Field(
        9, 
        gt=0, 
        description="MACD signal line period"
    )
    entry_timeframes: List[Timeframe] = Field(
        default=...,
        description="Timeframes for entry analysis (e.g., ['5m', '15m'])"
    )
    exit_timeframes: Optional[List[Timeframe]] = Field(
        None, 
        description="Timeframes for exit analysis (e.g., ['1h'])"
    )

    @field_validator('entry_timeframes')
    @classmethod
    def validate_entry_timeframes_not_empty(cls, v):
        """Validate that entry_timeframes is not empty."""
        if not v:
            raise ValueError("Entry timeframes cannot be empty. Must contain at least one timeframe.")
        return v

    @field_validator('entry_timeframes', 'exit_timeframes')
    @classmethod
    def validate_and_check_unique_timeframes(cls, v):
        """Validate that timeframes are valid enum members and unique."""
        if v is None:
            return v
        
        unique_timeframes = set()
        for tf in v:
            if tf not in Timeframe:
                raise ValueError(f"Invalid timeframe: {tf}. Must be one of {list(Timeframe)}")
            if tf in unique_timeframes:
                raise ValueError(f"Duplicate timeframe found: {tf}. All timeframes must be unique.")
            unique_timeframes.add(tf)
        return v

    @field_validator('macd_slow_period')
    @classmethod
    def slow_period_must_be_greater_than_fast(cls, v, info):
        """Validate that slow period is greater than fast period."""
        if 'macd_fast_period' in info.data and v <= info.data['macd_fast_period']:
            raise ValueError('MACD slow period must be greater than fast period')
        return v

    @field_validator('rsi_overbought')
    @classmethod
    def overbought_must_be_greater_than_oversold(cls, v, info):
        """Validate that overbought threshold is greater than oversold threshold."""
        if 'rsi_oversold' in info.data and v <= info.data['rsi_oversold']:
            raise ValueError('RSI overbought must be greater than oversold')
        return v


class ArbitrageSimpleParameters(BaseModel):
    """Parameters specific to simple arbitrage strategy."""
    
    price_difference_percentage_threshold: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Minimum price difference percentage to trigger arbitrage"
    )
    min_trade_volume_quote: Optional[float] = Field(
        None, 
        gt=0, 
        description="Minimum trade volume in quote currency"
    )
    exchange_a_credential_label: str = Field(
        ..., 
        description="Reference to APICredential.credentialLabel for exchange A"
    )
    exchange_b_credential_label: str = Field(
        ..., 
        description="Reference to APICredential.credentialLabel for exchange B"
    )


class CustomAIDrivenParameters(BaseModel):
    """Parameters specific to custom AI-driven strategy."""
    
    primary_objective_prompt: str = Field(
        ..., 
        min_length=10, 
        description="Primary objective prompt for AI analysis"
    )
    context_window_configuration: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuration for AI context window"
    )
    decision_model_parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Parameters for AI decision model"
    )
    max_tokens_for_response: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum tokens for AI response"
    )


class MCPSignalFollowerParameters(BaseModel):
    """Parameters specific to MCP signal follower strategy."""
    
    mcp_source_config_id: str = Field(
        ..., 
        description="ID of UserConfiguration.mcpServerPreferences"
    )
    allowed_signal_types: Optional[List[str]] = Field(
        None, 
        description="List of allowed signal types to follow"
    )


class GridTradingParameters(BaseModel):
    """Parameters specific to grid trading strategy."""
    
    grid_upper_price: float = Field(..., gt=0, description="Upper price boundary of the grid")
    grid_lower_price: float = Field(..., gt=0, description="Lower price boundary of the grid")
    grid_levels: int = Field(..., ge=3, le=100, description="Number of grid levels")
    profit_per_grid: float = Field(
        ..., 
        gt=0, 
        le=1, 
        description="Profit percentage per grid level"
    )
    
    @field_validator('grid_upper_price')
    @classmethod
    def upper_price_must_be_greater_than_lower(cls, v, info):
        """Validate that upper price is greater than lower price."""
        if 'grid_lower_price' in info.data and v <= info.data['grid_lower_price']:
            raise ValueError('Grid upper price must be greater than lower price')
        return v


class DCAInvestingParameters(BaseModel):
    """Parameters specific to Dollar Cost Averaging strategy."""
    
    investment_amount: float = Field(..., gt=0, description="Amount to invest per interval")
    investment_interval_hours: int = Field(
        ..., 
        gt=0, 
        description="Hours between investments"
    )
    max_total_investment: Optional[float] = Field(
        None, 
        gt=0, 
        description="Maximum total investment amount"
    )
    price_deviation_trigger: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Price deviation percentage to trigger additional investment"
    )


# Union type for all strategy-specific parameters
StrategySpecificParameters = Union[
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
    Dict[str, Any]  # Fallback for unknown strategies
]


class DynamicFilter(BaseModel):
    """Dynamic filter criteria for strategy applicability."""
    
    min_daily_volatility_percentage: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Minimum daily volatility percentage"
    )
    max_daily_volatility_percentage: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Maximum daily volatility percentage"
    )
    min_market_cap_usd: Optional[float] = Field(
        None, 
        gt=0, 
        description="Minimum market cap in USD"
    )
    included_watchlist_ids: Optional[List[str]] = Field(
        None, 
        description="IDs of watchlists to include"
    )
    asset_categories: Optional[List[str]] = Field(
        None, 
        description="Asset categories to include"
    )

    @field_validator('max_daily_volatility_percentage')
    @classmethod
    def max_volatility_must_be_greater_than_min(cls, v, info):
        """Validate that max volatility is greater than min volatility."""
        if (v is not None and 
            'min_daily_volatility_percentage' in info.data and 
            info.data['min_daily_volatility_percentage'] is not None and 
            v <= info.data['min_daily_volatility_percentage']):
            raise ValueError('Max daily volatility must be greater than min daily volatility')
        return v


class ApplicabilityRules(BaseModel):
    """Rules defining when and where a strategy applies."""
    
    explicit_pairs: Optional[List[str]] = Field(
        None, 
        description="Explicit trading pairs to apply strategy to"
    )
    include_all_spot: Optional[bool] = Field(
        False, 
        description="Whether to include all spot trading pairs"
    )
    dynamic_filter: Optional[DynamicFilter] = Field(
        None, 
        description="Dynamic filtering criteria"
    )


class RiskParametersOverride(BaseModel):
    """Risk parameter overrides for a specific strategy."""
    
    per_trade_capital_risk_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Capital risk percentage per trade"
    )
    max_concurrent_trades_for_this_strategy: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum concurrent trades for this strategy"
    )
    max_capital_allocation_quote: Optional[float] = Field(
        None, 
        gt=0, 
        description="Maximum capital allocation in quote currency"
    )


class PerformanceMetrics(BaseModel):
    """Performance metrics for a trading strategy."""
    
    total_trades_executed: Optional[int] = Field(0, ge=0)
    winning_trades: Optional[int] = Field(0, ge=0)
    losing_trades: Optional[int] = Field(0, ge=0)
    win_rate: Optional[float] = Field(None, ge=0, le=1)
    cumulative_pnl_quote: Optional[float] = Field(None)
    average_winning_trade_pnl: Optional[float] = Field(None)
    average_losing_trade_pnl: Optional[float] = Field(None)
    profit_factor: Optional[float] = Field(None, ge=0)
    sharpe_ratio: Optional[float] = Field(None)
    last_calculated_at: Optional[datetime] = None

    @field_validator('winning_trades')
    @classmethod
    def winning_trades_validation(cls, v, info):
        """Validate winning trades count."""
        if 'total_trades_executed' in info.data and v > info.data['total_trades_executed']:
            raise ValueError('Winning trades cannot exceed total trades')
        return v

    @field_validator('losing_trades')
    @classmethod
    def losing_trades_validation(cls, v, info):
        """Validate losing trades count."""
        total = info.data.get('total_trades_executed', 0)
        winning = info.data.get('winning_trades', 0)
        if v + winning > total:
            raise ValueError('Sum of winning and losing trades cannot exceed total trades')
        return v


class MarketConditionFilter(BaseModel):
    """Filter based on market conditions."""
    
    filter_type: str = Field(
        ..., 
        description="Type of market condition filter"
    )
    source_id: Optional[str] = Field(
        None, 
        description="Source identifier for the filter"
    )
    condition: str = Field(
        ..., 
        description="Condition type (less_than, greater_than, etc.)"
    )
    threshold_value: Union[float, List[float]] = Field(
        ..., 
        description="Threshold value(s) for the condition"
    )
    action_on_trigger: str = Field(
        ..., 
        description="Action to take when condition is triggered"
    )


class ActivationSchedule(BaseModel):
    """Schedule configuration for strategy activation."""
    
    cron_expression: Optional[str] = Field(
        None, 
        description="Cron expression for scheduling"
    )
    time_zone: Optional[str] = Field(
        "UTC", 
        description="Timezone for the schedule"
    )
    event_triggers: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="Event-based triggers"
    )


class StrategyDependency(BaseModel):
    """Dependency on other strategies."""
    
    strategy_config_id: str = Field(
        ..., 
        description="ID of the dependent strategy configuration"
    )
    required_status_for_activation: Optional[str] = Field(
        None, 
        description="Required status of the dependent strategy"
    )


class SharingMetadata(BaseModel):
    """Metadata for strategy sharing and templates."""
    
    is_template: Optional[bool] = Field(False, description="Whether this is a template")
    author_user_id: Optional[str] = Field(None, description="Author user ID")
    shared_at: Optional[datetime] = None
    user_rating_average: Optional[float] = Field(None, ge=0, le=5)
    download_or_copy_count: Optional[int] = Field(0, ge=0)
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")


class TradingStrategyConfig(BaseModel):
    """Main trading strategy configuration model."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    config_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        description="Descriptive name for the strategy"
    )
    base_strategy_type: BaseStrategyType = Field(
        ..., 
        description="Base type of the trading strategy"
    )
    description: Optional[str] = Field(
        None, 
        description="Detailed description of the strategy"
    )
    
    is_active_paper_mode: bool = Field(
        False, 
        description="Whether strategy is active in paper trading mode"
    )
    is_active_real_mode: bool = Field(
        False, 
        description="Whether strategy is active in real trading mode"
    )
    
    parameters: StrategySpecificParameters = Field(
        ..., 
        description="Strategy-specific parameters"
    )
    
    applicability_rules: Optional[ApplicabilityRules] = Field(
        None, 
        description="Rules defining strategy applicability"
    )
    
    ai_analysis_profile_id: Optional[str] = Field(
        None, 
        description="Reference to AI analysis profile"
    )
    
    risk_parameters_override: Optional[RiskParametersOverride] = Field(
        None, 
        description="Risk parameter overrides"
    )
    
    version: int = Field(1, ge=1, description="Strategy configuration version")
    parent_config_id: Optional[str] = Field(
        None, 
        description="Parent configuration ID for versioning"
    )
    
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, 
        description="Performance metrics"
    )
    
    market_condition_filters: Optional[List[MarketConditionFilter]] = Field(
        None, 
        description="Market condition filters"
    )
    
    activation_schedule: Optional[ActivationSchedule] = Field(
        None, 
        description="Activation schedule configuration"
    )
    
    depends_on_strategies: Optional[List[StrategyDependency]] = Field(
        None, 
        description="Dependencies on other strategies"
    )
    
    sharing_metadata: Optional[SharingMetadata] = Field(
        None, 
        description="Sharing and template metadata"
    )
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic model configuration."""
        
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"  # Prevent extra fields
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @field_validator('config_name')
    @classmethod
    def config_name_must_not_be_empty(cls, v):
        """Validate that config name is not empty after stripping."""
        if not v.strip():
            raise ValueError('Configuration name cannot be empty')
        return v.strip()

    @field_validator('parameters')
    @classmethod
    def validate_parameters_match_strategy_type(cls, v, info):
        """Validate that parameters match the strategy type."""
        if 'base_strategy_type' not in info.data:
            # This should ideally not happen if base_strategy_type is a required field
            # and processed before this validator.
            return v # Or raise an error if base_strategy_type is strictly needed here

        strategy_type_enum_member = info.data.get('base_strategy_type')

        # Ensure strategy_type_enum_member is an actual Enum member
        if not isinstance(strategy_type_enum_member, BaseStrategyType):
            # If it's a string, Pydantic should have converted it based on type hints.
            # If it's still a string here, there might be an issue upstream or
            # the input data was not what Pydantic expected for the enum.
            # We attempt a final conversion, but this path suggests a potential problem.
            try:
                strategy_type_enum_member = BaseStrategyType(str(strategy_type_enum_member))
            except ValueError:
                raise ValueError(
                    f"Invalid base_strategy_type value '{strategy_type_enum_member}'. "
                    f"Expected one of {list(BaseStrategyType.__members__.keys())}."
                )
        
        expected_parameter_models = {
            BaseStrategyType.SCALPING: ScalpingParameters,
            BaseStrategyType.DAY_TRADING: DayTradingParameters,
            BaseStrategyType.ARBITRAGE_SIMPLE: ArbitrageSimpleParameters,
            BaseStrategyType.CUSTOM_AI_DRIVEN: CustomAIDrivenParameters,
            BaseStrategyType.MCP_SIGNAL_FOLLOWER: MCPSignalFollowerParameters,
            BaseStrategyType.GRID_TRADING: GridTradingParameters,
            BaseStrategyType.DCA_INVESTING: DCAInvestingParameters,
        }
        
        expected_model = expected_parameter_models.get(strategy_type_enum_member)
        
        if expected_model:
            # If 'v' (the parameters field) is a dictionary, and not already an instance
            # of the expected model, attempt to parse it into the expected model.
            # Pydantic's Union handling might have left it as a dict if it matched Dict[str, Any] first.
            if isinstance(v, dict) and not isinstance(v, expected_model):
                try:
                    v = expected_model(**v)
                except ValidationError as e:
                    # Re-raise with a more informative message, possibly including field details
                    raise ValueError(
                        f"Invalid parameters for strategy type '{strategy_type_enum_member.value}'. "
                        f"Details: {e.errors()}"
                    )
            # If 'v' is already an instance of the correct model, or another valid type in the Union,
            # and it's not a dict that needs conversion, it's fine.
            elif not isinstance(v, (expected_model, dict)): # Allow dict if no specific model or if it's a fallback
                 # This case might need refinement based on how StrategySpecificParameters Union is defined
                 # If StrategySpecificParameters = Union[ModelA, ModelB, Dict[str, Any]],
                 # then a dict is a valid type for 'v'.
                 # The goal is to ensure if a specific model is expected, 'v' becomes an instance of it.
                pass # It's already a specific Pydantic model from the Union or a fallback dict.

        return v

    @field_validator('is_active_real_mode')
    @classmethod
    def real_mode_requires_validation(cls, v, info):
        """Add validation warnings for real mode activation."""
        if v and info.data.get('is_active_paper_mode', False):
            # Both modes active - could be intentional for comparison
            pass
        elif v and not info.data.get('is_active_paper_mode', False):
            # Only real mode active - should have been tested in paper first
            # This is a business logic warning, not a validation error
            pass
        return v
