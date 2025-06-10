import logging
from typing import Optional, Dict, Any
from uuid import UUID

from src.ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration, RealTradingSettings
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.core.exceptions import ConfigurationError, RealTradeLimitReachedError, InsufficientUSDTBalanceError
from src.ultibot_backend.app_config import settings

logger = logging.getLogger(__name__)

class ConfigurationService:
    """
    Servicio para gestionar la configuración del usuario.
    """

    def __init__(
        self,
        persistence_service: SupabasePersistenceService,
        notification_service: NotificationService,
    ):
        self.persistence_service = persistence_service
        self.notification_service = notification_service
        self._user_configuration: Optional[UserConfiguration] = None

    async def _load_config_from_db(self, user_id: UUID) -> UserConfiguration:
        try:
            config_data = await self.persistence_service.get_user_configuration(user_id)
            if config_data:
                user_config = UserConfiguration(**config_data)
                if user_config.realTradingSettings is None:
                    user_config.realTradingSettings = RealTradingSettings(
                        real_trading_mode_active=False,
                    )
                return user_config
            else:
                logger.info(f"No configuration found for user {user_id}. Creating default configuration.")
                default_config = self.get_default_configuration(user_id)
                await self.save_user_configuration(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration for user {user_id}: {e}", exc_info=True)
            return self.get_default_configuration(user_id)

    async def get_user_configuration(self, user_id: UUID) -> UserConfiguration:
        # For simplicity, we can always load from DB. Caching can be added if performance becomes an issue.
        self._user_configuration = await self._load_config_from_db(user_id)
        return self._user_configuration

    def get_cached_user_configuration(self) -> Optional[UserConfiguration]:
        return self._user_configuration

    async def reload_user_configuration(self, user_id: UUID) -> UserConfiguration:
        self._user_configuration = await self._load_config_from_db(user_id)
        return self._user_configuration

    async def save_user_configuration(self, config: UserConfiguration):
        if not config.user_id:
            raise ConfigurationError("User ID is required to save a configuration.")

        try:
            config_dict = config.model_dump(mode='json', by_alias=True, exclude_none=True)
            await self.persistence_service.upsert_user_configuration(config_dict)
            logger.info(f"Configuration saved successfully for user {config.user_id}.")
            self._user_configuration = config
        except Exception as e:
            logger.error(f"Error saving configuration for user {config.user_id}: {e}", exc_info=True)
            raise ConfigurationError("Could not save configuration.") from e

    def get_default_configuration(self, user_id: UUID) -> UserConfiguration:
        return UserConfiguration(
            user_id=user_id,
            id=UUID(int=0), # A default, placeholder ID
            paperTradingActive=True,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_real_trades=5
            )
        )

    def is_paper_trading_mode_active(self) -> bool:
        if not self._user_configuration:
            logger.warning("Attempted to check paper trading mode without loaded user configuration.")
            return False
        return self._user_configuration.paperTradingActive is True

    async def activate_real_trading_mode(self, user_id: UUID, min_usdt_balance: float = 10.0):
        config = await self.get_user_configuration(user_id)
        real_settings = config.realTradingSettings
        assert real_settings is not None

        # This logic would typically involve checks against a portfolio service, etc.
        # For now, we just activate the mode if not already active.
        if real_settings.real_trading_mode_active:
            logger.info(f"Real trading mode is already active for user {user_id}.")
            return

        real_settings.real_trading_mode_active = True
        await self.save_user_configuration(config)
        logger.info(f"Real trading mode activated successfully for user {user_id}.")
        if self.notification_service:
            await self.notification_service.send_real_trading_mode_activated_notification(config)

    async def deactivate_real_trading_mode(self, user_id: UUID):
        config = await self.get_user_configuration(user_id)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        if real_settings.real_trading_mode_active:
            real_settings.real_trading_mode_active = False
            await self.save_user_configuration(config)
            logger.info(f"Real trading mode deactivated for user {user_id}.")

    async def increment_real_trades_count(self, user_id: UUID):
        config = await self.get_user_configuration(user_id)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        real_settings.real_trades_executed_count += 1
        await self.save_user_configuration(config)
        logger.info(f"Real trades count incremented for user {user_id}. New count: {real_settings.real_trades_executed_count}")

    async def get_real_trading_status(self, user_id: UUID) -> Dict[str, Any]:
        config = await self.get_user_configuration(user_id)
        real_settings = config.realTradingSettings
        assert real_settings is not None
        return {
            "real_trading_mode_active": real_settings.real_trading_mode_active,
            "real_trades_executed_count": real_settings.real_trades_executed_count,
            "max_real_trades": real_settings.max_real_trades,
        }
