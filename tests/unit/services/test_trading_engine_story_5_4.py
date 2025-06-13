"""
Tests unitarios para la HU 5.4: Integración del AI Orchestrator con el Trading Engine.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal

from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.ports import (
    IAIOrchestrator, IOrderExecutionPort, IPersistencePort, 
    ICredentialService, IMarketDataProvider
)
from ultibot_backend.core.domain_models.ai_models import TradingOpportunity, AIAnalysisResult, AIProcessingStage
from ultibot_backend.core.domain_models.trading import Order, OrderSide, OrderType
from ultibot_backend.app_config import settings

@pytest.fixture
def mock_order_execution_port() -> AsyncMock:
    return AsyncMock(spec=IOrderExecutionPort)

@pytest.fixture
def mock_persistence_port() -> AsyncMock:
    return AsyncMock(spec=IPersistencePort)

@pytest.fixture
def mock_credential_service() -> AsyncMock:
    return AsyncMock(spec=ICredentialService)

@pytest.fixture
def mock_market_data_provider() -> AsyncMock:
    mock = AsyncMock(spec=IMarketDataProvider)
    mock.get_latest_price.return_value = Decimal("50000.0")
    return mock

@pytest.fixture
def mock_ai_orchestrator() -> AsyncMock:
    """Mock del IAIOrchestrator port."""
    return AsyncMock(spec=IAIOrchestrator)

@pytest.fixture
def trading_engine(
    mock_order_execution_port: AsyncMock,
    mock_persistence_port: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_market_data_provider: AsyncMock,
    mock_ai_orchestrator: AsyncMock,
) -> TradingEngine:
    """
    Crea una instancia del TradingEngine con todas las dependencias mockeadas.
    """
    return TradingEngine(
        order_execution_port=mock_order_execution_port,
        persistence_port=mock_persistence_port,
        credential_service=mock_credential_service,
        market_data_provider=mock_market_data_provider,
        ai_orchestrator=mock_ai_orchestrator,
    )

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_buy_decision(
    trading_engine: TradingEngine,
    mock_ai_orchestrator: AsyncMock,
    mock_persistence_port: AsyncMock,
):
    """
    Verifica que el TradingEngine procesa una oportunidad, obtiene una
    decisión de COMPRA del AI Orchestrator y ejecuta la orden.
    """
    # 1. Oportunidad de trading
    opportunity = TradingOpportunity(
        opportunity_id=uuid4(),
        symbol="BTCUSDT", 
        strategy_id=uuid4(),
        confidence=Decimal("0.8"),
        data={}
    )
    user_id = uuid4()
    
    # 2. Mock de la decisión de la IA
    ai_decision = AIAnalysisResult(
        recommendation="BUY",
        confidence=0.95,
        reasoning="All indicators align for a strong buy.",
        request_id=opportunity.opportunity_id,
        stage=AIProcessingStage.COMPLETED,
        total_execution_time_ms=100
    )
    # This method doesn't exist on the orchestrator, the test is for the engine
    # The engine should call the orchestrator, so we mock the orchestrator's method
    # The orchestrator method is `analyze_opportunity`
    
    # The engine method `process_opportunity_with_ai_decision` will call the orchestrator
    # So we need to mock the orchestrator's `analyze_opportunity` method
    trading_engine.ai_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución de la orden (que es interna al engine)
    trading_engine.execute_order = AsyncMock(return_value=Order(id=uuid4(), order_id="order_123", status=OrderSide.BUY, symbol="BTCUSDT", type=OrderType.MARKET, side=OrderSide.BUY, quantity=Decimal("0.001"), price=Decimal("50000")))
    
    # 4. Ejecutar el método a probar
    await trading_engine.process_opportunity_with_ai_decision(opportunity, user_id)
    
    # 5. Verificaciones
    trading_engine.ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    trading_engine.execute_order.assert_awaited_once()
    call_args = trading_engine.execute_order.call_args
    assert call_args.kwargs["side"] == OrderSide.BUY
    assert call_args.kwargs["symbol"] == "BTCUSDT"
    mock_persistence_port.update_opportunity_analysis.assert_awaited_once()

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_hold_decision(
    trading_engine: TradingEngine,
    mock_ai_orchestrator: AsyncMock,
    mock_persistence_port: AsyncMock,
):
    """
    Verifica que el TradingEngine no ejecuta una orden si la IA
    recomienda MANTENER (HOLD).
    """
    # 1. Oportunidad
    opportunity = TradingOpportunity(
        opportunity_id=uuid4(),
        symbol="ETHUSDT", 
        strategy_id=uuid4(),
        confidence=Decimal("0.7"),
        data={}
    )
    user_id = uuid4()
    
    # 2. Mock de la decisión de la IA
    ai_decision = AIAnalysisResult(
        recommendation="HOLD",
        confidence=0.88,
        reasoning="Market is neutral, wait for a clearer signal.",
        request_id=opportunity.opportunity_id,
        stage=AIProcessingStage.COMPLETED,
        total_execution_time_ms=120
    )
    trading_engine.ai_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución (no debería ser llamado)
    trading_engine.execute_order = AsyncMock()
    
    # 4. Ejecutar
    await trading_engine.process_opportunity_with_ai_decision(opportunity, user_id)
    
    # 5. Verificaciones
    trading_engine.ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    trading_engine.execute_order.assert_not_awaited()
    mock_persistence_port.update_opportunity_analysis.assert_awaited_once()

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_low_confidence(
    trading_engine: TradingEngine,
    mock_ai_orchestrator: AsyncMock,
    mock_persistence_port: AsyncMock,
):
    """
    Verifica que no se ejecuta una orden si la confianza de la IA es baja,
    incluso si la recomendación es comprar o vender.
    """
    # 1. Oportunidad
    opportunity = TradingOpportunity(
        opportunity_id=uuid4(),
        symbol="XRPUSDT", 
        strategy_id=uuid4(),
        confidence=Decimal("0.9"),
        data={}
    )
    user_id = uuid4()
    
    # 2. Mock de la decisión de la IA (con baja confianza)
    ai_decision = AIAnalysisResult(
        recommendation="BUY",
        confidence=0.60, # Por debajo del umbral
        reasoning="Signal is weak, high risk.",
        request_id=opportunity.opportunity_id,
        stage=AIProcessingStage.COMPLETED,
        total_execution_time_ms=90
    )
    trading_engine.ai_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución (no debería ser llamado)
    trading_engine.execute_order = AsyncMock()
    
    # 4. Ejecutar
    await trading_engine.process_opportunity_with_ai_decision(opportunity, user_id)
    
    # 5. Verificaciones
    trading_engine.ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    trading_engine.execute_order.assert_not_awaited()
    mock_persistence_port.update_opportunity_analysis.assert_awaited_once()
