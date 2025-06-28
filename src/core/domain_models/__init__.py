"""Domain Models Package.

This package contains all the Pydantic models for the domain entities
used throughout the UltiBotInversiones application.
"""

# Trading Strategy Models
from .trading_strategy_models import (
    BaseStrategyType,
    TradingStrategyConfig,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
    StrategySpecificParameters,
    ApplicabilityRules,
    DynamicFilter,
    RiskParametersOverride,
    PerformanceMetrics,
    MarketConditionFilter,
    ActivationSchedule,
    StrategyDependency,
    SharingMetadata,
)

# User Configuration Models
from .user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
    NotificationPreference,
    Watchlist,
    RiskProfileSettings,
    RealTradingSettings,
    MCPServerPreference,
    DashboardLayoutProfile,
    CloudSyncPreferences,
    NotificationChannel,
    RiskProfile,
    Theme,
)

# Opportunity and Trade Models
from .opportunity_models import (
    Opportunity,
    OpportunityStatus,
    SourceType,
    Direction,
    SuggestedAction,
    InitialSignal,
    AIAnalysis,
    DataVerification,
    RecommendedTradeParams,
    InvestigationDetails,
    UserFeedback,
    ExpirationLogic,
    PostTradeFeedback,
    PostFactoSimulationResults,
)

# Trade Models
from .trade_models import (
    Trade,
    TradeSide,
    TradeMode,
    PositionStatus,
    OrderType,
    OrderStatus,
    TradeOrderDetails,
    Commission,
    RiskRewardAdjustment,
    ExternalEventLink,
    BacktestDetails,
    AIInfluenceDetails,
)

__all__ = [
    # Trading Strategy Models
    "BaseStrategyType",
    "TradingStrategyConfig", 
    "ScalpingParameters",
    "DayTradingParameters",
    "ArbitrageSimpleParameters",
    "CustomAIDrivenParameters",
    "MCPSignalFollowerParameters",
    "GridTradingParameters", 
    "DCAInvestingParameters",
    "StrategySpecificParameters",
    "ApplicabilityRules",
    "DynamicFilter",
    "RiskParametersOverride",
    "PerformanceMetrics",
    "MarketConditionFilter",
    "ActivationSchedule",
    "StrategyDependency",
    "SharingMetadata",
    
    # User Configuration Models
    "UserConfiguration",
    "AIStrategyConfiguration",
    "ConfidenceThresholds",
    "NotificationPreference",
    "Watchlist", 
    "RiskProfileSettings",
    "RealTradingSettings",
    "MCPServerPreference",
    "DashboardLayoutProfile",
    "CloudSyncPreferences",
    "NotificationChannel",
    "RiskProfile",
    "Theme",
    
    # Opportunity Models
    "Opportunity",
    "OpportunityStatus",
    "SourceType",
    "Direction",
    "SuggestedAction",
    "InitialSignal",
    "AIAnalysis",
    "DataVerification",
    "RecommendedTradeParams",
    "InvestigationDetails",
    "UserFeedback",
    "ExpirationLogic",
    "PostTradeFeedback",
    "PostFactoSimulationResults",
    
    # Trade Models
    "Trade",
    "TradeSide",
    "TradeMode",
    "PositionStatus",
    "OrderType",
    "OrderStatus",
    "TradeOrderDetails",
    "Commission",
    "RiskRewardAdjustment",
    "ExternalEventLink",
    "BacktestDetails",
    "AIInfluenceDetails",
]
