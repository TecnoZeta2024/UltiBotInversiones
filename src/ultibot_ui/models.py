from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel

class AssetHolding(BaseModel):
    asset_id: str
    quantity: float
    average_purchase_price: Optional[float] = None
    current_value: Optional[float] = None

class PortfolioSnapshot(BaseModel):
    snapshot_id: UUID
    timestamp: datetime
    user_id: UUID
    holdings: List[AssetHolding]
    total_value: float
    cash_balance: float
    performance_metrics: Optional[Dict[str, Any]] = None

class TradeOrderDetails(BaseModel):
    order_id: UUID
    user_id: UUID
    asset_id: str
    order_type: str  # e.g., "buy", "sell"
    quantity: float
    price: Optional[float] = None  # For limit orders
    status: str  # e.g., "pending", "executed", "cancelled"
    timestamp: datetime
    exchange_order_id: Optional[str] = None

class Notification(BaseModel):
    notification_id: UUID
    user_id: UUID
    message: str
    timestamp: datetime
    read_status: bool = False
    type: str  # e.g., "alert", "trade_confirmation"

class Opportunity(BaseModel):
    opportunity_id: UUID
    asset_id: str
    type: str  # e.g., "arbitrage", "trend_following"
    details: Dict[str, Any]
    potential_profit: Optional[float] = None
    status: str  # e.g., "new", "analyzing", "acted_upon"
    timestamp: datetime

class Kline(BaseModel):
    timestamp: int  # Or datetime, depending on how it's represented
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketData(BaseModel):
    asset_id: str
    interval: str # e.g., "1m", "5m", "1h", "1d"
    klines: List[Kline]
