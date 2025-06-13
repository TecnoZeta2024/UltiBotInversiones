"""
Módulo que define el modelo de dominio puro para un Trade (operación de trading).
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

class OrderCategory(str, Enum):
    """Categoría de la orden (ej. entrada, salida, stop-loss)."""
    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    LIQUIDATION = "liquidation"
    ADJUSTMENT = "adjustment"

class TradeOrderDetails(BaseModel):
    """Detalles de una orden específica dentro de un trade."""
    orderId_internal: UUID = Field(default_factory=uuid4)
    clientOrderId_exchange: str
    symbol: str
    side: str
    type: str
    quantity: Decimal
    price: Decimal
    executedQty: Optional[Decimal] = None
    executedPrice: Optional[Decimal] = None
    status: str
    transactTime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    commission: Optional[Decimal] = None
    commissionAsset: Optional[str] = None
    isMaker: Optional[bool] = None
    fee: Optional[Decimal] = None
    feeAsset: Optional[str] = None
    orderCategory: OrderCategory

    model_config = ConfigDict(frozen=True)

class Trade(BaseModel):
    """Representa una operación de trading ejecutada."""
    id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    symbol: str
    trade_type: str # 'BUY' or 'SELL'
    quantity: Decimal
    price: Decimal
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pnl: Optional[Decimal] = None # Profit and Loss, calculated upon closing a position
    status: str = "open" # 'open', 'closed'
    entryOrder: Optional[TradeOrderDetails] = None
    exitOrders: Optional[list[TradeOrderDetails]] = None
    closingReason: Optional[str] = None
    pnl_percentage: Optional[Decimal] = None
    aiAnalysisConfidence: Optional[float] = None

    model_config = ConfigDict(frozen=True)
