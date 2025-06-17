from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Annotated, Optional, List, Literal, Any
from uuid import UUID
from datetime import date

from shared.data_types import Trade
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend import dependencies as deps
from ultibot_backend.app_config import settings

router = APIRouter()

# Trading mode type alias for consistent validation
TradingMode = Literal["paper", "real", "both"]

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
    user_id = settings.FIXED_USER_ID
    try:
        filters: dict[str, Any] = {"user_id": user_id}
        
        if trading_mode != "both":
            filters["mode"] = trading_mode
        
        if status_filter:
            filters["positionStatus"] = status_filter
        if symbol_filter:
            filters["symbol"] = symbol_filter
        if date_from:
            filters["created_at_gte"] = date_from
        if date_to:
            filters["created_at_lte"] = date_to
            
        trades_data = await persistence_service.get_trades_with_filters(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return trades_data
            
    except Exception as e:
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
    user_id = settings.FIXED_USER_ID
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count trades: {str(e)}"
        )

