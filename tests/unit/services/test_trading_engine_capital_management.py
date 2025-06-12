"""
Unit tests for the capital management aspects of the TradingEngine.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal

from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.domain_models.portfolio import Portfolio
from ultibot_backend.core.domain_models.trading import Order
from ultibot_backend.core.exceptions import InsufficientFundsError

@pytest.fixture
def mock_portfolio_manager():
    """Fixture for a mock portfolio manager."""
    manager = MagicMock()
    manager.get_portfolio_snapshot = AsyncMock()
    return manager

@pytest.fixture
def trading_engine_with_mocks(mock_portfolio_manager):
    """Fixture for a TradingEngine with mocked dependencies."""
    # Mock other dependencies needed by TradingEngine
    mock_binance_adapter = AsyncMock()
    mock_event_broker = AsyncMock()
    
    engine = TradingEngine(
        binance_adapter=mock_binance_adapter,
        portfolio_manager=mock_portfolio_manager,
        event_broker=mock_event_broker
    )
    return engine

@pytest.mark.asyncio
async def test_check_sufficient_funds_success(trading_engine_with_mocks, mock_portfolio_manager):
    """
    Verify that check_sufficient_funds returns True when balance is adequate.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        user_id="test_user",
        trading_mode="paper",
        available_balance_usdt=Decimal("1000.0"),
        total_assets_value_usd=Decimal("0.0"),
        total_portfolio_value_usd=Decimal("1000.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio
    
    order_value = Decimal("500.0") # 500 USDT order
    
    # Act
    has_sufficient_funds = await engine._check_sufficient_funds("test_user", "paper", order_value)
    
    # Assert
    assert has_sufficient_funds is True
    mock_portfolio_manager.get_portfolio_snapshot.assert_awaited_once_with("test_user", "paper")

@pytest.mark.asyncio
async def test_check_sufficient_funds_failure(trading_engine_with_mocks, mock_portfolio_manager):
    """
    Verify that check_sufficient_funds returns False when balance is insufficient.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        user_id="test_user",
        trading_mode="paper",
        available_balance_usdt=Decimal("499.0"),
        total_assets_value_usd=Decimal("0.0"),
        total_portfolio_value_usd=Decimal("499.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio
    
    order_value = Decimal("500.0") # 500 USDT order
    
    # Act
    has_sufficient_funds = await engine._check_sufficient_funds("test_user", "paper", order_value)
    
    # Assert
    assert has_sufficient_funds is False
    mock_portfolio_manager.get_portfolio_snapshot.assert_awaited_once_with("test_user", "paper")

@pytest.mark.asyncio
async def test_execute_order_raises_insufficient_funds_error(trading_engine_with_mocks, mock_portfolio_manager):
    """
    Test that execute_order raises InsufficientFundsError if funds are not sufficient.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    # Patch the internal _check_sufficient_funds to return False
    engine._check_sufficient_funds = AsyncMock(return_value=False)
    
    # Act & Assert
    with pytest.raises(InsufficientFundsError, match="Insufficient funds for order value"):
        await engine.execute_order(
            user_id="test_user",
            trading_mode="paper",
            symbol="BTCUSDT",
            order_type="MARKET",
            side="BUY",
            quantity=Decimal("0.1"),
            price=Decimal("50000") # Order value = 5000
        )
    
    engine._check_sufficient_funds.assert_awaited_once()

@pytest.mark.asyncio
async def test_capital_allocation_per_trade(trading_engine_with_mocks, mock_portfolio_manager):
    """
    Test the logic for allocating a percentage of capital to a trade.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        user_id="test_user",
        trading_mode="paper",
        available_balance_usdt=Decimal("10000.0"),
        total_portfolio_value_usd=Decimal("10000.0"),
        assets=[]
    )
    mock_portfolio_manager.get_portfolio_snapshot.return_value = mock_portfolio
    
    risk_percentage = Decimal("0.02") # Allocate 2% of capital
    
    # Act
    allocated_capital = await engine.get_capital_for_trade("test_user", "paper", risk_percentage)
    
    # Assert
    # Expected: 10000 * 0.02 = 200
    assert allocated_capital == Decimal("200.0")
    mock_portfolio_manager.get_portfolio_snapshot.assert_awaited_once_with("test_user", "paper")

@pytest.mark.asyncio
async def test_calculate_order_quantity(trading_engine_with_mocks):
    """
    Test the calculation of order quantity based on allocated capital and price.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    capital_to_allocate = Decimal("200.0") # 200 USDT
    asset_price = Decimal("50000.0") # BTC price
    
    # Act
    quantity = engine._calculate_quantity(capital_to_allocate, asset_price)
    
    # Assert
    # Expected: 200 / 50000 = 0.004
    assert quantity == Decimal("0.004")
