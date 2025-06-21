"""User Configuration Domain Models.

This module defines the Pydantic models for user configuration settings,
including AI strategy configurations for integration with Gemini analysis.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
import json

from pydantic import BaseModel, Field, field_validator, ValidationInfo


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
    daily_loss_limit_absolute: Optional[Decimal] = Field(
        None, 
        gt=Decimal(0), 
        description="Daily loss limit in quote currency"
    )
    daily_profit_target_absolute: Optional[Decimal] = Field(
        None, 
        gt=Decimal(0), 
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
    daily_capital_risked_usd: Optional[Decimal] = Field(
        Decimal("0.0"),
        ge=0, 
        description="Total capital risked in USD for the current day"
    )
    last_daily_reset: Optional[datetime] = Field(
        None, 
        description="Timestamp of the last daily capital reset"
    )


class ConfidenceThresholds(BaseModel):
    """AI confidence thresholds for different trading modes."""
    
    paper_trading: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Confidence threshold for paper trading"
    )
    real_trading: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Confidence threshold for real trading"
    )

    @field_validator('real_trading')
    @classmethod
    def real_trading_should_be_higher_than_paper(cls, v: float, info: ValidationInfo) -> float:
        """Validate that real trading threshold is higher than paper trading."""
        if v is not None and 'paper_trading' in info.data and info.data['paper_trading'] is not None:
            if v <= info.data['paper_trading']:
                raise ValueError('Real trading confidence threshold should be higher than paper trading')
        return v


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
    quantity: Decimal = Field(..., description="The quantity of the asset held")
    entry_price: Decimal = Field(..., description="The average entry price for this holding")


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
    default_paper_trading_capital: Optional[Decimal] = Field(
        None, 
        gt=Decimal(0), 
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

    class Config:
        """Pydantic model configuration."""
        
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @field_validator(
        'notification_preferences', 'paper_trading_assets', 'watchlists',
        'favorite_pairs', 'risk_profile_settings', 'real_trading_settings',
        'ai_strategy_configurations', 'ai_analysis_confidence_thresholds',
        'mcp_server_preferences', 'dashboard_layout_profiles',
        'dashboard_layout_config', 'cloud_sync_preferences',
        mode='before'
    )
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string")
        return v

    @field_validator('ai_strategy_configurations', 'watchlists', 'mcp_server_preferences', mode='after')
    @classmethod
    def validate_unique_ids(cls, v: List[Any], info: ValidationInfo) -> List[Any]:
        """Validate that IDs are unique within lists of objects."""
        if not v:
            return v
        
        ids = [item.id for item in v]
        if len(ids) != len(set(ids)):
            raise ValueError(f'{info.field_name} IDs must be unique')
        return v

    def get_ai_configuration_by_id(self, config_id: str) -> Optional[AIStrategyConfiguration]:
        """Get AI strategy configuration by ID.
        
        Args:
            config_id: The configuration ID to search for.
            
        Returns:
            The AIStrategyConfiguration if found, None otherwise.
        """
        # Acceder a través del alias si se usa, o directamente si Pydantic lo maneja
        if not self.ai_strategy_configurations:
            return None
        
        for config in self.ai_strategy_configurations:
            if config.id == config_id:
                return config
        
        return None

    def get_effective_confidence_thresholds(
        self, 
        ai_config_id: Optional[str] = None
    ) -> Optional[ConfidenceThresholds]:
        """Get effective confidence thresholds.
        
        Args:
            ai_config_id: Optional AI configuration ID to get specific thresholds.
            
        Returns:
            Confidence thresholds from AI config if provided and found,
            otherwise global thresholds.
        """
        if ai_config_id:
            ai_config = self.get_ai_configuration_by_id(ai_config_id)
            if ai_config and ai_config.confidence_thresholds:
                return ai_config.confidence_thresholds
        
        # Acceder a través del alias si se usa, o directamente si Pydantic lo maneja
        return self.ai_analysis_confidence_thresholds
