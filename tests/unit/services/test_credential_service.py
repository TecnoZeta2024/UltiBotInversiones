import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from cryptography.fernet import Fernet

from src.services.credential_service import CredentialService, CredentialError
from src.shared.data_types import APICredential, ServiceName
from src.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
from datetime import datetime

# Generar una clave Fernet válida para las pruebas
TEST_FERNET_KEY = Fernet.generate_key().decode('utf-8')

@pytest.fixture
def mock_binance_adapter():
    """Mock para BinanceAdapter."""
    adapter = AsyncMock(spec=BinanceAdapter)
    adapter.get_account_info = AsyncMock()
    return adapter

@pytest.fixture
def credential_service(mock_persistence_service: AsyncMock, mock_binance_adapter: MagicMock):
    """
    Fixture principal para CredentialService con dependencias mockeadas.
    Utiliza el mock_persistence_service de conftest.py para consistencia.
    """
    with patch.dict(os.environ, {"CREDENTIAL_ENCRYPTION_KEY": TEST_FERNET_KEY}):
        service = CredentialService(
            persistence_service=mock_persistence_service,
            binance_adapter=mock_binance_adapter
        )
        return service

@pytest.fixture
def sample_credential_data():
    """Datos de ejemplo para una credencial."""
    return {
        "service_name": ServiceName.BINANCE_SPOT,
        "credential_label": "test_binance",
        "api_key": "my_api_key",
        "api_secret": "my_api_secret"
    }

