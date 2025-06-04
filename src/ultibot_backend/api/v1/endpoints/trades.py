from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, List, Literal, Any
from uuid import UUID
from datetime import datetime, date

from src.shared.data_types import Trade, PerformanceMetrics
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Mantener para type hinting
from src.ultibot_backend import dependencies as deps # Importar deps

router = APIRouter()

# Trading mode type alias for consistent validation
TradingMode = Literal["paper", "real", "both"]

@router.get("/{user_id}", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_user_trades(
    user_id: UUID,
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
    Get trades for the specified user filtered by trading mode and other criteria.
    
    Args:
        user_id: User identifier
        trading_mode: Filter by trading mode ('paper', 'real', 'both')
        status_filter: Filter by position status
        symbol_filter: Filter by trading symbol
        date_from: Filter trades from this date
        date_to: Filter trades until this date
        limit: Maximum number of trades to return
        offset: Number of trades to skip (for pagination)
        
    Returns:
        List of trades matching the criteria
    """
    try:
        # Build filter conditions
        filters: dict[str, Any] = {"user_id": user_id}
        
        # Add trading mode filter
        if trading_mode == "paper":
            filters["mode"] = "paper"
        elif trading_mode == "real":
            filters["mode"] = "real"
        # For "both", don't add mode filter
        
        # Add other filters
        if status_filter:
            filters["positionStatus"] = status_filter
        if symbol_filter:
            filters["symbol"] = symbol_filter
        if date_from:
            filters["created_at_gte"] = date_from
        if date_to:
            filters["created_at_lte"] = date_to
            
        # Get trades from persistence service
        # Note: This is a placeholder - the actual implementation would depend on 
        # the persistence service having a method to query trades with filters
        # For now, we'll return an empty list and add a TODO
        
        # TODO: Implement get_trades_with_filters method in SupabasePersistenceService
        # trades_data = await persistence_service.get_trades_with_filters(
        #     filters=filters,
        #     limit=limit,
        #     offset=offset
        # )
        
        # For now, return empty list with appropriate message
        if trading_mode == "both":
            return []  # Would return both paper and real trades
        elif trading_mode == "paper":
            return []  # Would return only paper trades
        else:  # real
            return []  # Would return only real trades
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trades: {str(e)}"
        )

@router.get("/{user_id}/open", response_model=List[Trade], status_code=status.HTTP_200_OK)
async def get_open_trades(
    user_id: UUID,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both"
):
    """
    Get only open trades for the specified user and trading mode.
    
    Args:
        user_id: User identifier
        trading_mode: Filter by trading mode ('paper', 'real', 'both')
        
    Returns:
        List of open trades
    """
    try:
        # Use the general trades endpoint with status filter
        return await get_user_trades(
            user_id=user_id,
            trading_mode=trading_mode,
            status_filter="open",
            persistence_service=persistence_service
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve open trades: {str(e)}"
        )

@router.get("/{user_id}/performance", response_model=PerformanceMetrics, status_code=status.HTTP_200_OK)
async def get_trading_performance(
    user_id: UUID,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode: 'paper' or 'real'")] = "paper",
    date_from: Annotated[Optional[date], Query(description="Start date for metrics calculation (YYYY-MM-DD)")] = None,
    date_to: Annotated[Optional[date], Query(description="End date for metrics calculation (YYYY-MM-DD)")] = None
):
    """
    Get trading performance metrics for the specified mode and period.
    
    Args:
        user_id: User identifier
        trading_mode: Trading mode ('paper' or 'real') - 'both' not supported for metrics
        date_from: Start date for metrics calculation
        date_to: End date for metrics calculation
        
    Returns:
        Performance metrics for the specified period and mode
    """
    try:
        if trading_mode == "both":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Performance metrics cannot be calculated for 'both' modes. Use 'paper' or 'real'."
            )
            
        # TODO: Implement performance metrics calculation in persistence service
        # For now, return a placeholder with default values
        
        default_metrics = PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            avg_pnl_per_trade=0.0,
            best_trade_pnl=0.0,
            worst_trade_pnl=0.0,
            best_trade_symbol=None,
            worst_trade_symbol=None,
            period_start=datetime.combine(date_from, datetime.min.time()) if date_from else None,
            period_end=datetime.combine(date_to, datetime.min.time()) if date_to else None,
            total_volume_traded=0.0
        )
        
        return default_metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate performance metrics: {str(e)}"
        )

@router.get("/{user_id}/count", status_code=status.HTTP_200_OK)
async def get_trades_count(
    user_id: UUID,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both",
    status_filter: Annotated[Optional[str], Query(description="Position status filter: 'open', 'closed', etc.")] = None,
    date_from: Annotated[Optional[date], Query(description="Start date filter (YYYY-MM-DD)")] = None,
    date_to: Annotated[Optional[date], Query(description="End date filter (YYYY-MM-DD)")] = None
):
    """
    Get count of trades matching the specified criteria.
    
    Args:
        user_id: User identifier
        trading_mode: Filter by trading mode ('paper', 'real', 'both')
        status_filter: Filter by position status
        date_from: Filter trades from this date
        date_to: Filter trades until this date
        
    Returns:
        Count information by trading mode
    """
    try:
        # TODO: Implement count method in persistence service
        # For now, return placeholder counts
        
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
