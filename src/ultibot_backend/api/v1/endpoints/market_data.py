from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend import dependencies as deps
from src.ultibot_backend.security import core as security_core
from src.ultibot_backend.security import schemas as security_schemas

router = APIRouter()

@router.get("/market/tickers", response_model=List[Dict[str, Any]])
async def get_market_tickers(
    symbols_str: str = Query(..., alias="symbols", description="Comma-separated list of trading symbols, e.g. 'BTC/USDT,ETH/USDT'"),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service),
    current_user: security_schemas.User = Depends(security_core.get_current_active_user)
):
    """
    Get ticker data (last price, 24h change, volume) for a list of symbols for the authenticated user.
    """
    if not isinstance(current_user.id, UUID):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
    # Dividir la cadena de símbolos en una lista
    symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
    
    try:
        data = await market_data_service.get_market_data_rest(current_user.id, symbols)
        # Return as a list for frontend compatibility
        return [
            {"symbol": symbol, **info} for symbol, info in data.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {e}")

@router.get("/market/klines", response_model=List[Dict[str, Any]])
async def get_market_klines(
    symbol: str = Query(..., description="Trading symbol, e.g. 'BTCUSDT'"),
    interval: str = Query(..., description="Kline interval, e.g. '1m', '1h', '1d'"),
    limit: int = Query(200, description="Number of klines to return (default 200)"),
    start_time: Optional[int] = Query(None, description="Start time in ms since epoch (optional)"),
    end_time: Optional[int] = Query(None, description="End time in ms since epoch (optional)"),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service),
    current_user: security_schemas.User = Depends(security_core.get_current_active_user)
):
    """
    Get candlestick (OHLCV) data for a symbol and interval for the authenticated user.
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")
        klines = await market_data_service.get_candlestick_data(
            user_id=current_user.id,
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        return klines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch klines: {e}")
