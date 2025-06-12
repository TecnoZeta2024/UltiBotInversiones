"""
Endpoints de API para análisis de IA y recomendaciones de trading.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.core.domain_models.ai_models import AIAnalysisResult
from src.ultibot_backend.dependencies import AIOrchestratorDep

logger = logging.getLogger(__name__)

router = APIRouter()

# Request Models
class TradingAnalysisRequest(BaseModel):
    """Modelo de solicitud para análisis de trading."""
    opportunity_id: str = Field(..., description="ID de la oportunidad a analizar")
    market_data: Dict[str, Any] = Field(..., description="Datos de mercado para el análisis")
    strategy_context: Optional[Dict[str, Any]] = Field(default=None, description="Contexto de la estrategia")

# Response Models
class AnalysisStatusResponse(BaseModel):
    """Estado del análisis."""
    analysis_id: UUID
    status: str
    message: str

class TradingAnalysisResponse(BaseModel):
    """Respuesta completa de análisis de trading."""
    result_id: UUID
    recommendation: str
    confidence: float
    reasoning: Optional[str]
    risk_assessment: Optional[str]
    
# Endpoints
@router.post("/analyze/trading", response_model=TradingAnalysisResponse)
async def analyze_trading_opportunity(
    request: TradingAnalysisRequest,
    ai_service: AIOrchestratorService = Depends(AIOrchestratorDep)
) -> TradingAnalysisResponse:
    """
    Analiza una oportunidad de trading usando IA.
    """
    try:
        logger.info(f"Recibida solicitud de análisis de trading para oportunidad: {request.opportunity_id}")
        
        ai_result: AIAnalysisResult = await ai_service.analyze_opportunity(
            opportunity_id=request.opportunity_id,
            market_data=request.market_data,
            strategy_context=request.strategy_context
        )
        
        response = TradingAnalysisResponse(
            result_id=ai_result.result_id,
            recommendation=ai_result.recommendation,
            confidence=ai_result.confidence,
            reasoning=ai_result.reasoning,
            risk_assessment=ai_result.risk_assessment,
        )
        
        logger.info(f"Análisis completado para {request.opportunity_id}: {response.recommendation} ({response.confidence:.1%})")
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis de trading: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar análisis de trading: {str(e)}"
        )

@router.get("/health")
async def ai_health_check(
    ai_service: AIOrchestratorService = Depends(AIOrchestratorDep)
) -> Dict[str, Any]:
    """
    Verifica el estado del servicio de IA.
    """
    try:
        # Una comprobación de salud podría implicar llamar a un método de diagnóstico en el servicio
        is_healthy = await ai_service.is_healthy()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "message": "AI Orchestrator service is running" if is_healthy else "AI service not properly configured",
            "model_provider": ai_service.get_provider_name() if is_healthy else None,
        }
    except Exception as e:
        logger.error(f"Error checking AI health: {e}")
        return {"status": "error", "message": f"Health check failed: {str(e)}"}

@router.get("/models/info")
async def get_ai_models_info(
    ai_service: AIOrchestratorService = Depends(AIOrchestratorDep)
) -> Dict[str, Any]:
    """
    Obtiene información sobre los modelos de IA configurados.
    """
    try:
        return {
            "primary_model": {
                "name": ai_service.get_model_name(),
                "provider": ai_service.get_provider_name()
            },
            "capabilities": ["trading_analysis", "structured_output", "tool_integration", "async_processing"]
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service not configured: {e}")
