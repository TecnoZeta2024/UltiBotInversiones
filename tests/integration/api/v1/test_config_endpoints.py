import pytest
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import datetime, timezone

from src.ultibot_backend.main import app # Importar 'app' desde la ruta correcta
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigService
from src.shared.data_types import UserConfiguration

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture(scope="module")
async def client():
    """
    Fixture para un cliente de prueba asíncrono de FastAPI.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def cleanup_db_after_each_test():
    """
    Limpia la base de datos después de cada test para asegurar un estado limpio.
    """
    persistence_service = SupabasePersistenceService()
    await persistence_service.connect()
    try:
        # Eliminar la configuración del usuario fijo si existe
        await persistence_service.execute_raw_sql(f"DELETE FROM user_configurations WHERE user_id = '{FIXED_USER_ID}';")
        await persistence_service.execute_raw_sql(f"DELETE FROM api_credentials WHERE user_id = '{FIXED_USER_ID}';")
        await persistence_service.execute_raw_sql(f"DELETE FROM notifications WHERE user_id = '{FIXED_USER_ID}';")
    finally:
        await persistence_service.disconnect()

@pytest.mark.asyncio
async def test_get_user_config_initial(client):
    """
    Verifica que GET /config retorne la configuración por defecto si no existe.
    """
    response = await client.get("/api/v1/config")
    assert response.status_code == 200
    config_data = response.json()
    assert config_data["userId"] == str(FIXED_USER_ID)
    assert config_data["selectedTheme"] == "dark"
    assert config_data["defaultPaperTradingCapital"] == 10000.0
    assert config_data["paperTradingActive"] is True # Verificar el nuevo campo

@pytest.mark.asyncio
async def test_patch_user_config_update_paper_trading(client):
    """
    Verifica que PATCH /config actualice el estado de paper trading y capital.
    """
    # Primero, obtener la configuración inicial (o asegurar que exista)
    await client.get("/api/v1/config") # Esto creará la config por defecto si no existe

    # Datos para actualizar
    update_payload = {
        "paperTradingActive": False,
        "defaultPaperTradingCapital": 500.50
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["userId"] == str(FIXED_USER_ID)
    assert updated_config["paperTradingActive"] is False
    assert updated_config["defaultPaperTradingCapital"] == 500.50
    # Verificar que otros campos por defecto no se hayan alterado
    assert updated_config["selectedTheme"] == "dark"

    # Verificar que la configuración persista
    response_get = await client.get("/api/v1/config")
    assert response_get.status_code == 200
    persisted_config = response_get.json()
    assert persisted_config["paperTradingActive"] is False
    assert persisted_config["defaultPaperTradingCapital"] == 500.50

@pytest.mark.asyncio
async def test_patch_user_config_only_paper_trading_active(client):
    """
    Verifica que PATCH /config solo actualice paperTradingActive.
    """
    await client.get("/api/v1/config") # Asegurar config por defecto

    update_payload = {
        "paperTradingActive": False
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is False
    assert updated_config["defaultPaperTradingCapital"] == 10000.0 # Debe permanecer igual
    assert updated_config["selectedTheme"] == "dark" # Debe permanecer igual

@pytest.mark.asyncio
async def test_patch_user_config_only_capital(client):
    """
    Verifica que PATCH /config solo actualice defaultPaperTradingCapital.
    """
    await client.get("/api/v1/config") # Asegurar config por defecto

    update_payload = {
        "defaultPaperTradingCapital": 25000.0
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is True # Debe permanecer igual
    assert updated_config["defaultPaperTradingCapital"] == 25000.0
    assert updated_config["selectedTheme"] == "dark" # Debe permanecer igual

@pytest.mark.asyncio
async def test_patch_user_config_invalid_data(client):
    """
    Verifica que PATCH /config maneje datos inválidos.
    """
    update_payload = {
        "defaultPaperTradingCapital": "not_a_number" # Dato inválido
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 422 # Unprocessable Entity (error de validación de Pydantic)
    assert "value is not a valid float" in response.json()["detail"][0]["msg"]
