"""
Unit tests for the TradingEngine core functionalities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from decimal import Decimal

from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.domain_models.portfolio import Portfolio
from ultibot_backend.core.domain_models.trading import Order
from ultibot_backend.core.domain_models.events import OrderPlacedEvent
from ultibot_backend.core.exceptions import InsufficientFundsError

@pytest.fixture
def mock_binance_adapter():
    """Fixture for a mock Binance adapter."""
    adapter = MagicMock()
    adapter.execute_order = AsyncMock()
    adapter.cancel_order = AsyncMock()
    return adapter

@pytest.fixture
def mock_portfolio_manager():
    """Fixture for a mock portfolio manager."""
    manager = MagicMock()
    manager.get_portfolio_snapshot = AsyncMock()
    manager.update_portfolio_snapshot = AsyncMock()
    return manager

@pytest.fixture
def mock_event_broker():
    """Fixture for a mock event broker."""
    broker = MagicMock()
    broker.publish = AsyncMock()
    return broker

@pytest.fixture
def trading_engine(mock_binance_adapter, mock_portfolio_manager, mock_event_broker):
    """Fixture to create a TradingEngine instance with mocked dependencies."""
    return TradingEngine(
        binance_adapter=mock_binance_adapter,
        portfolio_manager=mock_portfolio_manager,
        event_broker=mock_event_broker
    )

@pytest.mark.asyncio
async def test_execute_market_order_paper_trading_success(
    trading_engine, mock_binance_adapter, mock_portfolio_manager, mock_event_broker
):
    """
    Test successful execution of a market order in paper trading mode.
    """
    # Arrange
    user_id = "test_user_paper"
    symbol = "BTCUSDT"
    quantity = Decimal("0.01")
    price = Decimal("50000")
    order_value = quantity * price

    mock_portfolio = Portfolio(
        user_id=user_id,
        trading_mode="paper",
        available_balance_usdt=Decimal("10000.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio

    expected_order = Order(
        id="paper_order_1",
        user_id=user_id,
        symbol=symbol,
        order_type="MARKET",
        side="BUY",
        quantity=quantity,
        price=price,
        status="FILLED",
        trading_mode="paper"
    )
    # In paper mode, the engine itself generates the order result
    
    # Act
    result_order = await trading_engine.execute_order(
        user_id=user_id,
        symbol=symbol,
        order_type="MARKET",
        side="BUY",
        quantity=quantity,
        price=price,
        trading_mode="paper"
    )

    # Assert
    assert result_order.status == "FILLED"
    assert result_order.trading_mode == "paper"
    mock_portfolio_manager.get_portfolio_snapshot.assert_awaited_once_with(user_id, "paper")
    mock_portfolio_manager.update_portfolio_snapshot.assert_awaited_once()
    
    # Verify event publication
    mock_event_broker.publish.assert_awaited_once()
    published_event = mock_event_broker.publish.call_args[0][0]
    assert isinstance(published_event, OrderPlacedEvent)
    assert published_event.order_id == result_order.id

@pytest.mark.asyncio
async def test_execute_market_order_real_trading_success(
    trading_engine, mock_binance_adapter, mock_portfolio_manager, mock_event_broker
):
    """
    Test successful execution of a market order in real trading mode.
    """
    # Arrange
    user_id = "test_user_real"
    symbol = "ETHUSDT"
    quantity = Decimal("0.5")
    price = Decimal("3000")
    api_key = "test_key"
    api_secret = "test_secret"

    mock_portfolio = Portfolio(
        user_id=user_id,
        trading_mode="real",
        available_balance_usdt=Decimal("2000.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio

    expected_order_from_adapter = Order(
        id="real_order_2",
        user_id=user_id,
        symbol=symbol,
        order_type="MARKET",
        side="BUY",
        quantity=quantity,
        price=price,
        status="FILLED",
        trading_mode="real"
    )
    mock_binance_adapter.execute_order.return_value = expected_order_from_adapter

    # Act
    result_order = await trading_engine.execute_order(
        user_id=user_id,
        symbol=symbol,
        order_type="MARKET",
        side="BUY",
        quantity=quantity,
        price=price,
        trading_mode="real",
        api_key=api_key,
        api_secret=api_secret
    )

    # Assert
    assert result_order == expected_order_from_adapter
    mock_binance_adapter.execute_order.assert_awaited_once_with(
        symbol=symbol,
        order_type="MARKET",
        side="BUY",
        quantity=quantity,
        price=price,
        api_key=api_key,
        api_secret=api_secret
    )
    mock_portfolio_manager.update_portfolio_snapshot.assert_awaited_once()
    mock_event_broker.publish.assert_awaited_once()

@pytest.mark.asyncio
async def test_execute_order_insufficient_funds(trading_engine, mock_portfolio_manager):
    """
    Test that executing an order with insufficient funds raises an error.
    """
    # Arrange
    user_id = "test_user_poor"
    mock_portfolio = Portfolio(
        user_id=user_id,
        trading_mode="paper",
        available_balance_usdt=Decimal("100.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio

    # Act & Assert
    with pytest.raises(InsufficientFundsError):
        await trading_engine.execute_order(
            user_id=user_id,
            symbol="BTCUSDT",
            order_type="MARKET",
            side="BUY",
            quantity=Decimal("0.01"),
            price=Decimal("50000"), # Order value: 500
            trading_mode="paper"
        )

@pytest.mark.asyncio
async def test_cancel_order_success(trading_engine, mock_binance_adapter, mock_event_broker):
    """
    Test successful cancellation of an order.
    """
    # Arrange
    user_id = "test_user_cancel"
    order_id = "order_to_cancel"
    api_key = "key"
    api_secret = "secret"
    
    mock_binance_adapter.cancel_order.return_value = True

    # Act
    result = await trading_engine.cancel_order(
        user_id=user_id,
        order_id=order_id,
        api_key=api_key,
        api_secret=api_secret
    )

    # Assert
    assert result is True
    mock_binance_adapter.cancel_order.assert_awaited_once_with(
        order_id=order_id, api_key=api_key, api_secret=api_secret
    )
    mock_event_broker.publish.assert_awaited_once()

@pytest.mark.asyncio
async def test_real_mode_requires_credentials(trading_engine):
    """
    Test that real mode operations fail without API credentials.
    """
    with pytest.raises(ValueError, match="API key and secret are required for real trading mode"):
        await trading_engine.execute_order(
            user_id="user",
            symbol="BTCUSDT",
            order_type="MARKET",
            side="BUY",
            quantity=Decimal("1"),
            price=Decimal("1"),
            trading_mode="real" # Missing credentials
        )
