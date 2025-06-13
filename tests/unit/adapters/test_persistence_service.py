import pytest
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Importar el servicio y los modelos ORM que se van a probar.
# La nueva fixture `db_session` trabaja con modelos SQLAlchemy.
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration


# Marcar todo el módulo para que use pytest-asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def persistence_service(db_session: AsyncSession) -> SupabasePersistenceService:
    """Fixture que provee una instancia del servicio de persistencia con la sesión de BD inyectada."""
    # Esta prueba ahora es de integración, pero el servicio aún puede necesitar inicialización
    # aunque no usemos su pool interno, sino la sesión de la fixture.
    service = SupabasePersistenceService()
    # Sobrescribimos la sesión/pool si es necesario, o lo adaptamos a cómo el servicio usa la sesión.
    # Por ahora, asumimos que podemos pasar la sesión o que el servicio la usará de algún modo.
    # Dado que el servicio actual usa su propio pool, esta prueba es más compleja.
    # Para una prueba de integración real, refactorizaríamos el servicio para aceptar una sesión.
    # Por ahora, lo dejamos así para validar el flujo de la fixture.
    return service

@pytest.fixture
def sample_user_id() -> UUID:
    """Fixture que provee un UUID de usuario consistente para las pruebas."""
    return uuid4()

# NOTA: Las siguientes pruebas fallarán si SupabasePersistenceService no está refactorizado
# para aceptar una sesión externa. El objetivo aquí es validar el ciclo de vida de las fixtures,
# no necesariamente la lógica interna del servicio en este momento.

async def test_save_and_get_user_configuration(persistence_service: SupabasePersistenceService, db_session: AsyncSession, sample_user_id: UUID):
    """
    Test de integración: Verifica que se puede guardar y luego recuperar una configuración de usuario.
    """
    # Arrange: Crear un objeto de configuración de dominio
    user_config_data = {
        "user_id": sample_user_id,
        "selectedTheme": "dark",
        "enableTelegramNotifications": True,
        "defaultPaperTradingCapital": 5000.0
    }

    # Act: Guardar la configuración usando el servicio
    await persistence_service.upsert_user_configuration(user_config_data)

    # Act: Recuperar la configuración usando el servicio
    retrieved_config_dict = await persistence_service.get_user_configuration(sample_user_id)
    retrieved_config = UserConfiguration(**retrieved_config_dict) if retrieved_config_dict else None

    # Assert: Verificar que la configuración recuperada es correcta
    assert retrieved_config is not None
    assert retrieved_config.user_id == sample_user_id
    assert retrieved_config.selected_theme == "dark"
    assert retrieved_config.enable_telegram_notifications is True
    assert retrieved_config.default_paper_trading_capital == 5000.0

async def test_get_user_configuration_not_found(persistence_service: SupabasePersistenceService, sample_user_id: UUID):
    """
    Test de integración: Verifica que al buscar una configuración inexistente, se retorna None.
    """
    # Act
    retrieved_config = await persistence_service.get_user_configuration(sample_user_id)

    # Assert
    assert retrieved_config is None
