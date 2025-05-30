import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone # Importar timezone
from typing import Dict, Any
import asyncpg # Importar asyncpg

from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.app_config import settings
from src.shared.data_types import UserConfiguration, APICredential, ServiceName

# Mock para asyncpg.Connection
@pytest.fixture
def mock_asyncpg_connection():
    mock_conn = AsyncMock(spec=asyncpg.Connection)
    return mock_conn

# Fixture para SupabasePersistenceService con mock de conexión
@pytest.fixture
def persistence_service(mock_asyncpg_connection):
    service = SupabasePersistenceService()
    service.connection = mock_asyncpg_connection # Inyectar el mock de conexión
    service.database_url = "postgresql://user:pass@host:5432/db" # Necesario para evitar error en connect() si se llama
    return service

@pytest.fixture
def fixed_user_id():
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_get_user_configuration_found(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration retorne la configuración cuando se encuentra.
    """
    mock_record = MagicMock()
    mock_record.__getitem__.side_effect = lambda key: {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selected_theme": "dark",
        "enable_telegram_notifications": True,
        "default_paper_trading_capital": 10000.0,
        "created_at": datetime.now(timezone.utc), # Usar datetime.now(timezone.utc)
        "updated_at": datetime.now(timezone.utc), # Usar datetime.now(timezone.utc)
    }[key]
    mock_record.__contains__.side_effect = lambda key: key in {
        "id", "user_id", "selected_theme", "enable_telegram_notifications", 
        "default_paper_trading_capital", "created_at", "updated_at"
    }
    mock_record.keys.return_value = [
        "id", "user_id", "selected_theme", "enable_telegram_notifications", 
        "default_paper_trading_capital", "created_at", "updated_at"
    ]
    mock_asyncpg_connection.fetchrow.return_value = mock_record

    config_data = await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.fetchrow.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = $1;", fixed_user_id
    )
    assert isinstance(config_data, Dict)
    assert UUID(config_data["user_id"]) == fixed_user_id
    assert config_data["selected_theme"] == "dark"

@pytest.mark.asyncio
async def test_get_user_configuration_not_found(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration retorne None si no se encuentra la configuración.
    """
    mock_asyncpg_connection.fetchrow.return_value = None

    config_data = await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.fetchrow.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = $1;", fixed_user_id
    )
    assert config_data is None

@pytest.mark.asyncio
async def test_get_user_configuration_db_error(persistence_service, mock_asyncpg_connection, fixed_user_id):
    """
    Verifica que get_user_configuration propague errores de la base de datos.
    """
    mock_asyncpg_connection.fetchrow.side_effect = asyncpg.exceptions.PostgresError("DB connection lost")

    with pytest.raises(asyncpg.exceptions.PostgresError):
        await persistence_service.get_user_configuration(fixed_user_id)

    mock_asyncpg_connection.fetchrow.assert_called_once_with(
        "SELECT * FROM user_configurations WHERE user_id = $1;", fixed_user_id
    )

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
    mock_asyncpg_connection.fetchrow.return_value = MagicMock() # Simular que retorna un registro

    await persistence_service.upsert_user_configuration(fixed_user_id, new_config_data)

    mock_asyncpg_connection.fetchrow.assert_called_once()
    args, kwargs = mock_asyncpg_connection.fetchrow.call_args
    query = args[0]
    values = args[1:]

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
    mock_asyncpg_connection.fetchrow.return_value = MagicMock() # Simular que retorna un registro

    await persistence_service.upsert_user_configuration(fixed_user_id, updated_config_data)

    mock_asyncpg_connection.fetchrow.assert_called_once()
    args, kwargs = mock_asyncpg_connection.fetchrow.call_args
    query = args[0]
    values = args[1:]

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
    mock_asyncpg_connection.fetchrow.side_effect = asyncpg.exceptions.PostgresError("DB write error")

    with pytest.raises(asyncpg.exceptions.PostgresError):
        await persistence_service.upsert_user_configuration(fixed_user_id, test_config_data)

    mock_asyncpg_connection.fetchrow.assert_called_once()

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
        "id": mock_credential.id, # UUID object
        "user_id": mock_credential.user_id, # UUID object
        "service_name": mock_credential.service_name, # Ya es el valor de string del Enum
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
        "created_at": datetime.now(timezone.utc), # Usar datetime.now(timezone.utc)
        "updated_at": datetime.now(timezone.utc), # Usar datetime.now(timezone.utc)
    }
    mock_asyncpg_connection.fetchrow.return_value = mock_record_data # Retornar el diccionario directamente

    saved_credential = await persistence_service.save_credential(mock_credential)

    mock_asyncpg_connection.fetchrow.assert_called_once()
    assert saved_credential.id == mock_credential.id
    assert saved_credential.service_name == mock_credential.service_name # Debería comparar el Enum
