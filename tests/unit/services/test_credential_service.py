import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4, UUID
from datetime import datetime
from cryptography.fernet import Fernet, InvalidToken

from ultibot_backend.services.credential_service import CredentialService, CredentialError
from shared.data_types import APICredential, ServiceName
from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError

# Generar una clave Fernet válida para las pruebas
TEST_FERNET_KEY = Fernet.generate_key().decode('utf-8')

@pytest.fixture
def mock_persistence_service():
    return AsyncMock()

@pytest.fixture
def mock_binance_adapter():
    adapter = AsyncMock(spec=BinanceAdapter)
    adapter.get_account_info = AsyncMock()
    return adapter

@pytest.fixture
def credential_service(mock_persistence_service, mock_binance_adapter):
    # Mockear las dependencias que CredentialService inicializa internamente
    with patch('ultibot_backend.services.credential_service.SupabasePersistenceService', return_value=mock_persistence_service), \
         patch('ultibot_backend.services.credential_service.BinanceAdapter', return_value=mock_binance_adapter):
        service = CredentialService(encryption_key=TEST_FERNET_KEY)
        # Re-asignar mocks si es necesario, aunque el patch debería cubrirlos
        service.persistence_service = mock_persistence_service
        service.binance_adapter = mock_binance_adapter
        return service

@pytest.fixture
def sample_user_id():
    return uuid4()

