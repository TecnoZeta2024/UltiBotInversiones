import asyncio
import pytest
import pytest_asyncio
import sys
import os

# SRST-DB-SETUP: Establecer el modo de prueba ANTES de cualquier otra importación.
# Esto asegura que app_config cargue .env.test y se use la base de datos de prueba.
os.environ['TESTING'] = 'True'
from typing import AsyncGenerator
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
from datetime import datetime, timezone
from psycopg.sql import SQL # Añadir esta importación

# Añadir el directorio 'src' al sys.path para que las importaciones de módulos funcionen correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from ultibot_backend.main import app
from ultibot_backend.dependencies import (
    get_performance_service,
    get_strategy_service,
    get_persistence_service,
)
from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService

@pytest.fixture(scope="session")
def event_loop():
    """Crea una instancia del event loop para toda la sesión de tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_persistence_service_integration():
    """Mock para el servicio de persistencia."""
    mock = AsyncMock(spec=SupabasePersistenceService)
    mock.get_all_trades_for_user.return_value = []
    return mock

@pytest.fixture
def mock_strategy_service_integration():
    """Mock para el servicio de estrategias."""
    return MagicMock(spec=StrategyService)

@pytest_asyncio.fixture
async def client(
    mock_persistence_service_integration, mock_strategy_service_integration
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture que proporciona un AsyncClient para interactuar con la aplicación de forma asíncrona.
    Este enfoque es crucial para asegurar que el ciclo de vida (lifespan) de la aplicación FastAPI
    se ejecute correctamente, inicializando el contenedor de dependencias antes de las pruebas.
    """
    mocked_performance_service = PerformanceService(
        persistence_service=mock_persistence_service_integration,
        strategy_service=mock_strategy_service_integration
    )
    
    app.dependency_overrides[get_persistence_service] = lambda: mock_persistence_service_integration
    app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
    app.dependency_overrides[get_performance_service] = lambda: mocked_performance_service

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_after_each_test():
    """
    Limpia la base de datos después de cada test para asegurar un estado limpio.
    """
    persistence_service = SupabasePersistenceService()
    try:
        await persistence_service.connect()
        if persistence_service.pool: # Verificar que el pool se haya inicializado correctamente
            async with persistence_service.pool.connection() as conn:
                async with conn.cursor() as cur:
                    # Eliminar la configuración del usuario fijo si existe
                    await cur.execute(SQL("DELETE FROM user_configurations WHERE user_id = %s;"), (FIXED_USER_ID,))
                    await cur.execute(SQL("DELETE FROM api_credentials WHERE user_id = %s;"), (FIXED_USER_ID,))
                    await cur.execute(SQL("DELETE FROM notifications WHERE user_id = %s;"), (FIXED_USER_ID,))
    except Exception as e:
        # Log the error but don't fail the test cleanup
        print(f"Error during database cleanup: {e}")
    finally:
        await persistence_service.disconnect()
