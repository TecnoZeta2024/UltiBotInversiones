import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone # Importar timezone
from typing import Dict, Any
import asyncpg # Importar asyncpg
from psycopg.sql import SQL, Literal # Importar SQL y Literal
import os # Importar os para mockear variables de entorno

from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.app_config import settings
from shared.data_types import UserConfiguration, APICredential, ServiceName

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch # Importar patch

# Mock para asyncpg.Connection
@pytest.fixture
def mock_asyncpg_connection():
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    # Simular que la conexión no está cerrada por defecto
    type(mock_conn).closed = PropertyMock(return_value=False)
    # Mockear commit y rollback como corrutinas
    mock_conn.commit = AsyncMock()
    mock_conn.rollback = AsyncMock()

    # Mockear el cursor y sus métodos
    mock_cursor = AsyncMock()
    mock_cursor.__aenter__.return_value = mock_cursor # Para async with
    mock_cursor.__aexit__.return_value = None # Para async with
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock(return_value=[]) # Por defecto, devuelve lista vacía

    mock_conn.cursor.return_value = mock_cursor
    return mock_conn

# Fixture para SupabasePersistenceService con mock de conexión
@pytest.fixture
def persistence_service(mock_asyncpg_connection):
    # Usar patch.dict para simular la variable de entorno DATABASE_URL
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@host:5432/db"}):
        service = SupabasePersistenceService()
        service.connection = mock_asyncpg_connection # Inyectar el mock de conexión
        return service

@pytest.fixture
def fixed_user_id():
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_get_user_configuration_found(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration retorne la configuración cuando se encuentra.
    """
    mock_asyncpg_connection.cursor.return_value.fetchone.return_value = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selected_theme": "dark",
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": 10000.0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    config_data = await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once_with(
        SQL("SELECT * FROM user_configurations WHERE user_id = %s;"), (fixed_user_id,)
    )
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()
    assert isinstance(config_data, Dict)
    assert UUID(config_data["user_id"]) == fixed_user_id
    assert config_data["selected_theme"] == "dark"

@pytest.mark.asyncio
async def test_get_user_configuration_not_found(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration retorne None si no se encuentra la configuración.
    """
    mock_asyncpg_connection.cursor.return_value.fetchone.return_value = None

    config_data = await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once_with(
        SQL("SELECT * FROM user_configurations WHERE user_id = %s;"), (fixed_user_id,)
    )
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()
    assert config_data is None

@pytest.mark.asyncio
async def test_get_user_configuration_db_error(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration propague errores de la base de datos.
    """
    mock_asyncpg_connection.cursor.return_value.execute.side_effect = asyncpg.exceptions.PostgresError("DB connection lost")

    with pytest.raises(asyncpg.exceptions.PostgresError):
        await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once_with(
        SQL("SELECT * FROM user_configurations WHERE user_id = %s;"), (fixed_user_id,)
    )
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()

@pytest.mark.asyncio
async def test_upsert_user_configuration_insert(persistence_service, mock_asyncpg_connection, fixed_user_id):
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
    mock_asyncpg_connection.cursor.return_value.fetchone.return_value = {"id": str(uuid4()), "user_id": str(fixed_user_id)} # Simular que retorna un registro

    await persistence_service.upsert_user_configuration(fixed_user_id, new_config_data)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once()
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()
    mock_asyncpg_connection.commit.assert_called_once()
    args, kwargs = mock_asyncpg_connection.cursor.return_value.execute.call_args
    query = args[0]
    values = args[1] # Los valores son el segundo argumento de execute

    assert "INSERT INTO user_configurations" in query
    assert "ON CONFLICT (user_id) DO UPDATE SET" in query
    assert fixed_user_id in values # Cambiado de str(fixed_user_id) a fixed_user_id
    assert "light" in values
    assert 15000.0 in values

@pytest.mark.asyncio
async def test_upsert_user_configuration_update(persistence_service, mock_asyncpg_connection, fixed_user_id):
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
    mock_asyncpg_connection.cursor.return_value.fetchone.return_value = {"id": str(uuid4()), "user_id": str(fixed_user_id)} # Simular que retorna un registro

    await persistence_service.upsert_user_configuration(fixed_user_id, updated_config_data)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once()
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()
    mock_asyncpg_connection.commit.assert_called_once()
    args, kwargs = mock_asyncpg_connection.cursor.return_value.execute.call_args
    query = args[0]
    values = args[1] # Los valores son el segundo argumento de execute

    assert "INSERT INTO user_configurations" in query # La consulta es UPSERT, siempre tiene INSERT
    assert "ON CONFLICT (user_id) DO UPDATE SET" in query
    assert fixed_user_id in values # Cambiado de str(fixed_user_id) a fixed_user_id
    assert "dark" in values
    assert 12000.0 in values
    # Asegurarse de que el ID de la configuración no se use en la parte de actualización si se excluyó
    assert "id" not in query.split("DO UPDATE SET")[1] # No debería estar en el SET de UPDATE

@pytest.mark.asyncio
async def test_upsert_user_configuration_db_error(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que upsert_user_configuration propague errores de la base de datos.
    """
    test_config_data = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selectedTheme": "dark",
    }
    mock_asyncpg_connection.cursor.return_value.execute.side_effect = asyncpg.exceptions.PostgresError("DB write error")

    with pytest.raises(asyncpg.exceptions.PostgresError):
        await persistence_service.upsert_user_configuration(fixed_user_id, test_config_data)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once()
    mock_asyncpg_connection.commit.assert_called_once()

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
    mock_record_data = { # Usar un diccionario para el mock_record
        "id": str(mock_credential.id), # Convertir a string para el mock de la BD
        "user_id": str(mock_credential.user_id), # Convertir a string para el mock de la BD
        "service_name": mock_credential.service_name.value, # Usar .value aquí
        "credential_label": mock_credential.credential_label,
        "encrypted_api_key": mock_credential.encrypted_api_key,
        "encrypted_api_secret": None,
        "encrypted_other_details": None,
        "status": "active",
        "last_verified_at": None,
        "permissions": None,
        "permissions_checked_at": None,
        "expires_at": None,
        "rotation_reminder_policy_days": None,
        "usage_count": 0,
        "last_used_at": None,
        "purpose_description": None,
        "tags": None,
        "notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(), # Convertir a string ISO para el mock de la BD
        "updated_at": datetime.now(timezone.utc).isoformat(), # Convertir a string ISO para el mock de la BD
    }
    mock_asyncpg_connection.cursor.return_value.fetchone.return_value = mock_record_data # Retornar el diccionario directamente

    saved_credential = await persistence_service.save_credential(mock_credential)

    mock_asyncpg_connection.cursor.return_value.execute.assert_called_once()
    mock_asyncpg_connection.cursor.return_value.fetchone.assert_called_once()
    mock_asyncpg_connection.commit.assert_called_once()
    assert saved_credential.id == mock_credential.id
    assert saved_credential.service_name == mock_credential.service_name # Debería comparar el Enum

