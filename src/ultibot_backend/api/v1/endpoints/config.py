from __future__ import annotations # Importar para type hints adelantados

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.services.config_service import ConfigurationService
from src.ultibot_backend.dependencies import get_config_service
from src.ultibot_backend.app_config import settings
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
)

router = APIRouter()

@router.get("/config", response_model=UserConfiguration)
async def get_user_config(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Retorna la configuración actual del usuario.
    """
    try:
        user_id_str = str(settings.FIXED_USER_ID)
        config = await config_service.get_user_configuration(user_id_str)
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

@router.patch("/config", response_model=UserConfiguration)
async def update_user_config(
    updated_config: UserConfiguration,
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuraciรณn del usuario.
    """
    try:
        user_id_str = str(settings.FIXED_USER_ID)
        user_id_uuid = settings.FIXED_USER_ID
        
        existing_config = await config_service.get_user_configuration(user_id_str)
        if not existing_config:
            new_config_data = updated_config.model_dump(exclude_unset=True)
            new_config_data['user_id'] = user_id_uuid
            config_to_save = UserConfiguration(**new_config_data)
            await config_service.save_user_configuration(config_to_save)
            return config_to_save

        update_data = updated_config.model_dump(exclude_unset=True)
        
        update_data.pop('user_id', None)
        update_data.pop('id', None)
        update_data.pop('createdAt', None)
        update_data.pop('updatedAt', None)

        final_updated_data = existing_config.model_dump()
        final_updated_data.update(update_data)
        final_updated_data['user_id'] = user_id_uuid
        
        merged_config = UserConfiguration(**final_updated_data)
        
        await config_service.save_user_configuration(merged_config)
        return merged_config
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
        user_id_str = str(settings.FIXED_USER_ID)
        await config_service.activate_real_trading_mode(user_id_str)
        return {"message": "Modo de operativa real limitada activado exitosamente."}
    except RealTradeLimitReachedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message
        )
    except BinanceAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except InsufficientUSDTBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuraciรณn: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al activar el modo real: {e}"
        )

@router.post("/config/real-trading-mode/deactivate", response_model=dict)
async def deactivate_real_trading_mode_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Desactiva el modo de operativa real limitada para el usuario.
    """
    try:
        user_id_str = str(settings.FIXED_USER_ID)
        await config_service.deactivate_real_trading_mode(user_id_str)
        return {"message": "Modo de operativa real limitada desactivado."}
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuraciรณn: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al desactivar el modo real: {e}"
        )

@router.get("/config/real-trading-mode/status", response_model=dict)
async def get_real_trading_mode_status_endpoint(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Retorna el estado actual del modo de operativa real limitada y el contador para el usuario.
    """
    try:
        user_id_str = str(settings.FIXED_USER_ID)
        status_data = await config_service.get_real_trading_status(user_id_str)
        return status_data
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuraciรณn: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al obtener el estado del modo real: {e}"
        )

@router.get("/user/configuration", response_model=UserConfiguration)
async def get_user_configuration(
    config_service: ConfigurationService = Depends(get_config_service)
):
    """
    Endpoint compatible con frontend: retorna la configuración de usuario.
    """
    try:
        user_id_str = str(settings.FIXED_USER_ID)
        config = await config_service.get_user_configuration(user_id_str)
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
