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
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# 2. Cargar variables de entorno desde .env.test
dotenv_path = Path(__file__).parent.parent / ".env.test"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    print(f"Advertencia: El archivo {dotenv_path} no fue encontrado. Las pruebas pueden fallar si dependen de variables de entorno.")

# 3. Establecer variable de entorno para PySide6 (si se realizan pruebas de UI)
os.environ['QT_API'] = 'pyside6'

# --- Importación de Modelos ORM para que sean descubiertos por la Base ---
# Esta importación es crucial para que Base.metadata.create_all() funcione.
from ultibot_backend.adapters.sql_alchemy_mappers import TradeORM


# --- Fixtures de Ciclo de Vida Asíncrono (pytest-asyncio) ---

@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture de pytest-asyncio para crear un único event loop para toda la sesión de pruebas.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_engine():
    """
    Crea y gestiona el motor de base de datos para toda la sesión de pruebas.
    Usa SQLite en memoria para aislamiento completo y evitar dependencias externas.
    """
    from ultibot_backend.adapters.sql_alchemy_mappers import Base

    # Usar SQLite en memoria para pruebas aisladas
    test_db_url = "sqlite+aiosqlite:///:memory:"
    
    engine = create_async_engine(test_db_url, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """
    Proporciona una sesión de base de datos transaccional para cada función de prueba.
    """
    AsyncSessionLocal = sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as session:
        await session.begin_nested()
        yield session
        await session.rollback()
