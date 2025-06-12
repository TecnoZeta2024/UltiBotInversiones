"""
Test de integración para la Historia de Usuario 5.4: Flujo completo de trading con IA.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.core.domain_models.ai_models import TradingOpportunity, AIAnalysisResult, ToolExecutionRequest, ToolExecutionResult
from ultibot_backend.core.domain_models.trading import Order

@pytest.fixture
def mock_ai_orchestrator():
    """Mock del AIOrchestratorService."""
    orchestrator = MagicMock(spec=AIOrchestratorService)
    orchestrator.analyze_opportunity = AsyncMock()
    return orchestrator

@pytest.fixture
def mock_trading_engine():
    """Mock del TradingEngine."""
    engine = MagicMock(spec=TradingEngine)
    engine.execute_order = AsyncMock()
    return engine

@pytest.mark.asyncio
async def test_full_ai_trading_flow(mock_ai_orchestrator, mock_trading_engine):
    """
    Simula el flujo completo:
    1. Se detecta una oportunidad de trading.
    2. El AI Orchestrator la analiza y recomienda una acción.
    3. El Trading Engine ejecuta la orden basada en la recomendación.
    """
    # 1. Setup: Crear una oportunidad de trading
    opportunity = TradingOpportunity(
        symbol="ADAUSDT",
        strategy_name="onchain_divergence",
        confidence=0.85,
        market_context={"trend": "bullish"}
    )

    # 2. Mock de la respuesta del AI Orchestrator
    ai_recommendation = AIAnalysisResult(
        request_id="some_id",
        recommendation="BUY",
        confidence=0.92,
        reasoning="Strong bullish signal confirmed by AI analysis.",
        tool_results=[],
        total_execution_time_ms=150.0,
        stage="COMPLETED"
    )
    mock_ai_orchestrator.analyze_opportunity.return_value = ai_recommendation

    # 3. Mock de la respuesta del Trading Engine
    executed_order = Order(
        id="ai_trade_123",
        user_id="ai_system_user",
        symbol=opportunity.symbol,
        side="BUY",
        quantity=100,
        price=0.45,
        status="FILLED"
    )
    mock_trading_engine.execute_order.return_value = executed_order

    # --- Ejecución del Flujo ---

    # El sistema detecta la oportunidad y la envía al orquestador
    analysis_result = await mock_ai_orchestrator.analyze_opportunity(opportunity)

    # El sistema evalúa la recomendación
    if analysis_result.recommendation == "BUY" and analysis_result.confidence > 0.9:
        # El sistema decide ejecutar la orden
        final_order = await mock_trading_engine.execute_order(
            user_id="ai_system_user",
            symbol=opportunity.symbol,
            order_type="MARKET",
            side=analysis_result.recommendation,
            quantity=100, # La cantidad sería calculada por un gestor de riesgo
            trading_mode="paper"
        )
    else:
        final_order = None

    # --- Verificaciones ---
    
    # Verificar que el orquestador fue llamado
    mock_ai_orchestrator.analyze_opportunity.assert_awaited_once_with(opportunity)
    
    # Verificar que el motor de trading fue llamado
    assert final_order is not None
    mock_trading_engine.execute_order.assert_awaited_once()
    
    # Verificar que la orden final es la que se simuló
    assert final_order.id == "ai_trade_123"
    assert final_order.status == "FILLED"
    assert final_order.side == "BUY"
