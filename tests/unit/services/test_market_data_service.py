import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.services.credential_service import CredentialService, CredentialError
from ultibot_backend.adapters.binance_adapter import BinanceAdapter, BinanceAPIError
from shared.data_types import APICredential, ServiceName, BinanceConnectionStatus, AssetBalance
from ultibot_backend.core.exceptions import UltiBotError

@pytest.fixture
def mock_credential_service():
    service = AsyncMock(spec=CredentialService)
    service.get_credential = AsyncMock()
    service.verify_credential = AsyncMock()
    return service

@pytest.fixture
def mock_binance_adapter():
    adapter = AsyncMock(spec=BinanceAdapter)
    adapter.get_spot_balances = AsyncMock()
    return adapter

@pytest.fixture
def market_data_service(mock_credential_service, mock_binance_adapter):
    return MarketDataService(mock_credential_service, mock_binance_adapter)

@pytest.fixture
def sample_user_id():
    return uuid4()

@pytest.fixture
def sample_binance_credential(sample_user_id):
    # Simula una credencial que sería devuelta por CredentialService.get_credential
    # Esta credencial ya tendría los campos 'encrypted_api_key' y 'encrypted_api_secret'
    # con los valores desencriptados, según la implementación de CredentialService.get_credential.
    return APICredential(
        id=uuid4(),
        user_id=sample_user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default",
        encrypted_api_key="decrypted_api_key_value", # Simula valor ya desencriptado
        encrypted_api_secret="decrypted_api_secret_value", # Simula valor ya desencriptado
        status="active",
        last_verified_at=datetime.utcnow(),
        permissions=["SPOT_TRADING"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_get_binance_connection_status_success(market_data_service: MarketDataService, mock_credential_service, sample_user_id, sample_binance_credential):
    mock_credential_service.get_credential.return_value = sample_binance_credential
    mock_credential_service.verify_credential.return_value = True
    # verify_credential actualiza sample_binance_credential internamente (last_verified_at, permissions)
    # Para la prueba, podemos simular esa actualización aquí si es necesario para el assert,
    # o confiar en que el mock de verify_credential lo haría.
    # Por simplicidad, asumimos que los valores en sample_binance_credential son post-verificación.
    
    status_result = await market_data_service.get_binance_connection_status(sample_user_id)

    assert status_result.is_connected is True
    assert status_result.status_message == "Conexión con Binance exitosa."
    assert status_result.last_verified_at == sample_binance_credential.last_verified_at
    assert status_result.account_permissions == sample_binance_credential.permissions
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=sample_user_id, service_name=ServiceName.BINANCE_SPOT, credential_label="default"
    )
    mock_credential_service.verify_credential.assert_called_once_with(sample_binance_credential)

@pytest.mark.asyncio
async def test_get_binance_connection_status_no_credentials(market_data_service: MarketDataService, mock_credential_service, sample_user_id):
    mock_credential_service.get_credential.return_value = None

    status_result = await market_data_service.get_binance_connection_status(sample_user_id)

    assert status_result.is_connected is False
    assert status_result.status_message == "Credenciales de Binance no encontradas. Por favor, configúrelas."
    assert status_result.status_code == "CREDENTIALS_NOT_FOUND"

@pytest.mark.asyncio
async def test_get_binance_connection_status_verification_failed(market_data_service: MarketDataService, mock_credential_service, sample_user_id, sample_binance_credential):
    mock_credential_service.get_credential.return_value = sample_binance_credential
    mock_credential_service.verify_credential.return_value = False # Simula fallo de verificación

    status_result = await market_data_service.get_binance_connection_status(sample_user_id)

    assert status_result.is_connected is False
    assert status_result.status_message == "Fallo en la verificación de conexión con Binance. Revise sus credenciales y permisos."
    assert status_result.status_code == "VERIFICATION_FAILED"

@pytest.mark.asyncio
async def test_get_binance_connection_status_credential_error(market_data_service: MarketDataService, mock_credential_service, sample_user_id):
    mock_credential_service.get_credential.side_effect = CredentialError("Decryption failed")

    status_result = await market_data_service.get_binance_connection_status(sample_user_id)
    
    assert status_result.is_connected is False
    assert "Error al acceder a las credenciales de Binance: Decryption failed" in status_result.status_message
    assert status_result.status_code == "CREDENTIAL_ERROR"

@pytest.mark.asyncio
async def test_get_binance_connection_status_binance_api_error(market_data_service: MarketDataService, mock_credential_service, sample_user_id, sample_binance_credential):
    mock_credential_service.get_credential.return_value = sample_binance_credential
    
    # Crear una instancia de BinanceAPIError y establecer el atributo code
    mock_api_error = BinanceAPIError("API unavailable", status_code=503)
    mock_api_error.code = "BINANCE_SPECIFIC_ERROR_CODE" # Simular un código específico
    mock_credential_service.verify_credential.side_effect = mock_api_error

    status_result = await market_data_service.get_binance_connection_status(sample_user_id)

    assert status_result.is_connected is False
    assert "Error de la API de Binance: API unavailable" in status_result.status_message
    assert status_result.status_code == "BINANCE_SPECIFIC_ERROR_CODE"


@pytest.mark.asyncio
async def test_get_binance_spot_balances_success(market_data_service: MarketDataService, mock_credential_service, mock_binance_adapter, sample_user_id, sample_binance_credential):
    mock_credential_service.get_credential.return_value = sample_binance_credential
    expected_balances = [AssetBalance(asset="BTC", free=1.0, locked=0.0, total=1.0)]
    mock_binance_adapter.get_spot_balances.return_value = expected_balances

    balances = await market_data_service.get_binance_spot_balances(sample_user_id)

    assert balances == expected_balances
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=sample_user_id, service_name=ServiceName.BINANCE_SPOT, credential_label="default"
    )
    mock_binance_adapter.get_spot_balances.assert_called_once_with(
        sample_binance_credential.encrypted_api_key, # Que es la clave desencriptada
        sample_binance_credential.encrypted_api_secret # Que es el secret desencriptado
    )

@pytest.mark.asyncio
async def test_get_binance_spot_balances_credential_not_found(market_data_service: MarketDataService, mock_credential_service, sample_user_id):
    mock_credential_service.get_credential.return_value = None

    with pytest.raises(CredentialError) as excinfo:
        await market_data_service.get_binance_spot_balances(sample_user_id)
    assert "Credenciales de Binance no encontradas para obtener balances." in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_binance_spot_balances_api_error(market_data_service: MarketDataService, mock_credential_service, mock_binance_adapter, sample_user_id, sample_binance_credential):
    mock_credential_service.get_credential.return_value = sample_binance_credential
    mock_binance_adapter.get_spot_balances.side_effect = BinanceAPIError("Failed to fetch balances")

    with pytest.raises(UltiBotError) as excinfo: # MarketDataService envuelve BinanceAPIError en UltiBotError
        await market_data_service.get_binance_spot_balances(sample_user_id)
    assert "No se pudieron obtener los balances de Binance: Failed to fetch balances" in str(excinfo.value)
