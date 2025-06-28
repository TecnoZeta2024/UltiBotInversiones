"""Request and Response models for Strategy API endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from core.domain_models.trading_strategy_models import (
    BaseStrategyType,
    TradingStrategyConfig,
    StrategySpecificParameters,
    ApplicabilityRules,
    RiskParametersOverride,
    PerformanceMetrics,
    MarketConditionFilter,
    ActivationSchedule,
    StrategyDependency,
    SharingMetadata,
)


class CreateTradingStrategyRequest(BaseModel):
    """Request model for creating a new trading strategy configuration."""
    
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
    parent_config_id: Optional[str] = Field(
        None, 
        description="Parent configuration ID for versioning"
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

    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        extra = "forbid"


class UpdateTradingStrategyRequest(BaseModel):
    """Request model for updating a trading strategy configuration."""
    
    config_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255, 
        description="Descriptive name for the strategy"
    )
    base_strategy_type: Optional[BaseStrategyType] = Field(
        None, 
        description="Base type of the trading strategy"
    )
    description: Optional[str] = Field(
        None, 
        description="Detailed description of the strategy"
    )
    is_active_paper_mode: Optional[bool] = Field(
        None, 
        description="Whether strategy is active in paper trading mode"
    )
    is_active_real_mode: Optional[bool] = Field(
        None, 
        description="Whether strategy is active in real trading mode"
    )
    parameters: Optional[StrategySpecificParameters] = Field(
        None, 
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

    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        extra = "forbid"


class TradingStrategyResponse(BaseModel):
    """Response model for trading strategy configuration."""
    
    id: str = Field(..., description="Unique strategy identifier")
    user_id: str = Field(..., description="User identifier")
    config_name: str = Field(..., description="Strategy name")
    base_strategy_type: BaseStrategyType = Field(..., description="Strategy type")
    description: Optional[str] = Field(None, description="Strategy description")
    is_active_paper_mode: bool = Field(..., description="Paper mode active status")
    is_active_real_mode: bool = Field(..., description="Real mode active status")
    parameters: StrategySpecificParameters = Field(..., description="Strategy parameters")
    applicability_rules: Optional[ApplicabilityRules] = Field(None, description="Applicability rules")
    ai_analysis_profile_id: Optional[str] = Field(None, description="AI analysis profile reference")
    risk_parameters_override: Optional[RiskParametersOverride] = Field(None, description="Risk overrides")
    version: int = Field(..., description="Strategy version")
    parent_config_id: Optional[str] = Field(None, description="Parent configuration ID")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    market_condition_filters: Optional[List[MarketConditionFilter]] = Field(None, description="Market filters")
    activation_schedule: Optional[ActivationSchedule] = Field(None, description="Activation schedule")
    depends_on_strategies: Optional[List[StrategyDependency]] = Field(None, description="Strategy dependencies")
    sharing_metadata: Optional[SharingMetadata] = Field(None, description="Sharing metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic model configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @classmethod
    def from_strategy_config(cls, strategy: TradingStrategyConfig) -> "TradingStrategyResponse":
        """Create response model from TradingStrategyConfig."""
        return cls(
            id=strategy.id,
            user_id=strategy.user_id,
            config_name=strategy.config_name,
            base_strategy_type=strategy.base_strategy_type,
            description=strategy.description,
            is_active_paper_mode=strategy.is_active_paper_mode,
            is_active_real_mode=strategy.is_active_real_mode,
            parameters=strategy.parameters,
            applicability_rules=strategy.applicability_rules,
            ai_analysis_profile_id=strategy.ai_analysis_profile_id,
            risk_parameters_override=strategy.risk_parameters_override,
            version=strategy.version,
            parent_config_id=strategy.parent_config_id,
            performance_metrics=strategy.performance_metrics,
            market_condition_filters=strategy.market_condition_filters,
            activation_schedule=strategy.activation_schedule,
            depends_on_strategies=strategy.depends_on_strategies,
            sharing_metadata=strategy.sharing_metadata,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at,
        )


class StrategyListResponse(BaseModel):
    """Response model for listing strategies."""
    
    strategies: List[TradingStrategyResponse] = Field(
        ..., 
        description="List of strategy configurations"
    )
    total_count: int = Field(..., description="Total number of strategies")


class ActivateStrategyRequest(BaseModel):
    """Request model for activating/deactivating a strategy."""
    
    mode: str = Field(
        ..., 
        description="Trading mode to activate/deactivate"
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Validate trading mode."""
        if v not in ['paper', 'real']:
            raise ValueError('Mode must be "paper" or "real"')
        return v


class StrategyActivationResponse(BaseModel):
    """Response model for strategy activation/deactivation."""
    
    strategy_id: str = Field(..., description="Strategy identifier")
    mode: str = Field(..., description="Trading mode")
    is_active: bool = Field(..., description="New activation status")
    message: str = Field(..., description="Operation result message")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Specific error code")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
