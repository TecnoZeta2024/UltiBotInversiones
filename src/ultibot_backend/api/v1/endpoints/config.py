from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.dependencies import get_config_service
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
    CredentialError,
)
from src.ultibot_backend.app_config import settings

router = APIRouter()

@router.get("/config", response_model=UserConfiguration)
async def get_user_config(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Retorna la configuración actual del usuario.
    """
    try:
        user_id = settings.FIXED_USER_ID
        config = await config_service.get_user_configuration(user_id)
        if not config:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User configuration not found.")
        return config
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar la configuración: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al cargar la configuración: {e}"
        )

@router.patch("/config", response_model=UserConfiguration)
async def update_user_config(
    updated_config: UserConfiguration,
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuración del usuario.
    """
    try:
        user_id = settings.FIXED_USER_ID
        existing_config = await config_service.get_user_configuration(user_id)
        
        update_data = updated_config.model_dump(exclude_unset=True)
        
        # Prevenir la sobreescritura de campos críticos
        update_data.pop('user_id', None)
        update_data.pop('id', None)

        updated_config_model = existing_config.model_copy(update=update_data)
        
        await config_service.save_user_configuration(updated_config_model)
        return updated_config_model
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la configuración: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al actualizar la configuración: {e}"
        )

@router.post("/config/real-trading-mode/activate", response_model=dict)
async def activate_real_trading_mode_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Intenta activar el modo de operativa real limitada para el usuario.
    """
    try:
        user_id = settings.FIXED_USER_ID
        await config_service.activate_real_trading_mode(user_id)
        return {"message": "Modo de operativa real limitada activado exitosamente."}
    except RealTradeLimitReachedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except (BinanceAPIError, InsufficientUSDTBalanceError, CredentialError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuración: {e}")
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
        user_id = settings.FIXED_USER_ID
        await config_service.deactivate_real_trading_mode(user_id)
        return {"message": "Modo de operativa real limitada desactivado."}
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuración: {e}")
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
        user_id = settings.FIXED_USER_ID
        status_data = await config_service.get_real_trading_status(user_id)
        return status_data
    except ConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de configuración: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {e}")
