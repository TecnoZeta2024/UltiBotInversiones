from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

# Usando importaciones absolutas para mayor claridad y robustez
from src.ultibot_backend.api.v1.models.performance_models import (
    StrategyPerformanceResponse,
    OperatingMode
)
from src.ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.dependencies import get_performance_service
from src.ultibot_backend.app_config import settings
from fastapi import HTTPException, status

router = APIRouter()

@router.get(
    "/strategies",
    response_model=StrategyPerformanceResponse,
    summary="Get Performance Data for Strategies",
    description="Retrieves a list of performance metrics for each trading strategy, "
                "optionally filtered by operating mode.",
)
async def get_strategies_performance(
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
    user_id = settings.FIXED_USER_ID
    try:
        # La llamada al servicio ahora debería funcionar correctamente
        performance_data = await performance_service.get_all_strategies_performance(
            user_id=user_id, mode_filter=mode
        )
        return performance_data
    except Exception as e:
        # Captura de excepciones más específica podría ser útil aquí
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while fetching strategy performance: {str(e)}"
        )
