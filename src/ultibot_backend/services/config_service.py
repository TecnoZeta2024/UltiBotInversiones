import logging
from typing import Optional
from uuid import UUID, uuid4

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, persistence_service: SupabasePersistenceService):
        self.persistence_service = persistence_service

    async def load_user_configuration(self, user_id: UUID) -> UserConfiguration:
        """
        Carga la configuración del usuario desde la base de datos.
        Si no se encuentra, retorna una configuración por defecto.
        Maneja errores de carga.
        """
        try:
            config_data = await self.persistence_service.get_user_configuration(user_id)
            if config_data:
                return UserConfiguration(**config_data)
            else:
                logger.info(f"No se encontró configuración para el usuario {user_id}. Retornando configuración por defecto.")
                return self.get_default_configuration()
        except Exception as e:
            logger.error(f"Error al cargar la configuración para el usuario {user_id}: {e}", exc_info=True)
            # Intentar arrancar con una configuración mínima segura por defecto en caso de error crítico
            return self.get_default_configuration()

    async def save_user_configuration(self, user_id: UUID, config: UserConfiguration):
        """
        Guarda la configuración del usuario en la base de datos.
        Maneja errores de guardado.
        """
        try:
            # Asegurar que los datos se serialicen correctamente para JSONB
            config_dict = config.model_dump(mode='json', by_alias=True, exclude_none=True)
            await self.persistence_service.upsert_user_configuration(user_id, config_dict)
            logger.info(f"Configuración guardada exitosamente para el usuario {user_id}.")
        except Exception as e:
            logger.error(f"Error al guardar la configuración para el usuario {user_id}: {e}", exc_info=True)
            raise ConfigurationError(f"No se pudo guardar la configuración para el usuario {user_id}.") from e

    def get_default_configuration(self) -> UserConfiguration:
        """
        Provee una instancia de UserConfiguration con valores por defecto.
        """
        # Para la v1.0, se puede asumir un user_id fijo si no hay un sistema de autenticación de usuarios completo.
        # Aquí se usa un UUID de ejemplo, que debería ser reemplazado por el user_id real del usuario autenticado.
        default_user_id = UUID("00000000-0000-0000-0000-000000000001") # Ejemplo de UUID fijo para desarrollo

        return UserConfiguration(
            id=uuid4(), # Generar un nuevo UUID para la configuración
            user_id=default_user_id,
            selectedTheme='dark',
            enableTelegramNotifications=False,
            defaultPaperTradingCapital=10000.0,
            aiAnalysisConfidenceThresholds={"paperTrading": 0.7, "realTrading": 0.8},
            # Otros valores por defecto según sea necesario
        )
