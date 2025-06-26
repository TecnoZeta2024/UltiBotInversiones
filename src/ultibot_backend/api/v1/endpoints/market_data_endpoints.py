from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.dependencies import get_market_data_service
import logging

logger = logging.getLogger(__name__)

logger.info("Cargando market_data_endpoints.py") # Añadir esta línea

router = APIRouter()

@router.get("/market/tickers", response_model=Dict[str, Any])
async def get_tickers(
    symbols: str = Query(..., description="Lista de símbolos de trading separados por coma (ej. BTCUSDT,ETHUSDT)"),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Obtiene los últimos datos de ticker (precio, cambio 24h, volumen) para una lista de símbolos.
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="Se requiere al menos un símbolo.")
    
    try:
        tickers_data = await market_data_service.get_market_data_rest(symbol_list)
        return tickers_data
    except Exception as e:
        logger.error(f"Error al obtener datos de tickers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener tickers: {e}")

@router.get("/market/klines", response_model=List[Dict[str, Any]])
async def get_klines(
    symbol: str = Query(..., description="Símbolo de trading (ej. BTCUSDT)"),
    interval: str = Query(..., description="Intervalo de tiempo (ej. 1h, 4h, 1d)"),
    limit: int = Query(200, ge=1, le=1000, description="Número máximo de velas a devolver"),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Obtiene datos históricos de velas (OHLCV) para un símbolo e intervalo dados.
    """
    try:
        klines = await market_data_service.get_candlestick_data(symbol, interval, limit)
        return klines
    except Exception as e:
        logger.error(f"Error al obtener datos de klines para {symbol}-{interval}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener klines: {e}")
