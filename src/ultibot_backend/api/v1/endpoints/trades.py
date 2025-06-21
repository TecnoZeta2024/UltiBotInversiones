from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
import logging
from datetime import datetime, date
from typing import Annotated, Optional, List, Literal, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel

from shared.data_types import Trade
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend import dependencies as deps
from ultibot_backend.app_config import get_app_settings
from ultibot_backend.services.trading_report_service import TradingReportService # Importar TradingReportService

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Trading mode type alias for consistent validation
TradingMode = Literal["paper", "real", "both"]

# Modelos para los parámetros de consulta (copia de reports.py)
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

@router.get("", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_user_trades(
    request: Request,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both",
    status_filter: Annotated[Optional[str], Query(description="Position status filter: 'open', 'closed', etc.")] = None,
    symbol_filter: Annotated[Optional[str], Query(description="Symbol filter (e.g., 'BTCUSDT')")] = None,
    date_from: Annotated[Optional[date], Query(description="Start date filter (YYYY-MM-DD)")] = None,
    date_to: Annotated[Optional[date], Query(description="End date filter (YYYY-MM-DD)")] = None,
    limit: Annotated[int, Query(description="Maximum number of trades to return", ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(description="Number of trades to skip", ge=0)] = 0
):
    """
    Get trades for the fixed user filtered by trading mode and other criteria.
    """
    user_id_str = str(get_app_settings().FIXED_USER_ID) # Convertir UUID a str
    try:
        # Convertir date a datetime para la persistencia
        start_datetime = datetime.combine(date_from, datetime.min.time()) if date_from else None
        end_datetime = datetime.combine(date_to, datetime.max.time()) if date_to else None
            
        trades_data = await persistence_service.get_trades_with_filters(
            user_id=user_id_str,
            trading_mode=trading_mode,
            status=status_filter,
            symbol=symbol_filter,
            start_date=start_datetime,
            end_date=end_datetime,
            limit=limit,
            offset=offset
        )
        
        return trades_data
            
    except Exception as e:
        logger.error(f"Error al obtener trades de usuario: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trades: {str(e)}"
        )

@router.get("/open", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_open_trades(
    request: Request,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both"
):
    """
    Get only open trades for the fixed user and trading mode.
    """
    try:
        # We need to pass the request object to the redirected call
        return await get_user_trades(
            request=request,
            persistence_service=persistence_service,
            trading_mode=trading_mode,
            status_filter="open"
        )
        
    except Exception as e:
        logger.error(f"Error al obtener trades abiertos: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve open trades: {str(e)}"
        )

@router.get("/count", status_code=status.HTTP_200_OK)
async def get_trades_count(
    request: Request,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both",
    status_filter: Annotated[Optional[str], Query(description="Position status filter: 'open', 'closed', etc.")] = None,
    date_from: Annotated[Optional[date], Query(description="Start date filter (YYYY-MM-DD)")] = None,
    date_to: Annotated[Optional[date], Query(description="End date filter (YYYY-MM-DD)")] = None
):
    """
    Get count of trades matching the specified criteria for the fixed user.
    """
    user_id = get_app_settings().FIXED_USER_ID
    try:
        # TODO: Implement count method in persistence service
        if trading_mode == "both":
            return {
                "user_id": user_id,
                "paper_trades_count": 0,
                "real_trades_count": 0,
                "total_count": 0,
                "filters_applied": {
                    "status": status_filter,
                    "date_from": date_from,
                    "date_to": date_to
                }
            }
        else:
            return {
                "user_id": user_id,
                "trading_mode": trading_mode,
                "count": 0,
                "filters_applied": {
                    "status": status_filter,
                    "date_from": date_from,
                    "date_to": date_to
                }
            }
            
    except Exception as e:
        logger.error(f"Error al contar trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count trades: {str(e)}"
        )

@router.get("/history/paper", response_model=TradeHistoryResponse, tags=["trades"])
async def get_paper_trading_history(
    request: Request,
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
    user_id = get_app_settings().FIXED_USER_ID
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de operaciones: {str(e)}"
        )

@router.get("/history/real", response_model=TradeHistoryResponse, tags=["trades"])
async def get_real_trading_history(
    request: Request,
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
    user_id = get_app_settings().FIXED_USER_ID
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener historial de operaciones reales: {str(e)}"
        )
