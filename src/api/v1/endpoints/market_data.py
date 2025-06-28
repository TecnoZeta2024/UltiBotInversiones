from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from typing import List, Dict, Any, Optional
from uuid import UUID

from services.market_data_service import MarketDataService
from dependencies import get_market_data_service
from core.exceptions import UltiBotError, MarketDataValidationError

router = APIRouter()

@router.get("/tickers", response_model=List[Dict[str, Any]])
async def get_market_tickers(
    symbols_str: str = Query(..., alias="symbols", description="Comma-separated list of trading symbols, e.g. 'BTC/USDT,ETH/USDT'"),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get ticker data (last price, 24h change, volume) for a list of symbols.
    """
    symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
    
    try:
        data = await market_data_service.get_market_data_rest(symbols)
        return [
            {"symbol": symbol, **info} for symbol, info in data.items()
        ]
    except UltiBotError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch tickers: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/ticker/24hr/{symbol}", response_model=Dict[str, Any])
async def get_ticker_24hr(
    symbol: str,
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get 24-hour ticker price change statistics for a specific symbol.
    """
    try:
        ticker_data = await market_data_service.get_ticker_24hr(symbol)
        return ticker_data
    except MarketDataValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except UltiBotError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch 24hr ticker data: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/klines", response_model=List[Dict[str, Any]])
async def get_market_klines(
    symbol: str = Query(..., description="Trading symbol, e.g. 'BTCUSDT'"),
    interval: str = Query(..., description="Kline interval, e.g. '1m', '1h', '1d'"),
    limit: int = Query(200, description="Number of klines to return (default 200)"),
    start_time: Optional[int] = Query(None, description="Start time in ms since epoch (optional)"),
    end_time: Optional[int] = Query(None, description="End time in ms since epoch (optional)"),
    market_data_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Get candlestick (OHLCV) data for a symbol and interval.
    """
    try:
        klines = await market_data_service.get_candlestick_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        return klines
    except MarketDataValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.message)
    except UltiBotError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch klines: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
