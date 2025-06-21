import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal # Importar Decimal

from ultibot_backend.main import app # Importar 'app' desde la ruta correcta
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from shared.data_types import UserConfiguration

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_get_user_config_initial(client_with_db):
    """
    Verifica que GET /config retorne la configuración por defecto si no existe.
    """
    response = await client_with_db.get("/api/v1/config")
    assert response.status_code == 200
    config_data = response.json()
    assert config_data["user_id"] == str(FIXED_USER_ID)
    assert config_data["selected_theme"] == "dark"
    assert Decimal(config_data["default_paper_trading_capital"]) == Decimal("10000.0")
    assert config_data["paper_trading_active"] is True

@pytest.mark.asyncio
async def test_patch_user_config_update_paper_trading(client_with_db):
    """
    Verifica que PATCH /config actualice el estado de paper trading y capital.
    """
    # Primero, obtener la configuración inicial (o asegurar que exista)
    await client_with_db.get("/api/v1/config") # Esto creará la config por defecto si no existe

    # Datos para actualizar
    update_payload = {
        "paperTradingActive": False,
        "defaultPaperTradingCapital": 500.50
    }
    response = await client_with_db.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["user_id"] == str(FIXED_USER_ID)
    assert updated_config["paper_trading_active"] is False
    assert Decimal(updated_config["default_paper_trading_capital"]) == Decimal("500.50")
    # Verificar que otros campos por defecto no se hayan alterado
    assert updated_config["selected_theme"] == "dark"

    # Verificar que la configuración persista
    response_get = await client_with_db.get("/api/v1/config")
    assert response_get.status_code == 200
    persisted_config = response_get.json()
    assert persisted_config["paper_trading_active"] is False
    assert Decimal(persisted_config["default_paper_trading_capital"]) == Decimal("500.50")

@pytest.mark.asyncio
async def test_patch_user_config_only_paper_trading_active(client_with_db):
    """
    Verifica que PATCH /config solo actualice paperTradingActive.
    """
    await client_with_db.get("/api/v1/config") # Asegurar config por defecto

    update_payload = {
        "paperTradingActive": False
    }
    response = await client_with_db.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paper_trading_active"] is False
    assert Decimal(updated_config["default_paper_trading_capital"]) == Decimal("10000.0") # Debe permanecer igual
    assert updated_config["selected_theme"] == "dark" # Debe permanecer igual

@pytest.mark.asyncio
async def test_patch_user_config_only_capital(client_with_db):
    """
    Verifica que PATCH /config solo actualice defaultPaperTradingCapital.
    """
    await client_with_db.get("/api/v1/config") # Asegurar config por defecto

    update_payload = {
        "defaultPaperTradingCapital": 25000.0
    }
    response = await client_with_db.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paper_trading_active"] is True # Debe permanecer igual
    assert Decimal(updated_config["default_paper_trading_capital"]) == Decimal("25000.0")
    assert updated_config["selected_theme"] == "dark" # Debe permanecer igual

@pytest.mark.asyncio
async def test_patch_user_config_invalid_data(client_with_db):
    """
    Verifica que PATCH /config maneje datos inválidos.
    """
    update_payload = {
        "defaultPaperTradingCapital": "not_a_number" # Dato inválido
    }
    response = await client_with_db.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 422 # Unprocessable Entity (error de validación de Pydantic)
    # El mensaje de error puede variar, pero debe indicar un problema de tipo.
    # Pydantic v2 a menudo da mensajes más genéricos si el tipo base falla.
    assert "Input should be a valid decimal" in response.json()["detail"][0]["msg"]
