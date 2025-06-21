import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from uuid import UUID
from decimal import Decimal

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_get_user_config_initial(client: tuple[AsyncClient, FastAPI]):
    """
    Verifica que GET /config retorne la configuración por defecto si no existe.
    """
    test_client, _ = client
    response = await test_client.get("/api/v1/config")
    assert response.status_code == 200
    config_data = response.json()
    assert config_data["userId"] == str(FIXED_USER_ID)
    assert config_data["selectedTheme"] == "dark"
    assert Decimal(config_data["defaultPaperTradingCapital"]) == Decimal("10000.0")
    assert config_data["paperTradingActive"] is True


@pytest.mark.asyncio
async def test_patch_user_config_update_paper_trading(client: tuple[AsyncClient, FastAPI]):
    """
    Verifica que PATCH /config actualice el estado de paper trading y capital.
    """
    test_client, _ = client
    # Primero, obtener la configuración inicial (o asegurar que exista)
    await test_client.get("/api/v1/config")  # Esto creará la config por defecto si no existe

    # Datos para actualizar
    update_payload = {
        "paperTradingActive": False,
        "defaultPaperTradingCapital": 500.50
    }
    response = await test_client.patch("/api/v1/config", json=update_payload)

    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["userId"] == str(FIXED_USER_ID)
    assert updated_config["paperTradingActive"] is False
    assert Decimal(updated_config["defaultPaperTradingCapital"]) == Decimal("500.50")
    # Verificar que otros campos por defecto no se hayan alterado
    assert updated_config["selectedTheme"] == "dark"

    # Verificar que la configuración persista
    response_get = await test_client.get("/api/v1/config")
    assert response_get.status_code == 200
    persisted_config = response_get.json()
    assert persisted_config["paperTradingActive"] is False
    assert Decimal(persisted_config["defaultPaperTradingCapital"]) == Decimal("500.50")


@pytest.mark.asyncio
async def test_patch_user_config_only_paper_trading_active(client: tuple[AsyncClient, FastAPI]):
    """
    Verifica que PATCH /config solo actualice paperTradingActive.
    """
    test_client, _ = client
    await test_client.get("/api/v1/config")  # Asegurar config por defecto

    update_payload = {
        "paperTradingActive": False
    }
    response = await test_client.patch("/api/v1/config", json=update_payload)

    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is False
    assert Decimal(updated_config["defaultPaperTradingCapital"]) == Decimal("10000.0")  # Debe permanecer igual
    assert updated_config["selectedTheme"] == "dark"  # Debe permanecer igual


@pytest.mark.asyncio
async def test_patch_user_config_only_capital(client: tuple[AsyncClient, FastAPI]):
    """
    Verifica que PATCH /config solo actualice defaultPaperTradingCapital.
    """
    test_client, _ = client
    await test_client.get("/api/v1/config")  # Asegurar config por defecto

    update_payload = {
        "defaultPaperTradingCapital": 25000.0
    }
    response = await test_client.patch("/api/v1/config", json=update_payload)

    assert response.status_code == 200
    updated_config = response.json()
    assert updated_config["paperTradingActive"] is True  # Debe permanecer igual
    assert Decimal(updated_config["defaultPaperTradingCapital"]) == Decimal("25000.0")
    assert updated_config["selectedTheme"] == "dark"  # Debe permanecer igual


@pytest.mark.asyncio
async def test_patch_user_config_invalid_data(client: tuple[AsyncClient, FastAPI]):
    """
    Verifica que PATCH /config maneje datos inválidos.
    """
    test_client, _ = client
    update_payload = {
        "defaultPaperTradingCapital": "not_a_number"  # Dato inválido
    }
    response = await test_client.patch("/api/v1/config", json=update_payload)

    assert response.status_code == 422  # Unprocessable Entity (error de validación de Pydantic)
    
    # El mensaje de error puede variar, pero debe indicar un problema de tipo.
    # La comprobación exacta puede ser frágil, pero verificamos que el detalle exista.
    error_detail = response.json().get("detail", [])
    assert isinstance(error_detail, list)
    assert len(error_detail) > 0
    
    # Buscar un mensaje de error relacionado con decimal
    assert any("decimal" in msg.get("msg", "").lower() for msg in error_detail)
