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
                return self.get_default_configuration(user_id) # Pasar user_id
        except Exception as e:
            logger.error(f"Error al cargar la configuración para el usuario {user_id}: {e}", exc_info=True)
            # Intentar arrancar con una configuración mínima segura por defecto en caso de error crítico
            return self.get_default_configuration(user_id) # Pasar user_id

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

    def get_default_configuration(self, user_id: UUID) -> UserConfiguration:
        """
        Provee una instancia de UserConfiguration con valores por defecto para un user_id dado.
        """
        return UserConfiguration(
            id=user_id, # Usar el user_id proporcionado como ID de la configuración
            user_id=user_id,
            selectedTheme='dark',
            enableTelegramNotifications=False,
            defaultPaperTradingCapital=10000.0,
            paperTradingActive=True, # Nuevo campo por defecto
            aiAnalysisConfidenceThresholds={"paperTrading": 0.7, "realTrading": 0.8},
            favoritePairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"], # Valores por defecto
            # Otros valores por defecto según sea necesario
        )
