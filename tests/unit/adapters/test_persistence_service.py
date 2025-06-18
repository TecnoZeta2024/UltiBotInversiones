import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Dict, Any
import asyncpg
from psycopg.sql import SQL, Literal
import os
import aiosqlite
import json

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.app_config import settings
from shared.data_types import UserConfiguration, APICredential, ServiceName

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

# Mock para asyncpg.Connection
@pytest.fixture
def mock_asyncpg_connection():
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    type(mock_conn).closed = PropertyMock(return_value=False)
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()

    mock_cursor = AsyncMock()
    mock_cursor.__aenter__.return_value = mock_cursor
    mock_cursor.__aexit__.return_value = None
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[])

    mock_conn.cursor.return_value = mock_cursor
    return mock_conn

# Fixture para SupabasePersistenceService con mock de conexión
@pytest.fixture
def persistence_service():
    mock_sqlite_cursor_instance = AsyncMock()
    mock_sqlite_cursor_instance.execute = AsyncMock()
    # Devolver un diccionario vacío por defecto para asegurar que sea iterable
    mock_sqlite_cursor_instance.fetchone = AsyncMock(return_value={})
    mock_sqlite_cursor_instance.fetchall = AsyncMock(return_value=[])
    mock_sqlite_cursor_instance.__aenter__.return_value = mock_sqlite_cursor_instance
    mock_sqlite_cursor_instance.__aexit__.return_value = None

    mock_sqlite_conn = AsyncMock()
    mock_sqlite_conn.cursor = MagicMock(return_value=mock_sqlite_cursor_instance)
    mock_sqlite_conn.commit = AsyncMock()
    mock_sqlite_conn.row_factory = aiosqlite.Row

    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test_db.sqlite"}):
        with patch('aiosqlite.connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = mock_sqlite_conn
            
            service = SupabasePersistenceService()
            service.connect = AsyncMock(side_effect=lambda: setattr(service, '_is_sqlite', True) or setattr(service, 'sqlite_conn', mock_sqlite_conn))
            service._check_pool = AsyncMock(side_effect=service.connect)
            service._is_sqlite = True
            service.sqlite_conn = mock_sqlite_conn
            return service

@pytest.fixture
def fixed_user_id():
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_get_user_configuration_found(persistence_service, fixed_user_id):
    """
    Verifica que get_user_configuration retorne la configuración cuando se encuentra.
    """
    persistence_service.sqlite_conn.cursor.return_value.fetchone.return_value = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selected_theme": "dark",
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": 10000.0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    config_data = await persistence_service.get_user_configuration()

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = ?;", (str(fixed_user_id),)
    )
    persistence_service.sqlite_conn.cursor.return_value.fetchone.assert_called_once()
    assert isinstance(config_data, Dict)
    assert UUID(config_data["user_id"]) == fixed_user_id
    assert config_data["selected_theme"] == "dark"

@pytest.mark.asyncio
async def test_get_user_configuration_not_found(persistence_service, fixed_user_id):
    """
    Verifica que get_user_configuration retorne None si no se encuentra la configuración.
    """
    persistence_service.sqlite_conn.cursor.return_value.fetchone.return_value = None

    config_data = await persistence_service.get_user_configuration()

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = ?;", (str(fixed_user_id),)
    )
    persistence_service.sqlite_conn.cursor.return_value.fetchone.assert_called_once()
    assert config_data is None

@pytest.mark.asyncio
async def test_get_user_configuration_db_error(persistence_service, fixed_user_id):
    """
    Verifica que get_user_configuration propague errores de la base de datos.
    """
    persistence_service.sqlite_conn.cursor.return_value.execute.side_effect = aiosqlite.Error("DB connection lost")

    with pytest.raises(aiosqlite.Error):
        await persistence_service.get_user_configuration()

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = ?;", (str(fixed_user_id),)
    )
    persistence_service.sqlite_conn.cursor.return_value.fetchone.assert_not_called()

