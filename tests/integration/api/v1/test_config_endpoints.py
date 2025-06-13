import pytest
from httpx import AsyncClient
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from ultibot_backend.main import app
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.dependencies import get_persistence_service

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture para un cliente de prueba asíncrono de FastAPI.
    Sobrescribe la dependencia de persistencia para usar la sesión de BD del test.
    """
    
    # Crear una instancia del servicio de persistencia con la sesión del test
    persistence_service_override = SupabasePersistenceService(db_session=db_session)

    # Crear una función que devuelva nuestra instancia sobreescrita
    def override_get_persistence_service():
        return persistence_service_override

    # Aplicar el override a la app de FastAPI
    app.dependency_overrides[get_persistence_service] = override_get_persistence_service

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Limpiar el override después del test
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_user_config_initial(client: AsyncClient):
    """
    Verifica que GET /config retorne la configuración por defecto si no existe.
    La db_session transaccional asegura que la BD está limpia.
    """
    response = await client.get("/api/v1/config")
    assert response.status_code == 200
    config_data = response.json()
    assert config_data["userId"] == str(FIXED_USER_ID)
    assert config_data["selectedTheme"] == "dark"
    assert config_data["defaultPaperTradingCapital"] == 10000.0
    assert config_data["paperTradingActive"] is True

@pytest.mark.asyncio
async def test_patch_user_config_update_paper_trading(client: AsyncClient):
    """
    Verifica que PATCH /config actualice el estado de paper trading y capital.
    """
    # Primero, obtener la configuración inicial para que se cree en la BD
    await client.get("/api/v1/config")

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
    assert updated_config["selectedTheme"] == "dark"

    # Verificar que la configuración persista dentro de la misma transacción
    response_get = await client.get("/api/v1/config")
    assert response_get.status_code == 200
    persisted_config = response_get.json()
    assert persisted_config["paperTradingActive"] is False
    assert persisted_config["defaultPaperTradingCapital"] == 500.50

@pytest.mark.asyncio
async def test_patch_user_config_only_paper_trading_active(client: AsyncClient):
    """
    Verifica que PATCH /config solo actualice paperTradingActive.
    """
    await client.get("/api/v1/config")

    update_payload = {
        "paperTradingActive": False
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is False
    assert updated_config["defaultPaperTradingCapital"] == 10000.0

@pytest.mark.asyncio
async def test_patch_user_config_only_capital(client: AsyncClient):
    """
    Verifica que PATCH /config solo actualice defaultPaperTradingCapital.
    """
    await client.get("/api/v1/config")

    update_payload = {
        "defaultPaperTradingCapital": 25000.0
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is True
    assert updated_config["defaultPaperTradingCapital"] == 25000.0

@pytest.mark.asyncio
async def test_patch_user_config_invalid_data(client: AsyncClient):
    """
    Verifica que PATCH /config maneje datos inválidos.
    """
    update_payload = {
        "defaultPaperTradingCapital": "not_a_number"
    }
    response = await client.patch("/api/v1/config", json=update_payload)
    
    assert response.status_code == 422
    assert "value is not a valid float" in response.json()["detail"][0]["msg"]
