"""Opportunity and Trade Domain Models.

This module defines the Pydantic models for trading opportunities and trades.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal # Importar Decimal

from pydantic import BaseModel, Field
try:
    from pydantic import field_validator  # Pydantic v2
except ImportError:
    from pydantic import validator as field_validator  # fallback para v1


class OpportunityStatus(str, Enum):
    """Enumeration of opportunity status values."""
    
    NEW = "new"
    PENDING_AI_ANALYSIS = "pending_ai_analysis"
    UNDER_AI_ANALYSIS = "under_ai_analysis"
    ANALYSIS_COMPLETE = "analysis_complete"
    REJECTED_BY_AI = "rejected_by_ai"
    REJECTED_BY_SYSTEM = "rejected_by_system"
    REJECTED_BY_USER = "rejected_by_user"
    UNDER_EVALUATION = "under_evaluation"
    PENDING_USER_CONFIRMATION_REAL = "pending_user_confirmation_real"
    CONVERTED_TO_TRADE_PAPER = "converted_to_trade_paper"
    CONVERTED_TO_TRADE_REAL = "converted_to_trade_real"
    CONFIRMED_BY_AI = "confirmed_by_ai"
    CONFIRMED_BY_AUTONOMOUS = "confirmed_by_autonomous"
    EXPIRED = "expired"
    ERROR_IN_PROCESSING = "error_in_processing"
    PENDING_FURTHER_INVESTIGATION = "pending_further_investigation"
    INVESTIGATION_COMPLETE = "investigation_complete"
    SIMULATED_POST_FACTO = "simulated_post_facto"


class SourceType(str, Enum):
    """Enumeration of opportunity source types."""
    
    MCP_SIGNAL = "mcp_signal"
    INTERNAL_INDICATOR_ALGO = "internal_indicator_algo"
    AI_SUGGESTION_PROACTIVE = "ai_suggestion_proactive"
    MANUAL_ENTRY = "manual_entry"
    USER_DEFINED_ALERT = "user_defined_alert"
    UNKNOWN = "unknown"


class Direction(str, Enum):
    """Enumeration of trading directions."""
    
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    HOLD = "hold"


class SuggestedAction(str, Enum):
    """Enumeration of AI suggested actions."""
    
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD_NEUTRAL = "hold_neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    FURTHER_INVESTIGATION_NEEDED = "further_investigation_needed"
    NO_CLEAR_OPPORTUNITY = "no_clear_opportunity"


class InitialSignal(BaseModel):
    """Initial signal data for an opportunity."""
    
    direction_sought: Optional[Direction] = Field(
        None, 
        description="Direction of the trading signal"
    )
    entry_price_target: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Target entry price"
    )
    stop_loss_target: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Target stop loss price"
    )
    take_profit_target: Optional[Union[Decimal, List[Decimal]]] = Field(
        None, 
        description="Target take profit price(s)"
    )
    timeframe: Optional[str] = Field(
        None, 
        description="Timeframe for the signal"
    )
    reasoning_source_structured: Optional[Dict[str, Any]] = Field(
        None, 
        description="Structured reasoning from signal source"
    )
    reasoning_source_text: Optional[str] = Field(
        None, 
        description="Text reasoning from signal source"
    )
    confidence_source: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Confidence from signal source"
    )

    @field_validator('take_profit_target')
    @classmethod
    def validate_take_profit_target(cls, v: Optional[Union[Decimal, List[Decimal]]]) -> Optional[Union[Decimal, List[Decimal]]]:
        """Validate take profit target format."""
        if v is None:
            return v
        if isinstance(v, (int, float, Decimal)):
            return [Decimal(str(v))]
        elif isinstance(v, list):
            return [Decimal(str(x)) for x in v if isinstance(x, (int, float, Decimal))]
        else:
            raise ValueError("Take profit target must be a number or list of numbers")


class DataVerification(BaseModel):
    """Data verification results from AI analysis."""
    
    mobula_check_status: Optional[str] = Field(
        None, 
        description="Status of Mobula data verification"
    )
    mobula_discrepancies: Optional[str] = Field(
        None, 
        description="Any discrepancies found in Mobula data"
    )
    binance_data_check_status: Optional[str] = Field(
        None, 
        description="Status of Binance data verification"
    )


class RecommendedTradeParams(BaseModel):
    """Recommended trade parameters from AI analysis."""
    
    entry_price: Optional[Decimal] = Field(None, gt=0, description="Recommended entry price")
    stop_loss_price: Optional[Decimal] = Field(None, gt=0, description="Recommended stop loss price")
    take_profit_levels: Optional[List[Decimal]] = Field(
        None, 
        description="Recommended take profit levels"
    )
    trade_size_percentage: Optional[Decimal] = Field(
        None, 
        gt=0, 
        le=1, 
        description="Recommended trade size as percentage of capital"
    )


class AIAnalysis(BaseModel):
    """AI analysis results for an opportunity."""
    
    analysis_id: Optional[str] = Field(None, description="Unique analysis identifier")
    analyzed_at: datetime = Field(..., description="When the analysis was performed")
    model_used: Optional[str] = Field(None, description="AI model used for analysis")
    
    calculated_confidence: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="AI calculated confidence (0-1)"
    )
    suggested_action: SuggestedAction = Field(
        ..., 
        description="AI suggested action"
    )
    
    recommended_trade_strategy_type: Optional[str] = Field(
        None, 
        description="Recommended trade strategy type"
    )
    recommended_trade_params: Optional[RecommendedTradeParams] = Field(
        None, 
        description="Recommended trade parameters"
    )
    
    reasoning_ai: str = Field(..., description="AI reasoning for the recommendation")
    
    data_verification: Optional[DataVerification] = Field(
        None, 
        description="Data verification results"
    )
    
    processing_time_ms: Optional[int] = Field(
        None, 
        gt=0, 
        description="Processing time in milliseconds"
    )
    ai_warnings: Optional[List[str]] = Field(
        None, 
        description="Warnings from AI analysis"
    )


class InvestigationNote(BaseModel):
    """Investigation note for an opportunity."""
    
    note: str = Field(..., description="Investigation note text")
    author: str = Field(..., description="Author of the note")
    timestamp: datetime = Field(..., description="When the note was created")


class InvestigationDetails(BaseModel):
    """Investigation details for an opportunity."""
    
    assigned_to: Optional[str] = Field(
        None, 
        description="Who the investigation is assigned to"
    )
    investigation_notes: Optional[List[InvestigationNote]] = Field(
        None, 
        description="Investigation notes"
    )
    next_steps: Optional[str] = Field(None, description="Next steps for investigation")
    status: Optional[str] = Field(None, description="Investigation status")


class UserFeedback(BaseModel):
    """User feedback for an opportunity."""
    
    action_taken: str = Field(..., description="Action taken by user")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    modification_notes: Optional[str] = Field(None, description="Modification notes")
    timestamp: datetime = Field(..., description="When feedback was provided")


class ExpirationLogic(BaseModel):
    """Expiration logic for an opportunity."""
    
    type: str = Field(..., description="Type of expiration logic")
    value: Optional[Union[str, int, float]] = Field(
        None, 
        description="Value for expiration logic"
    )


class PostTradeFeedback(BaseModel):
    """Post-trade feedback for an opportunity."""
    
    related_trade_ids: List[str] = Field(..., description="Related trade IDs")
    overall_outcome: Optional[str] = Field(None, description="Overall outcome")
    final_pnl_quote: Optional[float] = Field(None, description="Final P&L in quote currency")
    outcome_matches_ai_suggestion: Optional[bool] = Field(
        None, 
        description="Whether outcome matches AI suggestion"
    )
    ai_confidence_was_justified: Optional[bool] = Field(
        None, 
        description="Whether AI confidence was justified"
    )
    key_learnings_or_observations: Optional[str] = Field(
        None, 
        description="Key learnings or observations"
    )
    feedback_timestamp: datetime = Field(..., description="When feedback was provided")


class PostFactoSimulationResults(BaseModel):
    """Post-facto simulation results for an opportunity."""
    
    simulated_at: datetime = Field(..., description="When simulation was performed")
    parameters_used: Dict[str, Any] = Field(..., description="Parameters used in simulation")
    estimated_pnl: Optional[float] = Field(None, description="Estimated P&L")
    max_favorable_excursion: Optional[float] = Field(
        None, 
        description="Maximum favorable excursion"
    )
    max_adverse_excursion: Optional[float] = Field(
        None, 
        description="Maximum adverse excursion"
    )
    notes: Optional[str] = Field(None, description="Simulation notes")


from uuid import UUID

class Opportunity(BaseModel):
    """Trading opportunity model."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    strategy_id: Optional[UUID] = Field(None, description="ID of the strategy associated with this opportunity")
    exchange: Optional[str] = Field(None, description="Exchange where the opportunity was detected (e.g., 'BINANCE')") # Añadir este campo
    
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USDT')")
    detected_at: datetime = Field(..., description="When opportunity was detected")
    
    source_type: SourceType = Field(..., description="Type of opportunity source")
    source_name: Optional[str] = Field(None, description="Name of specific source")
    source_data: Optional[Dict[str, Any]] = Field(None, description="Source data")
    
    initial_signal: InitialSignal = Field(..., description="Initial signal data")
    
    system_calculated_priority_score: Optional[int] = Field(
        None, 
        ge=0, 
        le=100, 
        description="System calculated priority score (0-100)"
    )
    last_priority_calculation_at: Optional[datetime] = Field(
        None, 
        description="When priority was last calculated"
    )
    
    status: OpportunityStatus = Field(
        OpportunityStatus.NEW, 
        description="Current opportunity status"
    )
    status_reason_code: Optional[str] = Field(None, description="Status reason code")
    status_reason_text: Optional[str] = Field(None, description="Status reason text")
    
    ai_analysis: Optional[AIAnalysis] = Field(None, description="AI analysis results")
    
    investigation_details: Optional[InvestigationDetails] = Field(
        None, 
        description="Investigation details"
    )
    user_feedback: Optional[UserFeedback] = Field(None, description="User feedback")
    
    linked_trade_ids: Optional[List[str]] = Field(
        None, 
        description="IDs of trades generated from this opportunity"
    )
    
    expires_at: Optional[datetime] = Field(None, description="When opportunity expires")
    expiration_logic: Optional[ExpirationLogic] = Field(
        None, 
        description="Logic for opportunity expiration"
    )
    
    post_trade_feedback: Optional[PostTradeFeedback] = Field(
        None, 
        description="Feedback after trades complete"
    )
    post_facto_simulation_results: Optional[PostFactoSimulationResults] = Field(
        None, 
        description="Post-facto simulation results"
    )
    
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

    def is_ai_analysis_required(self) -> bool:
        """Check if AI analysis is required for this opportunity."""
        return self.status in [
            OpportunityStatus.PENDING_AI_ANALYSIS,
            OpportunityStatus.UNDER_AI_ANALYSIS,
        ]
    
    def is_ai_analysis_complete(self) -> bool:
        """Check if AI analysis is complete for this opportunity."""
        return self.ai_analysis is not None and self.status == OpportunityStatus.ANALYSIS_COMPLETE
    
    def get_effective_confidence(self) -> Optional[float]:
        """Get effective confidence from AI analysis or source."""
        if self.ai_analysis is not None and self.ai_analysis.calculated_confidence is not None:
            return self.ai_analysis.calculated_confidence
        elif self.initial_signal is not None and self.initial_signal.confidence_source is not None:
            return self.initial_signal.confidence_source
        return None
    
    def can_convert_to_trade(self, confidence_threshold: float = 0.6) -> bool:
        """Check if opportunity can be converted to trade based on confidence."""
        if not self.is_ai_analysis_complete():
            return False
        
        confidence = self.get_effective_confidence()
        if confidence is None:
            return False
        
        return confidence >= confidence_threshold
    
    def add_investigation_note(self, note: str, author: str) -> None:
        """Add an investigation note to the opportunity."""
        if not self.investigation_details:
            self.investigation_details = InvestigationDetails(assigned_to=None, investigation_notes=[], next_steps=None, status=None)
        
        if not self.investigation_details.investigation_notes:
            self.investigation_details.investigation_notes = []
        
        investigation_note = InvestigationNote(
            note=note,
            author=author,
            timestamp=datetime.now()
        )
        
        self.investigation_details.investigation_notes.append(investigation_note)

class AIAnalysisRequest(BaseModel):
    """Request model for AI analysis."""
    opportunities: List[Opportunity] = Field(..., description="List of opportunities for AI analysis")
    # Puedes añadir otros campos si el request de IA necesita más contexto, como user_id, etc.

class AIAnalysisResponse(BaseModel):
    """Response model for AI analysis."""
    opportunities: List[Opportunity] = Field(..., description="List of opportunities after AI analysis")
    message: Optional[str] = Field(None, description="Optional message about the analysis result")
    # Puedes añadir otros campos como un ID de transacción, estado de procesamiento, etc.
