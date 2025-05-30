from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar SupabasePersistenceService
from src.ultibot_backend.core.exceptions import ConfigurationError

router = APIRouter()

# Para la v1.0, se puede asumir un user_id fijo si no hay un sistema de autenticación de usuarios completo.
# Este user_id debería ser el mismo que el usado en ConfigService.get_default_configuration()
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Dependencia para obtener el ConfigService
def get_config_service(persistence_service: SupabasePersistenceService = Depends(SupabasePersistenceService)) -> ConfigService:
    return ConfigService(persistence_service)

@router.get("/config", response_model=UserConfiguration)
async def get_user_config(config_service: ConfigService = Depends(get_config_service)):
    """
    Retorna la configuración actual del usuario.
    """
    try:
        config = await config_service.load_user_configuration(FIXED_USER_ID)
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
    updated_config: UserConfiguration, # Pydantic se encarga de la validación de entrada
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Permite actualizar parcialmente la configuración del usuario.
    """
    try:
        # Cargar la configuración existente para fusionar los cambios
        current_config = await config_service.load_user_configuration(FIXED_USER_ID)
        
        # Fusionar los campos de updated_config en current_config
        # Usamos model_dump(exclude_unset=True) para solo incluir los campos que fueron explícitamente enviados
        # en la solicitud PATCH, evitando sobrescribir con None los campos no enviados.
        update_data = updated_config.model_dump(exclude_unset=True, by_alias=True)
        
        # Asegurarse de no sobrescribir el user_id o id de la configuración si no se desea
        update_data.pop('user_id', None)
        update_data.pop('id', None)
        update_data.pop('createdAt', None)
        update_data.pop('updatedAt', None)

        # Fusionar los datos. Pydantic's copy(update=...) es ideal para esto.
        # Esto creará una nueva instancia de UserConfiguration con los campos actualizados.
        merged_config = current_config.model_copy(update=update_data)

        await config_service.save_user_configuration(FIXED_USER_ID, merged_config)
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