@pytest.mark.asyncio
async def test_upsert_user_configuration_insert(persistence_service, fixed_user_id):
    """
    Verifica que upsert_user_configuration inserte una nueva configuración.
    """
    new_config_data = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selectedTheme": "light",
        "enableTelegramNotifications": False,
        "defaultPaperTradingCapital": 15000.0,
    }
    persistence_service.sqlite_conn.cursor.return_value.fetchone.return_value = {"id": str(uuid4()), "user_id": str(fixed_user_id)}

    await persistence_service.upsert_user_configuration(new_config_data)

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once()
    persistence_service.sqlite_conn.commit.assert_called_once()

@pytest.mark.asyncio
async def test_upsert_user_configuration_update(persistence_service, fixed_user_id):
    """
    Verifica que upsert_user_configuration actualice una configuración existente.
    """
    existing_config_id = uuid4()
    updated_config_data = {
        "id": str(existing_config_id),
        "user_id": str(fixed_user_id),
        "selectedTheme": "dark",
        "enableTelegramNotifications": True,
        "defaultPaperTradingCapital": 12000.0,
    }
    persistence_service.sqlite_conn.cursor.return_value.fetchone.return_value = {"id": str(uuid4()), "user_id": str(fixed_user_id)}

    await persistence_service.upsert_user_configuration(updated_config_data)

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once()
    persistence_service.sqlite_conn.commit.assert_called_once()

@pytest.mark.asyncio
async def test_upsert_user_configuration_db_error(persistence_service, fixed_user_id):
    """
    Verifica que upsert_user_configuration propague errores de la base de datos.
    """
    test_config_data = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selectedTheme": "dark",
    }
    persistence_service.sqlite_conn.cursor.return_value.execute.side_effect = aiosqlite.Error("DB write error")

    with pytest.raises(aiosqlite.Error):
        await persistence_service.upsert_user_configuration(test_config_data)

    persistence_service.sqlite_conn.cursor.return_value.execute.assert_called_once()
    persistence_service.sqlite_conn.commit.assert_not_called()

# Pruebas para métodos existentes (ejemplo: save_credential)
@pytest.mark.asyncio
async def test_save_credential(persistence_service, mock_asyncpg_connection, fixed_user_id):
    mock_credential = APICredential(
        id=uuid4(),
        user_id=fixed_user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="test_label",
        encrypted_api_key="encrypted_key"
    )
    mock_record_data = {
        "id": mock_credential.id,
        "user_id": mock_credential.user_id,
        "service_name": mock_credential.service_name, # service_name ya es el valor del Enum debido a use_enum_values=True
        "credential_label": mock_credential.credential_label,
        "encrypted_api_key": mock_credential.encrypted_api_key,
        "encrypted_api_secret": mock_credential.encrypted_api_secret,
        "encrypted_other_details": mock_credential.encrypted_other_details,
        "status": mock_credential.status,
        "last_verified_at": mock_credential.last_verified_at,
        "permissions": json.dumps(mock_credential.permissions) if mock_credential.permissions else None,
        "permissions_checked_at": mock_credential.permissions_checked_at,
        "expires_at": mock_credential.expires_at,
        "rotation_reminder_policy_days": mock_credential.rotation_reminder_policy_days,
        "usage_count": mock_credential.usage_count,
        "last_used_at": mock_credential.last_used_at,
        "purpose_description": mock_credential.purpose_description,
        "tags": json.dumps(mock_credential.tags) if mock_credential.tags else None,
        "notes": mock_credential.notes,
        "created_at": mock_credential.created_at,
        "updated_at": mock_credential.updated_at,
    }
    persistence_service.sqlite_conn.cursor.return_value.fetchone.return_value = mock_record_data

    saved_credential = await persistence_service.save_credential(mock_credential)

    assert persistence_service.sqlite_conn.cursor.return_value.execute.call_count == 2
    persistence_service.sqlite_conn.cursor.return_value.fetchone.assert_called_once()
    persistence_service.sqlite_conn.commit.assert_called_once()
    assert saved_credential.id == mock_credential.id
    assert saved_credential.service_name == mock_credential.service_name
