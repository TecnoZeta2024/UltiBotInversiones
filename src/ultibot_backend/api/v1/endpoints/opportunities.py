from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from src.shared.data_types import UserConfiguration, RealTradingSettings
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigurationService
import logging
from src.ultibot_backend.dependencies import (
    get_persistence_service,
    get_config_service
)
from src.ultibot_backend.app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/real-trading-candidates", response_model=List[Opportunity])
async def get_real_trading_candidates(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Devuelve una lista de oportunidades de muy alta confianza pendientes de confirmación
    para operativa real para el usuario fijo, si el modo de trading real está activo y hay cupos disponibles.
    """
    user_id = settings.FIXED_USER_ID
    user_config_dict = await config_service.get_user_configuration(str(user_id))
    if not user_config_dict:
        raise HTTPException(status_code=404, detail="User configuration not found")
        
    # Convertir explcitamente a dict y aadir user_id
    config_data = dict(user_config_dict)
    config_data['user_id'] = user_id
    user_config = UserConfiguration(**config_data)


    real_trading_settings = user_config.realTradingSettings
    if real_trading_settings is None:
        real_trading_settings = RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_real_trades=5
        )

    # if not real_trading_settings.real_trading_mode_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="El modo de trading real no est activo para este usuario."
    #     )

    closed_real_trades_count = await persistence_service.get_closed_trades_count(
        user_id=user_id,
        is_real_trade=True
    )

    if closed_real_trades_count >= real_trading_settings.max_real_trades:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Se ha alcanzado el lmite de {real_trading_settings.max_real_trades} operaciones reales."
        )

    opportunities = await persistence_service.get_opportunities_by_status(
        user_id=user_id,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL
    )

    return opportunities

@router.get("/ai", response_model=List[Opportunity])
async def get_ai_opportunities(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Endpoint para compatibilidad con la ruta anterior de oportunidades de IA.
    Redirige o sirve los mismos datos que /opportunities/real-trading-candidates.
    """
    return await get_real_trading_candidates(persistence_service, config_service)
