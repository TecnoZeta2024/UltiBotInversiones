"""
Endpoints de la API para la consulta de operaciones de trading (trades).
"""
import logging
from typing import List, Optional, Literal, Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.shared.data_types import Trade
from src.ultibot_backend.core.ports import IPersistencePort
from src.ultibot_backend.dependencies import PersistenceServiceDep
from src.ultibot_backend.app_config import settings

router = APIRouter(prefix="/trades", tags=["Trades"])
logger = logging.getLogger(__name__)

TradingMode = Literal["paper", "real", "both"]

@router.get("", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_user_trades(
    persistence_port = PersistenceServiceDep,
    trading_mode: TradingMode = Query("both", description="Filtro de modo de trading: 'paper', 'real', o 'both'"),
    status_filter: Optional[str] = Query(None, description="Filtro de estado de posición: 'open', 'closed', etc."),
    symbol_filter: Optional[str] = Query(None, description="Filtro por símbolo (ej., 'BTCUSDT')"),
    date_from: Optional[date] = Query(None, description="Filtro por fecha de inicio (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Filtro por fecha de fin (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de trades a devolver"),
    offset: int = Query(0, ge=0, description="Número de trades a saltar para paginación"),
):
    """
    Obtiene las operaciones del usuario fijo, filtradas por modo de trading y otros criterios.
    """
    user_id = settings.FIXED_USER_ID
    try:
        filters: dict[str, Any] = {"user_id": str(user_id)}
        
        if trading_mode != "both":
            filters["is_real_trade"] = trading_mode == "real"
        
        if status_filter:
            filters["status"] = status_filter
        if symbol_filter:
            filters["symbol"] = symbol_filter
        if date_from:
            filters["start_date_gte"] = date_from
        if date_to:
            filters["end_date_lte"] = date_to
            
        trades_data = await persistence_port.get_trades(
            filters=filters,
            limit=limit,
            offset=offset,
        )
        return trades_data
            
    except Exception as e:
        logger.error(f"Fallo al obtener trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron obtener las operaciones: {str(e)}",
        )

@router.get("/open", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_open_trades(
    persistence_port = PersistenceServiceDep,
    trading_mode: TradingMode = Query("both", description="Filtro de modo de trading: 'paper', 'real', o 'both'"),
):
    """
    Obtiene solo las operaciones abiertas para el usuario y modo de trading especificados.
    """
    return await get_user_trades(
        persistence_port=persistence_port,
        trading_mode=trading_mode,
        status_filter="open",
    )

@router.get("/count", status_code=status.HTTP_200_OK)
async def get_trades_count(
    persistence_port = PersistenceServiceDep,
    trading_mode: TradingMode = Query("both", description="Filtro de modo de trading: 'paper', 'real', o 'both'"),
    status_filter: Optional[str] = Query(None, description="Filtro de estado de posición: 'open', 'closed', etc."),
):
    """
    Obtiene el conteo de operaciones que coinciden con los criterios especificados.
    """
    user_id = settings.FIXED_USER_ID
    try:
        filters: dict[str, Any] = {"user_id": str(user_id)}
        if trading_mode != "both":
            filters["is_real_trade"] = trading_mode == "real"
        if status_filter:
            filters["status"] = status_filter

        count = await persistence_port.get_trades_count(filters=filters)
        
        return {
            "user_id": str(user_id),
            "trading_mode": trading_mode,
            "status_filter": status_filter,
            "count": count,
        }
            
    except Exception as e:
        logger.error(f"Fallo al contar trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo contar las operaciones: {str(e)}",
        )
