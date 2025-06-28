from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from core.domain_models.user_configuration_models import (
    UserConfiguration, 
    UserConfigurationUpdate
)
from services.config_service import ConfigurationService
from dependencies import get_config_service
from core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
    CredentialError,
)

router = APIRouter()

@router.get("/config", response_model=UserConfiguration, response_model_by_alias=True)
async def get_user_config(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Retorna la configuraciรณn actual del usuario.
    """
    try:
        config = await config_service.get_user_configuration()
        if not config:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User configuration not found.")
        return config
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar la configuraciรณn: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al cargar la configuraciรณn: {e}"
        )

@router.patch("/config", response_model=UserConfiguration, response_model_by_alias=True)
async def update_user_config(
    config_update: UserConfigurationUpdate,
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuraciรณn del usuario.
    Utiliza Pydantic para un parcheo robusto y seguro.
    """
    try:
        existing_config = await config_service.get_user_configuration()
        if not existing_config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User configuration not found.")

        update_data = config_update.model_dump(exclude_unset=True)
        
        updated_config = existing_config.model_copy(update=update_data)
        
        await config_service.save_user_configuration(updated_config)
        return updated_config
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la configuraciรณn: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al actualizar la configuraciรณn: {e}"
        )

@router.post("/config/real-trading-mode/activate", response_model=dict)
async def activate_real_trading_mode_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Intenta activar el modo de operativa real limitada para el usuario.
    """
    try:
        await config_service.activate_real_trading_mode()
        return {"message": "Modo de operativa real limitada activado exitosamente."}
    except RealTradeLimitReachedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except (BinanceAPIError, InsufficientUSDTBalanceError, CredentialError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuraciรณn: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

@router.post("/config/real-trading-mode/deactivate", response_model=dict)
async def deactivate_real_trading_mode_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Desactiva el modo de operativa real limitada para el usuario.
    """
    try:
        await config_service.deactivate_real_trading_mode()
        return {"message": "Modo de operativa real limitada desactivado."}
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuraciรณn: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")

@router.get("/config/real-trading-mode/status", response_model=dict)
async def get_real_trading_mode_status_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Retorna el estado actual del modo de operativa real limitada y el contador para el usuario.
    """
    try:
        status_data = await config_service.get_real_trading_status()
        return status_data
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuraciรณn: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")
