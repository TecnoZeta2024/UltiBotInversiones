from fastapi import APIRouter, HTTPException
from typing import List
from ultibot_backend.services.ai_orchestrator_service import AIOrchestrator, OpportunityData
from ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType
from ultibot_backend.core.domain_models.user_configuration_models import AIStrategyConfiguration, ConfidenceThresholds
from datetime import datetime, timezone
import threading
import logging

router = APIRouter()
# Usar el logger raíz directamente para asegurar que usa la configuración de main.py
logger = logging.getLogger() 
# El nivel del logger raíz ya está en INFO según main.py, así que setLevel aquí no es estrictamente necesario
# pero no hace daño y asegura la intención.
logger.setLevel(logging.INFO) 

# Simple in-memory cache for demo IA data (thread-safe)
_cache_lock = threading.Lock()
_cached_ia_data = None
_cached_ia_timestamp = None
_CACHE_TTL_SECONDS = 30  # Cache expiry (seconds)

@router.get("/gemini/opportunities", response_model=List[dict])
async def get_gemini_opportunities():
    logger.info("[TRACE] BACKEND: Solicitud GET a /gemini/opportunities recibida.")
    print("[TRACE] BACKEND: Solicitud GET a /gemini/opportunities recibida.")
    from time import time
    global _cached_ia_data, _cached_ia_timestamp
    now = time()
    with _cache_lock:
        if _cached_ia_data is not None and _cached_ia_timestamp is not None:
            if now - _cached_ia_timestamp < _CACHE_TTL_SECONDS:
                logger.info("[TRACE] BACKEND: Devolviendo oportunidades de IA desde la caché.")
                print("[TRACE] BACKEND: Devolviendo oportunidades de IA desde la caché.")
                return _cached_ia_data
    logger.info("[TRACE] BACKEND: Generando nuevas oportunidades de IA (caché expirada o vacía).")
    print("[TRACE] BACKEND: Generando nuevas oportunidades de IA (caché expirada o vacía).")
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
        id="demo-strategy-scalping-01", # Added ID
        user_id="00000000-0000-0000-0000-000000000001",
        config_name="DemoScalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="A demonstration scalping strategy for BTC/USDT.", # Added description
        is_active_paper_mode=True, # Explicitly set, though default is False
        is_active_real_mode=False, # Explicitly set
        parameters={
            "profit_target_percentage": 0.005, # Scalping params need to match ScalpingParameters model
            "stop_loss_percentage": 0.002,
            "max_holding_time_seconds": 300,
            "leverage": 10.0
        },
        applicability_rules=None, # Explicitly None
        ai_analysis_profile_id=None, # Explicitly None
        risk_parameters_override=None, # Explicitly None
        version=1, # Explicitly set, though default is 1
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=datetime.now(timezone.utc), # Add timestamps
        updated_at=datetime.now(timezone.utc)
    )
    ai_config = AIStrategyConfiguration(
        id="default-gemini",
        name="Default Gemini AI Config",
        gemini_prompt_template=None,
        tools_available_to_gemini=["MobulaChecker", "TechnicalIndicators"],
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.6, real_trading=0.8),
        max_context_window_tokens=4000,
        # Add missing optional fields for AIStrategyConfiguration
        applies_to_strategies=None,
        applies_to_pairs=None,
        output_parser_config=None,
        indicator_weights=None
    )
    # Ejecutar análisis mock (ahora async)
    analysis_result = await orchestrator._mock_gemini_analysis(
        analysis_id="mock-1",
        prompt="",
        opportunity=opportunity,
        strategy=strategy,
        ai_config=ai_config,
    )

    # Transformar el resultado para que coincida con lo que espera la UI
    # La UI espera claves como: symbol, side, entry_price, confidence_score, strategy_id, exchange, timestamp_utc
    transformed_result = {
        "id": opportunity.opportunity_id, # Usar el ID de la oportunidad
        "symbol": opportunity.symbol,
        "side": (analysis_result.suggested_action.upper() if analysis_result.suggested_action else "N/A"), # Mapear suggested_action
        "entry_price": (analysis_result.recommended_trade_params.get("entry_price") if analysis_result.recommended_trade_params and analysis_result.recommended_trade_params.get("entry_price") is not None else "N/A"),
        "confidence_score": (analysis_result.calculated_confidence if analysis_result.calculated_confidence is not None else 0.0),
        "strategy_id": (strategy.config_name if strategy.config_name else "N/A"), # Usar el nombre de la estrategia de ejemplo
        "exchange": "Binance (Demo)", # Valor de ejemplo
        "timestamp_utc": analysis_result.analyzed_at.isoformat(), # Usar analyzed_at
        # Incluir otros campos de analysis_result si son útiles para la UI o para depuración
        "raw_suggested_action": analysis_result.suggested_action,
        "reasoning": analysis_result.reasoning_ai,
        "raw_analysis_id": analysis_result.analysis_id
    }
    
    result = [transformed_result] # Devolver una lista con el diccionario transformado
    logger.info(f"Devolviendo oportunidades de IA: {result}") # Añadir log aquí

    with _cache_lock:
        _cached_ia_data = result
        _cached_ia_timestamp = now
    return result

