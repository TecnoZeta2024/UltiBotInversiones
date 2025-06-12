"""
Tests unitarios para la HU 5.4: Integración del AI Orchestrator con el Trading Engine.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from ultibot_backend.core.domain_models.ai_models import TradingOpportunity, AIAnalysisResult
from ultibot_backend.core.domain_models.trading import Order

@pytest.fixture
def mock_ai_orchestrator():
    """Mock del AIOrchestratorService."""
    return MagicMock(spec=AIOrchestratorService)

@pytest.fixture
def trading_engine_for_ai_flow(mock_ai_orchestrator):
    """
    Crea una instancia del TradingEngine con un AIOrchestrator mockeado
    y otras dependencias necesarias.
    """
    mock_binance_adapter = AsyncMock()
    mock_portfolio_manager = AsyncMock()
    mock_event_broker = AsyncMock()
    
    engine = TradingEngine(
        binance_adapter=mock_binance_adapter,
        portfolio_manager=mock_portfolio_manager,
        event_broker=mock_event_broker
    )
    # Inyectar el orquestador mockeado
    engine.ai_orchestrator = mock_ai_orchestrator
    return engine, mock_ai_orchestrator

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_buy_decision(trading_engine_for_ai_flow):
    """
    Verifica que el TradingEngine procesa una oportunidad, obtiene una
    decisión de COMPRA del AI Orchestrator y ejecuta la orden.
    """
    engine, mock_orchestrator = trading_engine_for_ai_flow
    
    # 1. Oportunidad de trading
    opportunity = TradingOpportunity(symbol="BTCUSDT", strategy_name="test_strat", confidence=0.8)
    
    # 2. Mock de la decisión de la IA
    ai_decision = AIAnalysisResult(
        recommendation="BUY",
        confidence=0.95,
        reasoning="All indicators align for a strong buy.",
        request_id="req_1",
        stage="COMPLETED",
        total_execution_time_ms=100
    )
    mock_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución de la orden
    engine.execute_order = AsyncMock(return_value=Order(id="order_123", status="FILLED"))
    
    # 4. Ejecutar el método a probar
    await engine.process_opportunity_with_ai(opportunity)
    
    # 5. Verificaciones
    mock_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    engine.execute_order.assert_awaited_once()
    call_args = engine.execute_order.call_args
    assert call_args.kwargs["side"] == "BUY"
    assert call_args.kwargs["symbol"] == "BTCUSDT"

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_hold_decision(trading_engine_for_ai_flow):
    """
    Verifica que el TradingEngine no ejecuta una orden si la IA
    recomienda MANTENER (HOLD).
    """
    engine, mock_orchestrator = trading_engine_for_ai_flow
    
    # 1. Oportunidad
    opportunity = TradingOpportunity(symbol="ETHUSDT", strategy_name="test_strat", confidence=0.7)
    
    # 2. Mock de la decisión de la IA
    ai_decision = AIAnalysisResult(
        recommendation="HOLD",
        confidence=0.88,
        reasoning="Market is neutral, wait for a clearer signal.",
        request_id="req_2",
        stage="COMPLETED",
        total_execution_time_ms=120
    )
    mock_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución (no debería ser llamado)
    engine.execute_order = AsyncMock()
    
    # 4. Ejecutar
    await engine.process_opportunity_with_ai(opportunity)
    
    # 5. Verificaciones
    mock_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    engine.execute_order.assert_not_awaited()

@pytest.mark.asyncio
async def test_process_opportunity_with_ai_low_confidence(trading_engine_for_ai_flow):
    """
    Verifica que no se ejecuta una orden si la confianza de la IA es baja,
    incluso si la recomendación es comprar o vender.
    """
    engine, mock_orchestrator = trading_engine_for_ai_flow
    
    # 1. Oportunidad
    opportunity = TradingOpportunity(symbol="XRPUSDT", strategy_name="test_strat", confidence=0.9)
    
    # 2. Mock de la decisión de la IA (con baja confianza)
    ai_decision = AIAnalysisResult(
        recommendation="BUY",
        confidence=0.60, # Por debajo del umbral (asumido en 0.75 o similar)
        reasoning="Signal is weak, high risk.",
        request_id="req_3",
        stage="COMPLETED",
        total_execution_time_ms=90
    )
    mock_orchestrator.analyze_opportunity = AsyncMock(return_value=ai_decision)
    
    # 3. Mock de la ejecución (no debería ser llamado)
    engine.execute_order = AsyncMock()
    
    # 4. Ejecutar
    await engine.process_opportunity_with_ai(opportunity)
    
    # 5. Verificaciones
    mock_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    engine.execute_order.assert_not_awaited()
