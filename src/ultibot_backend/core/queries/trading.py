"""
Trading Queries Module.

This module defines the query models for trading operations, following the
CQRS pattern. These queries are simple, immutable data structures that
represent a request to retrieve data without changing the system state.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class GetPortfolioQuery(BaseModel):
    """Query to retrieve a user's portfolio."""
    user_id: UUID
    trading_mode: str

    class Config:
        frozen = True

class GetOrderHistoryQuery(BaseModel):
    """Query to retrieve a user's order history."""
    user_id: UUID
    limit: Optional[int] = Field(default=100, description="Maximum number of orders to retrieve")
    trading_mode: Optional[str] = Field(default=None, description="Filter by trading mode")

    class Config:
        frozen = True

class GetTradeDetailsQuery(BaseModel):
    """Query to retrieve details of a specific trade."""
    trade_id: UUID
    user_id: Optional[UUID] = Field(default=None, description="User ID for authorization check")

    class Config:
        frozen = True
