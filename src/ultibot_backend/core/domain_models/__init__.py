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
]
