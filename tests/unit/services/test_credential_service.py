import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4, UUID
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ultibot_backend.services.credential_service import CredentialService, CredentialError
from shared.data_types import APICredential, ServiceName
from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

# Generar una clave Fernet válida para las pruebas
TEST_FERNET_KEY = Fernet.generate_key().decode('utf-8')

@pytest.fixture
def mock_session_factory():
    """Mock para async_sessionmaker que devuelve una sesión mockeada."""
    mock_session = AsyncMock(spec=AsyncSession)
    session_factory = MagicMock(spec=async_sessionmaker)
    session_factory.return_value.__aenter__.return_value = mock_session
    return session_factory

@pytest.fixture
def mock_binance_adapter():
    adapter = AsyncMock(spec=BinanceAdapter)
    adapter.get_account_info = AsyncMock()
    return adapter

@pytest.fixture
def mock_persistence_service():
    """Mock para SupabasePersistenceService."""
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def credential_service(mock_session_factory, mock_binance_adapter):
    """Fixture principal para CredentialService con dependencias mockeadas."""
    with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": TEST_FERNET_KEY}):
        service = CredentialService(
            session_factory=mock_session_factory,
            binance_adapter=mock_binance_adapter
        )
        return service

@pytest.fixture
def sample_credential_data():
    return {
        "service_name": ServiceName.BINANCE_SPOT,
        "credential_label": "test_binance",
        "api_key": "my_api_key",
        "api_secret": "my_api_secret"
    }

