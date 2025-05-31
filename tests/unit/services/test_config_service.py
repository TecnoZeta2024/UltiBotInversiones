import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.shared.data_types import UserConfiguration, RealTradingSettings
from src.ultibot_backend.core.exceptions import (
    ConfigurationError,
    BinanceAPIError,
    InsufficientUSDTBalanceError,
    RealTradeLimitReachedError,
    CredentialError
)

@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_credential_service():
    return AsyncMock(spec=CredentialService)

@pytest.fixture
def mock_portfolio_service():
    return AsyncMock(spec=PortfolioService)

@pytest.fixture
def mock_notification_service(): # Nuevo fixture para NotificationService
    return AsyncMock(spec=NotificationService)

@pytest.fixture
def config_service(mock_persistence_service, mock_credential_service, mock_portfolio_service, mock_notification_service):
    return ConfigService(
        persistence_service=mock_persistence_service,
        credential_service=mock_credential_service,
        portfolio_service=mock_portfolio_service,
        notification_service=mock_notification_service # Pasar el mock del servicio de notificación
    )

@pytest.fixture
def sample_user_id():
    return uuid4()

@pytest.fixture
def default_user_config(sample_user_id):
    return UserConfiguration(
        id=uuid4(),
        user_id=sample_user_id,
        selectedTheme='dark',
        enableTelegramNotifications=False,
        defaultPaperTradingCapital=10000.0,
        paperTradingActive=True,
        aiAnalysisConfidenceThresholds={"paperTrading": 0.7, "realTrading": 0.8},
        favoritePairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        notificationPreferences=[],
        watchlists=[],
        aiStrategyConfigurations=[],
        mcpServerPreferences=[],
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0
        )
    )

