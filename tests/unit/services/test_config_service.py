import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone

from src.adapters.persistence_service import SupabasePersistenceService
from src.services.config_service import ConfigurationService
from src.core.domain_models.user_configuration_models import (
    UserConfiguration,
    RealTradingSettings,
    RiskProfile,
    Theme,
    ConfidenceThresholds,
)
from src.core.exceptions import ConfigurationError
from src.app_config import AppSettings

from src.services.credential_service import CredentialService
from src.services.portfolio_service import PortfolioService
from src.services.notification_service import NotificationService

@pytest.fixture
def mock_persistence_service() -> MagicMock:
    """Mock for SupabasePersistenceService."""
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_credential_service() -> MagicMock:
    """Mock for CredentialService."""
    return AsyncMock(spec=CredentialService)

@pytest.fixture
def mock_portfolio_service() -> MagicMock:
    """Mock for PortfolioService."""
    return AsyncMock(spec=PortfolioService)

@pytest.fixture
def mock_notification_service() -> MagicMock:
    """Mock for NotificationService."""
    return AsyncMock(spec=NotificationService)

@pytest.fixture
def config_service(
    mock_persistence_service: SupabasePersistenceService,
    mock_credential_service: CredentialService,
    mock_portfolio_service: PortfolioService,
    mock_notification_service: NotificationService,
    app_settings_fixture: AppSettings
) -> ConfigurationService:
    """Fixture for ConfigurationService with all dependencies mocked."""
    service = ConfigurationService(
        persistence_service=mock_persistence_service,
        credential_service=mock_credential_service,
        portfolio_service=mock_portfolio_service,
        notification_service=mock_notification_service
    )
    service._user_id = app_settings_fixture.FIXED_USER_ID
    return service

@pytest.fixture
def sample_user_id(app_settings_fixture: AppSettings) -> UUID:
    """Use the fixed user ID from app_settings_fixture for consistency."""
    return app_settings_fixture.FIXED_USER_ID

@pytest.fixture
def default_user_config(sample_user_id: UUID) -> UserConfiguration:
    """Provides a complete and valid UserConfiguration object."""
    # Note: Pydantic's alias_generator=to_camel makes the model expect camelCase keys
    # during initialization if populate_by_name is True.
    return UserConfiguration(
        id=str(uuid4()),
        user_id=str(sample_user_id),
        telegramChatId=None,
        notificationPreferences=[],
        enableTelegramNotifications=False,
        defaultPaperTradingCapital=Decimal("10000.0"),
        paperTradingActive=True,
        paperTradingAssets=[],
        favoritePairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        watchlists=[],
        riskProfile=RiskProfile.MODERATE,
        riskProfileSettings=None,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=datetime.now(timezone.utc),
            max_concurrent_operations=None,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None
        ),
        aiStrategyConfigurations=[],
        aiAnalysisConfidenceThresholds=ConfidenceThresholds(
            paper_trading=0.7,
            real_trading=0.8
        ),
        mcpServerPreferences=[],
        selectedTheme=Theme.DARK,
        dashboardLayoutProfiles={},
        activeDashboardLayoutProfileId=None,
        dashboardLayoutConfig={},
        cloudSyncPreferences=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc)
    )


class TestConfigService:
    """Test suite for the ConfigurationService."""

    @pytest.mark.asyncio
    async def test_get_user_configuration_loads_from_db(
        self,
        config_service: ConfigurationService,
        sample_user_id: UUID,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that get_user_configuration correctly loads an existing configuration from persistence.
        """
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=default_user_config)
        config = await config_service.get_user_configuration()
        config_service.persistence_service.get_user_configuration.assert_called_once_with(user_id=str(sample_user_id))
        assert config == default_user_config
        assert config.user_id == str(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_user_configuration_creates_default_if_not_found(
        self,
        config_service: ConfigurationService,
        sample_user_id: UUID,
    ):
        """
        Verify that get_user_configuration creates and saves a default config if none is found in persistence.
        """
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=None)
        # Configure the mock to return the object it was called with
        config_service.persistence_service.upsert_user_configuration = AsyncMock(side_effect=lambda x: x)
        config = await config_service.get_user_configuration()
        config_service.persistence_service.get_user_configuration.assert_called_once_with(user_id=str(sample_user_id))
        config_service.persistence_service.upsert_user_configuration.assert_called_once()
        saved_config = config_service.persistence_service.upsert_user_configuration.call_args[0][0]
        assert saved_config is not None # Ensure it's not None
        assert saved_config.user_id == str(sample_user_id)
        assert saved_config.paper_trading_active is True
        assert config.user_id == str(sample_user_id)

    @pytest.mark.asyncio
    async def test_save_user_configuration_success(
        self,
        config_service: ConfigurationService,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that save_user_configuration correctly calls the persistence service's upsert method.
        """
        config_service.persistence_service.upsert_user_configuration = AsyncMock()
        await config_service.save_user_configuration(default_user_config)
        config_service.persistence_service.upsert_user_configuration.assert_called_once_with(default_user_config)
        assert config_service.get_cached_user_configuration() == default_user_config

    @pytest.mark.asyncio
    async def test_save_user_configuration_raises_error_for_wrong_user(
        self,
        config_service: ConfigurationService,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that save_user_configuration raises a ConfigurationError if the config's user_id
        does not match the service's user_id.
        """
        wrong_user_config = default_user_config.model_copy(update={"user_id": str(uuid4())})
        with pytest.raises(ConfigurationError, match="Intentando guardar una configuración para un ID de usuario incorrecto."):
            await config_service.save_user_configuration(wrong_user_config)

    @pytest.mark.asyncio
    async def test_get_user_configuration_uses_cache(
        self,
        config_service: ConfigurationService,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that get_user_configuration returns the cached config on subsequent calls
        without hitting the database.
        """
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=default_user_config)
        first_config = await config_service.get_user_configuration()
        config_service.persistence_service.get_user_configuration.assert_called_once()
        assert first_config == default_user_config
        second_config = await config_service.get_user_configuration()
        config_service.persistence_service.get_user_configuration.assert_called_once()
        assert second_config == first_config

    @pytest.mark.asyncio
    async def test_reload_user_configuration_forces_db_read(
        self,
        config_service: ConfigurationService,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that reload_user_configuration forces a read from the database,
        bypassing and updating the cache.
        """
        config_service._user_configuration = default_user_config
        new_config_data = default_user_config.model_copy(update={"paper_trading_active": False})
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=new_config_data)
        reloaded_config = await config_service.reload_user_configuration()
        config_service.persistence_service.get_user_configuration.assert_called_once()
        assert reloaded_config is not None
        assert reloaded_config.paper_trading_active is False
        assert config_service.get_cached_user_configuration() == reloaded_config
        cached_config = config_service.get_cached_user_configuration()
        assert cached_config is not None
        assert cached_config.paper_trading_active is False
