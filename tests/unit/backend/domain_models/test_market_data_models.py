
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.ultibot_backend.core.domain_models.orm_models import MarketDataORM

# Test MarketDataORM Model
def test_market_data_orm_creation():
    market_data = MarketDataORM(
        id=uuid4(),
        symbol="BTC/USDT",
        timestamp=datetime.now(),
        open=Decimal("10000.00"),
        high=Decimal("10500.00"),
        low=Decimal("9800.00"),
        close=Decimal("10300.00"),
        volume=Decimal("100.00"),
    )
    assert isinstance(market_data.id, UUID)
    assert market_data.symbol == "BTC/USDT"
    assert isinstance(market_data.timestamp, datetime)
    assert market_data.open == Decimal("10000.00")
    assert market_data.high == Decimal("10500.00")
    assert market_data.low == Decimal("9800.00")
    assert market_data.close == Decimal("10300.00")
    assert market_data.volume == Decimal("100.00")

def test_market_data_orm_repr():
    timestamp = datetime.now()
    market_data = MarketDataORM(
        id=uuid4(),
        symbol="ETH/USDT",
        timestamp=timestamp,
        open=Decimal("2000.00"),
        high=Decimal("2100.00"),
        low=Decimal("1900.00"),
        close=Decimal("2050.00"),
        volume=Decimal("500.00"),
    )
    expected_repr = f"<MarketDataORM(symbol='ETH/USDT', timestamp='{timestamp}')>"
    assert repr(market_data) == expected_repr
