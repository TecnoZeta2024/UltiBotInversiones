from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

from ultibot_backend.api.v1.models.performance_models import (
    StrategyPerformanceResponse,
    OperatingMode
)
from ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.main import get_performance_service, FIXED_USER_ID # Importar servicio y FIXED_USER_ID

router = APIRouter()

# Dependencia para obtener el User ID (usando FIXED_USER_ID para v1.0)
async def get_current_user_id() -> UUID:
    return FIXED_USER_ID

@router.get(
    "/strategies",
    response_model=StrategyPerformanceResponse,
    summary="Get Performance Data for Strategies",
    description="Retrieves a list of performance metrics for each trading strategy, "
                "optionally filtered by operating mode.",
)
async def get_strategies_performance(
    mode: Optional[OperatingMode] = Query(
        None,
        description="Filter by operating mode (paper or real). If not provided, "
                    "data for all modes applicable to the user will be returned."
    ),
    performance_service: PerformanceService = Depends(get_performance_service),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Endpoint to fetch performance data for trading strategies.

    - **mode**: Optionally filter by 'paper' or 'real' trading mode.
    """
    return await performance_service.get_all_strategies_performance(
        user_id=current_user_id, mode_filter=mode
    )
