"""
Endpoints de API para análisis de IA y recomendaciones de trading.
"""

import logging
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.core.domain_models.ai import TradingAIResponse, TradingRecommendation
from src.ultibot_backend.dependencies import get_ai_orchestrator_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])

# Request Models
class TradingAnalysisRequest(BaseModel):
    """Modelo de solicitud para análisis de trading."""
    strategy_context: str = Field(
        ..., 
        description="Contexto de la estrategia de trading (tipo, parámetros, objetivos)",
        min_length=10,
        max_length=2000
    )
    opportunity_context: str = Field(
        ..., 
        description="Información de la oportunidad detectada (par, precio, indicadores)",
        min_length=10,
        max_length=2000
    )
    historical_context: str = Field(
        default="Sin historial previo disponible",
        description="Historial de operaciones previas y métricas de performance",
        max_length=3000
    )
    tool_outputs: str = Field(
        default="Datos básicos de mercado disponibles",
        description="Resultados de herramientas de análisis externas",
        max_length=3000
    )
    trading_mode: str = Field(
        default="paper",
        description="Modo de trading: 'paper' o 'real'",
        pattern="^(paper|real)$"
    )

class QuickAnalysisRequest(BaseModel):
    """Modelo para análisis rápido con datos mínimos."""
    symbol: str = Field(..., description="Par de trading (ej: BTC/USDT)")
    current_price: float = Field(..., gt=0, description="Precio actual")
    strategy_type: str = Field(..., description="Tipo de estrategia: scalping, day_trading, arbitrage")
    timeframe: str = Field(default="1m", description="Marco temporal")

# Response Models
class AnalysisStatusResponse(BaseModel):
    """Estado del análisis."""
    analysis_id: str
    status: str
    message: str

class TradingAnalysisResponse(BaseModel):
    """Respuesta completa de análisis de trading."""
    analysis_id: str
    recommendation: TradingRecommendation
    confidence: float
    reasoning: str
    warnings: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_level: Optional[str] = None
    timeframe: Optional[str] = None
    is_high_confidence: bool
    is_suitable_for_real_trading: bool
    summary: str
    telegram_message: str

# Endpoints
@router.post("/analyze/trading", response_model=TradingAnalysisResponse)
async def analyze_trading_opportunity(
    request: TradingAnalysisRequest,
    background_tasks: BackgroundTasks,
    ai_service: AIOrchestratorService = Depends(get_ai_orchestrator_service)
) -> TradingAnalysisResponse:
    """
    Analiza una oportunidad de trading usando IA.
    
    Proporciona recomendaciones estructuradas basadas en:
    - Contexto de la estrategia
    - Datos de la oportunidad
    - Historial de performance
    - Herramientas de análisis
    
    Returns:
        TradingAnalysisResponse: Análisis completo con recomendación
    """
    try:
        logger.info(f"Recibida solicitud de análisis de trading para modo: {request.trading_mode}")
        
        # Realizar análisis con la IA
        ai_response = await ai_service.analyze_trading_opportunity_async(
            strategy_context=request.strategy_context,
            opportunity_context=request.opportunity_context,
            historical_context=request.historical_context,
            tool_outputs=request.tool_outputs
        )
        
        # Convertir respuesta
        response = TradingAnalysisResponse(
            analysis_id=ai_response.analysis_id,
            recommendation=ai_response.recommendation,
            confidence=ai_response.confidence,
            reasoning=ai_response.reasoning,
            warnings=ai_response.warnings,
            entry_price=ai_response.entry_price,
            stop_loss=ai_response.stop_loss,
            take_profit=ai_response.take_profit,
            risk_level=ai_response.risk_level,
            timeframe=ai_response.timeframe,
            is_high_confidence=ai_response.is_high_confidence(),
            is_suitable_for_real_trading=ai_response.is_suitable_for_real_trading(),
            summary=ai_response.get_summary(),
            telegram_message=ai_response.to_telegram_message()
        )
        
        logger.info(f"Análisis completado: {response.recommendation.value} ({response.confidence:.1%})")
        
        # TODO: Opcional - guardar análisis en base de datos en background
        # background_tasks.add_task(save_analysis_to_db, ai_response)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis de trading: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar análisis de trading: {str(e)}"
        )

