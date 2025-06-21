import pytest
from httpx import AsyncClient
from fastapi import FastAPI, Depends, APIRouter
from typing import Tuple
from ultibot_backend.app_config import AppSettings, get_app_settings
from ultibot_backend.main import app as fastapi_app

# Añadir un endpoint de prueba a la aplicación principal para este test
config_router = APIRouter()

@config_router.get("/test-config")
def get_test_config(settings: AppSettings = Depends(get_app_settings)):
    return {"log_level": settings.LOG_LEVEL}

@pytest.mark.asyncio
async def test_config_dependency_injection(
    client: Tuple[AsyncClient, FastAPI], app_settings_fixture: AppSettings
):
    """
    Tests that the dependency override for AppSettings works correctly by
    creating a modified settings object and injecting it into the test client's app instance.
    """
    test_client, test_app = client
    
    # Include the test router in the isolated test app instance
    test_app.include_router(config_router)

    # 1. Test with default settings from .env.test (via app_settings_fixture)
    response_default = await test_client.get("/test-config")
    assert response_default.status_code == 200
    # La configuración por defecto en .env.test es INFO
    assert response_default.json() == {"log_level": "INFO"}

    # 2. Test with a manually modified and injected settings object
    # Create a new settings object based on the original, but with a different LOG_LEVEL
    modified_settings_dict = app_settings_fixture.model_dump()
    modified_settings_dict['LOG_LEVEL'] = 'DEBUG_TEST'
    modified_settings = AppSettings(**modified_settings_dict)
    
    # Correct way: Override the dependency on the app instance used by the client
    test_app.dependency_overrides[get_app_settings] = lambda: modified_settings

    response_patched = await test_client.get("/test-config")
    assert response_patched.status_code == 200
    assert response_patched.json() == {"log_level": "DEBUG_TEST"}
    
    # Cleanup the override to not affect other tests
    test_app.dependency_overrides.clear()
