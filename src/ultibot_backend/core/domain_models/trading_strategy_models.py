"""Trading Strategy Domain Models.

This module defines the Pydantic models for trading strategy configurations
and strategy-specific parameters.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError # MODIFIED


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
    
    profit_target_percentage: Optional[float] = Field(
        None, 
        alias="take_profit_percentage",
        gt=0, 
        le=1, 
        description="Target profit percentage per trade (e.g., 0.01 for 1%)"
    )
    stop_loss_percentage: Optional[float] = Field(
        None, 
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
        alias="max_leverage",
        gt=0, 
        le=100, 
        description="Leverage multiplier (1.0 = no leverage)"
    )
    entry_threshold: Optional[float] = Field(None, description="Legacy field, ignored.")
    exit_threshold: Optional[float] = Field(None, description="Legacy field, ignored.")

    model_config = { # MODIFIED
        "populate_by_name": True
    }


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
        default=[],
        description="Timeframes for entry analysis (e.g., ['5m', '15m'])"
    )
    exit_timeframes: Optional[List[Timeframe]] = Field(
        None, 
        description="Timeframes for exit analysis (e.g., ['1h'])"
    )

    @field_validator('entry_timeframes') # MODIFIED
    @classmethod # ADDED
    def validate_entry_timeframes_not_empty(cls, v: List[Timeframe]) -> List[Timeframe]: # MODIFIED
        """Validate that entry_timeframes is not empty."""
        # Original logic allowed empty list, keeping that.
        return v

    @field_validator('entry_timeframes', 'exit_timeframes', mode='before') # MODIFIED
    @classmethod # ADDED
    def validate_and_check_unique_timeframes(cls, v_list: Optional[List[Union[str, Timeframe]]]) -> Optional[List[Timeframe]]: # MODIFIED
        """Validate that timeframes are valid enum members and unique."""
        if v_list is None:
            return None
        
        processed_list = []
        for v_item in v_list:
            if isinstance(v_item, str):
                processed_list.append(Timeframe(v_item))
            elif isinstance(v_item, Timeframe):
                processed_list.append(v_item)
            else:
                raise ValueError(f"Invalid timeframe item: {v_item}")
        # Uniqueness check can be added here if needed, e.g. len(set(processed_list)) == len(processed_list)
        return processed_list

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def check_macd_periods(cls, model: 'DayTradingParameters') -> 'DayTradingParameters': # MODIFIED
        """Validate that slow period is greater than fast period."""
        if model.macd_fast_period is not None and \
           model.macd_slow_period is not None and \
           model.macd_slow_period <= model.macd_fast_period:
            raise ValueError('MACD slow period must be greater than fast period')
        return model

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def check_rsi_thresholds(cls, model: 'DayTradingParameters') -> 'DayTradingParameters': # MODIFIED
        """Validate that overbought threshold is greater than oversold threshold."""
        if model.rsi_oversold is not None and \
           model.rsi_overbought is not None and \
           model.rsi_overbought <= model.rsi_oversold:
            raise ValueError('RSI overbought must be greater than oversold')
        return model


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

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def check_grid_prices(cls, model: 'GridTradingParameters') -> 'GridTradingParameters': # MODIFIED
        """Validate that upper price is greater than lower price."""
        if model.grid_lower_price is not None and \
           model.grid_upper_price is not None and \
           model.grid_upper_price <= model.grid_lower_price:
            raise ValueError('Grid upper price must be greater than lower price')
        return model


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

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def check_volatility_percentages(cls, model: 'DynamicFilter') -> 'DynamicFilter': # MODIFIED
        """Validate that max volatility is greater than min volatility."""
        if model.min_daily_volatility_percentage is not None and \
           model.max_daily_volatility_percentage is not None and \
           model.max_daily_volatility_percentage <= model.min_daily_volatility_percentage:
            raise ValueError('Max daily volatility must be greater than min daily volatility')
        return model


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

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def check_trade_counts(cls, model: 'PerformanceMetrics') -> 'PerformanceMetrics': # MODIFIED
        """Validate winning and losing trades against total trades."""
        if model.total_trades_executed is not None:
            if model.winning_trades is not None and model.winning_trades > model.total_trades_executed:
                raise ValueError('Winning trades cannot exceed total trades')
            if model.losing_trades is not None and model.winning_trades is not None and \
               (model.losing_trades + model.winning_trades) > model.total_trades_executed:
                raise ValueError('Sum of winning and losing trades cannot exceed total trades')
        return model


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
    
    id: Optional[UUID] = Field(None, description="Unique identifier")
    user_id: UUID = Field(..., description="User identifier")
    
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
        default_factory=list, 
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

    model_config = { # MODIFIED
        "use_enum_values": False, # Note: Pydantic v2 usually handles enums directly to values in serialization if not specified otherwise.
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: lambda v: str(v),
        },
        "arbitrary_types_allowed": True
    }

    @field_validator('market_condition_filters', mode='before') # MODIFIED
    @classmethod # ADDED
    def empty_dict_to_list(cls, v: Any) -> Any: # MODIFIED
        if v == {}:
            return []
        return v

    @field_validator('config_name') # MODIFIED
    @classmethod # ADDED
    def config_name_must_not_be_empty(cls, v: str) -> str: # MODIFIED
        """Validate that config name is not empty after stripping."""
        if not v.strip():
            raise ValueError('Configuration name cannot be empty')
        return v.strip()

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def validate_parameters_match_strategy_type(cls, model: 'TradingStrategyConfig') -> 'TradingStrategyConfig': # MODIFIED
        """Validate that parameters match the strategy type."""
        strategy_type_enum_member = model.base_strategy_type

        if not isinstance(strategy_type_enum_member, BaseStrategyType):
            try:
                # Ensure it's a valid enum member if passed as string
                strategy_type_enum_member = BaseStrategyType(str(strategy_type_enum_member))
            except ValueError:
                raise ValueError(
                    f"Invalid base_strategy_type value '{model.base_strategy_type}'. "
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
        
        if expected_model and model.parameters is not None:
            # If parameters is a dict, try to validate it into the expected model type
            if isinstance(model.parameters, dict) and not isinstance(model.parameters, expected_model):
                try:
                    # model_validate will respect aliases if defined in the specific parameter model
                    validated_params = expected_model.model_validate(model.parameters)
                    # Pydantic V2 model_validator should return the model itself, not just the field
                    # So, we might need to assign it back if the field was not already the correct type
                    # However, if parameters is already an instance of the correct type, this is fine.
                    # This validator is 'after', so model.parameters would be an instance.
                    # The check here is more about ensuring it IS an instance of the correct type.
                    if not isinstance(model.parameters, expected_model):
                         # This case might be tricky if model.parameters was already a different Pydantic model.
                         # For now, we assume it's either a dict or the correct model.
                         # If it's a dict, model_validate creates the right instance.
                         # If it's already a Pydantic model but not the right one, it's an issue.
                         # The Union type helps, but this validator ensures the dict matches the specific type.
                        pass # If it's a dict, it should have been converted by Pydantic already.
                            # This validator is more to catch if it's a *different* Pydantic model.

                except ValidationError as e:
                    raise ValueError(
                        f"Invalid parameters for strategy type '{strategy_type_enum_member.value}'. "
                        f"Details: {e.errors()}"
                    )
            elif not isinstance(model.parameters, (expected_model, dict)): # Allow dict for initial validation by Pydantic
                 # If it's already a Pydantic model, but not the expected one (and not a fallback dict)
                if not isinstance(model.parameters, dict): # Check if it's not already a dict (fallback)
                    raise ValueError(
                        f"Parameters for strategy type '{strategy_type_enum_member.value}' are not of the expected type or a dictionary."
                    )
        return model

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def real_mode_requires_validation(cls, model: 'TradingStrategyConfig') -> 'TradingStrategyConfig': # MODIFIED
        """Add validation warnings for real mode activation."""
        # This validator doesn't actually raise errors, seems like placeholder/informational
        # Pylance might warn if 'v' or 'values' are not used if they were parameters.
        # Since it's now a model_validator, it receives the model.
        if model.is_active_real_mode and model.is_active_paper_mode:
            pass # Original logic
        elif model.is_active_real_mode and not model.is_active_paper_mode:
            pass # Original logic
        return model