@pytest.fixture
def sample_credential_data(sample_user_id):
    return {
        "user_id": sample_user_id,
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
        user_id=sample_credential_data["user_id"],
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
    mock_persistence_service.save_credential = AsyncMock(return_value=APICredential(**sample_credential_data, id=uuid4(), encrypted_api_key="enc_key", encrypted_api_secret="enc_secret"))
    
    created_credential = await credential_service.add_credential(**sample_credential_data)

    assert created_credential is not None
    mock_persistence_service.save_credential.assert_called_once()
    call_args = mock_persistence_service.save_credential.call_args[0][0]
    assert call_args.user_id == sample_credential_data["user_id"]
    assert call_args.service_name == sample_credential_data["service_name"]
    # Verificar que los datos estén encriptados
    assert credential_service.decrypt_data(call_args.encrypted_api_key) == sample_credential_data["api_key"]
    assert credential_service.decrypt_data(call_args.encrypted_api_secret) == sample_credential_data["api_secret"]

@pytest.mark.asyncio
async def test_get_credential_success(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service, sample_credential_data):
    mock_persistence_service.get_credential_by_service_label = AsyncMock(return_value=sample_encrypted_credential)

    retrieved_credential = await credential_service.get_credential(
        user_id=sample_encrypted_credential.user_id,
        service_name=sample_encrypted_credential.service_name,
        credential_label=sample_encrypted_credential.credential_label
    )

    assert retrieved_credential is not None
    # En get_credential, encrypted_api_key y secret se reemplazan con los valores desencriptados
    assert retrieved_credential.encrypted_api_key == sample_credential_data["api_key"] 
    assert retrieved_credential.encrypted_api_secret == sample_credential_data["api_secret"]
    mock_persistence_service.get_credential_by_service_label.assert_called_once_with(
        sample_encrypted_credential.user_id,
        sample_encrypted_credential.service_name,
        sample_encrypted_credential.credential_label
    )

@pytest.mark.asyncio
async def test_get_credential_decryption_failure_key(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service):
    # Simular que la clave está corrupta o fue encriptada con otra Fernet key
    sample_encrypted_credential.encrypted_api_key = "corrupted_or_different_key_encrypted_data"
    mock_persistence_service.get_credential_by_service_label = AsyncMock(return_value=sample_encrypted_credential)

    with pytest.raises(CredentialError) as excinfo:
        await credential_service.get_credential(
            user_id=sample_encrypted_credential.user_id,
            service_name=sample_encrypted_credential.service_name,
            credential_label=sample_encrypted_credential.credential_label
        )
    assert "API Key para BINANCE_SPOT no pudo ser desencriptada" in str(excinfo.value)

@pytest.mark.asyncio
async def test_verify_credential_binance_success(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter, mock_persistence_service, sample_credential_data):
    mock_binance_adapter.get_account_info.return_value = {"canTrade": True, "permissions": ["SPOT"]}
    
    # El objeto sample_encrypted_credential tiene los campos encriptados.
    # verify_credential los desencriptará internamente.
    is_valid = await credential_service.verify_credential(sample_encrypted_credential)

    assert is_valid is True
    mock_binance_adapter.get_account_info.assert_called_once_with(
        sample_credential_data["api_key"], sample_credential_data["api_secret"]
    )
    # Verificar que se actualizó el estado y permisos
    mock_persistence_service.update_credential_status.assert_called_with(
        sample_encrypted_credential.id, "active", ANY # Usar ANY para el timestamp
    )
    mock_persistence_service.update_credential_permissions.assert_called_with(
        sample_encrypted_credential.id, ["SPOT_TRADING"], ANY # Usar ANY para el timestamp
    )


@pytest.mark.asyncio
async def test_verify_credential_binance_api_error(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter, mock_persistence_service, sample_credential_data):
    mock_binance_adapter.get_account_info.side_effect = BinanceAPIError("Binance Down", status_code=500)
    
    is_valid = await credential_service.verify_credential(sample_encrypted_credential)

    assert is_valid is False
    mock_binance_adapter.get_account_info.assert_called_once_with(
        sample_credential_data["api_key"], sample_credential_data["api_secret"]
    )
    mock_persistence_service.update_credential_status.assert_called_with(
        sample_encrypted_credential.id, "verification_failed", ANY # Usar ANY para el timestamp
    )

@pytest.mark.asyncio
async def test_verify_credential_decryption_error(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service):
    # Simular que la clave está corrupta
    original_fernet_decrypt = credential_service.fernet.decrypt
    def mock_decrypt_fail(token_bytes): # Renombrar token a token_bytes para claridad
        # sample_encrypted_credential.encrypted_api_key es un string
        # credential_service.fernet.decrypt espera bytes
        if token_bytes == sample_encrypted_credential.encrypted_api_key.encode('utf-8'):
            raise InvalidToken # Usar la excepción importada directamente
        return original_fernet_decrypt(token_bytes)

    with patch.object(credential_service.fernet, 'decrypt', side_effect=mock_decrypt_fail):
        with pytest.raises(CredentialError) as excinfo:
            await credential_service.verify_credential(sample_encrypted_credential)
        assert "API Key para BINANCE_SPOT no pudo ser desencriptada" in str(excinfo.value)
    
    mock_persistence_service.update_credential_status.assert_called_with(
        sample_encrypted_credential.id, "verification_failed", ANY # Usar ANY para el timestamp
    )

@pytest.mark.asyncio
async def test_verify_credential_telegram_success(credential_service: CredentialService, sample_user_id, mock_persistence_service):
    telegram_credential = APICredential(
        id=uuid4(),
        user_id=sample_user_id,
        service_name=ServiceName.TELEGRAM_BOT,
        credential_label="test_telegram",
        encrypted_api_key=credential_service.encrypt_data("telegram_token"), # El token es la API Key
        status="verification_pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    mock_notification_service = AsyncMock()
    mock_notification_service.send_test_telegram_notification = AsyncMock(return_value=True)
    
    is_valid = await credential_service.verify_credential(telegram_credential, notification_service=mock_notification_service)
    
    assert is_valid is True
    mock_notification_service.send_test_telegram_notification.assert_called_once_with(sample_user_id)
    mock_persistence_service.update_credential_status.assert_called_with(
        telegram_credential.id, "active", ANY # Usar ANY para el timestamp
    )

# Se pueden añadir más pruebas para update_credential, delete_credential, otros servicios, etc.
