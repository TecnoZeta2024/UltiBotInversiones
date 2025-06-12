"""
Endpoints de la API para obtener datos de mercado.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ....shared.data_types import MarketData
from ...services.market_data_service import MarketDataService
from ...core.exceptions import UltiBotError
from ...dependencies import MarketDataServiceDep

router = APIRouter(prefix="/market-data", tags=["Market Data"])
logger = logging.getLogger(__name__)

@router.get("/tickers", response_model=List[Dict[str, Any]])
async def get_market_tickers(
    symbols_str: str = Query(..., alias="symbols", description="Lista de símbolos de trading separados por comas, ej. 'BTC/USDT,ETH/USDT'"),
    market_service = MarketDataServiceDep,
):
    """
    Obtiene datos de ticker (último precio, cambio 24h, volumen) para una lista de símbolos.
    """
    symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
    if not symbols:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe proporcionar al menos un símbolo.")

    try:
        # Use the market_data_service get_market_data_rest method
        data = await market_service.get_market_data_rest(symbols)
        return [
            {"symbol": symbol, **info} for symbol, info in data.items()
        ]
    except UltiBotError as e:
        logger.error(f"Error al obtener tickers: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"No se pudieron obtener los tickers: {e}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener tickers: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocurrió un error inesperado: {e}")

@router.get("/klines", response_model=List[Dict[str, Any]])
async def get_market_klines(
    symbol: str = Query(..., description="Símbolo de trading, ej. 'BTCUSDT'"),
    interval: str = Query(..., description="Intervalo de klines, ej. '1m', '1h', '1d'"),
    limit: int = Query(200, ge=1, le=1000, description="Número de klines a devolver (default 200)"),
    start_time: Optional[int] = Query(None, description="Timestamp de inicio en ms desde epoch (opcional)"),
    end_time: Optional[int] = Query(None, description="Timestamp de fin en ms desde epoch (opcional)"),
    market_service = MarketDataServiceDep,
):
    """
    Obtiene datos de velas (OHLCV) para un símbolo e intervalo.
    """
    try:
        # Use the market_data_service get_candlestick_data method
        klines = await market_service.get_candlestick_data(
            symbol=symbol.upper(),
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        return klines
    except UltiBotError as e:
        logger.error(f"Error al obtener klines para {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"No se pudieron obtener los klines: {e}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener klines: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocurrió un error inesperado: {e}")

@router.get("/history/{symbol}", response_model=List[MarketData])
async def get_market_history(
    symbol: str,
    interval: str = Query("1h", description="El intervalo de los klines, ej., '1h', '4h', '1d'"),
    limit: int = Query(1000, ge=1, le=2000, description="Número de puntos de datos a recuperar"),
    market_service = MarketDataServiceDep,
):
    """
    Obtiene datos históricos de mercado para un símbolo dado desde la base de datos.
    """
    try:
        # Use the market_data_service get_historical_market_data method
        historical_data = await market_service.get_historical_market_data(
            symbol=symbol.upper(),
            interval=interval,
            limit=limit
        )
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron datos históricos para el símbolo '{symbol}' con el intervalo '{interval}'."
            )
        return historical_data
    except UltiBotError as e:
        logger.error(f"Error al obtener el historial de mercado para {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"No se pudo obtener el historial de datos: {e}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener el historial de mercado: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocurrió un error inesperado: {e}")
