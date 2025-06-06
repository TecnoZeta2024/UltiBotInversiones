from fastapi import APIRouter, Depends, Query
from typing import Optional
from uuid import UUID

from ..models.performance_models import (
    StrategyPerformanceResponse,
    OperatingMode
)
from ....services.performance_service import PerformanceService
from src.ultibot_backend.dependencies import get_performance_service # Importar desde dependencies
# from src.ultibot_backend.app_config import settings # Ya no se usa settings.FIXED_USER_ID
from src.ultibot_backend.security import core as security_core
from src.ultibot_backend.security import schemas as security_schemas
from fastapi import HTTPException, status # Para manejar errores de UUID

router = APIRouter()

# Ya no se necesita get_current_user_id, se usará get_current_active_user

@router.get(
    "/strategies",
    response_model=StrategyPerformanceResponse,
    summary="Get Performance Data for Strategies",
    description="Retrieves a list of performance metrics for each trading strategy, "
                "optionally filtered by operating mode.",
)
async def get_strategies_performance(
    performance_service: PerformanceService = Depends(get_performance_service),
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    mode: Optional[OperatingMode] = Query(
        None,
        description="Filter by operating mode (paper or real). If not provided, "
                    "data for all modes applicable to the user will be returned."
    )
):
    """
    Endpoint to fetch performance data for trading strategies for the authenticated user.

    - **current_user**: Authenticated user object.
    - **mode**: Optionally filter by 'paper' or 'real' trading mode.
    """
    if not isinstance(current_user.id, UUID):
        # Este check es más por robustez y para satisfacer a Pylance si hubiera dudas.
        # La dependencia get_current_active_user ya debería asegurar un User válido.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

    return await performance_service.get_all_strategies_performance(
        user_id=current_user.id, mode_filter=mode
    )
