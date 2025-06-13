"""
Unit tests for the TradingEngine core functionalities.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
import uuid
from uuid import uuid4

from ultibot_backend.services.trading_engine_service import TradingEngine, AIAnalysisResult
from ultibot_backend.core.domain_models.portfolio import Portfolio
from ultibot_backend.core.domain_models.trading import Order, OrderSide, OrderType, OrderStatus, Trade
from ultibot_backend.core.domain_models.ai_models import TradingOpportunity
from ultibot_backend.core.exceptions import InsufficientFundsError
from ultibot_backend.core.ports import (
    IOrderExecutionPort,
    IPersistencePort,
    ICredentialService,
    IMarketDataProvider,
    IAIOrchestrator
)

@pytest.fixture
def mock_order_execution_port():
    """Fixture for a mock order execution port."""
    port = AsyncMock(spec=IOrderExecutionPort)
    port.execute_order = AsyncMock()
    port.cancel_order = AsyncMock()
    return port

@pytest.fixture
def mock_persistence_port():
    """Fixture for a mock persistence port."""
    port = AsyncMock(spec=IPersistencePort)
    port.get_portfolio = AsyncMock()
    port.save_portfolio = AsyncMock()
    port.update_opportunity_analysis = AsyncMock()
    port.upsert_trade = AsyncMock()
    return port

@pytest.fixture
def mock_credential_service():
    """Fixture for a mock credential service."""
    service = AsyncMock(spec=ICredentialService)
    service.get_first_decrypted_credential_by_service = AsyncMock(return_value={"api_key": "test_key", "api_secret": "test_secret"})
    return service

@pytest.fixture
def mock_market_data_provider():
    """Fixture for a mock market data provider."""
    provider = AsyncMock(spec=IMarketDataProvider)
    provider.get_latest_price = AsyncMock(return_value=Decimal("50000.0"))
    return provider

@pytest.fixture
def mock_ai_orchestrator():
    """Fixture for a mock AI orchestrator."""
    orchestrator = AsyncMock(spec=IAIOrchestrator)
    orchestrator.analyze_opportunity = AsyncMock()
    return orchestrator

@pytest.fixture
def trading_engine(
    mock_order_execution_port,
    mock_persistence_port,
    mock_credential_service,
    mock_market_data_provider,
    mock_ai_orchestrator,
):
    """Fixture to create a TradingEngine instance with mocked dependencies."""
    with pytest.MonkeyPatch.context() as m:
        mock_settings = MagicMock()
        mock_settings.FIXED_USER_ID = "test_user"
        mock_settings.DEFAULT_REAL_TRADING_EXCHANGE = "binance"
        mock_settings.AI_TRADING_CONFIDENCE_THRESHOLD = 0.75
        m.setattr("ultibot_backend.services.trading_engine_service.settings", mock_settings)
        
        engine = TradingEngine(
            order_execution_port=mock_order_execution_port,
            persistence_port=mock_persistence_port,
            credential_service=mock_credential_service,
            market_data_provider=mock_market_data_provider,
            ai_orchestrator=mock_ai_orchestrator,
        )
    return engine

@pytest.mark.asyncio
async def test_execute_paper_order_success(
    trading_engine, mock_persistence_port, mock_market_data_provider
):
    """
    Test successful execution of a market order in paper trading mode.
    """
    # Arrange
    user_id = uuid4()
    symbol = "BTCUSDT"
    quantity = Decimal("0.01")
    
    mock_market_data_provider.get_latest_price.return_value = Decimal("50000")

    # Act
    result_order = await trading_engine.execute_order(
        user_id=user_id,
        symbol=symbol,
        order_type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=quantity,
        price=None,
        trading_mode="paper"
    )

    # Assert
    assert result_order.status == OrderStatus.FILLED
    assert result_order.side == OrderSide.BUY
    mock_persistence_port.upsert_trade.assert_awaited_once()

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_buy_decision(
    trading_engine, mock_ai_orchestrator, mock_persistence_port
):
    """
    Test processing a trading opportunity where the AI decides to buy.
    """
    # Arrange
    user_id = uuid4()
    opportunity = TradingOpportunity(
        opportunity_id=uuid4(),
        symbol="BTCUSDT",
        signal_strength=0.9,
        detected_at="2025-01-01T12:00:00Z",
        strategy_id="test_strategy",
        details={"price": "50000"}
    )
    
    ai_result = AIAnalysisResult(
        recommendation="BUY",
        confidence=0.8,
        reasoning="Strong bullish signals.",
        trade_executed=False
    )
    mock_ai_orchestrator.analyze_opportunity.return_value = ai_result
    
    # Mock la ejecución de la orden para que devuelva una orden válida
    trading_engine.execute_order = AsyncMock(return_value=Order(
        id=uuid4(),
        symbol="BTCUSDT",
        type=OrderType.MARKET,
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
        status=OrderStatus.FILLED
    ))

    # Act
    final_result = await trading_engine.process_opportunity_with_ai_decision(opportunity, user_id)

    # Assert
    mock_ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    trading_engine.execute_order.assert_awaited_once()
    mock_persistence_port.update_opportunity_analysis.assert_awaited_once()
    assert final_result.trade_executed is True
    assert final_result.recommendation == "BUY"

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_hold_decision(
    trading_engine, mock_ai_orchestrator, mock_persistence_port
):
    """
    Test processing a trading opportunity where the AI decides to hold.
    """
    # Arrange
    user_id = uuid4()
    opportunity = TradingOpportunity(
        opportunity_id=uuid4(),
        symbol="ETHUSDT",
        signal_strength=0.6,
        detected_at="2025-01-01T13:00:00Z",
        strategy_id="test_strategy",
        details={"price": "3000"}
    )
    
    ai_result = AIAnalysisResult(
        recommendation="HOLD",
        confidence=0.6,
        reasoning="Neutral market signals.",
        trade_executed=False
    )
    mock_ai_orchestrator.analyze_opportunity.return_value = ai_result
    trading_engine.execute_order = AsyncMock()

    # Act
    final_result = await trading_engine.process_opportunity_with_ai_decision(opportunity, user_id)

    # Assert
    mock_ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    trading_engine.execute_order.assert_not_awaited()
    mock_persistence_port.update_opportunity_analysis.assert_awaited_once()
    assert final_result.trade_executed is False
    assert final_result.recommendation == "HOLD"
