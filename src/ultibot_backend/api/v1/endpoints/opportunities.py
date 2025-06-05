from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from src.shared.data_types import Opportunity, OpportunityStatus, UserConfiguration, RealTradingSettings # Añadir RealTradingSettings
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigService
import logging # Importar logging
from src.ultibot_backend.dependencies import ( # Importar desde el nuevo módulo de dependencias
    get_persistence_service,
    get_config_service
)
from src.ultibot_backend.app_config import settings # Importar settings

logger = logging.getLogger(__name__) # Inicializar logger

router = APIRouter()
print(f"DEBUG: Router de oportunidades inicializado: {router}") # Añadir print para depuración
logger.info(f"Router de oportunidades inicializado: {router}") # Añadir log para depuración

@router.get("/opportunities/real-trading-candidates", response_model=List[Opportunity])
async def get_real_trading_candidates(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Devuelve una lista de oportunidades de muy alta confianza pendientes de confirmación
    para operativa real, si el modo de trading real está activo y hay cupos disponibles.
    """
    # Las dependencias ya están inyectadas, no es necesario verificar si son None aquí.

    # config_service.get_user_configuration ya devuelve una instancia de UserConfiguration
    # o una configuración por defecto si no se encuentra en la BD.
    user_config: UserConfiguration = await config_service.get_user_configuration(str(settings.FIXED_USER_ID))

    # Asegurarse de que realTradingSettings no sea None
    real_trading_settings = user_config.realTradingSettings
    if real_trading_settings is None:
        # Usar una instancia por defecto, especificando los valores para evitar el falso positivo de Pylance
        real_trading_settings = RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_real_trades=5
        )
        # Opcional: podrías considerar guardar esta configuración por defecto en la BD
        # await config_service.upsert_user_configuration(FIXED_USER_ID, user_config.model_dump())

    # if not real_trading_settings.real_trading_mode_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="El modo de trading real no está activo para este usuario."
    #     )

    # Obtener el número de operaciones reales cerradas para el usuario
    closed_real_trades_count = await persistence_service.get_closed_trades_count(
        user_id=settings.FIXED_USER_ID,
        is_real_trade=True
    )

    if closed_real_trades_count >= real_trading_settings.max_real_trades:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Se ha alcanzado el límite de {real_trading_settings.max_real_trades} operaciones reales."
        )

    # Obtener oportunidades con estado PENDING_USER_CONFIRMATION_REAL
    opportunities = await persistence_service.get_opportunities_by_status(
        user_id=settings.FIXED_USER_ID,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL
    )

    return opportunities
