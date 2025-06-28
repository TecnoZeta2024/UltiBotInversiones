import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone

from src.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
)
from src.core.domain_models.opportunity_models import (
    Opportunity,
    InitialSignal,
    SourceType,
    OpportunityStatus,
)
from src.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
    RiskProfileSettings,
)
from src.services.trading_engine_service import TradingEngine, TradingDecision
from src.services.ai_orchestrator_service import AIAnalysisResult, SuggestedAction

# Fixtures para configuración básica
@pytest.fixture
def mock_user_id():
    return uuid4()

@pytest.fixture
def mock_opportunity(mock_user_id):
    return Opportunity(
        id=uuid4(),
        user_id=mock_user_id,
        symbol="BTC/USDT",
        status=OpportunityStatus.DETECTED,
        source_type=SourceType.MANUAL_INPUT,
        initial_signal=InitialSignal(
            entry_price_target=Decimal("50000"),
            take_profit_target=[Decimal("51000")],
            stop_loss_target=[Decimal("49500")],
        ),
    )

@pytest.fixture
def mock_user_config(mock_user_id):
    return UserConfiguration(
        user_id=str(mock_user_id),
        paper_trading_active=True,
        risk_profile_settings=RiskProfileSettings(
            per_trade_capital_risk_percentage=Decimal("1.0"),
            daily_capital_risk_percentage=Decimal("5.0"),
        ),
        ai_strategy_configurations=[
            AIStrategyConfiguration(
                id="ai_profile_1",
                name="Default AI Profile",
                confidence_thresholds=ConfidenceThresholds(
                    paper_trading=0.7,
                    real_trading=0.85
                )
            )
        ]
    )

@pytest.fixture
def mock_services():
    """Crea mocks para todos los servicios dependientes del TradingEngine."""
    return {
        "persistence_service": AsyncMock(),
        "market_data_service": AsyncMock(),
        "unified_order_execution_service": AsyncMock(),
        "credential_service": AsyncMock(),
        "notification_service": AsyncMock(),
        "strategy_service": AsyncMock(),
        "configuration_service": AsyncMock(),
        "portfolio_service": AsyncMock(),
        "ai_orchestrator": AsyncMock(),
    }

@pytest.fixture
def trading_engine(mock_services):
    """Inicializa el TradingEngine con servicios mockeados."""
    return TradingEngine(**mock_services)

# Pruebas por tipo de estrategia
@pytest.mark.asyncio
async def test_process_opportunity_with_scalping_strategy_generates_buy_decision(
    trading_engine, mock_services, mock_opportunity, mock_user_config, mock_user_id
):
    """
    Verifica que el TradingEngine procesa una oportunidad con una estrategia de Scalping
    y genera una decisión de compra cuando el AI Orchestrator devuelve una señal fuerte.
    """
    # 1. Configuración del Test (Arrange)
    strategy_id = uuid4()
    scalping_strategy = TradingStrategyConfig(
        id=strategy_id,
        user_id=str(mock_user_id),
        config_name="Scalping BTC",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(timeframe="1m", profit_target_percentage=0.5, stop_loss_percentage=0.25),
        is_active_paper_mode=True,
        ai_analysis_profile_id="ai_profile_1",
    )

    # Mockear las llamadas a los servicios dependientes
    mock_services["configuration_service"].get_user_configuration.return_value = mock_user_config
    mock_services["strategy_service"].get_active_strategies.return_value = [scalping_strategy]
    mock_services["strategy_service"].is_strategy_applicable_to_symbol.return_value = True

    # Mockear la respuesta del AI Orchestrator para simular una señal de compra
    ai_result = AIAnalysisResult(
        analysis_id="test_analysis",
        calculated_confidence=0.95,
        suggested_action=SuggestedAction.STRONG_BUY,
        reasoning_ai="AI analysis indicates a strong upward trend.",
        recommended_trade_params={"entry_price": 50100}
    )
    # Patching the method inside the mocked object
    trading_engine.ai_orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock(return_value=ai_result)
    
    # 2. Ejecución (Act)
    decisions = await trading_engine.process_opportunity(mock_opportunity)

    # 3. Verificación (Assert)
    assert len(decisions) == 1
    decision = decisions[0]
    assert isinstance(decision, TradingDecision)
    assert decision.decision == "execute_trade"
    assert decision.confidence == 0.95
    assert decision.strategy_id == str(strategy_id)
    assert decision.ai_analysis_used is True
    assert decision.reasoning == "AI analysis indicates a strong upward trend."

    # Verificar que los mocks fueron llamados
    mock_services["configuration_service"].get_user_configuration.assert_called_once_with(str(mock_user_id))
    mock_services["strategy_service"].get_active_strategies.assert_called_once_with(str(mock_user_id), "paper")
    trading_engine.ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
