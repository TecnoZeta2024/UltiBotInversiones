import logging
from typing import Optional
from uuid import UUID, uuid4

from src.shared.data_types import UserConfiguration
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, persistence_service: SupabasePersistenceService, user_id: Optional[UUID] = None): # user_id opcional en constructor
        self.persistence_service = persistence_service
        self._current_user_id: Optional[UUID] = user_id
        self._user_configuration: Optional[UserConfiguration] = None # Caché para la configuración

    async def _load_config_from_db(self, user_id: UUID) -> UserConfiguration:
        """Método privado para cargar desde DB o devolver default."""
        try:
            config_data = await self.persistence_service.get_user_configuration(user_id)
            if config_data:
                return UserConfiguration(**config_data)
            else:
                logger.info(f"No se encontró configuración para el usuario {user_id}. Retornando configuración por defecto.")
                return self.get_default_configuration(user_id)
        except Exception as e:
            logger.error(f"Error al cargar la configuración para el usuario {user_id}: {e}", exc_info=True)
            return self.get_default_configuration(user_id)

    async def get_user_configuration(self, user_id: Optional[UUID] = None) -> UserConfiguration:
        """
        Obtiene la configuración del usuario.
        Si user_id no se provee, usa el _current_user_id si está seteado.
        Carga desde la base de datos si no está en caché o si el user_id cambia.
        """
        target_user_id = user_id or self._current_user_id
        if not target_user_id:
            raise ConfigurationError("Se requiere user_id para obtener la configuración.")

        if self._user_configuration and self._current_user_id == target_user_id:
            return self._user_configuration
        
        self._current_user_id = target_user_id
        self._user_configuration = await self._load_config_from_db(target_user_id)
        return self._user_configuration
    
    def get_cached_user_configuration(self) -> Optional[UserConfiguration]:
        """Retorna la configuración cacheada si existe."""
        return self._user_configuration

    async def reload_user_configuration(self, user_id: Optional[UUID] = None) -> UserConfiguration:
        """Fuerza la recarga de la configuración desde la base de datos."""
        target_user_id = user_id or self._current_user_id
        if not target_user_id:
            raise ConfigurationError("Se requiere user_id para recargar la configuración.")
        
        self._current_user_id = target_user_id
        self._user_configuration = await self._load_config_from_db(target_user_id)
        return self._user_configuration

    async def set_current_user_id(self, user_id: UUID):
        """Establece el user_id actual y carga su configuración."""
        if self._current_user_id != user_id:
            self._current_user_id = user_id
            self._user_configuration = await self._load_config_from_db(user_id)
        elif not self._user_configuration: # Si es el mismo ID pero no hay config cargada
            self._user_configuration = await self._load_config_from_db(user_id)


    async def save_user_configuration(self, config: UserConfiguration): # user_id se toma de config.user_id
        """
        Guarda la configuración del usuario en la base de datos.
        Actualiza la caché interna.
        Maneja errores de guardado.
        """
        if not config.user_id:
            raise ConfigurationError("UserConfiguration debe tener un user_id para ser guardada.")
        
        try:
            config_dict = config.model_dump(mode='json', by_alias=True, exclude_none=True)
            await self.persistence_service.upsert_user_configuration(config.user_id, config_dict)
            logger.info(f"Configuración guardada exitosamente para el usuario {config.user_id}.")
            # Actualizar caché
            self._current_user_id = config.user_id
            self._user_configuration = config
        except Exception as e:
            logger.error(f"Error al guardar la configuración para el usuario {config.user_id}: {e}", exc_info=True)
            raise ConfigurationError(f"No se pudo guardar la configuración para el usuario {config.user_id}.") from e

    def get_default_configuration(self, user_id: UUID) -> UserConfiguration:
        """
        Provee una instancia de UserConfiguration con valores por defecto para un user_id dado.
        """
        # El docstring de "Maneja errores de carga." parece estar fuera de lugar aquí,
        # pertenecía a _load_config_from_db o get_user_configuration.
        # Lo he eliminado de aquí.
        return UserConfiguration(
            id=uuid4(), # El ID de la entidad UserConfiguration es propio
            user_id=user_id, # Este es el user_id al que pertenece la configuración
            selectedTheme='dark',
            enableTelegramNotifications=False,
            defaultPaperTradingCapital=10000.0,
            paperTradingActive=True,
            aiAnalysisConfidenceThresholds={"paperTrading": 0.7, "realTrading": 0.8},
            favoritePairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            # Inicializar listas vacías para evitar None donde se esperan listas
            notificationPreferences=[],
            watchlists=[],
            aiStrategyConfigurations=[],
            mcpServerPreferences=[],
            # Otros valores por defecto según sea necesario
        )

    def is_paper_trading_mode_active(self) -> bool:
        """
        Verifica si el modo Paper Trading está activo según la configuración cacheada.
        Requiere que la configuración haya sido cargada previamente.
        """
        if not self._user_configuration:
            # Esto podría ser un error si se llama antes de cargar la config.
            # O podría cargarla aquí si _current_user_id está seteado.
            # Por ahora, seremos estrictos: la config debe estar cargada.
            logger.warning("Se intentó verificar el modo paper trading sin configuración cargada.")
            # Podría retornar un valor por defecto o lanzar un error.
            # Retornar False como un default seguro si no hay config.
            return False 
        return self._user_configuration.paperTradingActive is True # Asegurar que sea explícitamente True
