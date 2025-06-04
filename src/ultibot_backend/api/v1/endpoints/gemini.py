from fastapi import APIRouter, HTTPException
from typing import List
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestrator, OpportunityData
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType
from src.ultibot_backend.core.domain_models.user_configuration_models import AIStrategyConfiguration, ConfidenceThresholds
from datetime import datetime, timezone
import threading

router = APIRouter()

# Simple in-memory cache for demo IA data (thread-safe)
_cache_lock = threading.Lock()
_cached_ia_data = None
_cached_ia_timestamp = None
_CACHE_TTL_SECONDS = 30  # Cache expiry (seconds)

@router.get("/gemini/opportunities", response_model=List[dict])
async def get_gemini_opportunities():
    """
    Devuelve oportunidades detectadas por la IA usando Gemini (mock/demo).
    Implementa caché en memoria para evitar reprocesar IA en cada request.
    """
    from time import time
    global _cached_ia_data, _cached_ia_timestamp
    now = time()
    with _cache_lock:
        if _cached_ia_data is not None and _cached_ia_timestamp is not None:
            if now - _cached_ia_timestamp < _CACHE_TTL_SECONDS:
                return _cached_ia_data
    orchestrator = AIOrchestrator()
    # Simulación: crear una oportunidad de ejemplo
    opportunity = OpportunityData(
        opportunity_id="demo-opp-1",
        symbol="BTC/USDT",
        initial_signal={"price": 30000, "volume": 1000},
        source_type="gemini_demo",
        source_name="Gemini",
        detected_at=datetime.now(timezone.utc),
    )
    strategy = TradingStrategyConfig(
        user_id="00000000-0000-0000-0000-000000000001",
        config_name="DemoScalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters={
            "window": 5,
            "risk": 0.02,
            "profit_target_percentage": 0.5,
            "stop_loss_percentage": 0.2
        },
    )
    ai_config = AIStrategyConfiguration(
        id="default-gemini",
        name="Default Gemini AI Config",
        gemini_prompt_template=None,
        tools_available_to_gemini=["MobulaChecker", "TechnicalIndicators"],
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.6, real_trading=0.8),
        max_context_window_tokens=4000,
    )
    # Ejecutar análisis mock (ahora async)
    analysis_result = await orchestrator._mock_gemini_analysis(
        analysis_id="mock-1",
        prompt="",
        opportunity=opportunity,
        strategy=strategy,
        ai_config=ai_config,
    )
    result = [analysis_result.__dict__]
    with _cache_lock:
        _cached_ia_data = result
        _cached_ia_timestamp = now
    return result
