"""
Unit tests for the capital management aspects of the TradingEngine.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from uuid import uuid4

from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.domain_models.portfolio import Portfolio
from ultibot_backend.core.exceptions import InsufficientFundsError
from ultibot_backend.core.ports import (
    IOrderExecutionPort,
    IPersistencePort,
    ICredentialService,
    IMarketDataProvider,
    IAIOrchestrator  # Importar el puerto correcto
)
from ultibot_backend.core.domain_models.trading import Order, OrderSide, OrderType

@pytest.fixture
def mock_persistence_port():
    """Fixture for a mock persistence port."""
    port = AsyncMock(spec=IPersistencePort)
    port.get_portfolio = AsyncMock()
    port.save_portfolio = AsyncMock()
    return port

@pytest.fixture
def mock_ai_orchestrator():
    """Fixture for a mock AI orchestrator."""
    return AsyncMock(spec=IAIOrchestrator)

@pytest.fixture
def trading_engine_with_mocks(mock_persistence_port, mock_ai_orchestrator):
    """Fixture for a TradingEngine with mocked dependencies."""
    mock_order_execution_port = AsyncMock(spec=IOrderExecutionPort)
    mock_credential_service = AsyncMock(spec=ICredentialService)
    mock_market_data_provider = AsyncMock(spec=IMarketDataProvider)
    
    # Simular el objeto settings
    mock_settings = MagicMock()
    mock_settings.FIXED_USER_ID = "test_user"

    # Usar un mock para las settings dentro del módulo
    with pytest.MonkeyPatch.context() as m:
        m.setattr("ultibot_backend.services.trading_engine_service.settings", mock_settings)
        
        engine = TradingEngine(
            order_execution_port=mock_order_execution_port,
            persistence_port=mock_persistence_port,
            credential_service=mock_credential_service,
            market_data_provider=mock_market_data_provider,
            ai_orchestrator=mock_ai_orchestrator  # Usar el nuevo mock
        )
    return engine

@pytest.mark.asyncio
async def test_check_sufficient_funds_success(trading_engine_with_mocks, mock_persistence_port):
    """
    Verify that _check_sufficient_funds returns True when balance is adequate.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        id=uuid4(),
        user_id="test_user",
        mode="paper",
        cash_balance=Decimal("1000.0"),
        positions=[]
    )
    mock_persistence_port.get_portfolio.return_value = mock_portfolio
    
    order_value = Decimal("500.0") # 500 USDT order
    
    # Act
    has_sufficient_funds = await engine._check_sufficient_funds("test_user", "paper", order_value)
    
    # Assert
    assert has_sufficient_funds is True
    mock_persistence_port.get_portfolio.assert_awaited_once_with("test_user", "paper")

@pytest.mark.asyncio
async def test_check_sufficient_funds_failure(trading_engine_with_mocks, mock_persistence_port):
    """
    Verify that _check_sufficient_funds returns False when balance is insufficient.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        id=uuid4(),
        user_id="test_user",
        mode="paper",
        cash_balance=Decimal("499.0"),
        positions=[]
    )
    mock_persistence_port.get_portfolio.return_value = mock_portfolio
    
    order_value = Decimal("500.0") # 500 USDT order
    
    # Act
    has_sufficient_funds = await engine._check_sufficient_funds("test_user", "paper", order_value)
    
    # Assert
    assert has_sufficient_funds is False
    mock_persistence_port.get_portfolio.assert_awaited_once_with("test_user", "paper")

@pytest.mark.asyncio
async def test_execute_order_raises_insufficient_funds_error(trading_engine_with_mocks, mock_persistence_port):
    """
    Test that execute_order raises InsufficientFundsError if funds are not sufficient.
    """
    engine = trading_engine_with_mocks
    
    # Mock para _check_sufficient_funds para forzar el error
    engine._check_sufficient_funds = AsyncMock(return_value=False)
    
    # Act & Assert
    with pytest.raises(InsufficientFundsError, match="Insufficient funds for order value"):
        await engine.execute_order(
            user_id=uuid4(),
            trading_mode="paper",
            symbol="BTCUSDT",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=Decimal("0.1"),
            price=Decimal("5000") # Order value = 500
        )
    
    engine._check_sufficient_funds.assert_awaited_once()


@pytest.mark.asyncio
async def test_capital_allocation_per_trade(trading_engine_with_mocks, mock_persistence_port):
    """
    Test the logic for allocating a percentage of capital to a trade.
    """
    engine = trading_engine_with_mocks
    
    # Arrange
    mock_portfolio = Portfolio(
        id=uuid4(),
        user_id="test_user",
        mode="paper",
        cash_balance=Decimal("10000.0"),
        positions=[]
    )
    mock_persistence_port.get_portfolio.return_value = mock_portfolio
    
    risk_percentage = Decimal("0.02") # Allocate 2% of capital
    
    # Act
    allocated_capital = await engine.get_capital_for_trade("test_user", "paper", risk_percentage)
    
    # Assert
    # Expected: 10000 * 0.02 = 200
    assert allocated_capital == Decimal("200.0")
    mock_persistence_port.get_portfolio.assert_awaited_once_with("test_user", "paper")

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
