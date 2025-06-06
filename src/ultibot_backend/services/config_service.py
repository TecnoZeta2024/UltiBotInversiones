from __future__ import annotations # Importar para type hints adelantados

import logging
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from src.shared.data_types import UserConfiguration, RealTradingSettings, AIAnalysisConfidenceThresholds
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
    UltiBotError
)
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, 
                 persistence_service: SupabasePersistenceService, 
                 credential_service: CredentialService,
                 portfolio_service: PortfolioService,
                 # notification_service: NotificationService, # Made optional to break circular dependency
                 notification_service: Optional[NotificationService] = None, 
                 user_id: Optional[UUID] = None):
        self.persistence_service = persistence_service
        self.credential_service = credential_service
        self.portfolio_service = portfolio_service
        self.notification_service = notification_service # Can be None initially
        self._current_user_id: Optional[UUID] = user_id # Internally, we'll store UUID
        self._user_configuration: Optional[UserConfiguration] = None

    def set_notification_service(self, notification_service: NotificationService):
        """Allows setting NotificationService after initialization to break circular dependency."""
        if not self.notification_service: # Only set if not already set (e.g. by constructor)
            self.notification_service = notification_service
        else:
            logger.warning("NotificationService already set in ConfigService, ignoring attempt to reset.")

    async def _load_config_from_db(self, user_id: UUID) -> UserConfiguration:
        """Método privado para cargar desde DB o devolver default."""
        # This method consistently uses UUID as it's internal and talks to persistence
        try:
            config_data = await self.persistence_service.get_user_configuration(user_id)
            if config_data:
                user_config = UserConfiguration(**config_data)
                if user_config.realTradingSettings is None:
                    user_config.realTradingSettings = RealTradingSettings(
                        real_trading_mode_active=False,
                        real_trades_executed_count=0,
                        max_real_trades=5
                    )
                return user_config
            else:
                logger.info(f"No se encontró configuración para el usuario {user_id}. Retornando configuración por defecto.")
                return self.get_default_configuration(user_id)
        except Exception as e:
            logger.error(f"Error al cargar la configuración para el usuario {user_id}: {e}", exc_info=True)
            return self.get_default_configuration(user_id) # user_id here is UUID

    async def get_user_configuration(self, user_id_str: Optional[str] = None) -> UserConfiguration:
        """
        Obtiene la configuración del usuario.
        Si user_id_str no se provee, usa el _current_user_id (UUID) si está seteado.
        Carga desde la base de datos si no está en caché o si el user_id cambia.
        El parámetro de entrada es string, pero internamente se maneja como UUID.
        """
        target_user_uuid: Optional[UUID] = None
        if user_id_str:
            try:
                target_user_uuid = UUID(user_id_str)
            except ValueError:
                raise ConfigurationError(f"Formato de user_id inválido: {user_id_str}. Debe ser un UUID válido.")
        else:
            target_user_uuid = self._current_user_id

        if not target_user_uuid:
            raise ConfigurationError("Se requiere user_id para obtener la configuración.")

        if self._user_configuration and self._current_user_id == target_user_uuid:
            return self._user_configuration
        
        self._current_user_id = target_user_uuid
        self._user_configuration = await self._load_config_from_db(target_user_uuid)
        return self._user_configuration
    
    def get_cached_user_configuration(self) -> Optional[UserConfiguration]:
        """Retorna la configuración cacheada si existe."""
        return self._user_configuration

    async def reload_user_configuration(self, user_id_str: Optional[str] = None) -> UserConfiguration:
        """Fuerza la recarga de la configuración desde la base de datos."""
        target_user_uuid: Optional[UUID] = None
        if user_id_str:
            try:
                target_user_uuid = UUID(user_id_str)
            except ValueError:
                raise ConfigurationError(f"Formato de user_id inválido: {user_id_str}. Debe ser un UUID válido.")
        else:
            target_user_uuid = self._current_user_id
            
        if not target_user_uuid:
            raise ConfigurationError("Se requiere user_id para recargar la configuración.")
        
        self._current_user_id = target_user_uuid
        self._user_configuration = await self._load_config_from_db(target_user_uuid)
        return self._user_configuration

    async def set_current_user_id(self, user_id_str: str):
        """Establece el user_id actual (desde string) y carga su configuración."""
        if not user_id_str:
            raise ConfigurationError("user_id_str no puede ser nulo o vacío.")
        try:
            target_user_uuid = UUID(user_id_str)
        except ValueError:
            raise ConfigurationError(f"Formato de user_id inválido: {user_id_str}. Debe ser un UUID válido.")

        if self._current_user_id != target_user_uuid:
            self._current_user_id = target_user_uuid
            self._user_configuration = await self._load_config_from_db(target_user_uuid)
        elif not self._user_configuration: # Si es el mismo ID pero no hay config cargada
            self._user_configuration = await self._load_config_from_db(target_user_uuid)

    async def save_user_configuration(self, config: UserConfiguration):
        """
        Guarda la configuración del usuario en la base de datos.
        Actualiza la caché interna.
        Maneja errores de guardado.
        """
        if not config.user_id: # config.user_id es UUID
            raise ConfigurationError("UserConfiguration debe tener un user_id para ser guardada.")
        
        try:
            config_dict = config.model_dump(mode='json', by_alias=True, exclude_none=True)
            await self.persistence_service.upsert_user_configuration(config.user_id, config_dict) # persistence espera UUID
            logger.info(f"Configuración guardada exitosamente para el usuario {config.user_id}.")
            self._current_user_id = config.user_id # UUID
            self._user_configuration = config
        except Exception as e:
            logger.error(f"Error al guardar la configuración para el usuario {config.user_id}: {e}", exc_info=True)
            raise ConfigurationError(f"No se pudo guardar la configuración para el usuario {config.user_id}.") from e

    def get_default_configuration(self, user_id: UUID) -> UserConfiguration: # user_id aquí es UUID
        """
        Provee una instancia de UserConfiguration con valores por defecto para un user_id dado.
        """
        return UserConfiguration(
            id=uuid4(),
            user_id=user_id,
            selectedTheme='dark',
            enableTelegramNotifications=False,
            defaultPaperTradingCapital=10000.0,
            paperTradingActive=True,
            aiAnalysisConfidenceThresholds=AIAnalysisConfidenceThresholds(
                paperTrading=0.7, 
                realTrading=0.8,
                dataVerificationPriceDiscrepancyPercent=5.0,
                dataVerificationMinVolumeQuote=1000.0
            ),
            favoritePairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            notificationPreferences=[],
            watchlists=[],
            aiStrategyConfigurations=[],
            mcpServerPreferences=[],
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_real_trades=5
            )
        )

    def is_paper_trading_mode_active(self) -> bool:
        """
        Verifica si el modo Paper Trading está activo según la configuración cacheada.
        Requiere que la configuración haya sido cargada previamente (y _current_user_id esté seteado).
        """
        if not self._user_configuration:
            # Esto podría pasar si se llama antes de cargar alguna configuración de usuario.
            # O si la carga falló y _user_configuration es None.
            # Para V1 con FIXED_USER_ID, es probable que la config se cargue al inicio.
            # Para multi-usuario, esto dependerá del contexto.
            logger.warning("Se intentó verificar el modo paper trading sin configuración de usuario cargada en ConfigService.")
            # Devolver False o un valor por defecto, o lanzar un error podría ser una opción.
            # Si se espera que la config esté siempre cargada para el usuario en contexto, lanzar error es más estricto.
            # Por ahora, mantenemos el comportamiento de devolver False.
            return False 
        return self._user_configuration.paperTradingActive is True

    async def activate_real_trading_mode(self, user_id_str: str, min_usdt_balance: float = 10.0):
        """
        Activa el modo de operativa real limitada para el usuario.
        Realiza verificaciones de pre-activación.
        user_id_str es string.
        """
        user_id_uuid = UUID(user_id_str) # Convertir a UUID para uso interno y con get_user_configuration (si se decide mantenerlo con UUID)
                                      # O directamente pasar user_id_str si get_user_configuration lo toma.
                                      # Dado que modifiqué get_user_configuration para tomar str, lo uso.
        config = await self.get_user_configuration(user_id_str=user_id_str)
        real_settings = config.realTradingSettings
        assert real_settings is not None

        current_trades_count = real_settings.real_trades_executed_count
        REAL_TRADE_LIMIT = 5 # Idealmente, esto también podría ser parte de UserConfiguration
        if current_trades_count >= REAL_TRADE_LIMIT:
            error_message = f"Límite de {REAL_TRADE_LIMIT} operaciones reales alcanzado."
            if self.notification_service: # Check if notification_service is available
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message) # config.user_id es UUID
            else:
                logger.warning("NotificationService not available in ConfigService. Cannot send activation failed notification.")
            raise RealTradeLimitReachedError(
                message=error_message,
                executed_count=current_trades_count,
                limit=REAL_TRADE_LIMIT
            )

        try:
            await self.credential_service.verify_binance_api_key(config.user_id) # credential_service espera UUID
            logger.info(f"Verificación de API Key de Binance exitosa para el usuario {config.user_id}.")
        except BinanceAPIError as e:
            error_message = f"Fallo en la verificación de la API Key de Binance: {e.message}"
            logger.error(f"Fallo en la verificación de la API Key de Binance para {config.user_id}: {e.message}", exc_info=True)
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message)
            raise e
        except Exception as e:
            error_message = f"Error inesperado al verificar la API Key de Binance: {str(e)}"
            logger.error(f"Error inesperado al verificar la API Key de Binance para {config.user_id}: {str(e)}", exc_info=True)
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message)
            raise BinanceAPIError(message=error_message, original_exception=e)

        try:
            usdt_balance = await self.portfolio_service.get_real_usdt_balance(config.user_id) # portfolio_service espera UUID
            if usdt_balance < min_usdt_balance:
                error_message = f"Saldo de USDT insuficiente. Se requiere al menos {min_usdt_balance} USDT."
                if self.notification_service:
                    await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message)
                raise InsufficientUSDTBalanceError(
                    message=error_message,
                    available_balance=usdt_balance,
                    required_amount=min_usdt_balance
                )
            logger.info(f"Saldo de USDT suficiente ({usdt_balance}) para el usuario {config.user_id}.")
        except InsufficientUSDTBalanceError as e:
            error_message = f"Saldo de USDT insuficiente: {e.message}"
            logger.error(f"Saldo de USDT insuficiente para {config.user_id}: {e.message}", exc_info=True)
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message)
            raise e
        except Exception as e:
            error_message = f"Error inesperado al verificar el saldo de USDT: {str(e)}"
            logger.error(f"Error inesperado al verificar el saldo de USDT para {config.user_id}: {str(e)}", exc_info=True)
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config.user_id, error_message)
            raise InsufficientUSDTBalanceError(message=error_message, original_exception=e)

        real_settings.real_trading_mode_active = True
        await self.save_user_configuration(config)
        logger.info(f"Modo de operativa real limitada activado exitosamente para el usuario {config.user_id}.")
        if self.notification_service:
            await self.notification_service.send_real_trading_mode_activated_notification(config.user_id)

    async def deactivate_real_trading_mode(self, user_id_str: str):
        """
        Desactiva el modo de operativa real limitada para el usuario.
        user_id_str es string.
        """
        config = await self.get_user_configuration(user_id_str=user_id_str)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        if real_settings.real_trading_mode_active:
            real_settings.real_trading_mode_active = False
            await self.save_user_configuration(config)
            logger.info(f"Modo de operativa real limitada desactivado para el usuario {config.user_id}.")
        else:
            logger.info(f"El modo de operativa real limitada ya estaba inactivo para el usuario {config.user_id}.")

    async def increment_real_trades_count(self, user_id_str: str):
        """
        Incrementa el contador de operaciones reales ejecutadas.
        Este método debe ser llamado por TradingEngineService después de una operación real exitosa.
        user_id_str es string.
        """
        config = await self.get_user_configuration(user_id_str=user_id_str)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        REAL_TRADE_LIMIT = 5 # Idealmente, esto también podría ser parte de UserConfiguration
        if real_settings.real_trades_executed_count < REAL_TRADE_LIMIT:
            real_settings.real_trades_executed_count += 1
            await self.save_user_configuration(config)
            logger.info(f"Contador de operaciones reales incrementado para el usuario {config.user_id}. Nuevo conteo: {real_settings.real_trades_executed_count}")
        else:
            logger.warning(f"Se intentó incrementar el contador de operaciones reales para el usuario {config.user_id}, pero ya se alcanzó el límite de {REAL_TRADE_LIMIT}.")

    async def get_real_trading_status(self, user_id_str: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual del modo de operativa real limitada y el contador.
        user_id_str es string.
        """
        config = await self.get_user_configuration(user_id_str=user_id_str)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        REAL_TRADE_LIMIT = 5 # Idealmente, esto también podría ser parte de UserConfiguration
        return {
            "isActive": real_settings.real_trading_mode_active,
            "executedCount": real_settings.real_trades_executed_count,
            "limit": REAL_TRADE_LIMIT
        }
