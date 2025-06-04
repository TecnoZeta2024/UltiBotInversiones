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
# SupabasePersistenceService ya no se importa directamente aquí si TradingReportService se obtiene de deps
# from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend import dependencies as deps # Importar deps

# Configurar logging
logger = logging.getLogger(__name__)

# Crear el router
router = APIRouter()

# Las funciones de dependencia locales get_persistence_service y get_trading_report_service ya no son necesarias
# si usamos deps.get_trading_report_service directamente.

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
    Obtiene el historial de operaciones de Paper Trading cerradas.
    
    Permite filtrar por par de trading y rango de fechas. Soporta paginación.
    """
    try:
        # Usar user_id fijo para v1.0
        from src.ultibot_backend.app_config import settings
        
        logger.info(f"Obteniendo historial de paper trading para usuario {settings.FIXED_USER_ID}")
        logger.info(f"Filtros: symbol={symbol}, start_date={start_date}, end_date={end_date}, limit={limit}, offset={offset}")
        
        # Obtener los trades usando el servicio
        trades = await report_service.get_closed_trades(
            user_id=settings.FIXED_USER_ID,
            mode='paper',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Para determinar si hay más resultados, intentamos obtener uno más
        has_more = False
        if len(trades) == limit:
            # Comprobar si hay más trades
            check_trades = await report_service.get_closed_trades(
                user_id=settings.FIXED_USER_ID,
                mode='paper',
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                limit=1,
                offset=offset + limit
            )
            has_more = len(check_trades) > 0
        
        # Calcular el total aproximado (esto es costoso de hacer exacto cada vez)
        # Para v1.0, usamos una aproximación basada en los resultados obtenidos
        total_count = offset + len(trades)
        if has_more:
            total_count += 1  # Sabemos que hay al menos uno más
        
        logger.info(f"Devolviendo {len(trades)} trades de paper trading")
        
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
    Obtiene las métricas de rendimiento consolidadas para Paper Trading.
    
    Calcula P&L total, Win Rate, número total de operaciones y P&L promedio por operación.
    """
    try:
        # Usar user_id fijo para v1.0
        from src.ultibot_backend.app_config import settings # Ya debería estar importado, pero por si acaso
        
        logger.info(f"Calculando métricas de rendimiento de paper trading para usuario {settings.FIXED_USER_ID}")
        logger.info(f"Filtros: symbol={symbol}, start_date={start_date}, end_date={end_date}")
        
        # Calcular las métricas usando el servicio
        metrics = await report_service.calculate_performance_metrics(
            user_id=settings.FIXED_USER_ID,
            mode='paper',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Métricas calculadas: {metrics.total_trades} trades, Win Rate: {metrics.win_rate:.2f}%, P&L Total: {metrics.total_pnl:.2f}")
        
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
    Obtiene el historial de operaciones de Trading Real cerradas.
    
    Similar al endpoint de paper trading pero para operaciones reales.
    """
    try:
        # Usar user_id fijo para v1.0
        from src.ultibot_backend.app_config import settings # Ya debería estar importado
        
        logger.info(f"Obteniendo historial de trading real para usuario {settings.FIXED_USER_ID}")
        
        # Obtener los trades usando el servicio
        trades = await report_service.get_closed_trades(
            user_id=settings.FIXED_USER_ID,
            mode='real',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Determinar si hay más resultados
        has_more = False
        if len(trades) == limit:
            check_trades = await report_service.get_closed_trades(
                user_id=settings.FIXED_USER_ID,
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
        
        logger.info(f"Devolviendo {len(trades)} trades de trading real")
        
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
    Obtiene las métricas de rendimiento consolidadas para Trading Real.
    """
    try:
        # Usar user_id fijo para v1.0
        from src.ultibot_backend.app_config import settings # Ya debería estar importado
        
        logger.info(f"Calculando métricas de rendimiento de trading real para usuario {settings.FIXED_USER_ID}")
        
        # Calcular las métricas usando el servicio
        metrics = await report_service.calculate_performance_metrics(
            user_id=settings.FIXED_USER_ID,
            mode='real',
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Métricas de trading real calculadas: {metrics.total_trades} trades, Win Rate: {metrics.win_rate:.2f}%, P&L Total: {metrics.total_pnl:.2f}")
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error al calcular métricas de rendimiento real: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular métricas de rendimiento real: {str(e)}"
        )
