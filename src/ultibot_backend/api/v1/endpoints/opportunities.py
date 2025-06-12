"""
Endpoints de la API para la gestión y consulta de oportunidades de trading.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from ...core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from ...dependencies import PersistenceServiceDep, ConfigurationServiceDep
from ...app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

@router.get("/real-trading-candidates", response_model=List[Opportunity])
async def get_real_trading_candidates(
    persistence_service = PersistenceServiceDep,
    config_service = ConfigurationServiceDep,
):
    """
    Devuelve una lista de oportunidades de muy alta confianza pendientes de confirmación
    para operativa real, si el modo de trading real está activo y hay cupos disponibles.
    """
    user_id = settings.FIXED_USER_ID
    
    try:
        user_config = await config_service.get_user_configuration(user_id)
        if not user_config or not user_config.real_trading_settings:
            raise HTTPException(status_code=404, detail="Configuración de usuario o de trading real no encontrada.")

        real_trading_settings = user_config.real_trading_settings

        # Comentado para permitir la visualización incluso si el modo no está activo.
        # if not real_trading_settings.real_trading_mode_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="El modo de trading real no está activo para este usuario."
        #     )

        closed_real_trades_count = await persistence_service.get_closed_trades_count(
            user_id=user_id, is_real_trade=True
        )

        if closed_real_trades_count >= real_trading_settings.max_real_trades:
            logger.warning(f"Límite de trades reales alcanzado para el usuario {user_id}.")
            return [] # Devolver lista vacía en lugar de error para que la UI pueda manejarlo.

        opportunities = await persistence_service.get_opportunities_by_status(
            user_id=user_id, status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL
        )

        return opportunities

    except Exception as e:
        logger.error(f"Error al obtener candidatos para trading real: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )

@router.get("/ai", response_model=List[Opportunity])
async def get_ai_opportunities(
    persistence_service = PersistenceServiceDep,
    config_service = ConfigurationServiceDep,
):
    """
    Endpoint para compatibilidad con la ruta anterior de oportunidades de IA.
    Redirige o sirve los mismos datos que /opportunities/real-trading-candidates.
    """
    logger.info("Redirigiendo llamada de /ai a /real-trading-candidates.")
    return await get_real_trading_candidates(persistence_service, config_service)
