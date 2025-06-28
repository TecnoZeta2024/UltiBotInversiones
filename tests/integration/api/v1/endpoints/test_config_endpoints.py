# tests/integration/api/v1/endpoints/test_config_endpoints.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from src.core.domain_models.user_configuration_models import UserConfiguration
from src.shared.data_types import APICredential # Corrected import path
from unittest.mock import AsyncMock
from src.dependencies import get_credential_service, get_portfolio_service, get_config_service # Added get_config_service
from src.shared.data_types import ServiceName
from uuid import uuid4
from datetime import datetime, timezone

# Marcar todos los tests de este módulo para que se ejecuten con pytest-asyncio
pytestmark = pytest.mark.asyncio


async def test_get_user_config(
    client: tuple[AsyncClient, any], db_session: AsyncSession
):
    """
    Tests fetching the user configuration.
    """
    http_client, _ = client
    response = await http_client.get("/api/v1/config")
    assert response.status_code == 200
    
    config_data = response.json()
    # Validar con el modelo Pydantic asegura la consistencia del contrato
    validated_config = UserConfiguration.model_validate(config_data)
    
    assert validated_config.user_id is not None
    assert "aiStrategyConfigurations" in config_data
    assert isinstance(config_data["aiStrategyConfigurations"], list)


async def test_update_user_config(
    client: tuple[AsyncClient, any], db_session: AsyncSession
):
    """
    Tests updating the user configuration.
    """
    http_client, _ = client
    update_payload = {
        "aiStrategyConfigurations": [], # Empty list for now, or add a mock AIStrategyConfiguration
        "defaultPaperTradingCapital": 15000.0
    }
    
    response = await http_client.patch("/api/v1/config", json=update_payload)
    assert response.status_code == 200
    
    updated_config = UserConfiguration.model_validate(response.json())
    
    assert updated_config.ai_strategy_configurations == []
    assert updated_config.default_paper_trading_capital == Decimal("15000.0")

    # Verificar que el cambio persiste
    response_after_update = await http_client.get("/api/v1/config")
    persisted_config = UserConfiguration.model_validate(response_after_update.json())
    assert persisted_config.ai_strategy_configurations == []


async def test_real_trading_mode_status_and_activation(
    client: tuple[AsyncClient, any], db_session: AsyncSession
):
    """
    Tests the status, activation, and deactivation of the real trading mode.
    """
    http_client, app = client # Desestructurar app

    # Arrange: Mockear servicios y sobrescribir dependencias
    # La fixture 'client' ya configura los mocks necesarios para CredentialService y PortfolioService
    # a través de app.dependency_overrides en conftest.py.
    # No es necesario crear y configurar mocks de ConfigurationService aquí,
    # ya que FastAPI inyectará la instancia real de ConfigurationService
    # que a su vez usará los mocks de CredentialService y PortfolioService
    # proporcionados por la fixture 'client'.

    # 1. Verificar estado inicial (debería ser inactivo por defecto)
    response_status = await http_client.get("/api/v1/config/real-trading-mode/status")
    assert response_status.status_code == 200
    assert response_status.json() == {"is_real_trading_enabled": False}

    # 2. Activar el modo de trading real
    response_activate = await http_client.post("/api/v1/config/real-trading-mode/activate")
    assert response_activate.status_code == 200
    assert "activado exitosamente" in response_activate.json()["message"]

    # 3. Verificar que el estado ha cambiado a activo
    response_status_after_activation = await http_client.get("/api/v1/config/real-trading-mode/status")
    assert response_status_after_activation.status_code == 200
    assert response_status_after_activation.json() == {"is_real_trading_enabled": True}

    # 4. Desactivar el modo de trading real
    response_deactivate = await http_client.post("/api/v1/config/real-trading-mode/deactivate")
    assert response_deactivate.status_code == 200
    assert "desactivado" in response_deactivate.json()["message"]
    
    # 5. Verificar que el estado ha vuelto a inactivo
    response_status_after_deactivation = await http_client.get("/api/v1/config/real-trading-mode/status")
    assert response_status_after_deactivation.status_code == 200
    assert response_status_after_deactivation.json() == {"is_real_trading_enabled": False}

    # Limpiar los overrides después del test
    app.dependency_overrides.clear()
