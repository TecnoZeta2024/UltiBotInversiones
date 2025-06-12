"""
Módulo que define los modelos de dominio puros relacionados con el portafolio de un usuario.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, NewType
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from src.ultibot_backend.core.domain_models.trading import TradingMode

UserId = NewType('UserId', UUID)

class Asset(BaseModel):
    """Representa un activo dentro del portafolio de un usuario."""
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Decimal
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

class Position(BaseModel):
    """Representa una posición en un activo específico dentro del portafolio."""
    asset: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal

    model_config = ConfigDict(frozen=True)

class PortfolioSnapshot(BaseModel):
    """Una instantánea del estado del portafolio en un momento dado."""
    snapshot_id: UUID = Field(default_factory=uuid4)
    portfolio_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_value_usd: Decimal
    positions: List[Position]
    cash_balance: Decimal

    model_config = ConfigDict(frozen=True)

class Portfolio(BaseModel):
    """Representa el portafolio de trading de un usuario."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UserId
    trading_mode: TradingMode
    positions: Dict[str, Position] = Field(default_factory=dict)
    total_value_usd: Decimal = Field(Decimal("0.0"))
    cash_balance: Decimal = Field(Decimal("10000.0")) # Default starting cash for paper trading
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
