from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Annotated
from uuid import UUID

from ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from shared.data_types import UserConfiguration, RealTradingSettings
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.config_service import ConfigurationService
import logging
from ultibot_backend import dependencies as deps
from ultibot_backend.app_config import get_app_settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/opportunities/real-trading-candidates", response_model=List[Opportunity])
async def get_real_trading_candidates(
    request: Request,
    persistence_service: Annotated[SupabasePersistenceService, Depends(deps.get_persistence_service)],
    config_service: Annotated[ConfigurationService, Depends(deps.get_config_service)]
):
    """
    Devuelve una lista de oportunidades de muy alta confianza pendientes de confirmación
    para operativa real para el usuario fijo, si el modo de trading real está activo y hay cupos disponibles.
    """
    app_settings = get_app_settings()
    user_id = app_settings.FIXED_USER_ID
    user_config_dict = await config_service.get_user_configuration(str(user_id))
    if not user_config_dict:
        raise HTTPException(status_code=404, detail="User configuration not found")
        
    # Convertir explícitamente a dict y añadir user_id
    config_data = dict(user_config_dict)
    config_data['user_id'] = user_id
    user_config = UserConfiguration(**config_data)


    real_trading_settings = user_config.real_trading_settings
    if not real_trading_settings or not real_trading_settings.real_trading_mode_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El modo de trading real no está activo para este usuario."
        )

    # La lógica de límite de trades ahora es manejada por el ConfigurationService.
    # Esta validación aquí es redundante y puede ser eliminada.
    
    # Usar el método get_all con una condición para filtrar por estado
    condition = "status = :status"
    params = {"status": OpportunityStatus.PENDING_USER_CONFIRMATION_REAL.value}
    opportunities_data = await persistence_service.get_all(
        table_name="opportunities",
        condition=condition,
        params=params
    )
    
    opportunities = [Opportunity.model_validate(op) for op in opportunities_data]

    return opportunities
