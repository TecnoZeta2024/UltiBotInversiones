import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from decimal import Decimal

# Corrected imports based on model definitions
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.configuration_service import ConfigurationService
from ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    RealTradingSettings,
    ConfidenceThresholds,
    CloudSyncPreferences,
    DashboardLayoutProfile,
    NotificationPreference,
    PaperTradingAsset,
    RiskProfile,
    RiskProfileSettings,
    Theme,
    Watchlist,
    AIStrategyConfiguration,
    MCPServerPreference,
    AutoPauseTradingConditions,
)
from ultibot_backend.core.exceptions import ConfigurationError

# Fixture for the persistence service mock
@pytest.fixture
def mock_persistence_service() -> MagicMock:
    """
    Mock for SupabasePersistenceService.
    This mock only simulates the connection and cursor logic, as the
    methods that actually use it (_get_user_config_from_db, etc.)
    are part of ConfigurationService and will be mocked directly on the service instance.
    """
    mock = AsyncMock(spec=SupabasePersistenceService)
    mock._ensure_connection = AsyncMock()
    
    # Mock the connection and its cursor/fetchone methods
    mock_cursor = AsyncMock()
    mock_cursor.fetchone.return_value = None  # Default to None for not found
    
    # Create a mock for the async context manager that cursor() will return
    mock_async_context_manager_for_cursor = AsyncMock()
    mock_async_context_manager_for_cursor.__aenter__.return_value = mock_cursor
    mock_async_context_manager_for_cursor.__aexit__.return_value = None
    
    # Mock the connection and its cursor method
    mock_connection = AsyncMock()
    # The cursor method itself is synchronous and returns an async context manager
    mock_connection.cursor = MagicMock(return_value=mock_async_context_manager_for_cursor)
    mock_connection.commit = AsyncMock() # Make commit awaitable
    mock_connection.rollback = AsyncMock() # Make rollback awaitable
    mock.connection = mock_connection
    
    return mock

# Fixture for the service under test, with correct dependency injection
@pytest.fixture
def config_service(mock_persistence_service: SupabasePersistenceService) -> ConfigurationService:
    """Fixture for ConfigurationService."""
    return ConfigurationService(persistence_service=mock_persistence_service)

# Fixture for a sample user ID
@pytest.fixture
def sample_user_id() -> UUID:
    """Generate a sample UUID for a user."""
    return uuid4()

# Fixture for a complete and valid default user configuration
@pytest.fixture
def default_user_config(sample_user_id: UUID) -> UserConfiguration:
    """
    Provides a complete and valid UserConfiguration object.
    This fixture is constructed based on the Pydantic model definition
    to prevent validation errors by providing default values for all fields.
    """
    profile_id = uuid4()
    return UserConfiguration(
        id=str(uuid4()),
        user_id=str(sample_user_id),
        telegram_chat_id="123456789",
        notification_preferences=[],
        enable_telegram_notifications=True,
        default_paper_trading_capital=10000.0,
        paper_trading_active=True,
        paper_trading_assets=[],
        watchlists=[],
        favorite_pairs=["BTCUSDT", "ETHUSDT"],
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=RiskProfileSettings(
            daily_capital_risk_percentage=0.01,
            per_trade_capital_risk_percentage=0.005,
            max_drawdown_percentage=0.05,
        ),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_concurrent_operations=5,
            daily_loss_limit_absolute=500.0,
            daily_profit_target_absolute=1000.0,
            asset_specific_stop_loss={},
            auto_pause_trading_conditions=AutoPauseTradingConditions(
                on_max_daily_loss_reached=True,
                on_max_drawdown_reached=True,
                on_consecutive_losses=5,
                on_market_volatility_index_exceeded=None,
            ),
        ),
        ai_strategy_configurations=[],
        ai_analysis_confidence_thresholds=ConfidenceThresholds(paper_trading=0.7, real_trading=0.8),
        mcp_server_preferences=[],
        selected_theme=Theme.DARK,
        dashboard_layout_profiles={
            str(profile_id): DashboardLayoutProfile(name="Default", configuration={})
        },
        active_dashboard_layout_profile_id=str(profile_id),
        dashboard_layout_config={},
        cloud_sync_preferences=CloudSyncPreferences(is_enabled=False, last_successful_sync=None),
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
        Verify that get_user_configuration correctly loads an existing
        configuration by mocking the internal DB access method.
        """
        # Arrange: Mock the internal method of the service instance directly
        db_record = config_service._user_config_to_db_format(default_user_config)
        config_service._get_user_config_from_db = AsyncMock(return_value=db_record)

        # Act: Call the method under test
        config = await config_service.get_user_configuration(str(sample_user_id))

        # Assert: Check that the internal method was called and the config is correct
        config_service._get_user_config_from_db.assert_called_once_with(
            str(sample_user_id)
        )
        assert isinstance(config, UserConfiguration)
        assert config.user_id == str(sample_user_id)
        assert config.selected_theme == Theme.DARK
        assert config.real_trading_settings is not None
        assert config.real_trading_settings.real_trading_mode_active is False

    @pytest.mark.asyncio
    async def test_get_user_configuration_returns_none_if_not_found(
        self,
        config_service: ConfigurationService,
        sample_user_id: UUID,
    ):
        """
        Verify that get_user_configuration returns None if the internal
        DB access method returns None.
        """
        # Arrange: Mock the internal method to return None
        config_service._get_user_config_from_db = AsyncMock(return_value=None)

        # Act: Call the method under test
        config = await config_service.get_user_configuration(str(sample_user_id))

        # Assert: Check that the internal method was called and None is returned
        config_service._get_user_config_from_db.assert_called_once_with(
            str(sample_user_id)
        )
        assert config is None

    @pytest.mark.asyncio
    async def test_create_or_update_user_configuration(
        self,
        config_service: ConfigurationService,
        sample_user_id: UUID,
        default_user_config: UserConfiguration,
    ):
        """
        Verify that create_or_update_user_configuration correctly calls the internal
        save method.
        """
        # Arrange
        config_data = default_user_config.model_dump(exclude_unset=True)
        
        # Mock the internal methods for this specific test case
        config_service._get_user_config_from_db = AsyncMock(return_value=None)
        config_service._save_user_config_to_db = AsyncMock()

        # Act: Call the method under test
        await config_service.create_or_update_user_configuration(str(sample_user_id), config_data)

        # Assert: Check that the save method was called with the correct data
        config_service._save_user_config_to_db.assert_called_once()
        args, _ = config_service._save_user_config_to_db.call_args
        saved_data = args[0]
        assert saved_data["user_id"] == str(sample_user_id)
        assert saved_data["selected_theme"] == "dark"
        assert '"real_trading_mode_active": false' in saved_data["real_trading_settings"]


    # --- The following tests are skipped as they test logic no longer in ConfigurationService ---

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_success(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_limit_reached(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_binance_api_error(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_activate_real_trading_mode_insufficient_usdt_balance(
        self, *args, **kwargs
    ):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_deactivate_real_trading_mode_success(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_deactivate_real_trading_mode_already_inactive(
        self, *args, **kwargs
    ):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_increment_real_trades_count_success(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_increment_real_trades_count_at_limit(self, *args, **kwargs):
        pass

    @pytest.mark.skip(
        reason="Business logic moved from ConfigurationService. Test to be relocated."
    )
    @pytest.mark.asyncio
    async def test_get_real_trading_status(self, *args, **kwargs):
        pass

