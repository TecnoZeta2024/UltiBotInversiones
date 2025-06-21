import pytest
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from httpx import AsyncClient

# 1. Modelo Pydantic Mínimo con alias_generator
class MinimalModel(BaseModel):
    snake_case_field: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

# 2. App de FastAPI Mínima
minimal_app = FastAPI()

@minimal_app.get("/test-serialization", response_model=MinimalModel, response_model_by_alias=True)
async def get_minimal_model():
    return MinimalModel(snake_case_field="test_value")

# 3. Test de Aislamiento
@pytest.mark.asyncio
async def test_minimal_serialization_logic():
    """
    Test de aislamiento para verificar si la serialización con alias_generator
    y response_model_by_alias=True funciona en un entorno mínimo.
    """
    async with AsyncClient(app=minimal_app, base_url="http://test") as client:
        response = await client.get("/test-serialization")
        
        # Debug: Imprimir la respuesta para ver qué está llegando
        print("Response status code:", response.status_code)
        print("Response JSON:", response.json())
        
        assert response.status_code == 200
        
        data = response.json()
        
        # La clave debería ser 'snakeCaseField' (camelCase) debido al alias_generator
        assert "snakeCaseField" in data
        assert "snake_case_field" not in data
        assert data["snakeCaseField"] == "test_value"
