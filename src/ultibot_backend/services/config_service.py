from __future__ import annotations
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4

from shared.data_types import UserConfiguration, RealTradingSettings, AIAnalysisConfidenceThresholds, ServiceName
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
    CredentialError
)
from ultibot_backend.app_config import settings

if TYPE_CHECKING:
    from ultibot_backend.services.credential_service import CredentialService
    from ultibot_backend.services.portfolio_service import PortfolioService
    from ultibot_backend.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ConfigurationService:
    def __init__(self, persistence_service: SupabasePersistenceService):
        self.persistence_service = persistence_service
        self.credential_service: Optional["CredentialService"] = None
        self.portfolio_service: Optional["PortfolioService"] = None
        self.notification_service: Optional["NotificationService"] = None
        self._user_configuration: Optional[UserConfiguration] = None
        self._user_id: UUID = settings.FIXED_USER_ID

    def set_credential_service(self, credential_service: "CredentialService"):
        if not self.credential_service:
            self.credential_service = credential_service
        else:
            logger.warning("CredentialService already set in ConfigService, ignoring attempt to reset.")

    def set_portfolio_service(self, portfolio_service: "PortfolioService"):
        if not self.portfolio_service:
            self.portfolio_service = portfolio_service
        else:
            logger.warning("PortfolioService already set in ConfigService, ignoring attempt to reset.")

    def set_notification_service(self, notification_service: "NotificationService"):
        if not self.notification_service:
            self.notification_service = notification_service
        else:
            logger.warning("NotificationService already set in ConfigService, ignoring attempt to reset.")

    async def _load_config_from_db(self) -> UserConfiguration:
        try:
            config_data = await self.persistence_service.get_user_configuration()
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
                logger.info("No se encontró configuración. Creando configuración por defecto.")
                default_config = self.get_default_configuration()
                await self.save_user_configuration(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error al cargar la configuración: {e}", exc_info=True)
            return self.get_default_configuration()

    async def get_user_configuration(self) -> UserConfiguration:
        if self._user_configuration:
            return self._user_configuration
        
        self._user_configuration = await self._load_config_from_db()
        return self._user_configuration
    
    def get_cached_user_configuration(self) -> Optional[UserConfiguration]:
        return self._user_configuration

    async def reload_user_configuration(self) -> UserConfiguration:
        self._user_configuration = await self._load_config_from_db()
        return self._user_configuration

    async def save_user_configuration(self, config: UserConfiguration):
        if config.user_id != self._user_id:
            raise ConfigurationError("Intentando guardar una configuración para un ID de usuario incorrecto.")
        
        try:
            config_dict = config.model_dump(mode='json', by_alias=True, exclude_none=True)
            await self.persistence_service.upsert_user_configuration(config_dict)
            logger.info("Configuración guardada exitosamente.")
            self._user_configuration = config
        except Exception as e:
            logger.error(f"Error al guardar la configuración: {e}", exc_info=True)
            raise ConfigurationError("No se pudo guardar la configuración.") from e

    def get_default_configuration(self) -> UserConfiguration:
        return UserConfiguration(
            id=uuid4(),
            user_id=self._user_id,
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
        if not self._user_configuration:
            logger.warning("Se intentó verificar el modo paper trading sin configuración de usuario cargada.")
            return False 
        return self._user_configuration.paperTradingActive is True

    async def activate_real_trading_mode(self, min_usdt_balance: float = 10.0):
        if not self.credential_service or not self.portfolio_service:
            raise ConfigurationError("Services (Credential, Portfolio) not initialized in ConfigService.")

        config = await self.get_user_configuration()
        real_settings = config.realTradingSettings
        assert real_settings is not None

        current_trades_count = real_settings.real_trades_executed_count
        REAL_TRADE_LIMIT = 5
        if current_trades_count >= REAL_TRADE_LIMIT:
            error_message = f"Límite de {REAL_TRADE_LIMIT} operaciones reales alcanzado."
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config, error_message)
            raise RealTradeLimitReachedError(message=error_message, executed_count=current_trades_count, limit=REAL_TRADE_LIMIT)

        try:
            credential = await self.credential_service.get_credential(ServiceName.BINANCE_SPOT, "default")
            if not credential or not await self.credential_service.verify_credential(credential):
                 raise CredentialError("Fallo en la verificación de la API Key de Binance.")
            logger.info("Verificación de API Key de Binance exitosa.")
        except (BinanceAPIError, CredentialError) as e:
            error_message = f"Fallo en la verificación de la API Key de Binance: {e}"
            logger.error(error_message, exc_info=True)
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config, error_message)
            raise e

        try:
            usdt_balance = await self.portfolio_service.get_real_usdt_balance(self._user_id)
            if usdt_balance < min_usdt_balance:
                error_message = f"Saldo de USDT insuficiente. Se requiere al menos {min_usdt_balance} USDT."
                if self.notification_service:
                    await self.notification_service.send_real_trading_mode_activation_failed_notification(config, error_message)
                raise InsufficientUSDTBalanceError(message=error_message, available_balance=usdt_balance, required_amount=min_usdt_balance)
            logger.info(f"Saldo de USDT suficiente ({usdt_balance}).")
        except InsufficientUSDTBalanceError as e:
            if self.notification_service:
                await self.notification_service.send_real_trading_mode_activation_failed_notification(config, str(e))
            raise e

        real_settings.real_trading_mode_active = True
        await self.save_user_configuration(config)
        logger.info("Modo de operativa real limitada activado exitosamente.")
        if self.notification_service:
            await self.notification_service.send_real_trading_mode_activated_notification(config)

    async def deactivate_real_trading_mode(self):
        config = await self.get_user_configuration()
        real_settings = config.realTradingSettings
        assert real_settings is not None
        if real_settings.real_trading_mode_active:
            real_settings.real_trading_mode_active = False
            await self.save_user_configuration(config)
            logger.info("Modo de operativa real limitada desactivado.")
        else:
            logger.info("El modo de operativa real limitada ya estaba inactivo.")

    async def increment_real_trades_count(self):
        config = await self.get_user_configuration()
        real_settings = config.realTradingSettings
        assert real_settings is not None
        REAL_TRADE_LIMIT = 5
        if real_settings.real_trades_executed_count < REAL_TRADE_LIMIT:
            real_settings.real_trades_executed_count += 1
            await self.save_user_configuration(config)
            logger.info(f"Contador de operaciones reales incrementado. Nuevo conteo: {real_settings.real_trades_executed_count}")
        else:
            logger.warning(f"Se intentó incrementar el contador de operaciones reales, pero ya se alcanzó el límite de {REAL_TRADE_LIMIT}.")

    async def get_real_trading_status(self) -> Dict[str, Any]:
        config = await self.get_user_configuration()
        real_settings = config.realTradingSettings
        assert real_settings is not None
        REAL_TRADE_LIMIT = 5
        return {
            "isActive": real_settings.real_trading_mode_active,
            "executedCount": real_settings.real_trades_executed_count,
            "limit": REAL_TRADE_LIMIT
        }

