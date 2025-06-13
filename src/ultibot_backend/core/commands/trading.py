"""
Trading Commands Module.

This module defines the command models for trading operations, following the
CQRS pattern. These commands are simple, immutable data structures that
represent an intent to change the state of the system.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from ultibot_backend.core.domain_models.trading import OrderType, OrderSide

class PlaceOrderCommand(BaseModel):
    """Command to place a new trading order."""
    user_id: UUID
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None
    trading_mode: str

    class Config:
        frozen = True

class CancelOrderCommand(BaseModel):
    """Command to cancel an existing trading order."""
    user_id: UUID
    order_id: str

    class Config:
        frozen = True

class UpdatePortfolioCommand(BaseModel):
    """Command to request a portfolio update."""
    user_id: UUID
    trading_mode: str

    class Config:
        frozen = True