@pytest.fixture
def sample_encrypted_credential(credential_service: CredentialService, sample_credential_data):
    """Crea un objeto APICredential encriptado como se almacenaría en la BD."""
    return APICredential(
        id=uuid4(),
        user_id=credential_service.fixed_user_id,
        service_name=sample_credential_data["service_name"],
        credential_label=sample_credential_data["credential_label"],
        encrypted_api_key=credential_service.encrypt_data(sample_credential_data["api_key"]),
        encrypted_api_secret=credential_service.encrypt_data(sample_credential_data["api_secret"]),
        status="verification_pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

# --- Pruebas de Encriptación/Desencriptación ---

def test_encrypt_decrypt_data(credential_service: CredentialService):
    original_data = "this_is_a_secret"
    encrypted = credential_service.encrypt_data(original_data)
    assert encrypted != original_data
    decrypted = credential_service.decrypt_data(encrypted)
    assert decrypted == original_data

def test_decrypt_invalid_token(credential_service: CredentialService):
    assert credential_service.decrypt_data("invalid_encrypted_string") is None

# --- Pruebas de Métodos del Servicio ---

@pytest.mark.asyncio
async def test_add_credential(credential_service: CredentialService, sample_credential_data, mock_persistence_service: AsyncMock):
    # Configurar el mock para que devuelva un valor simulado
    mock_persistence_service.upsert.return_value = None # O un objeto relevante si es necesario

    created_credential = await credential_service.add_credential(**sample_credential_data)

    assert created_credential is not None
    mock_persistence_service.upsert.assert_called_once()
    
    call_args = mock_persistence_service.upsert.call_args.kwargs
    assert call_args['table_name'] == "api_credentials"
    
    data_sent = call_args['data']
    assert data_sent['user_id'] == str(credential_service.fixed_user_id)
    assert data_sent['service_name'] == sample_credential_data["service_name"].value
    
    decrypted_key = credential_service.decrypt_data(data_sent['encrypted_api_key'])
    assert decrypted_key == sample_credential_data["api_key"]
    decrypted_secret = credential_service.decrypt_data(data_sent['encrypted_api_secret'])
    assert decrypted_secret == sample_credential_data["api_secret"]

@pytest.mark.asyncio
async def test_get_credential_success(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service: AsyncMock, sample_credential_data):
    mock_persistence_service.get_one.return_value = sample_encrypted_credential

    retrieved_credential = await credential_service.get_credential(
        service_name=sample_encrypted_credential.service_name,
        credential_label=sample_encrypted_credential.credential_label
    )

    assert retrieved_credential is not None
    assert retrieved_credential.encrypted_api_key == sample_credential_data["api_key"]
    assert retrieved_credential.encrypted_api_secret == sample_credential_data["api_secret"]
    
    mock_persistence_service.get_one.assert_called_once()
    call_args = mock_persistence_service.get_one.call_args.kwargs
    assert call_args['table_name'] == "api_credentials"
    assert f"service_name = '{sample_credential_data['service_name'].value}'" in call_args['condition']
    assert f"credential_label = '{sample_encrypted_credential.credential_label}'" in call_args['condition']

@pytest.mark.asyncio
async def test_get_credential_decryption_failure_key(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service: AsyncMock):
    sample_encrypted_credential.encrypted_api_key = "corrupted_or_different_key_encrypted_data"
    mock_persistence_service.get_one.return_value = sample_encrypted_credential

    with pytest.raises(CredentialError, match="API Key para .* no pudo ser desencriptada"):
        await credential_service.get_credential(
            service_name=sample_encrypted_credential.service_name,
            credential_label=sample_encrypted_credential.credential_label
        )

@pytest.mark.asyncio
async def test_verify_credential_binance_success(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter: MagicMock, mock_persistence_service: AsyncMock, sample_credential_data):
    mock_binance_adapter.get_account_info.return_value = {"canTrade": True, "permissions": ["SPOT"]}
    mock_persistence_service.get_one.return_value = sample_encrypted_credential

    is_valid = await credential_service.verify_credential(sample_encrypted_credential.credential_label, sample_encrypted_credential.service_name)

    assert is_valid is True
    mock_binance_adapter.get_account_info.assert_called_once_with(
        sample_credential_data["api_key"], sample_credential_data["api_secret"]
    )
    
    mock_persistence_service.upsert.assert_called_once()
    call_args = mock_persistence_service.upsert.call_args.kwargs
    assert call_args['data']['id'] == str(sample_encrypted_credential.id)
    assert call_args['data']['status'] == "active"
    assert call_args['data']['permissions'] == ["SPOT_TRADING"]

@pytest.mark.asyncio
async def test_verify_credential_binance_api_error(credential_service: CredentialService, sample_encrypted_credential, mock_binance_adapter: MagicMock, mock_persistence_service: AsyncMock, sample_credential_data):
    mock_binance_adapter.get_account_info.side_effect = BinanceAPIError("Binance Down", status_code=500)
    mock_persistence_service.get_one.return_value = sample_encrypted_credential

    is_valid = await credential_service.verify_credential(sample_encrypted_credential.credential_label, sample_encrypted_credential.service_name)

    assert is_valid is False
    mock_binance_adapter.get_account_info.assert_called_once_with(
        sample_credential_data["api_key"], sample_credential_data["api_secret"]
    )
    
    mock_persistence_service.upsert.assert_called_once()
    call_args = mock_persistence_service.upsert.call_args.kwargs
    assert call_args['data']['id'] == str(sample_encrypted_credential.id)
    assert call_args['data']['status'] == "verification_failed"

@pytest.mark.asyncio
async def test_verify_credential_decryption_error(credential_service: CredentialService, sample_encrypted_credential, mock_persistence_service: AsyncMock):
    mock_persistence_service.get_one.return_value = sample_encrypted_credential
    
    # Sobrescribir el mock de decrypt_data para este test específico.
    # El side_effect hace que la primera llamada (para la api_key) devuelva None.
    with patch.object(credential_service, 'decrypt_data', side_effect=[None, "valid_secret"]):
        # Se espera que se lance un CredentialError desde dentro de get_credential.
        with pytest.raises(CredentialError, match="API Key para .* no pudo ser desencriptada"):
            await credential_service.verify_credential(sample_encrypted_credential.credential_label, sample_encrypted_credential.service_name)
    
    # En este escenario de fallo, la excepción se lanza antes de que se pueda guardar
    # el estado. Por lo tanto, upsert no debe ser llamado.
    mock_persistence_service.upsert.assert_not_called()

@pytest.mark.asyncio
async def test_verify_credential_telegram_success(credential_service: CredentialService, mock_persistence_service: AsyncMock):
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
    mock_persistence_service.get_one.return_value = telegram_credential
    
    mock_notification_service = AsyncMock()
    mock_notification_service.send_test_telegram_notification = AsyncMock(return_value=True)
    
    is_valid = await credential_service.verify_credential(
        telegram_credential.credential_label, 
        telegram_credential.service_name,
        notification_service=mock_notification_service
    )
    
    assert is_valid is True
    mock_notification_service.send_test_telegram_notification.assert_called_once_with()
    
    mock_persistence_service.upsert.assert_called_once()
    call_args = mock_persistence_service.upsert.call_args.kwargs
    assert call_args['data']['id'] == str(telegram_credential.id)
    assert call_args['data']['status'] == "active"
