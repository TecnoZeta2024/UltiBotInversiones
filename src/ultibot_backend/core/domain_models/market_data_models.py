from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .base import Base

class MarketDataORM(Base):
    __tablename__ = 'market_data'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    high_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    low_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    change_24h: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)

    def __repr__(self):
        return f"<MarketDataORM(symbol='{self.symbol}', price='{self.price}', timestamp='{self.timestamp}')>"
