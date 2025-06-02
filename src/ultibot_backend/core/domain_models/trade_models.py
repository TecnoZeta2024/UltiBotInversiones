"""Trade Domain Models.

This module defines the Pydantic models for trading operations and execution.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class TradeSide(str, Enum):
    """Enumeration of trade sides."""
    
    BUY = "buy"
    SELL = "sell"


class TradeMode(str, Enum):
    """Enumeration of trade modes."""
    
    PAPER = "paper"
    REAL = "real"
    BACKTEST = "backtest"


class PositionStatus(str, Enum):
    """Enumeration of position status values."""
    
    PENDING_ENTRY_CONDITIONS = "pending_entry_conditions"
    OPENING = "opening"
    OPEN = "open"
    PARTIALLY_CLOSED = "partially_closed"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class OrderType(str, Enum):
    """Enumeration of order types."""
    
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP_LOSS = "trailing_stop_loss"
    MANUAL_CLOSE = "manual_close"
    OCO = "oco"
    CONDITIONAL_ENTRY = "conditional_entry"


class OrderStatus(str, Enum):
    """Enumeration of order status values."""
    
    NEW = "new"
    PENDING_SUBMIT = "pending_submit"
    SUBMITTED = "submitted"
    PENDING_OPEN = "pending_open"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    PENDING_CANCEL = "pending_cancel"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    TRIGGERED = "triggered"
    ERROR_SUBMISSION = "error_submission"


class Commission(BaseModel):
    """Commission information for an order."""
    
    amount: float = Field(..., description="Commission amount")
    asset: str = Field(..., description="Commission asset")
    timestamp: Optional[datetime] = Field(None, description="Commission timestamp")


class TradeOrderDetails(BaseModel):
    """Details of a trading order."""
    
    order_id_internal: str = Field(..., description="Internal order ID")
    order_id_exchange: Optional[str] = Field(None, description="Exchange order ID")
    client_order_id_exchange: Optional[str] = Field(None, description="Client order ID on exchange")
    
    type: OrderType = Field(..., description="Order type")
    status: OrderStatus = Field(..., description="Order status")
    exchange_status_raw: Optional[str] = Field(None, description="Raw exchange status")
    
    rejection_reason_code: Optional[str] = Field(None, description="Rejection reason code")
    rejection_reason_message: Optional[str] = Field(None, description="Rejection reason message")
    
    requested_price: Optional[float] = Field(None, gt=0, description="Requested price")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price")
    executed_price: Optional[float] = Field(None, gt=0, description="Average execution price")
    
    slippage_amount: Optional[float] = Field(None, description="Slippage amount")
    slippage_percentage: Optional[float] = Field(None, description="Slippage percentage")
    
    requested_quantity: float = Field(..., gt=0, description="Requested quantity")
    executed_quantity: Optional[float] = Field(None, ge=0, description="Executed quantity")
    cumulative_quote_qty: Optional[float] = Field(None, ge=0, description="Cumulative quote quantity")
    
    commissions: Optional[List[Commission]] = Field(None, description="Order commissions")
    
    timestamp: datetime = Field(..., description="Order creation timestamp")
    submitted_at: Optional[datetime] = Field(None, description="Order submission timestamp")
    last_update_timestamp: Optional[datetime] = Field(None, description="Last update timestamp")
    fill_timestamp: Optional[datetime] = Field(None, description="Order fill timestamp")
    
    # Trailing stop loss specific fields
    trailing_stop_activation_price: Optional[float] = Field(
        None, 
        description="Trailing stop activation price"
    )
    trailing_stop_callback_rate: Optional[float] = Field(
        None, 
        description="Trailing stop callback rate"
    )
    current_stop_price_tsl: Optional[float] = Field(
        None, 
        description="Current stop price for trailing stop"
    )
    
    # OCO specific fields
    oco_group_id_exchange: Optional[str] = Field(None, description="OCO group ID on exchange")


class RiskRewardAdjustment(BaseModel):
    """Risk/reward adjustment record."""
    
    timestamp: datetime = Field(..., description="Adjustment timestamp")
    new_stop_loss_price: Optional[float] = Field(None, description="New stop loss price")
    new_take_profit_price: Optional[float] = Field(None, description="New take profit price")
    updated_risk_quote_amount: Optional[float] = Field(
        None, 
        description="Updated risk amount in quote currency"
    )
    updated_reward_to_risk_ratio: Optional[float] = Field(
        None, 
        description="Updated reward to risk ratio"
    )
    reason: Optional[str] = Field(None, description="Reason for adjustment")


class ExternalEventLink(BaseModel):
    """Link to external event or analysis."""
    
    type: str = Field(..., description="Type of external event")
    reference_id: Optional[str] = Field(None, description="Reference ID")
    description: Optional[str] = Field(None, description="Event description")


class BacktestDetails(BaseModel):
    """Backtest specific details."""
    
    backtest_run_id: str = Field(..., description="Backtest run ID")
    iteration_id: Optional[str] = Field(None, description="Iteration ID")
    parameters_snapshot: Dict[str, Any] = Field(..., description="Parameters snapshot")


class AIInfluenceDetails(BaseModel):
    """Details about AI influence on a trade."""
    
    ai_analysis_profile_id: str = Field(..., description="AI analysis profile ID used")
    ai_confidence: float = Field(..., ge=0, le=1, description="AI confidence level")
    ai_suggested_action: str = Field(..., description="AI suggested action")
    ai_reasoning_summary: str = Field(..., description="Summary of AI reasoning")
    ai_model_used: Optional[str] = Field(None, description="AI model used")
    ai_analysis_timestamp: datetime = Field(..., description="When AI analysis was performed")
    ai_processing_time_ms: Optional[int] = Field(None, description="AI processing time")
    ai_warnings: Optional[List[str]] = Field(None, description="AI warnings")
    
    # Trade decision details
    decision_override_by_user: bool = Field(
        False, 
        description="Whether user overrode AI recommendation"
    )
    user_override_reason: Optional[str] = Field(
        None, 
        description="Reason for user override"
    )
    
    # Trade outcome vs AI prediction
    ai_prediction_accuracy: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Accuracy of AI prediction (populated after trade close)"
    )
    outcome_matches_ai_prediction: Optional[bool] = Field(
        None, 
        description="Whether final outcome matched AI prediction"
    )


class Trade(BaseModel):
    """Trading operation model."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    user_id: str = Field(..., description="User identifier")
    mode: TradeMode = Field(..., description="Trading mode")
    
    symbol: str = Field(..., description="Trading symbol")
    side: TradeSide = Field(..., description="Trade side")
    
    strategy_id: Optional[str] = Field(None, description="Strategy configuration ID")
    opportunity_id: Optional[str] = Field(None, description="Opportunity ID")
    ai_analysis_confidence: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="AI analysis confidence if used"
    )
    
    strategy_execution_instance_id: Optional[str] = Field(
        None, 
        description="Strategy execution instance ID for grouping trades"
    )
    
    position_status: PositionStatus = Field(..., description="Position status")
    
    entry_order: TradeOrderDetails = Field(..., description="Entry order details")
    exit_orders: Optional[List[TradeOrderDetails]] = Field(
        None, 
        description="Exit order details"
    )
    
    # Risk management
    initial_risk_quote_amount: Optional[float] = Field(
        None, 
        description="Initial risk amount in quote currency"
    )
    initial_reward_to_risk_ratio: Optional[float] = Field(
        None, 
        description="Initial reward to risk ratio"
    )
    risk_reward_adjustments: Optional[List[RiskRewardAdjustment]] = Field(
        None, 
        description="Risk/reward adjustments during trade"
    )
    current_risk_quote_amount: Optional[float] = Field(
        None, 
        description="Current risk amount"
    )
    current_reward_to_risk_ratio: Optional[float] = Field(
        None, 
        description="Current reward to risk ratio"
    )
    
    # P&L
    pnl: Optional[float] = Field(None, description="Realized P&L in quote currency")
    pnl_percentage: Optional[float] = Field(None, description="P&L percentage")
    closing_reason: Optional[str] = Field(None, description="Reason for closing")
    
    # Market context
    market_context_snapshots: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, 
        description="Market context at entry and exit"
    )
    external_event_or_analysis_link: Optional[ExternalEventLink] = Field(
        None, 
        description="Link to external event or analysis"
    )
    
    # Backtest specific
    backtest_details: Optional[BacktestDetails] = Field(
        None, 
        description="Backtest details if applicable"
    )
    
    # AI influence tracking
    ai_influence_details: Optional[AIInfluenceDetails] = Field(
        None, 
        description="Details about AI influence on this trade"
    )
    
    notes: Optional[str] = Field(None, description="Trade notes")
    
    created_at: Optional[datetime] = None
    opened_at: Optional[datetime] = Field(None, description="Position opened timestamp")
    closed_at: Optional[datetime] = Field(None, description="Position closed timestamp")
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic model configuration."""
        
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('exit_orders')
    def validate_exit_orders(cls, v):
        """Validate exit orders."""
        if v is not None and len(v) == 0:
            return None
        return v
    
    def is_ai_influenced(self) -> bool:
        """Check if this trade was influenced by AI."""
        return self.ai_influence_details is not None
    
    def get_ai_confidence(self) -> Optional[float]:
        """Get AI confidence if available."""
        if self.ai_influence_details:
            return self.ai_influence_details.ai_confidence
        return self.ai_analysis_confidence
    
    def add_ai_influence_details(
        self,
        ai_analysis_profile_id: str,
        ai_confidence: float,
        ai_suggested_action: str,
        ai_reasoning_summary: str,
        ai_model_used: Optional[str] = None,
        ai_processing_time_ms: Optional[int] = None,
        ai_warnings: Optional[List[str]] = None,
    ) -> None:
        """Add AI influence details to the trade.
        
        Args:
            ai_analysis_profile_id: AI analysis profile ID.
            ai_confidence: AI confidence level.
            ai_suggested_action: AI suggested action.
            ai_reasoning_summary: Summary of AI reasoning.
            ai_model_used: AI model used.
            ai_processing_time_ms: AI processing time.
            ai_warnings: AI warnings.
        """
        self.ai_influence_details = AIInfluenceDetails(
            ai_analysis_profile_id=ai_analysis_profile_id,
            ai_confidence=ai_confidence,
            ai_suggested_action=ai_suggested_action,
            ai_reasoning_summary=ai_reasoning_summary,
            ai_model_used=ai_model_used,
            ai_analysis_timestamp=datetime.now(),
            ai_processing_time_ms=ai_processing_time_ms,
            ai_warnings=ai_warnings,
        )
        
        # Also set the legacy field for compatibility
        self.ai_analysis_confidence = ai_confidence
    
    def mark_user_override(self, reason: str) -> None:
        """Mark that user overrode AI recommendation.
        
        Args:
            reason: Reason for override.
        """
        if self.ai_influence_details:
            self.ai_influence_details.decision_override_by_user = True
            self.ai_influence_details.user_override_reason = reason
    
    def update_ai_prediction_accuracy(
        self, 
        accuracy: float, 
        outcome_matches: bool
    ) -> None:
        """Update AI prediction accuracy after trade completion.
        
        Args:
            accuracy: Prediction accuracy (0-1).
            outcome_matches: Whether outcome matched AI prediction.
        """
        if self.ai_influence_details:
            self.ai_influence_details.ai_prediction_accuracy = accuracy
            self.ai_influence_details.outcome_matches_ai_prediction = outcome_matches
    
    def get_trade_summary_for_logging(self) -> str:
        """Get a concise trade summary for logging.
        
        Returns:
            Trade summary string.
        """
        ai_info = ""
        if self.is_ai_influenced():
            ai_confidence = self.get_ai_confidence()
            ai_profile = self.ai_influence_details.ai_analysis_profile_id
            ai_info = f" (AI: {ai_confidence:.2f} confidence, profile: {ai_profile})"
        
        return (
            f"Trade {self.id}: {self.side} {self.symbol} in {self.mode} mode, "
            f"strategy: {self.strategy_id}, status: {self.position_status}{ai_info}"
        )
