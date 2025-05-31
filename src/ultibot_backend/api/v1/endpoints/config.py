from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
)

router = APIRouter()

FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Dependencia para obtener el ConfigService con sus dependencias
def get_config_service(
    persistence_service: SupabasePersistenceService = Depends(SupabasePersistenceService),
    credential_service: CredentialService = Depends(CredentialService),
    portfolio_service: PortfolioService = Depends(PortfolioService),
    notification_service: NotificationService = Depends(NotificationService) # Añadir NotificationService
) -> ConfigService:
    return ConfigService(persistence_service, credential_service, portfolio_service, notification_service)

@router.get("/config", response_model=UserConfiguration)
async def get_user_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Retorna la configuración actual del usuario.
    """
    try:
        config = await config_service.get_user_configuration(FIXED_USER_ID)
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
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuración del usuario.
    """
    try:
        current_config = await config_service.get_user_configuration(FIXED_USER_ID)
        
        update_data = updated_config.model_dump(exclude_unset=True, by_alias=True)
        
        update_data.pop('user_id', None)
        update_data.pop('id', None)
        update_data.pop('createdAt', None)
        update_data.pop('updatedAt', None)

        merged_config = current_config.model_copy(update=update_data)

        await config_service.save_user_configuration(merged_config) # Corregido: no pasar user_id aquí
        return merged_config
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
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Intenta activar el modo de operativa real limitada.
    """
    try:
        await config_service.activate_real_trading_mode(FIXED_USER_ID)
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
            detail=f"Error de configuración: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al activar el modo real: {e}"
        )

@router.post("/config/real-trading-mode/deactivate", response_model=dict)
async def deactivate_real_trading_mode_endpoint(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Desactiva el modo de operativa real limitada.
    """
    try:
        await config_service.deactivate_real_trading_mode(FIXED_USER_ID)
        return {"message": "Modo de operativa real limitada desactivado."}
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuración: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al desactivar el modo real: {e}"
        )

@router.get("/config/real-trading-mode/status", response_model=dict)
async def get_real_trading_mode_status_endpoint(
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Retorna el estado actual del modo de operativa real limitada y el contador.
    """
    try:
        status_data = await config_service.get_real_trading_status(FIXED_USER_ID)
        return status_data
    except ConfigurationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuración: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al obtener el estado del modo real: {e}"
        )
