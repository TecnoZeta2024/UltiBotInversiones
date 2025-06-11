from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from typing import List, Dict, Any, Optional
from uuid import UUID

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.dependencies import DependencyContainer
from src.ultibot_backend.core.exceptions import UltiBotError
from src.shared.data_types import MarketData

router = APIRouter()

def get_container(request: Request) -> DependencyContainer:
    return request.app.state.container

@router.get("/tickers", response_model=List[Dict[str, Any]])
async def get_market_tickers(
    request: Request,
    symbols_str: str = Query(..., alias="symbols", description="Comma-separated list of trading symbols, e.g. 'BTC/USDT,ETH/USDT'")
):
    """
    Get ticker data (last price, 24h change, volume) for a list of symbols.
    """
    container = get_container(request)
    market_data_service = container.market_data_service
    assert market_data_service is not None, "MarketDataService no inicializado"
    
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

@router.get("/klines", response_model=List[Dict[str, Any]])
async def get_market_klines(
    request: Request,
    symbol: str = Query(..., description="Trading symbol, e.g. 'BTCUSDT'"),
    interval: str = Query(..., description="Kline interval, e.g. '1m', '1h', '1d'"),
    limit: int = Query(200, description="Number of klines to return (default 200)"),
    start_time: Optional[int] = Query(None, description="Start time in ms since epoch (optional)"),
    end_time: Optional[int] = Query(None, description="End time in ms since epoch (optional)")
):
    """
    Get candlestick (OHLCV) data for a symbol and interval.
    This endpoint fetches live data from the exchange and persists it.
    """
    container = get_container(request)
    market_data_service = container.market_data_service
    assert market_data_service is not None, "MarketDataService no inicializado"

    try:
        klines = await market_data_service.get_candlestick_data(
            symbol=symbol,
            interval=interval,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        return klines
    except UltiBotError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch klines: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

@router.get("/history/{symbol}", response_model=List[MarketData])
async def get_market_history(
    request: Request,
    symbol: str,
    interval: str = Query("1h", description="The interval of the klines, e.g., '1h', '4h', '1d'"),
    limit: int = Query(1000, ge=1, le=2000, description="Number of data points to retrieve")
):
    """
    Get historical market data for a given symbol from the database.
    """
    container = get_container(request)
    market_data_service = container.market_data_service
    assert market_data_service is not None, "MarketDataService no inicializado"
    
    try:
        historical_data = await market_data_service.get_historical_market_data(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for symbol '{symbol}' with interval '{interval}'."
            )
        return historical_data
    except UltiBotError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch historical data: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
