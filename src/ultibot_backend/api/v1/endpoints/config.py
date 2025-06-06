from __future__ import annotations # Importar para type hints adelantados

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Restaurar importaciรณn
from src.ultibot_backend.services.credential_service import CredentialService # Restaurar importaciรณn
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.security import core as security_core # Importar security_core
from src.ultibot_backend.security import schemas as security_schemas # Importar security_schemas
# Importar desde el nuevo mรณdulo de dependencias
from src.ultibot_backend.dependencies import (
    get_persistence_service,
    get_credential_service,
    get_portfolio_service,
    get_notification_service,
    get_config_service # No necesitamos el alias get_global_config_service
)
# from src.ultibot_backend.app_config import settings # Ya no se usará FIXED_USER_ID desde settings
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
)

router = APIRouter()

# Ya no se necesita get_config_service_dependency, se usará Depends(get_config_service) directamente.

@router.get("/config", response_model=UserConfiguration)
async def get_user_config(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Retorna la configuración actual del usuario autenticado.
    """
    try:
        config = await config_service.get_user_configuration(str(current_user.id))
        if not config: # Si get_user_configuration devuelve None porque no existe
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
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuraciรณn del usuario autenticado.
    """
    try:
        # Asegurarse de que el user_id en updated_config (si existe) coincida con el usuario autenticado o se ignore
        if updated_config.user_id and updated_config.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update configuration for another user."
            )

        # Forzar el user_id del usuario autenticado
        # updated_config_dict = updated_config.model_dump(exclude_unset=True)
        # updated_config_dict['user_id'] = current_user.id
        # config_to_save = UserConfiguration(**updated_config_dict)

        # Obtener la configuración actual para fusionar
        existing_config = await config_service.get_user_configuration(str(current_user.id))
        if not existing_config:
            # Si no existe configuración, creamos una nueva basada en updated_config,
            # asegurándonos de que el user_id es el correcto.
            new_config_data = updated_config.model_dump(exclude_unset=True)
            new_config_data['user_id'] = current_user.id
            # Aquí podríamos querer inicializar campos faltantes con valores por defecto de UserConfiguration
            # o simplemente guardar lo que se envió. Por ahora, guardamos lo enviado.
            config_to_save = UserConfiguration(**new_config_data)
            await config_service.save_user_configuration(config_to_save)
            return config_to_save

        # Fusionar: tomar updated_config, excluir valores no establecidos, y aplicar sobre existing_config
        update_data = updated_config.model_dump(exclude_unset=True)
        
        # Asegurar que no se intente cambiar el user_id a través del payload
        update_data.pop('user_id', None)
        update_data.pop('id', None) # El ID de la config (si es diferente al user_id) tampoco debería cambiarse así
        update_data.pop('createdAt', None)
        update_data.pop('updatedAt', None)

        # Aplicar actualizaciones a la configuración existente
        # merged_config = existing_config.model_copy(update=update_data)
        # El método save_user_configuration en ConfigService debería manejar la lógica de upsert
        # y la asignación correcta del user_id.
        # Le pasamos el UserConfiguration con los campos que el usuario quiere actualizar.
        # El servicio se encargará de fusionarlo con lo existente o crearlo.
        
        # Preparamos el objeto UserConfiguration que se pasará al servicio.
        # Debe tener el user_id correcto.
        payload_for_service = updated_config.model_copy(update={"user_id": current_user.id})
        # Limpiamos campos que no deben venir del payload para una actualización parcial
        # o que el servicio debe manejar internamente (como id, createdAt, updatedAt si son de la tabla y no del modelo)
        # El modelo UserConfiguration tiene id, user_id, createdAt, updatedAt.
        # El servicio save_user_configuration debe ser robusto a esto.
        
        # Re-evaluación: El servicio save_user_configuration espera un objeto UserConfiguration completo
        # que representa el estado deseado.
        # La lógica de fusión es más segura aquí en el endpoint.
        
        # Crear un UserConfiguration con los datos actualizados, asegurando el user_id correcto.
        # Esto es lo que se guardará.
        final_updated_data = existing_config.model_dump() # Empezar con todos los campos existentes
        final_updated_data.update(update_data) # Aplicar los cambios del payload
        final_updated_data['user_id'] = current_user.id # Asegurar el user_id correcto
        
        merged_config = UserConfiguration(**final_updated_data)
        
        await config_service.save_user_configuration(merged_config)
        return merged_config
    except ConfigurationError as e: # Este es el primer bloque ConfigurationError
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la configuraciรณn: {e}"
        )
    # El siguiente bloque ConfigurationError era el problemático y se elimina.
    # La lógica que usaba current_config dentro de un except ya no es necesaria
    # con la refactorización de la fusión.
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al actualizar la configuraciรณn: {e}"
        )

@router.post("/config/real-trading-mode/activate", response_model=dict)
async def activate_real_trading_mode_endpoint(
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Intenta activar el modo de operativa real limitada para el usuario autenticado.
    """
    try:
        await config_service.activate_real_trading_mode(str(current_user.id))
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
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Desactiva el modo de operativa real limitada para el usuario autenticado.
    """
    try:
        await config_service.deactivate_real_trading_mode(str(current_user.id))
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
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Retorna el estado actual del modo de operativa real limitada y el contador para el usuario autenticado.
    """
    try:
        status_data = await config_service.get_real_trading_status(str(current_user.id))
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
async def get_user_configuration( # Este endpoint parece un duplicado de GET /config
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Endpoint compatible con frontend: retorna la configuración de usuario autenticado.
    """
    try:
        config = await config_service.get_user_configuration(str(current_user.id))
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
