import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone # Importar timezone

from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.shared.data_types import UserConfiguration
from src.ultibot_backend.core.exceptions import ConfigurationError

@pytest.fixture
def mock_persistence_service():
    """Fixture para un mock de SupabasePersistenceService."""
    mock = AsyncMock(spec=SupabasePersistenceService)
    return mock

@pytest.fixture
def config_service(mock_persistence_service):
    """Fixture para una instancia de ConfigService con un mock de PersistenceService."""
    return ConfigService(persistence_service=mock_persistence_service)

@pytest.fixture
def fixed_user_id():
    """Fixture para un UUID de usuario fijo."""
    return UUID("00000000-0000-0000-0000-000000000001")

@pytest.mark.asyncio
async def test_load_user_configuration_existing(config_service, mock_persistence_service, fixed_user_id):
    """
    Verifica que load_user_configuration cargue una configuración existente correctamente.
    """
    mock_config_data = {
        "id": str(uuid4()),
        "user_id": str(fixed_user_id),
        "selectedTheme": "light",
        "enableTelegramNotifications": True,
        "defaultPaperTradingCapital": 5000.0,
        "paperTradingActive": True, # Añadir el nuevo campo
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }
    mock_persistence_service.get_user_configuration.return_value = mock_config_data

    config = await config_service.load_user_configuration(fixed_user_id)

    mock_persistence_service.get_user_configuration.assert_called_once_with(fixed_user_id)
    assert isinstance(config, UserConfiguration)
    assert config.user_id == fixed_user_id
    assert config.selectedTheme == "light"
    assert config.enableTelegramNotifications is True
    assert config.defaultPaperTradingCapital == 5000.0
    assert config.paperTradingActive is True # Verificar el nuevo campo

@pytest.mark.asyncio
async def test_load_user_configuration_not_found(config_service, mock_persistence_service, fixed_user_id):
    """
    Verifica que load_user_configuration retorne la configuración por defecto si no se encuentra.
    """
    mock_persistence_service.get_user_configuration.return_value = None

    config = await config_service.load_user_configuration(fixed_user_id)

    mock_persistence_service.get_user_configuration.assert_called_once_with(fixed_user_id)
    assert isinstance(config, UserConfiguration)
    assert config.user_id == fixed_user_id
    assert config.selectedTheme == "dark"
    assert config.defaultPaperTradingCapital == 10000.0
    assert config.paperTradingActive is True # Verificar el valor por defecto del nuevo campo

@pytest.mark.asyncio
async def test_load_user_configuration_persistence_error(config_service, mock_persistence_service, fixed_user_id):
    """
    Verifica que load_user_configuration maneje errores de persistencia y retorne la configuración por defecto.
    """
    mock_persistence_service.get_user_configuration.side_effect = Exception("Error de conexión a DB")

    config = await config_service.load_user_configuration(fixed_user_id)

    mock_persistence_service.get_user_configuration.assert_called_once_with(fixed_user_id)
    assert isinstance(config, UserConfiguration)
    assert config.user_id == fixed_user_id
    assert config.selectedTheme == "dark"
    assert config.defaultPaperTradingCapital == 10000.0
    assert config.paperTradingActive is True # Verificar el valor por defecto del nuevo campo

@pytest.mark.asyncio
async def test_save_user_configuration_success(config_service, mock_persistence_service, fixed_user_id):
    """
    Verifica que save_user_configuration guarde la configuración correctamente.
    """
    test_config = UserConfiguration(
        id=uuid4(),
        user_id=fixed_user_id,
        selectedTheme="light",
        enableTelegramNotifications=True,
        defaultPaperTradingCapital=7500.0,
        paperTradingActive=False # Añadir el nuevo campo
    )
    mock_persistence_service.upsert_user_configuration.return_value = None

    await config_service.save_user_configuration(fixed_user_id, test_config)

    mock_persistence_service.upsert_user_configuration.assert_called_once()
    args, kwargs = mock_persistence_service.upsert_user_configuration.call_args
    assert args[0] == fixed_user_id
    saved_config_dict = args[1]
    assert saved_config_dict['selectedTheme'] == "light"
    assert saved_config_dict['enableTelegramNotifications'] is True
    assert saved_config_dict['defaultPaperTradingCapital'] == 7500.0
    assert saved_config_dict['paperTradingActive'] is False # Verificar el nuevo campo
    assert 'id' in saved_config_dict
    assert 'user_id' in saved_config_dict

@pytest.mark.asyncio
async def test_save_user_configuration_persistence_error(config_service, mock_persistence_service, fixed_user_id):
    """
    Verifica que save_user_configuration maneje errores de persistencia.
    """
    test_config = UserConfiguration(
        id=uuid4(),
        user_id=fixed_user_id,
        selectedTheme="light"
    )
    mock_persistence_service.upsert_user_configuration.side_effect = Exception("Error de DB al guardar")

    with pytest.raises(ConfigurationError, match=f"No se pudo guardar la configuración para el usuario {fixed_user_id}."):
        await config_service.save_user_configuration(fixed_user_id, test_config)

    mock_persistence_service.upsert_user_configuration.assert_called_once()

def test_get_default_configuration(config_service, fixed_user_id):
    """
    Verifica que get_default_configuration retorne una instancia válida con valores por defecto.
    """
    default_config = config_service.get_default_configuration(fixed_user_id) # Pasar fixed_user_id

    assert isinstance(default_config, UserConfiguration)
    assert default_config.user_id == fixed_user_id
    assert default_config.selectedTheme == "dark"
    assert default_config.enableTelegramNotifications is False
    assert default_config.defaultPaperTradingCapital == 10000.0
    assert default_config.paperTradingActive is True # Verificar el valor por defecto del nuevo campo
    assert isinstance(default_config.id, UUID)
    assert isinstance(default_config.createdAt, datetime)
    assert isinstance(default_config.updatedAt, datetime)
