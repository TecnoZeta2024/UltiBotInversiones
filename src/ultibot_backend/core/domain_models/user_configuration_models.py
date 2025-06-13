"""User Configuration Domain Models.

This module defines the Pydantic models for user configuration settings,
including AI strategy configurations for integration with Gemini analysis,
and advanced market scanning and asset trading parameters.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator # MODIFIED

class NotificationChannel(str, Enum):
    """Enumeration of notification channels."""
    
    TELEGRAM = "telegram"
    UI = "ui"
    EMAIL = "email"

class RiskProfile(str, Enum):
    """Enumeration of risk profiles."""
    
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class Theme(str, Enum):
    """Enumeration of UI themes."""
    
    DARK = "dark"
    LIGHT = "light"

class MarketCapRange(str, Enum):
    """Enumeration of market cap ranges for filtering."""
    
    MICRO = "micro"        # < 300M
    SMALL = "small"        # 300M - 2B
    MID = "mid"           # 2B - 10B
    LARGE = "large"       # 10B - 200B
    MEGA = "mega"         # > 200B
    ALL = "all"

class VolumeFilter(str, Enum):
    """Enumeration of volume filter types."""
    
    ABOVE_AVERAGE = "above_average"
    HIGH_VOLUME = "high_volume"
    CUSTOM_THRESHOLD = "custom_threshold"
    NO_FILTER = "no_filter"

class TrendDirection(str, Enum):
    """Enumeration of trend directions."""
    
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    ANY = "any"

class NotificationPreference(BaseModel):
    """Notification preference configuration."""
    
    event_type: str = Field(
        ..., 
        description="Type of event (e.g., 'REAL_TRADE_EXECUTED', 'PAPER_OPPORTUNITY_HIGH_CONFIDENCE')"
    )
    channel: NotificationChannel = Field(
        ..., 
        description="Notification channel"
    )
    is_enabled: bool = Field(
        True, 
        description="Whether this notification is enabled"
    )
    min_confidence: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Minimum confidence threshold for events"
    )
    min_profitability: Optional[float] = Field(
        None, 
        ge=0, 
        description="Minimum profitability threshold for events"
    )

class Watchlist(BaseModel):
    """Watchlist configuration."""
    
    id: str = Field(..., description="Unique identifier for the watchlist")
    name: str = Field(..., description="Name of the watchlist")
    pairs: List[str] = Field(..., description="Trading pairs in this watchlist")
    default_alert_profile_id: Optional[str] = Field(
        None, 
        description="Default alert profile ID for this watchlist"
    )
    default_ai_analysis_profile_id: Optional[str] = Field(
        None, 
        description="Default AI analysis profile ID for this watchlist"
    )

class RiskProfileSettings(BaseModel):
    """Risk profile settings."""
    
    daily_capital_risk_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Maximum percentage of capital to risk daily"
    )
    per_trade_capital_risk_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Maximum percentage of capital to risk per trade"
    )
    max_drawdown_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Maximum drawdown before automatic pause"
    )

class AutoPauseTradingConditions(BaseModel):
    """Auto pause trading conditions."""
    
    on_max_daily_loss_reached: Optional[bool] = Field(
        None, 
        description="Pause on max daily loss"
    )
    on_max_drawdown_reached: Optional[bool] = Field(
        None, 
        description="Pause on max drawdown"
    )
    on_consecutive_losses: Optional[int] = Field(
        None, 
        gt=0, 
        description="Pause after X consecutive losses"
    )
    on_market_volatility_index_exceeded: Optional[Dict[str, Any]] = Field(
        None, 
        description="Pause on high market volatility"
    )

class RealTradingSettings(BaseModel):
    """Real trading mode settings."""
    
    real_trading_mode_active: Optional[bool] = Field(
        False, 
        description="Whether real trading mode is active"
    )
    real_trades_executed_count: Optional[int] = Field(
        0, 
        ge=0, 
        description="Count of executed real trades"
    )
    max_concurrent_operations: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum concurrent operations"
    )
    max_real_trades: Optional[int] = Field(
        10,
        gt=0,
        description="Maximum number of real trades to execute"
    )
    daily_loss_limit_absolute: Optional[float] = Field(
        None, 
        gt=0, 
        description="Daily loss limit in quote currency"
    )
    daily_profit_target_absolute: Optional[float] = Field(
        None, 
        gt=0, 
        description="Daily profit target in quote currency"
    )
    asset_specific_stop_loss: Optional[Dict[str, Dict[str, float]]] = Field(
        None, 
        description="Asset-specific stop loss settings"
    )
    auto_pause_trading_conditions: Optional[AutoPauseTradingConditions] = Field(
        None, 
        description="Auto pause conditions"
    )

class ConfidenceThresholds(BaseModel):
    """AI confidence thresholds for different trading modes."""
    
    paper_trading: Optional[float] = Field(
        0.5, 
        ge=0, 
        le=1, 
        description="Confidence threshold for paper trading (default: 50%)"
    )
    real_trading: Optional[float] = Field(
        0.95, 
        ge=0, 
        le=1, 
        description="Confidence threshold for real trading (default: 95%)"
    )

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def real_trading_should_be_higher_than_paper(cls, model: 'ConfidenceThresholds') -> 'ConfidenceThresholds': # MODIFIED
        """Validate that real trading threshold is higher than paper trading."""
        if model.real_trading is not None and model.paper_trading is not None:
            if model.real_trading <= model.paper_trading:
                raise ValueError('Real trading confidence threshold should be higher than paper trading')
        return model

class MarketScanConfiguration(BaseModel):
    """Configuration for market scanning and filtering criteria."""
    
    id: Optional[str] = Field(None, description="Unique identifier for this scan configuration")
    name: str = Field(..., description="Descriptive name for this scan configuration")
    description: Optional[str] = Field(None, description="Optional description")
    
    # Price Movement Filters
    min_price_change_24h_percent: Optional[float] = Field(
        None, 
        description="Minimum 24h price change percentage (e.g., 5.0 for 5%)"
    )
    max_price_change_24h_percent: Optional[float] = Field(
        None, 
        description="Maximum 24h price change percentage (e.g., 50.0 for 50%)"
    )
    min_price_change_7d_percent: Optional[float] = Field(
        None, 
        description="Minimum 7d price change percentage"
    )
    max_price_change_7d_percent: Optional[float] = Field(
        None, 
        description="Maximum 7d price change percentage"
    )
    
    # Volume Filters
    volume_filter_type: Optional[VolumeFilter] = Field(
        VolumeFilter.NO_FILTER, 
        description="Type of volume filter to apply"
    )
    min_volume_24h_usd: Optional[float] = Field(
        None, 
        gt=0, 
        description="Minimum 24h volume in USD"
    )
    min_volume_multiplier: Optional[float] = Field(
        None, 
        gt=0, 
        description="Minimum volume as multiplier of average (e.g., 2.0 for 2x average)"
    )
    
    # Market Cap Filters
    market_cap_ranges: Optional[List[MarketCapRange]] = Field(
        [MarketCapRange.ALL], 
        description="Market cap ranges to include"
    )
    min_market_cap_usd: Optional[float] = Field(
        None, 
        gt=0, 
        description="Minimum market cap in USD"
    )
    max_market_cap_usd: Optional[float] = Field(
        None, 
        gt=0, 
        description="Maximum market cap in USD"
    )
    
    # Liquidity and Trading Filters
    min_liquidity_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Minimum liquidity score (0-1)"
    )
    exclude_new_listings_days: Optional[int] = Field(
        None, 
        ge=0, 
        description="Exclude coins listed within X days"
    )
    
    # Technical Analysis Filters
    trend_direction: Optional[TrendDirection] = Field(
        TrendDirection.ANY, 
        description="Required trend direction"
    )
    min_rsi: Optional[float] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Minimum RSI value"
    )
    max_rsi: Optional[float] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Maximum RSI value"
    )
    
    # Exclusion Filters
    excluded_symbols: Optional[List[str]] = Field(
        None, 
        description="List of symbols to exclude from scan"
    )
    excluded_categories: Optional[List[str]] = Field(
        None, 
        description="List of categories to exclude (e.g., 'meme', 'stablecoin')"
    )
    
    # Quote Currency Filters
    allowed_quote_currencies: Optional[List[str]] = Field(
        ["USDT", "BUSD", "BTC", "ETH"], 
        description="Allowed quote currencies for trading pairs"
    )
    
    # Scan Settings
    max_results: Optional[int] = Field(
        50, 
        gt=0, 
        le=500, 
        description="Maximum number of results to return"
    )
    scan_interval_minutes: Optional[int] = Field(
        15, 
        gt=0, 
        description="Scan interval in minutes"
    )
    is_active: bool = Field(
        True, 
        description="Whether this scan configuration is active"
    )
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def max_price_change_should_be_higher_than_min(cls, model: 'MarketScanConfiguration') -> 'MarketScanConfiguration': # MODIFIED
        """Validate that max price change is higher than min."""
        if model.max_price_change_24h_percent is not None and \
           model.min_price_change_24h_percent is not None and \
           model.max_price_change_24h_percent <= model.min_price_change_24h_percent:
            raise ValueError('max_price_change_24h_percent should be higher than min_price_change_24h_percent')
        return model

    @model_validator(mode='after') # MODIFIED
    @classmethod # ADDED
    def max_rsi_should_be_higher_than_min(cls, model: 'MarketScanConfiguration') -> 'MarketScanConfiguration': # MODIFIED
        """Validate that max RSI is higher than min RSI."""
        if model.max_rsi is not None and \
           model.min_rsi is not None and \
           model.max_rsi <= model.min_rsi:
            raise ValueError('max_rsi should be higher than min_rsi')
        return model

class AssetTradingParameters(BaseModel):
    """Trading parameters specific to a particular asset or asset category."""
    
    id: str = Field(..., description="Unique identifier for this parameter set")
    name: str = Field(..., description="Descriptive name for this parameter set")
    
    # Asset Selection
    applies_to_symbols: Optional[List[str]] = Field(
        None, 
        description="Specific symbols this applies to (e.g., ['BTC', 'ETH'])"
    )
    applies_to_categories: Optional[List[str]] = Field(
        None, 
        description="Asset categories this applies to (e.g., ['defi', 'layer1'])"
    )
    applies_to_market_cap_range: Optional[MarketCapRange] = Field(
        None, 
        description="Market cap range this applies to"
    )
    
    # Trading Thresholds
    confidence_thresholds: Optional[ConfidenceThresholds] = Field(
        None, 
        description="Custom confidence thresholds for this asset group"
    )
    
    # Risk Management
    max_position_size_percent: Optional[float] = Field(
        None, 
        gt=0, 
        le=100, 
        description="Maximum position size as percentage of portfolio"
    )
    stop_loss_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        le=100, 
        description="Stop loss percentage for this asset"
    )
    take_profit_percentage: Optional[float] = Field(
        None, 
        gt=0, 
        description="Take profit percentage for this asset"
    )
    
    # Position Sizing
    dynamic_position_sizing: Optional[bool] = Field(
        False, 
        description="Whether to use dynamic position sizing based on volatility"
    )
    volatility_adjustment_factor: Optional[float] = Field(
        None, 
        gt=0, 
        le=2, 
        description="Factor to adjust position size based on volatility (0.5-2.0)"
    )
    
    # Trade Management
    allow_pyramiding: Optional[bool] = Field(
        False, 
        description="Whether to allow pyramiding (adding to winning positions)"
    )
    max_concurrent_positions: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum concurrent positions for this asset group"
    )
    min_time_between_trades_hours: Optional[int] = Field(
        None, 
        gt=0, 
        description="Minimum hours between trades for same asset"
    )
    
    # Execution Settings
    use_market_orders: Optional[bool] = Field(
        False, 
        description="Whether to use market orders instead of limit orders"
    )
    slippage_tolerance_percent: Optional[float] = Field(
        None, 
        gt=0, 
        le=5, 
        description="Maximum acceptable slippage percentage"
    )
    
    # Backtesting and Validation
    min_backtest_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Minimum required backtest score (0-1)"
    )
    require_forward_testing: Optional[bool] = Field(
        True, 
        description="Whether forward testing is required before real trading"
    )
    
    # Active Status
    is_active: bool = Field(
        True, 
        description="Whether these parameters are active"
    )
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ScanPreset(BaseModel):
    """Predefined market scan configuration for common scenarios."""
    
    id: str = Field(..., description="Unique identifier for this preset")
    name: str = Field(..., description="Name of the preset")
    description: str = Field(..., description="Description of what this preset does")
    category: str = Field(..., description="Category (e.g., 'momentum', 'breakout', 'value')")
    
    # Preset Configuration
    market_scan_configuration: MarketScanConfiguration = Field(
        ..., 
        description="The market scan configuration for this preset"
    )
    
    # Strategy Association
    recommended_strategies: Optional[List[str]] = Field(
        None, 
        description="List of strategy names that work well with this preset"
    )
    
    # Performance Tracking
    usage_count: Optional[int] = Field(
        0, 
        ge=0, 
        description="Number of times this preset has been used"
    )
    success_rate: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Historical success rate of this preset"
    )
    
    # Status
    is_system_preset: bool = Field(
        False, 
        description="Whether this is a system-provided preset (not user-created)"
    )
    is_active: bool = Field(
        True, 
        description="Whether this preset is active"
    )
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AlertConfiguration(BaseModel):
    """Configuration for price and market alerts."""
    
    id: str = Field(..., description="Unique identifier for this alert")
    name: str = Field(..., description="Name of the alert")
    symbol: str = Field(..., description="Trading symbol for the alert")
    
    # Alert Conditions
    alert_type: str = Field(
        ..., 
        description="Type of alert (price_above, price_below, volume_spike, etc.)"
    )
    threshold_value: float = Field(..., description="Threshold value for the alert")
    threshold_percentage: Optional[float] = Field(
        None, 
        description="Threshold as percentage change"
    )
    
    # Notification Settings
    notification_channels: List[NotificationChannel] = Field(
        [NotificationChannel.UI], 
        description="Channels to send notifications to"
    )
    repeat_interval_minutes: Optional[int] = Field(
        None, 
        gt=0, 
        description="Interval to repeat notifications (if still triggered)"
    )
    max_notifications: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum number of notifications to send"
    )
    
    # Status
    is_active: bool = Field(True, description="Whether this alert is active")
    triggered_count: Optional[int] = Field(0, ge=0, description="Number of times triggered")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger timestamp")
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PerformanceMetrics(BaseModel):
    """Performance tracking metrics."""
    
    # Period Tracking
    period_start: datetime = Field(..., description="Start of tracking period")
    period_end: Optional[datetime] = Field(None, description="End of tracking period")
    
    # Trading Performance
    total_trades: int = Field(0, ge=0, description="Total number of trades")
    winning_trades: int = Field(0, ge=0, description="Number of winning trades")
    losing_trades: int = Field(0, ge=0, description="Number of losing trades")
    
    # Financial Metrics
    total_pnl: float = Field(0.0, description="Total profit/loss")
    total_pnl_percentage: float = Field(0.0, description="Total P&L as percentage")
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    
    # Strategy Performance
    best_performing_strategy: Optional[str] = Field(None, description="Best performing strategy")
    worst_performing_strategy: Optional[str] = Field(None, description="Worst performing strategy")
    
    # Asset Performance
    best_performing_asset: Optional[str] = Field(None, description="Best performing asset")
    worst_performing_asset: Optional[str] = Field(None, description="Worst performing asset")

class AIStrategyConfiguration(BaseModel):
    """AI strategy configuration for Gemini analysis."""
    
    id: str = Field(..., description="Unique identifier for this AI configuration")
    name: str = Field(..., description="Descriptive name for this AI configuration")
    
    applies_to_strategies: Optional[List[str]] = Field(
        None, 
        description="Strategy names this configuration applies to"
    )
    applies_to_pairs: Optional[List[str]] = Field(
        None, 
        description="Trading pairs this configuration applies to"
    )
    
    gemini_prompt_template: Optional[str] = Field(
        None, 
        description="Template for Gemini prompts with placeholders like {strategy_type}, {strategy_params}, {opportunity_details}"
    )
    
    tools_available_to_gemini: Optional[List[str]] = Field(
        None, 
        description="List of LangChain tools this profile can use (e.g., 'MobulaChecker', 'BinanceMarketReader')"
    )
    
    output_parser_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Configuration for parsing Gemini responses (e.g., expected JSON structure)"
    )
    
    indicator_weights: Optional[Dict[str, float]] = Field(
        None, 
        description="Weighting of technical indicators (e.g., {'RSI': 0.7, 'MACD_Signal': 0.5})"
    )
    
    confidence_thresholds: Optional[ConfidenceThresholds] = Field(
        None, 
        description="Confidence thresholds specific to this AI configuration"
    )
    
    max_context_window_tokens: Optional[int] = Field(
        None, 
        gt=0, 
        description="Maximum tokens for context window in this strategy"
    )

class MCPServerPreference(BaseModel):
    """MCP server preference configuration."""
    
    id: str = Field(..., description="Unique identifier for the MCP server")
    type: str = Field(..., description="Type of MCP server (e.g., 'ccxt', 'web3', 'sentiment_analysis')")
    url: Optional[str] = Field(None, description="URL if configurable")
    api_key: Optional[str] = Field(None, description="API key if required (store securely)")
    is_enabled: Optional[bool] = Field(True, description="Whether this MCP is enabled")
    query_frequency_seconds: Optional[int] = Field(
        None, 
        gt=0, 
        description="Query frequency in seconds"
    )
    reliability_weight: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Reliability weight for AI consideration (0-1)"
    )
    custom_parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Custom parameters specific to this MCP"
    )

class DashboardLayoutProfile(BaseModel):
    """Dashboard layout profile configuration."""
    
    name: str = Field(..., description="Name of the layout profile")
    configuration: Dict[str, Any] = Field(..., description="Layout configuration data")

class CloudSyncPreferences(BaseModel):
    """Cloud synchronization preferences."""
    
    is_enabled: Optional[bool] = Field(False, description="Whether cloud sync is enabled")
    last_successful_sync: Optional[datetime] = Field(None, description="Last successful sync timestamp")

class PaperTradingAsset(BaseModel):
    """Represents a single asset holding in paper trading for persistence."""
    asset: str = Field(..., description="The asset symbol (e.g., 'BTC')")
    quantity: float = Field(..., description="The quantity of the asset held")
    entry_price: float = Field(..., description="The average entry price for this holding")

class UserConfiguration(BaseModel):
    """Main user configuration model."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    
    # --- Notification Preferences ---
    telegram_chat_id: Optional[str] = Field(
        None, 
        description="Telegram chat ID for notifications"
    )
    notification_preferences: Optional[List[NotificationPreference]] = Field(
        None, 
        description="List of notification preferences"
    )
    enable_telegram_notifications: Optional[bool] = Field(
        True, 
        description="Master switch for Telegram notifications"
    )
    
    # --- Trading Preferences ---
    default_paper_trading_capital: Optional[float] = Field(
        None, 
        gt=0, 
        description="Default capital for paper trading"
    )
    paper_trading_active: Optional[bool] = Field(
        False, 
        description="Whether paper trading is active"
    )
    paper_trading_assets: Optional[List[PaperTradingAsset]] = Field(
        None,
        description="List of asset holdings for paper trading."
    )
    
    watchlists: Optional[List[Watchlist]] = Field(
        None, 
        description="List of trading pair watchlists"
    )
    favorite_pairs: Optional[List[str]] = Field(
        None, 
        description="List of favorite trading pairs"
    )
    
    risk_profile: Optional[RiskProfile] = Field(
        RiskProfile.MODERATE, 
        description="General risk profile"
    )
    risk_profile_settings: Optional[RiskProfileSettings] = Field(
        None, 
        description="Custom risk profile settings"
    )
    real_trading_settings: Optional[RealTradingSettings] = Field(
        None, 
        description="Real trading mode settings"
    )
    
    # --- Advanced Market Configuration (NEW) ---
    market_scan_presets: Optional[List[ScanPreset]] = Field(
        None, 
        description="List of market scan presets for different scenarios"
    )
    active_market_scan_preset_id: Optional[str] = Field(
        None, 
        description="ID of currently active market scan preset"
    )
    custom_market_scan_configurations: Optional[List[MarketScanConfiguration]] = Field(
        None, 
        description="Custom market scan configurations created by user"
    )
    asset_trading_parameters: Optional[List[AssetTradingParameters]] = Field(
        None, 
        description="Asset-specific trading parameters and rules"
    )
    
    # --- Alert System (NEW) ---
    alert_configurations: Optional[List[AlertConfiguration]] = Field(
        None, 
        description="Price and market alert configurations"
    )
    
    # --- Performance Tracking (NEW) ---
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None, 
        description="Current performance tracking metrics"
    )
    performance_history: Optional[List[PerformanceMetrics]] = Field(
        None, 
        description="Historical performance metrics"
    )
    
    # --- AI and Analysis Preferences ---
    ai_strategy_configurations: Optional[List[AIStrategyConfiguration]] = Field(
        None, 
        description="List of AI strategy configurations for Gemini integration"
    )
    ai_analysis_confidence_thresholds: Optional[ConfidenceThresholds] = Field(
        None, 
        description="Global AI confidence thresholds (fallback)"
    )
    
    mcp_server_preferences: Optional[List[MCPServerPreference]] = Field(
        None, 
        description="MCP server preferences"
    )
    
    # --- UI Preferences ---
    selected_theme: Optional[Theme] = Field(
        Theme.DARK, 
        description="Selected UI theme"
    )
    
    dashboard_layout_profiles: Optional[Dict[str, DashboardLayoutProfile]] = Field(
        None, 
        description="Dashboard layout profiles"
    )
    active_dashboard_layout_profile_id: Optional[str] = Field(
        None, 
        description="Active dashboard layout profile ID"
    )
    dashboard_layout_config: Optional[Dict[str, Any]] = Field(
        None, 
        description="Current dashboard layout configuration"
    )
    
    # --- Persistence and Synchronization ---
    cloud_sync_preferences: Optional[CloudSyncPreferences] = Field(
        None, 
        description="Cloud synchronization preferences"
    )
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = { # MODIFIED
        "use_enum_values": True,
        "validate_assignment": True,
        "extra": "forbid",
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    @field_validator('ai_strategy_configurations') # MODIFIED
    @classmethod # ADDED
    def validate_unique_ai_config_ids(cls, v: Optional[List[AIStrategyConfiguration]]) -> Optional[List[AIStrategyConfiguration]]: # MODIFIED
        """Validate that AI configuration IDs are unique."""
        if v is None:
            return v
        
        ids = [config.id for config in v if config] # Added 'if config' for robustness
        if len(ids) != len(set(ids)):
            raise ValueError('AI strategy configuration IDs must be unique')
        return v

    @field_validator('watchlists') # MODIFIED
    @classmethod # ADDED
    def validate_unique_watchlist_ids(cls, v: Optional[List[Watchlist]]) -> Optional[List[Watchlist]]: # MODIFIED
        """Validate that watchlist IDs are unique."""
        if v is None:
            return v
        
        ids = [wl.id for wl in v if wl]
        if len(ids) != len(set(ids)):
            raise ValueError('Watchlist IDs must be unique')
        return v

    @field_validator('mcp_server_preferences') # MODIFIED
    @classmethod # ADDED
    def validate_unique_mcp_ids(cls, v: Optional[List[MCPServerPreference]]) -> Optional[List[MCPServerPreference]]: # MODIFIED
        """Validate that MCP server IDs are unique."""
        if v is None:
            return v
        
        ids = [mcp.id for mcp in v if mcp]
        if len(ids) != len(set(ids)):
            raise ValueError('MCP server IDs must be unique')
        return v

    @field_validator('market_scan_presets') # MODIFIED
    @classmethod # ADDED
    def validate_unique_scan_preset_ids(cls, v: Optional[List[ScanPreset]]) -> Optional[List[ScanPreset]]: # MODIFIED
        """Validate that scan preset IDs are unique."""
        if v is None:
            return v
        
        ids = [preset.id for preset in v if preset]
        if len(ids) != len(set(ids)):
            raise ValueError('Scan preset IDs must be unique')
        return v

    @field_validator('asset_trading_parameters') # MODIFIED
    @classmethod # ADDED
    def validate_unique_asset_trading_parameter_ids(cls, v: Optional[List[AssetTradingParameters]]) -> Optional[List[AssetTradingParameters]]: # MODIFIED
        """Validate that asset trading parameter IDs are unique."""
        if v is None:
            return v
        
        ids = [param.id for param in v if param]
        if len(ids) != len(set(ids)):
            raise ValueError('Asset trading parameter IDs must be unique')
        return v

    @field_validator('alert_configurations') # MODIFIED
    @classmethod # ADDED
    def validate_unique_alert_ids(cls, v: Optional[List[AlertConfiguration]]) -> Optional[List[AlertConfiguration]]: # MODIFIED
        """Validate that alert configuration IDs are unique."""
        if v is None:
            return v
        
        ids = [alert.id for alert in v if alert]
        if len(ids) != len(set(ids)):
            raise ValueError('Alert configuration IDs must be unique')
        return v

    def get_ai_configuration_by_id(self, config_id: str) -> Optional[AIStrategyConfiguration]:
        """Get AI strategy configuration by ID.
        
        Args:
            config_id: The configuration ID to search for.
            
        Returns:
            The AIStrategyConfiguration if found, None otherwise.
        """
        if not self.ai_strategy_configurations:
            return None
        
        for config in self.ai_strategy_configurations:
            if config.id == config_id:
                return config
        
        return None

    def get_scan_preset_by_id(self, preset_id: str) -> Optional[ScanPreset]:
        """Get scan preset by ID.
        
        Args:
            preset_id: The preset ID to search for.
            
        Returns:
            The ScanPreset if found, None otherwise.
        """
        if not self.market_scan_presets:
            return None
        
        for preset in self.market_scan_presets:
            if preset.id == preset_id:
                return preset
        
        return None

    def get_active_scan_preset(self) -> Optional[ScanPreset]:
        """Get the currently active scan preset.
        
        Returns:
            The active ScanPreset if set and found, None otherwise.
        """
        if not self.active_market_scan_preset_id:
            return None
        
        return self.get_scan_preset_by_id(self.active_market_scan_preset_id)

    def get_asset_trading_parameters_for_symbol(self, symbol: str) -> Optional[AssetTradingParameters]:
        """Get asset trading parameters for a specific symbol.
        
        Args:
            symbol: The trading symbol to get parameters for.
            
        Returns:
            The most specific AssetTradingParameters that applies to the symbol, None if none found.
        """
        if not self.asset_trading_parameters:
            return None
        
        # First, look for exact symbol match
        for params in self.asset_trading_parameters:
            if params.applies_to_symbols and symbol in params.applies_to_symbols:
                return params
        
        # Then, look for category or market cap range matches
        # This would require additional logic to determine symbol's category/market cap
        # For now, return None if no exact match
        return None

    def get_effective_confidence_thresholds(
        self, 
        symbol: Optional[str] = None,
        ai_config_id: Optional[str] = None
    ) -> Optional[ConfidenceThresholds]:
        """Get effective confidence thresholds with priority order.
        
        Priority order:
        1. Asset-specific thresholds (if symbol provided)
        2. AI config-specific thresholds (if ai_config_id provided)
        3. Global thresholds
        
        Args:
            symbol: Optional symbol to get asset-specific thresholds.
            ai_config_id: Optional AI configuration ID to get specific thresholds.
            
        Returns:
            The most specific confidence thresholds found.
        """
        # 1. Check asset-specific thresholds
        if symbol:
            asset_params = self.get_asset_trading_parameters_for_symbol(symbol)
            if asset_params and asset_params.confidence_thresholds:
                return asset_params.confidence_thresholds
        
        # 2. Check AI config-specific thresholds
        if ai_config_id:
            ai_config = self.get_ai_configuration_by_id(ai_config_id)
            if ai_config and ai_config.confidence_thresholds:
                return ai_config.confidence_thresholds
        
        # 3. Return global thresholds
        return self.ai_analysis_confidence_thresholds
