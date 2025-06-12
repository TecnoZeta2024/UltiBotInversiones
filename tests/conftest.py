import asyncio
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Configuración Inicial del Entorno de Pruebas ---

# 1. Añadir 'src' a sys.path para importaciones absolutas consistentes
# Esto asegura que `from ultibot_backend...` funcione en todo el entorno de pruebas.
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 2. Cargar variables de entorno desde .env.test
# Es crucial hacerlo ANTES de que cualquier módulo de la aplicación (como app_config) sea importado.
dotenv_path = Path(__file__).parent.parent / ".env.test"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    print(f"Advertencia: El archivo {dotenv_path} no fue encontrado. Las pruebas pueden fallar si dependen de variables de entorno.")

# 3. Establecer variable de entorno para PySide6 (si se realizan pruebas de UI)
os.environ['QT_API'] = 'pyside6'


# --- Fixtures de Ciclo de Vida Asíncrono (pytest-asyncio) ---

@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture de pytest-asyncio para crear un único event loop para toda la sesión de pruebas.
    Alcance: session
    Propósito: Prevenir errores de "Event loop is closed" al reutilizar el mismo bucle
               en todas las pruebas asíncronas, especialmente con fixtures de sesión.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """
    Crea y gestiona el motor de base de datos para toda la sesión de pruebas.
    Alcance: session
    Propósito: Centraliza la creación del motor y la gestión de tablas (creación/eliminación).
    """
    # Importar modelos y configuración aquí para asegurar que el entorno ya está configurado.
    from ultibot_backend.app_config import get_settings
    from ultibot_backend.adapters.persistence_service import Base  # Importar Base metadata

    settings = get_settings()
    test_db_url = settings.get_test_database_url()

    if not test_db_url:
        pytest.fail("La URL de la base de datos de prueba no está configurada. Verifique .env.test")

    engine = create_async_engine(test_db_url, echo=False)

    # Crear todas las tablas definidas en los metadatos de SQLAlchemy
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Eliminar todas las tablas al final de la sesión de pruebas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Desechar el pool de conexiones
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """
    Proporciona una sesión de base de datos transaccional para cada función de prueba.
    Alcance: function
    Propósito: Asegura que cada prueba se ejecute en una transacción aislada que se revierte
               al final, garantizando que las pruebas no interfieran entre sí.
    """
    AsyncSessionLocal = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        # Iniciar una transacción anidada
        await session.begin_nested()
        yield session
        # Revertir la transacción para limpiar después de la prueba
        await session.rollback()
