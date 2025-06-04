from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend import dependencies as deps

router = APIRouter()

@router.get("/market/tickers", response_model=List[Dict[str, Any]])
async def get_market_tickers(
    user_id: UUID = Query(..., description="User identifier for context (required for rate limits, etc.)"),
    symbols: List[str] = Query(..., description="List of trading symbols, e.g. ['BTCUSDT','ETHUSDT']"),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service)
):
    """
    Get ticker data (last price, 24h change, volume) for a list of symbols.
    """
    try:
        data = await market_data_service.get_market_data_rest(user_id, symbols)
        # Return as a list for frontend compatibility
        return [
            {"symbol": symbol, **info} for symbol, info in data.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickers: {e}")

@router.get("/market/klines", response_model=List[Dict[str, Any]])
async def get_market_klines(
    user_id: UUID = Query(..., description="User identifier for context (required for rate limits, etc.)"),
    symbol: str = Query(..., description="Trading symbol, e.g. 'BTCUSDT'"),
    interval: str = Query(..., description="Kline interval, e.g. '1m', '1h', '1d'"),
    limit: int = Query(200, description="Number of klines to return (default 200)"),
    start_time: Optional[int] = Query(None, description="Start time in ms since epoch (optional)"),
    end_time: Optional[int] = Query(None, description="End time in ms since epoch (optional)"),
    market_data_service: MarketDataService = Depends(deps.get_market_data_service)
):
    """
    Get candlestick (OHLCV) data for a symbol and interval.
    """
    try:
        klines = await market_data_service.get_candlestick_data(
            user_id=user_id,
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        return klines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch klines: {e}")