@pytest.fixture
def sample_encrypted_credential(credential_service: CredentialService, sample_credential_data):
    # Crear un APICredential encriptado como se almacenaría en la BD
    return APICredential(
        id=uuid4(),
        user_id=credential_service.fixed_user_id, # Usar el fixed_user_id del servicio
        service_name=sample_credential_data["service_name"],
        credential_label=sample_credential_data["credential_label"],
        encrypted_api_key=credential_service.encrypt_data(sample_credential_data["api_key"]),
        encrypted_api_secret=credential_service.encrypt_data(sample_credential_data["api_secret"]),
        status="verification_pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

# Pruebas de encriptación/desencriptación
def test_encrypt_decrypt_data(credential_service: CredentialService):
    original_data = "this_is_a_secret"
    encrypted = credential_service.encrypt_data(original_data)
    assert encrypted != original_data
    decrypted = credential_service.decrypt_data(encrypted)
    assert decrypted == original_data

def test_decrypt_invalid_token(credential_service: CredentialService):
    assert credential_service.decrypt_data("invalid_encrypted_string") is None

@pytest.mark.asyncio
async def test_add_credential(credential_service: CredentialService, sample_credential_data, mock_persistence_service):
    # Usamos patch para interceptar la creación de SupabasePersistenceService
    # dentro del método add_credential y devolver nuestro mock.
    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        created_credential = await credential_service.add_credential(**sample_credential_data)

        assert created_credential is not None
        
        # Verificamos que se llamó a 'upsert' en el mock, que es el método correcto.
        mock_persistence_service.upsert.assert_called_once()
        
        # Extraemos los argumentos con los que se llamó a 'upsert' para validarlos.
        call_args = mock_persistence_service.upsert.call_args.kwargs
        assert call_args['table_name'] == "api_credentials"
        
        data_sent = call_args['data']
        assert data_sent['user_id'] == str(credential_service.fixed_user_id)
        assert data_sent['service_name'] == sample_credential_data["service_name"].value
        
        # Validamos que los datos se encriptaron correctamente antes del upsert.
        decrypted_key = credential_service.decrypt_data(data_sent['encrypted_api_key'])
        assert decrypted_key == sample_credential_data["api_key"]
        
        decrypted_secret = credential_service.decrypt_data(data_sent['encrypted_api_secret'])
        assert decrypted_secret == sample_credential_data["api_secret"]

@pytest.mark.asyncio
async def test_get_credential_success(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service, sample_credential_data):
    # El servicio ahora usa get_one, así que mockeamos ese método.
    # Debe devolver un diccionario, como lo haría el servicio de persistencia real.
    mock_persistence_service.get_one.return_value = sample_encrypted_credential.model_dump()

    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        retrieved_credential = await credential_service.get_credential(
            service_name=sample_encrypted_credential.service_name,
            credential_label=sample_encrypted_credential.credential_label
        )

        assert retrieved_credential is not None
        # El método devuelve los datos desencriptados en los campos 'encrypted_*'
        assert retrieved_credential.encrypted_api_key == sample_credential_data["api_key"]
        assert retrieved_credential.encrypted_api_secret == sample_credential_data["api_secret"]
        
        # Verificamos que se llamó a get_one con la condición correcta.
        mock_persistence_service.get_one.assert_called_once()
        call_args = mock_persistence_service.get_one.call_args.kwargs
        assert call_args['table_name'] == "api_credentials"
        # El service_name en el objeto Pydantic es un enum, por lo que accedemos a .value
        assert f"service_name = '{sample_credential_data['service_name'].value}'" in call_args['condition']
        assert f"credential_label = '{sample_encrypted_credential.credential_label}'" in call_args['condition']

@pytest.mark.asyncio
async def test_get_credential_decryption_failure_key(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service):
    # Simular que la clave está corrupta
    sample_encrypted_credential.encrypted_api_key = "corrupted_or_different_key_encrypted_data"
    mock_persistence_service.get_one.return_value = sample_encrypted_credential.model_dump()

    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        with pytest.raises(CredentialError) as excinfo:
            await credential_service.get_credential(
                service_name=sample_encrypted_credential.service_name,
                credential_label=sample_encrypted_credential.credential_label
            )
        assert "API Key para BINANCE_SPOT no pudo ser desencriptada" in str(excinfo.value)

@pytest.mark.asyncio
async def test_verify_credential_binance_success(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter, mock_persistence_service, sample_credential_data):
    mock_binance_adapter.get_account_info.return_value = {"canTrade": True, "permissions": ["SPOT"]}

    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        is_valid = await credential_service.verify_credential(sample_encrypted_credential)

        assert is_valid is True
        mock_binance_adapter.get_account_info.assert_called_once_with(
            sample_credential_data["api_key"], sample_credential_data["api_secret"]
        )
        
        # El servicio ahora usa 'upsert'. Verificamos que se llamó con los datos correctos.
        mock_persistence_service.upsert.assert_called_once()
        call_args = mock_persistence_service.upsert.call_args.kwargs
        assert call_args['table_name'] == "api_credentials"
        assert call_args['on_conflict'] == ["id"]
        
        data_sent = call_args['data']
        assert data_sent['id'] == str(sample_encrypted_credential.id)
        assert data_sent['status'] == "active"
        assert json.loads(data_sent['permissions']) == ["SPOT_TRADING"]


@pytest.mark.asyncio
async def test_verify_credential_binance_api_error(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter, mock_persistence_service, sample_credential_data):
    mock_binance_adapter.get_account_info.side_effect = BinanceAPIError("Binance Down", status_code=500)

    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        is_valid = await credential_service.verify_credential(sample_encrypted_credential)

        assert is_valid is False
        mock_binance_adapter.get_account_info.assert_called_once_with(
            sample_credential_data["api_key"], sample_credential_data["api_secret"]
        )
        
        # Verificamos que se llamó a 'upsert' con el estado de fallo.
        mock_persistence_service.upsert.assert_called_once()
        call_args = mock_persistence_service.upsert.call_args.kwargs
        assert call_args['data']['id'] == str(sample_encrypted_credential.id)
        assert call_args['data']['status'] == "verification_failed"

@pytest.mark.asyncio
async def test_verify_credential_decryption_error(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service):
    # Simular que la clave está corrupta
    original_fernet_decrypt = credential_service.fernet.decrypt
    def mock_decrypt_fail(token_bytes):
        if token_bytes == sample_encrypted_credential.encrypted_api_key.encode('utf-8'):
            raise InvalidToken
        return original_fernet_decrypt(token_bytes)

    with patch.object(credential_service.fernet, 'decrypt', side_effect=mock_decrypt_fail):
        with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
            with pytest.raises(CredentialError) as excinfo:
                await credential_service.verify_credential(sample_encrypted_credential)
            assert "API Key o Secret para Binance son nulos o no pudieron ser desencriptados." in str(excinfo.value)
        
        # Verificamos que se llamó a 'upsert' con el estado de fallo.
        mock_persistence_service.upsert.assert_called_once()
        call_args = mock_persistence_service.upsert.call_args.kwargs
        assert call_args['data']['id'] == str(sample_encrypted_credential.id)
        assert call_args['data']['status'] == "verification_failed"

@pytest.mark.asyncio
async def test_verify_credential_telegram_success(credential_service: CredentialService, mock_persistence_service):
    telegram_credential = APICredential(
        id=uuid4(),
        user_id=credential_service.fixed_user_id,
        service_name=ServiceName.TELEGRAM_BOT,
        credential_label="test_telegram",
        encrypted_api_key=credential_service.encrypt_data("telegram_token"),
        status="verification_pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    mock_notification_service = AsyncMock()
    mock_notification_service.send_test_telegram_notification = AsyncMock(return_value=True)
    
    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service):
        is_valid = await credential_service.verify_credential(telegram_credential, notification_service=mock_notification_service)
        
        assert is_valid is True
        mock_notification_service.send_test_telegram_notification.assert_called_once_with()
        
        # Verificamos que se llamó a 'upsert' con el estado activo.
        mock_persistence_service.upsert.assert_called_once()
        call_args = mock_persistence_service.upsert.call_args.kwargs
        assert call_args['data']['id'] == str(telegram_credential.id)
        assert call_args['data']['status'] == "active"

# Se pueden añadir más pruebas para update_credential, delete_credential, otros servicios, etc.