@router.post("/analyze/quick", response_model=TradingAnalysisResponse)
async def quick_trading_analysis(
    request: QuickAnalysisRequest,
    ai_service: AIOrchestratorService = Depends(get_ai_orchestrator_service)
) -> TradingAnalysisResponse:
    """
    Análisis rápido con datos mínimos.
    
    Útil para obtener una recomendación rápida cuando no se tiene
    contexto histórico completo.
    
    Args:
        request: Datos básicos del análisis
        
    Returns:
        TradingAnalysisResponse: Análisis con recomendación
    """
    try:
        # Construir contextos simplificados
        strategy_context = f"""
        Estrategia: {request.strategy_type.replace('_', ' ').title()}
        Par objetivo: {request.symbol}
        Timeframe: {request.timeframe}
        Modo: Análisis rápido
        """
        
        opportunity_context = f"""
        Par: {request.symbol}
        Precio actual: ${request.current_price:,.2f}
        Timestamp: Análisis en tiempo real
        Tipo de análisis: Evaluación rápida
        """
        
        historical_context = "Análisis rápido - sin historial completo disponible"
        tool_outputs = "Datos básicos de mercado - análisis simplificado"
        
        # Realizar análisis
        ai_response = await ai_service.analyze_trading_opportunity_async(
            strategy_context=strategy_context,
            opportunity_context=opportunity_context,
            historical_context=historical_context,
            tool_outputs=tool_outputs
        )
        
        # Convertir respuesta
        response = TradingAnalysisResponse(
            analysis_id=ai_response.analysis_id,
            recommendation=ai_response.recommendation,
            confidence=ai_response.confidence,
            reasoning=ai_response.reasoning,
            warnings=ai_response.warnings,
            entry_price=ai_response.entry_price,
            stop_loss=ai_response.stop_loss,
            take_profit=ai_response.take_profit,
            risk_level=ai_response.risk_level,
            timeframe=ai_response.timeframe,
            is_high_confidence=ai_response.is_high_confidence(),
            is_suitable_for_real_trading=ai_response.is_suitable_for_real_trading(),
            summary=ai_response.get_summary(),
            telegram_message=ai_response.to_telegram_message()
        )
        
        logger.info(f"Análisis rápido completado para {request.symbol}: {response.recommendation.value}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error en análisis rápido: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar análisis rápido: {str(e)}"
        )

@router.get("/health")
async def ai_health_check(
    ai_service: AIOrchestratorService = Depends(get_ai_orchestrator_service)
) -> Dict[str, Any]:
    """
    Verifica el estado del servicio de IA.
    
    Returns:
        Dict con estado del servicio
    """
    try:
        # Verificar si el servicio está configurado
        if not ai_service.llm or not ai_service.trading_parser:
            return {
                "status": "unhealthy",
                "message": "AI service not properly configured",
                "configured": False
            }
        
        return {
            "status": "healthy",
            "message": "AI Orchestrator service is running",
            "model": ai_service.llm.model,
            "temperature": ai_service.llm.temperature,
            "configured": True
        }
        
    except Exception as e:
        logger.error(f"Error checking AI health: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "configured": False
        }

@router.get("/models/info")
async def get_ai_models_info(
    ai_service: AIOrchestratorService = Depends(get_ai_orchestrator_service)
) -> Dict[str, Any]:
    """
    Obtiene información sobre los modelos de IA configurados.
    
    Returns:
        Dict con información de modelos
    """
    try:
        if not ai_service.llm:
            raise HTTPException(status_code=503, detail="AI service not configured")
        
        return {
            "primary_model": {
                "name": ai_service.llm.model,
                "temperature": ai_service.llm.temperature,
                "provider": "Google Gemini"
            },
            "capabilities": {
                "trading_analysis": True,
                "structured_output": True,
                "tool_integration": True,
                "async_processing": True
            },
            "supported_formats": {
                "input": ["strategy_context", "opportunity_context", "historical_context", "tool_outputs"],
                "output": ["recommendation", "confidence", "reasoning", "warnings", "price_targets"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving model information: {str(e)}")
