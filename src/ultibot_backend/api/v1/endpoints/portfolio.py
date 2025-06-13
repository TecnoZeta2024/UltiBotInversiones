"""
Endpoints de la API para la gestión y consulta del portafolio de trading.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

# --- Imports Arquitectónicos Corregidos ---
from src.ultibot_backend.core.domain_models.portfolio import PortfolioSnapshot
from src.ultibot_backend.core.ports import IPortfolioManager
from src.ultibot_backend.dependencies import get_portfolio_service, get_app_settings
from src.ultibot_backend.app_config import AppSettings

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])
logger = logging.getLogger(__name__)

@router.get("/snapshot", response_model=PortfolioSnapshot, status_code=status.HTTP_200_OK)
async def get_portfolio_snapshot(
    portfolio_service: IPortfolioManager = Depends(get_portfolio_service),
    app_settings: AppSettings = Depends(get_app_settings),
):
    """
    Obtiene una instantánea completa del portafolio para el usuario configurado.
    La instantánea incluye todas las posiciones, tanto en modo 'paper' como 'real'.
    """
    try:
        user_id = UUID(app_settings.fixed_user_id)
        logger.info(f"Obteniendo snapshot del portafolio para el usuario {user_id}.")
        
        # La firma del método en la interfaz IPortfolioManager solo requiere user_id.
        snapshot = await portfolio_service.get_full_portfolio_snapshot(user_id)
        
        return snapshot
    except Exception as e:
        logger.error(f"Fallo al obtener el snapshot del portafolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo obtener la instantánea del portafolio: {str(e)}",
        )