class TestConfigService:

    @pytest.mark.asyncio
    async def test_get_user_configuration_loads_from_db(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')
        
        config = await config_service.get_user_configuration(sample_user_id)
        
        mock_persistence_service.get_user_configuration.assert_called_once_with(sample_user_id)
        assert config.user_id == sample_user_id
        assert config.selectedTheme == 'dark'
        assert config.realTradingSettings.real_trading_mode_active is False
        assert config.realTradingSettings.real_trades_executed_count == 0

    @pytest.mark.asyncio
    async def test_get_user_configuration_returns_default_if_not_found(self, config_service, mock_persistence_service, sample_user_id):
        mock_persistence_service.get_user_configuration.return_value = None
        
        config = await config_service.get_user_configuration(sample_user_id)
        
        mock_persistence_service.get_user_configuration.assert_called_once_with(sample_user_id)
        assert config.user_id == sample_user_id
        assert config.defaultPaperTradingCapital == 10000.0
        assert config.realTradingSettings.real_trading_mode_active is False
        assert config.realTradingSettings.real_trades_executed_count == 0

    @pytest.mark.asyncio
    async def test_save_user_configuration(self, config_service, mock_persistence_service, default_user_config):
        await config_service.save_user_configuration(default_user_config)
        
        mock_persistence_service.upsert_user_configuration.assert_called_once()
        args, kwargs = mock_persistence_service.upsert_user_configuration.call_args
        assert args[0] == default_user_config.user_id
        assert isinstance(args[1], dict)
        assert args[1]['selectedTheme'] == 'dark'
        assert args[1]['realTradingSettings']['real_trading_mode_active'] is False

    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_success(self, config_service, mock_persistence_service, mock_credential_service, mock_portfolio_service, sample_user_id, default_user_config):
        # Configurar mocks para el escenario de éxito
        default_user_config.realTradingSettings.real_trades_executed_count = 0
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')
        mock_credential_service.verify_binance_api_key.return_value = True
        mock_portfolio_service.get_real_usdt_balance.return_value = 100.0 # Saldo suficiente

        await config_service.activate_real_trading_mode(sample_user_id)

        mock_credential_service.verify_binance_api_key.assert_called_once_with(sample_user_id)
        mock_portfolio_service.get_real_usdt_balance.assert_called_once_with(sample_user_id)
        mock_persistence_service.upsert_user_configuration.assert_called_once()
        
        saved_config_data = mock_persistence_service.upsert_user_configuration.call_args[0][1]
        assert saved_config_data['realTradingSettings']['real_trading_mode_active'] is True
        assert saved_config_data['realTradingSettings']['real_trades_executed_count'] == 0

    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_limit_reached(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trades_executed_count = 5
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        with pytest.raises(RealTradeLimitReachedError) as excinfo:
            await config_service.activate_real_trading_mode(sample_user_id)
        
        assert "Límite de 5 operaciones reales alcanzado." in str(excinfo.value)
        config_service.credential_service.verify_binance_api_key.assert_not_called()
        config_service.portfolio_service.get_real_usdt_balance.assert_not_called()
        mock_persistence_service.upsert_user_configuration.assert_not_called()
        config_service.notification_service.send_real_trading_mode_activation_failed_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_binance_api_error(self, config_service, mock_persistence_service, mock_credential_service, mock_notification_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trades_executed_count = 0
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')
        mock_credential_service.verify_binance_api_key.side_effect = BinanceAPIError("Error de conexión Binance")

        with pytest.raises(BinanceAPIError) as excinfo:
            await config_service.activate_real_trading_mode(sample_user_id)
        
        assert "Error de conexión Binance" in str(excinfo.value)
        config_service.credential_service.verify_binance_api_key.assert_called_once_with(sample_user_id)
        config_service.portfolio_service.get_real_usdt_balance.assert_not_called()
        mock_persistence_service.upsert_user_configuration.assert_not_called()
        mock_notification_service.send_real_trading_mode_activation_failed_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_insufficient_usdt_balance(self, config_service, mock_persistence_service, mock_credential_service, mock_portfolio_service, mock_notification_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trades_executed_count = 0
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')
        mock_credential_service.verify_binance_api_key.return_value = True
        mock_portfolio_service.get_real_usdt_balance.return_value = 5.0 # Saldo insuficiente

        with pytest.raises(InsufficientUSDTBalanceError) as excinfo:
            await config_service.activate_real_trading_mode(sample_user_id)
        
        assert "Saldo de USDT insuficiente." in str(excinfo.value)
        config_service.credential_service.verify_binance_api_key.assert_called_once_with(sample_user_id)
        config_service.portfolio_service.get_real_usdt_balance.assert_called_once_with(sample_user_id)
        mock_persistence_service.upsert_user_configuration.assert_not_called()
        mock_notification_service.send_real_trading_mode_activation_failed_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_real_trading_mode_success(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trading_mode_active = True
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        await config_service.deactivate_real_trading_mode(sample_user_id)

        mock_persistence_service.upsert_user_configuration.assert_called_once()
        saved_config_data = mock_persistence_service.upsert_user_configuration.call_args[0][1]
        assert saved_config_data['realTradingSettings']['real_trading_mode_active'] is False

    @pytest.mark.asyncio
    async def test_deactivate_real_trading_mode_already_inactive(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trading_mode_active = False
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        await config_service.deactivate_real_trading_mode(sample_user_id)

        mock_persistence_service.upsert_user_configuration.assert_not_called() # No debería guardar si ya está inactivo

    @pytest.mark.asyncio
    async def test_increment_real_trades_count_success(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trades_executed_count = 0
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        await config_service.increment_real_trades_count(sample_user_id)

        mock_persistence_service.upsert_user_configuration.assert_called_once()
        saved_config_data = mock_persistence_service.upsert_user_configuration.call_args[0][1]
        assert saved_config_data['realTradingSettings']['real_trades_executed_count'] == 1

    @pytest.mark.asyncio
    async def test_increment_real_trades_count_at_limit(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trades_executed_count = 5
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        await config_service.increment_real_trades_count(sample_user_id)

        mock_persistence_service.upsert_user_configuration.assert_not_called() # No debería guardar si ya está en el límite

    @pytest.mark.asyncio
    async def test_get_real_trading_status(self, config_service, mock_persistence_service, sample_user_id, default_user_config):
        default_user_config.realTradingSettings.real_trading_mode_active = True
        default_user_config.realTradingSettings.real_trades_executed_count = 2
        mock_persistence_service.get_user_configuration.return_value = default_user_config.model_dump(mode='json')

        status = await config_service.get_real_trading_status(sample_user_id)

        assert status['isActive'] is True
        assert status['executedCount'] == 2
        assert status['limit'] == 5
