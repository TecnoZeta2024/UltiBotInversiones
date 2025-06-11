"""Trade Domain Models.

This module defines the Pydantic models for trading operations and execution.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, ConfigDict


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

class OrderCategory(str, Enum):
    ENTRY = "entry"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP_LOSS = "trailing_stop_loss"
    MANUAL_CLOSE = "manual_close"
    OCO_ORDER = "oco_order"

class Commission(BaseModel):
    """Commission information for an order."""
    
    amount: float = Field(..., description="Commission amount")
    asset: str = Field(..., description="Commission asset")
    timestamp: Optional[datetime] = Field(None, description="Commission timestamp")


class TradeOrderDetails(BaseModel):
    """
    Detalles de una orden de trading ejecutada o simulada.
    """
    orderId_internal: UUID = Field(default_factory=uuid4, description="ID interno único de la orden.")
    orderId_exchange: Optional[str] = Field(None, description="ID de la orden en el exchange (si es una orden real).")
    clientOrderId_exchange: Optional[str] = Field(None, description="ID de cliente de la orden en el exchange (si es una orden real).")
    orderCategory: OrderCategory = Field(..., description="Categoría de la orden (ej. 'entry', 'take_profit', 'stop_loss').")
    type: str = Field(..., description="Tipo de orden (ej. 'market', 'limit', 'stop_loss_limit', 'take_profit_limit').")
    status: str = Field(..., description="Estado de la orden (ej. 'filled', 'partial_fill', 'new', 'canceled', 'rejected').")
    requestedPrice: Optional[float] = Field(None, description="Precio solicitado en la orden (para órdenes limitadas).")
    requestedQuantity: float = Field(..., description="Cantidad solicitada en la orden.")
    executedQuantity: float = Field(..., description="Cantidad ejecutada de la orden.")
    executedPrice: float = Field(..., description="Precio promedio de ejecución de la orden.")
    cumulativeQuoteQty: Optional[float] = Field(None, description="Cantidad total de la moneda de cotización ejecutada.")
    commissions: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de comisiones pagadas por la orden.")
    commission: Optional[float] = Field(None, description="Comisión pagada por la orden (campo legado, preferir 'commissions').")
    commissionAsset: Optional[str] = Field(None, description="Activo en el que se pagó la comisión (campo legado, preferir 'commissions').")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo de la ejecución/actualización de la orden.")
    submittedAt: Optional[datetime] = Field(None, description="Marca de tiempo de cuando la orden fue enviada al exchange.")
    fillTimestamp: Optional[datetime] = Field(None, description="Marca de tiempo de cuando la orden fue completamente llenada.")
    rawResponse: Optional[Dict[str, Any]] = Field(None, description="Respuesta cruda del exchange (para órdenes reales).")
    ocoOrderListId: Optional[str] = Field(None, description="ID de la lista de órdenes OCO a la que pertenece esta orden (si aplica).")


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
    
    decision_override_by_user: bool = Field(
        False, 
        description="Whether user overrode AI recommendation"
    )
    user_override_reason: Optional[str] = Field(
        None, 
        description="Reason for user override"
    )
    
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
    """
    Representa una operación de trading completa (entrada y salida).
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    
    mode: str = Field(..., description="Modo de trading: 'paper' o 'real'.")
    symbol: str = Field(..., description="Símbolo del par de trading (ej. 'BTCUSDT').")
    side: str = Field(..., description="Dirección de la operación: 'BUY' o 'SELL'.")
    
    entryOrder: TradeOrderDetails = Field(..., description="Detalles de la orden de entrada.")
    exitOrders: List[TradeOrderDetails] = Field(default_factory=list, description="Lista de órdenes de salida (ej. TSL, TP).")
    
    positionStatus: str = Field(..., description="Estado de la posición: 'open', 'closed', 'liquidated'.")
    
    strategyId: Optional[UUID] = Field(None, description="ID de la estrategia asociada a este trade.")
    opportunityId: Optional[UUID] = Field(None, description="ID de la oportunidad de trading que originó este trade.")
    aiAnalysisConfidence: Optional[float] = Field(None, description="Confianza de la IA en la oportunidad (si aplica).")
    
    pnl_usd: Optional[float] = Field(None, description="Ganancia o pérdida en USD (para posiciones cerradas).")
    pnl_percentage: Optional[float] = Field(None, description="Ganancia o pérdida en porcentaje (para posiciones cerradas).")
    closingReason: Optional[str] = Field(None, description="Razón del cierre de la posición (ej. 'TP_HIT', 'SL_HIT', 'MANUAL_CLOSE', 'OCO_TRIGGERED').")
    ocoOrderListId: Optional[str] = Field(None, description="ID de la lista de órdenes OCO asociada a este trade (si aplica).")

    takeProfitPrice: Optional[float] = Field(None, description="Precio objetivo para Take Profit.")
    trailingStopActivationPrice: Optional[float] = Field(None, description="Precio al que se activa el Trailing Stop.")
    trailingStopCallbackRate: Optional[float] = Field(None, description="Porcentaje de retroceso para el Trailing Stop (ej. 0.01 para 1%).")
    currentStopPrice_tsl: Optional[float] = Field(None, description="Precio actual del Trailing Stop Loss.")
    
    riskRewardAdjustments: List[Dict[str, Any]] = Field(default_factory=list, description="Historial de ajustes de TSL/TP.")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(None, description="Timestamp del cierre de la posición.")

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
