import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timezone

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.config_service import ConfigurationService
from ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    RealTradingSettings,
    RiskProfile,
    Theme,
)
from shared.data_types import AIAnalysisConfidenceThresholds
from ultibot_backend.core.exceptions import ConfigurationError
from ultibot_backend.app_config import settings

@pytest.fixture
def mock_persistence_service() -> MagicMock:
    """Mock for SupabasePersistenceService."""
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def config_service(mock_persistence_service: SupabasePersistenceService) -> ConfigurationService:
    """Fixture for ConfigurationService."""
    service = ConfigurationService(persistence_service=mock_persistence_service)
    # Set the fixed user ID from settings, as the service does
    service._user_id = settings.FIXED_USER_ID
    return service

@pytest.fixture
def sample_user_id() -> UUID:
    """Use the fixed user ID from settings for consistency."""
    return settings.FIXED_USER_ID

@pytest.fixture
def default_user_config(sample_user_id: UUID) -> UserConfiguration:
    """Provides a complete and valid UserConfiguration object."""
    return UserConfiguration(
        id=str(uuid4()),
        user_id=str(sample_user_id),
        telegram_chat_id=None,
        paper_trading_assets=None,
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        selected_theme=Theme.DARK,
        enable_telegram_notifications=False,
        default_paper_trading_capital=Decimal("10000.0"),
        paper_trading_active=True,
        ai_analysis_confidence_thresholds=AIAnalysisConfidenceThresholds(
            paper_trading=0.7,
            real_trading=0.8
        ),
        favorite_pairs=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        notification_preferences=[],
        watchlists=[],
        ai_strategy_configurations=[],
        mcp_server_preferences=[],
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_concurrent_operations=None,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None,
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=datetime.now(timezone.utc)
        )
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
        # Arrange
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=default_user_config)

        # Act
        config = await config_service.get_user_configuration()

        # Assert
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
        # Arrange
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=None)
        config_service.persistence_service.upsert_user_configuration = AsyncMock()

        # Act
        config = await config_service.get_user_configuration()

        # Assert
        config_service.persistence_service.get_user_configuration.assert_called_once_with(user_id=str(sample_user_id))
        config_service.persistence_service.upsert_user_configuration.assert_called_once()
        
        # Check that the argument passed to upsert is a UserConfiguration instance
        saved_config = config_service.persistence_service.upsert_user_configuration.call_args[0][0]
        assert isinstance(saved_config, UserConfiguration)
        assert saved_config.user_id == str(sample_user_id)
        assert saved_config.paper_trading_active is True
        
        # The returned config should be the newly created default one
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
        # Arrange
        config_service.persistence_service.upsert_user_configuration = AsyncMock()

        # Act
        await config_service.save_user_configuration(default_user_config)

        # Assert
        config_service.persistence_service.upsert_user_configuration.assert_called_once_with(default_user_config)
        # Verify that the internal cache is updated
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
        # Arrange
        wrong_user_config = default_user_config.model_copy(update={"user_id": str(uuid4())})

        # Act & Assert
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
        # Arrange: First call loads from DB and populates cache
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=default_user_config)
        
        # Act 1: First call
        first_config = await config_service.get_user_configuration()

        # Assert 1
        config_service.persistence_service.get_user_configuration.assert_called_once()
        assert first_config == default_user_config

        # Act 2: Second call
        second_config = await config_service.get_user_configuration()

        # Assert 2: DB method should not be called again
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
        # Arrange
        # First, populate the cache
        config_service._user_configuration = default_user_config
        
        # Setup mock for the reload
        new_config_data = default_user_config.model_copy(update={"paper_trading_active": False})
        config_service.persistence_service.get_user_configuration = AsyncMock(return_value=new_config_data)

        # Act
        reloaded_config = await config_service.reload_user_configuration()

        # Assert
        config_service.persistence_service.get_user_configuration.assert_called_once()
        assert reloaded_config is not None
        assert reloaded_config.paper_trading_active is False
        assert config_service.get_cached_user_configuration() == reloaded_config
        
        cached_config = config_service.get_cached_user_configuration()
        assert cached_config is not None
        assert cached_config.paper_trading_active is False
