from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from typing import Optional
from uuid import UUID
from datetime import datetime

from api.v1.models.performance_models import (
    StrategyPerformanceResponse,
    OperatingMode,
)
from shared.data_types import PerformanceMetrics
from services.performance_service import PerformanceService
from dependencies import get_performance_service
from app_config import get_app_settings

router = APIRouter()

@router.get(
    "/strategies",
    response_model=StrategyPerformanceResponse,
    summary="Get Performance Data for Strategies",
    description="Retrieves a list of performance metrics for each trading strategy, "
                "optionally filtered by operating mode.",
)
async def get_strategies_performance(
    request: Request,
    performance_service: PerformanceService = Depends(get_performance_service),
    mode: Optional[OperatingMode] = Query(
        None,
        description="Filter by operating mode (paper or real). If not provided, "
                    "data for all modes applicable to the user will be returned."
    )
):
    """
    Endpoint to fetch performance data for trading strategies for the fixed user.

    - **mode**: Optionally filter by 'paper' or 'real' trading mode.
    """
    app_settings = get_app_settings()
    user_id = app_settings.FIXED_USER_ID
    try:
        performance_data = await performance_service.get_all_strategies_performance(
            user_id=user_id, mode_filter=mode
        )
        return performance_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while fetching strategy performance: {str(e)}"
        )

@router.get(
    "/metrics",
    response_model=PerformanceMetrics,
    summary="Get Performance Metrics for Trades",
    description="Retrieves aggregated performance metrics for trades, "
                "filterable by trading mode and date range.",
)
async def get_trades_performance(
    request: Request,
    trading_mode: OperatingMode = Query(..., description="The trading mode to filter by ('paper' or 'real')."),
    date_from: Optional[datetime] = Query(None, description="Start date for the analysis period (ISO 8601 format)."),
    date_to: Optional[datetime] = Query(None, description="End date for the analysis period (ISO 8601 format)."),
    performance_service: PerformanceService = Depends(get_performance_service),
):
    """
    Endpoint to fetch performance metrics for trades based on the specified mode and time frame.
    """
    app_settings = get_app_settings()
    user_id = app_settings.FIXED_USER_ID
    try:
        metrics = await performance_service.get_trade_performance_metrics(
            user_id=user_id,
            trading_mode=trading_mode.value,
            start_date=date_from,
            end_date=date_to,
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while fetching trade performance metrics: {str(e)}"
        )
