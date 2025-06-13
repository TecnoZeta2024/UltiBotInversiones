"""
API endpoints para generar informes de trading y métricas de rendimiento.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, Depends, status
from pydantic import BaseModel

from src.shared.data_types import Trade, PerformanceMetrics
from src.ultibot_backend.dependencies import PerformanceServiceDep
from src.ultibot_backend.app_config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])

class TradeHistoryResponse(BaseModel):
    """Respuesta para el historial de trades."""
    trades: List[Trade]
    total_count: int
    has_more: bool

@router.get("/trades/history/{mode}", response_model=TradeHistoryResponse)
async def get_trading_history(
    mode: str = Path(..., description="Modo de trading: 'paper' o 'real'"),
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de trades a devolver"),
    offset: int = Query(0, ge=0, description="Número de trades a saltar (para paginación)"),
    performance_service = PerformanceServiceDep
):
    """
    Obtiene el historial de operaciones cerradas para el modo de trading especificado.
    """
    if mode not in ["paper", "real"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Modo de trading inválido. Use 'paper' o 'real'.")

    user_id = settings.FIXED_USER_ID
    try:
        trades, total_count = await performance_service.get_trade_history(
            user_id=user_id,
            trading_mode=mode,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        has_more = (offset + len(trades)) < total_count
        
        return TradeHistoryResponse(
            trades=trades,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error al obtener historial de trading para el modo {mode}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de operaciones: {str(e)}"
        )

@router.get("/performance/summary/{mode}", response_model=PerformanceMetrics)
async def get_performance_summary(
    mode: str = Path(..., description="Modo de trading: 'paper' o 'real'"),
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    performance_service = PerformanceServiceDep
):
    """
    Obtiene las métricas de rendimiento consolidadas para el modo de trading especificado.
    """
    if mode not in ["paper", "real"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Modo de trading inválido. Use 'paper' o 'real'.")

    user_id = settings.FIXED_USER_ID
    try:
        metrics = await performance_service.get_trade_performance_metrics(
            user_id=user_id,
            trading_mode=mode,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
        
    except Exception as e:
        logger.error(f"Error al calcular métricas de rendimiento para el modo {mode}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular métricas de rendimiento: {str(e)}"
        )
