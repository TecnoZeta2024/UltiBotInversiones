"""
Endpoint de demostración para obtener oportunidades de trading analizadas por IA.
"""
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from src.ultibot_backend.core.ports import IAIOrchestrator
from src.ultibot_backend.dependencies import get_ai_orchestrator_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Caché simple en memoria para datos de demostración (no thread-safe para producción)
_cached_ia_data: List[Dict[str, Any]] = []
_cached_ia_timestamp: float = 0.0
_CACHE_TTL_SECONDS = 30  # Tiempo de vida de la caché en segundos

@router.get("/gemini/opportunities", response_model=List[Dict[str, Any]])
async def get_gemini_opportunities(
    ai_service: IAIOrchestrator = Depends(get_ai_orchestrator_service),
):
    """
    Proporciona una lista de oportunidades de trading simuladas y analizadas por el servicio de IA.
    Este endpoint es para fines de demostración y pruebas de la UI.
    Utiliza una caché simple para no sobrecargar el servicio de IA con solicitudes idénticas.
    """
    logger.info("Solicitud GET a /gemini/opportunities recibida.")
    
    global _cached_ia_data, _cached_ia_timestamp
    now = time.time()

    if _cached_ia_data and (now - _cached_ia_timestamp < _CACHE_TTL_SECONDS):
        logger.info("Devolviendo oportunidades de IA desde la caché.")
        return _cached_ia_data

    logger.info("Generando nuevas oportunidades de IA (caché expirada o vacía).")

    try:
        # Simular datos de entrada para el servicio de IA
        strategy_context = "Estrategia: Demo Scalping, Par: BTC/USDT, Timeframe: 1m"
        opportunity_context = "Par: BTC/USDT, Precio actual: $68,500.00, Volumen: 1500 BTC"
        
        # Usar el servicio de IA inyectado para obtener un análisis
        ai_response = await ai_service.analyze_trading_opportunity_async(
            strategy_context=strategy_context,
            opportunity_context=opportunity_context,
            historical_context="Análisis de demo - sin historial completo.",
            tool_outputs="Datos de mercado simulados.",
        )

        # Transformar la respuesta del servicio de IA al formato que espera la UI
        transformed_result = {
            "id": ai_response.analysis_id,
            "symbol": "BTC/USDT",
            "side": ai_response.recommendation.value.upper(),
            "entry_price": ai_response.entry_price or 68500.0,
            "confidence_score": ai_response.confidence,
            "strategy_id": "DemoScalping",
            "exchange": "Binance (Demo)",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "reasoning": ai_response.reasoning,
        }
        
        result = [transformed_result]
        logger.info(f"Nuevas oportunidades de IA generadas: {result}")

        # Actualizar la caché
        _cached_ia_data = result
        _cached_ia_timestamp = now
        
        return result

    except Exception as e:
        logger.error(f"Error generando oportunidades de Gemini: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"No se pudieron generar las oportunidades de IA: {str(e)}",
        )
