"""
Módulo que define el modelo de dominio puro para un Trade (operación de trading).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

class Trade(BaseModel):
    """Representa una operación de trading ejecutada."""
    id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    symbol: str
    trade_type: str # 'BUY' or 'SELL'
    quantity: Decimal
    price: Decimal
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    pnl: Optional[Decimal] = None # Profit and Loss, calculated upon closing a position
    status: str = "open" # 'open', 'closed'

    model_config = ConfigDict(frozen=True)
