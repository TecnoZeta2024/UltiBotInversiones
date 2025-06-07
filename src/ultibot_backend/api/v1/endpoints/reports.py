"""
API endpoints para generar informes de trading y métricas de rendimiento.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from src.shared.data_types import Trade, PerformanceMetrics
from src.ultibot_backend.services.trading_report_service import TradingReportService
from src.ultibot_backend import dependencies as deps
from src.ultibot_backend.app_config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter()

# Modelos para los parámetros de consulta
class TradeFilters(BaseModel):
    """Filtros para consultar trades históricos."""
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0

class TradeHistoryResponse(BaseModel):
    """Respuesta para el historial de trades."""
    trades: List[Trade]
    total_count: int
    has_more: bool

@router.get("/trades/history/paper", response_model=TradeHistoryResponse, tags=["reports"])
async def get_paper_trading_history(
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de trades a devolver"),
    offset: int = Query(0, ge=0, description="Número de trades a saltar (para paginación)"),
    report_service: TradingReportService = Depends(deps.get_trading_report_service)
) -> TradeHistoryResponse:
    """
    Obtiene el historial de operaciones de Paper Trading cerradas para el usuario fijo.
    """
    user_id = settings.FIXED_USER_ID
    try:
        trades = await report_service.get_closed_trades(
            user_id=user_id,
            mode='paper',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        has_more = False
        if len(trades) == limit:
            check_trades = await report_service.get_closed_trades(
                user_id=user_id,
                mode='paper',
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=1,
                offset=offset + limit
            )
            has_more = len(check_trades) > 0
        
        total_count = offset + len(trades)
        if has_more:
            total_count += 1
        
        return TradeHistoryResponse(
            trades=trades,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error al obtener historial de paper trading: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial de operaciones: {str(e)}"
        )

@router.get("/portfolio/paper/performance_summary", response_model=PerformanceMetrics, tags=["reports"])
async def get_paper_trading_performance(
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    report_service: TradingReportService = Depends(deps.get_trading_report_service)
) -> PerformanceMetrics:
    """
    Obtiene las métricas de rendimiento consolidadas para Paper Trading del usuario fijo.
    """
    user_id = settings.FIXED_USER_ID
    try:
        metrics = await report_service.calculate_performance_metrics(
            user_id=user_id,
            mode='paper',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
        
    except Exception as e:
        logger.error(f"Error al calcular métricas de rendimiento: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular métricas de rendimiento: {str(e)}"
        )

@router.get("/trades/history/real", response_model=TradeHistoryResponse, tags=["reports"])
async def get_real_trading_history(
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de trades a devolver"),
    offset: int = Query(0, ge=0, description="Número de trades a saltar (para paginación)"),
    report_service: TradingReportService = Depends(deps.get_trading_report_service)
) -> TradeHistoryResponse:
    """
    Obtiene el historial de operaciones de Trading Real cerradas para el usuario fijo.
    """
    user_id = settings.FIXED_USER_ID
    try:
        trades = await report_service.get_closed_trades(
            user_id=user_id,
            mode='real',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        has_more = False
        if len(trades) == limit:
            check_trades = await report_service.get_closed_trades(
                user_id=user_id,
                mode='real',
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=1,
                offset=offset + limit
            )
            has_more = len(check_trades) > 0
        
        total_count = offset + len(trades)
        if has_more:
            total_count += 1
        
        return TradeHistoryResponse(
            trades=trades,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error al obtener historial de trading real: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener historial de operaciones reales: {str(e)}"
        )

@router.get("/portfolio/real/performance_summary", response_model=PerformanceMetrics, tags=["reports"])
async def get_real_trading_performance(
    symbol: Optional[str] = Query(None, description="Filtrar por par de trading (ej. BTCUSDT)"),
    start_date: Optional[datetime] = Query(None, description="Fecha de inicio para filtrar"),
    end_date: Optional[datetime] = Query(None, description="Fecha de fin para filtrar"),
    report_service: TradingReportService = Depends(deps.get_trading_report_service)
) -> PerformanceMetrics:
    """
    Obtiene las métricas de rendimiento consolidadas para Trading Real del usuario fijo.
    """
    user_id = settings.FIXED_USER_ID
    try:
        metrics = await report_service.calculate_performance_metrics(
            user_id=user_id,
            mode='real',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
        
    except Exception as e:
        logger.error(f"Error al calcular métricas de rendimiento real: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular métricas de rendimiento real: {str(e)}"
        )
