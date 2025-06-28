import pytest
from unittest.mock import AsyncMock
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, Any
import asyncpg

from src.adapters.persistence_service import SupabasePersistenceService
from src.core.domain_models.user_configuration_models import RiskProfile, Theme
from src.shared.data_types import UserConfiguration, APICredential, ServiceName

@pytest.fixture
def mock_persistence_service() -> AsyncMock:
    """
    Provides a mocked instance of SupabasePersistenceService.
    """
    mock = AsyncMock(spec=SupabasePersistenceService)
    mock.get_user_configuration = AsyncMock()
    mock.upsert_user_configuration = AsyncMock()
    mock.save_credential = AsyncMock()
    # Add other methods that need mocking for your tests
    return mock

@pytest.fixture
def fixed_user_id() -> UUID:
    """Provides a fixed user ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_get_user_configuration_found(mock_persistence_service: AsyncMock, fixed_user_id: UUID):
    """
    Verifica que get_user_configuration retorne la configuración cuando se encuentra.
    """
    expected_config = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selected_theme": "dark",
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": 10000.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    mock_persistence_service.get_user_configuration.return_value = expected_config

    config_data = await mock_persistence_service.get_user_configuration(user_id=str(fixed_user_id))

    mock_persistence_service.get_user_configuration.assert_called_once_with(user_id=str(fixed_user_id))
    assert config_data == expected_config
    assert UUID(config_data["user_id"]) == fixed_user_id

@pytest.mark.asyncio
async def test_get_user_configuration_not_found(mock_persistence_service: AsyncMock, fixed_user_id: UUID):
    """
    Verifica que get_user_configuration retorne None si no se encuentra la configuración.
    """
    mock_persistence_service.get_user_configuration.return_value = None

    config_data = await mock_persistence_service.get_user_configuration(user_id=str(fixed_user_id))

    mock_persistence_service.get_user_configuration.assert_called_once_with(user_id=str(fixed_user_id))
    assert config_data is None

@pytest.mark.asyncio
async def test_get_user_configuration_db_error(mock_persistence_service: AsyncMock, fixed_user_id: UUID):
    """
    Verifica que get_user_configuration propague errores de la base de datos.
    """
    mock_persistence_service.get_user_configuration.side_effect = asyncpg.PostgresError("DB connection lost")

    with pytest.raises(asyncpg.PostgresError):
        await mock_persistence_service.get_user_configuration(user_id=str(fixed_user_id))

    mock_persistence_service.get_user_configuration.assert_called_once_with(user_id=str(fixed_user_id))

@pytest.mark.asyncio
async def test_upsert_user_configuration(mock_persistence_service: AsyncMock, fixed_user_id: UUID):
    """
    Verifica que upsert_user_configuration llame al método subyacente.
    """
    user_config = UserConfiguration(
        id=str(uuid4()),
        user_id=str(fixed_user_id),
        telegram_chat_id=None,
        notification_preferences=[],
        enable_telegram_notifications=False,
        default_paper_trading_capital=15000.0,
        paper_trading_active=False,
        paper_trading_assets=[],
        watchlists=[],
        favorite_pairs=[],
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=None,
        real_trading_settings=None,
        ai_strategy_configurations=[],
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=[],
        selected_theme=Theme.LIGHT,
        dashboard_layout_profiles={},
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config={},
        cloud_sync_preferences=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    await mock_persistence_service.upsert_user_configuration(user_config)

    mock_persistence_service.upsert_user_configuration.assert_called_once_with(user_config)

@pytest.mark.asyncio
async def test_save_credential(mock_persistence_service: AsyncMock, fixed_user_id: UUID):
    """
    Verifica que save_credential llame al método subyacente.
    """
    mock_credential = APICredential(
        id=uuid4(),
        user_id=fixed_user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="test_label",
        encrypted_api_key="encrypted_key"
    )
    
    mock_persistence_service.save_credential.return_value = mock_credential

    saved_credential = await mock_persistence_service.save_credential(mock_credential)

    mock_persistence_service.save_credential.assert_called_once_with(mock_credential)
    assert saved_credential == mock_credential
