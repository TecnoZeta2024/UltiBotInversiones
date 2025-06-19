import asyncio
import pytest
import pytest_asyncio
import logging
import sys
import os
from cryptography.fernet import Fernet
from decimal import Decimal
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional, Any, Dict, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from ultibot_backend.core.domain_models.base import Base # Importar Base
from ultibot_backend.core.domain_models import orm_models # Importar para asegurar que los modelos ORM se registren con Base.metadata

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Configuración Inicial Obligatoria ---

@pytest_asyncio.fixture(scope='session', autouse=True)
async def set_test_environment():
    """
    Fixture para configurar el entorno de prueba antes de que se ejecuten los tests.
    Se ejecuta automáticamente una vez por sesión.
    """
    os.environ['TESTING'] = 'True'
    
    valid_key = Fernet.generate_key()
    os.environ['CREDENTIAL_ENCRYPTION_KEY'] = valid_key.decode('utf-8')
    
    # Usar una base de datos SQLite en un directorio temporal para los tests
    # Esto asegura que la base de datos persista durante toda la sesión de tests
    temp_dir = tempfile.TemporaryDirectory()
    temp_db_path = Path(temp_dir.name) / "test_db.sqlite"
    os.environ['DATABASE_URL'] = f"sqlite+aiosqlite:///{temp_db_path}"
    
    logger.info(f"Entorno de prueba configurado. DATABASE_URL: {os.environ['DATABASE_URL']}")
    
    # Añadir 'src' al sys.path para asegurar que los módulos de la aplicación sean importables.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    
    yield
    
    # Limpieza después de que todos los tests hayan terminado
    del os.environ['TESTING']
    del os.environ['CREDENTIAL_ENCRYPTION_KEY']
    del os.environ['DATABASE_URL']
    # Deshabilitar la limpieza del directorio temporal para evitar PermissionError en Windows.
    # Esto es una solución temporal para permitir que los tests se ejecuten.
    # En un entorno de producción, se necesitaría una solución más robusta para la limpieza.
    pass 

# --- Importaciones de la Aplicación (Después de la Configuración) ---
from ultibot_backend.main import app as fastapi_app
from ultibot_backend.dependencies import (
    get_persistence_service, get_strategy_service, get_performance_service,
    get_config_service, get_credential_service, get_market_data_service,
    get_portfolio_service, get_notification_service, get_trading_engine_service,
    get_ai_orchestrator_service, get_unified_order_execution_service,
    get_db_session, DependencyContainer, get_container_async # Importar DependencyContainer y get_container_async
)
from fastapi import Request # Importar Request
from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.services.config_service import ConfigurationService
from ultibot_backend.services.credential_service import CredentialService
from ultibot_backend.adapters.binance_adapter import BinanceAdapter
from ultibot_backend.services.notification_service import NotificationService
from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.services.portfolio_service import PortfolioService
from ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from ultibot_backend.services.ai_orchestrator_service import AIOrchestrator
from ultibot_backend.services.trading_engine_service import TradingEngine
from ultibot_backend.app_config import settings as app_settings
from shared.data_types import APICredential, ServiceName
from ultibot_backend.core.domain_models.trade_models import OrderStatus, OrderCategory, TradeOrderDetails

# --- Configuración de la Base de Datos de Prueba (SQLite en memoria) ---

@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[Any, None]:
    """Crea un motor de BD SQLite en un archivo temporal para toda la sesión."""
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        # Crear tablas usando Base.metadata.create_all
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Asegurarse de que todas las conexiones se cierren antes de disponer del motor
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de BD transaccional para cada test.
    Asegura que cada test opere en su propia transacción aislada que puede ser revertida.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    async_session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield async_session
    finally:
        await async_session.close()
        await transaction.rollback()
        await connection.close()

# Eliminada persistence_service_fixture ya que get_persistence_service ahora usa get_db_session
# @pytest_asyncio.fixture
# async def persistence_service_fixture(db_session: AsyncSession) -> SupabasePersistenceService:
#     return SupabasePersistenceService(session=db_session)


@pytest.fixture(scope="session")
def event_loop():
    """Asegura un único event loop por sesión."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_persistence_service_integration():
    """Mock del servicio de persistencia para integración."""
    mock = AsyncMock(spec=SupabasePersistenceService)
    # Configurar el método get_trades_with_filters para que sea un AsyncMock
    mock.get_trades_with_filters = AsyncMock(return_value=[])
    return mock

@pytest.fixture
def mock_strategy_service_integration():
    """Mock para el servicio de estrategias con métodos asíncronos definidos."""
    service = MagicMock(spec=StrategyService)
    service.strategy_requires_ai_analysis = AsyncMock(return_value=True)
    service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    service.get_ai_configuration_for_strategy = AsyncMock()
    service.get_effective_confidence_thresholds_for_strategy = AsyncMock()
    service.get_active_strategies = AsyncMock()
    # Añadir mock para get_strategy_config para evitar AttributeErrors en tests
    service.get_strategy_config = AsyncMock(return_value=None)
    return service

@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
    mock_persistence_service_integration,
    mock_strategy_service_integration,
    # Mantener las otras fixtures en la firma para compatibilidad con otros tests
    configuration_service_fixture,
    credential_service_fixture,
    market_data_service_fixture,
    portfolio_service_fixture,
    mock_notification_service_fixture,
    unified_order_execution_service_fixture,
    ai_orchestrator_fixture,
    trading_engine_fixture
) -> AsyncGenerator[TestClient, None]:
    """
    Proporciona un TestClient que sobreescribe las dependencias a nivel de aplicación
    para asegurar que los mocks correctos sean inyectados, usando el patrón
    recomendado de FastAPI `app.dependency_overrides`.
    """
    # 1. Crear la instancia del servicio que queremos usar en el test,
    #    inyectándole manualmente sus propias dependencias mockeadas.
    mocked_performance_service = PerformanceService(
        session_factory=lambda: db_session,
        strategy_service=mock_strategy_service_integration,
        persistence_service=mock_persistence_service_integration
    )

    # 2. Crear una función de "override" que devuelva la instancia mockeada.
    async def override_get_performance_service() -> PerformanceService:
        return mocked_performance_service

    # 3. Aplicar el override al diccionario de dependencias de la aplicación.
    #    FastAPI usará `override_get_performance_service` en lugar de `get_performance_service`.
    fastapi_app.dependency_overrides[get_performance_service] = override_get_performance_service

    # 4. Usar TestClient como un gestor de contexto para asegurar que el lifespan se ejecute.
    with TestClient(fastapi_app) as c:
        yield c

    # 5. Limpiar los overrides después del test para no afectar a otros.
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def mock_binance_adapter_fixture():
    """Mock para el BinanceAdapter."""
    mock = AsyncMock(spec=BinanceAdapter)
    # Configurar retornos comunes si es necesario, ej:
    mock.get_ticker_24hr.return_value = {"lastPrice": "50000.0"}
    
    # Simular una ejecución de orden exitosa
    async def mock_execute_market_order(*args, **kwargs):
        return {
            "orderId_internal": "mock-order-id",
            "orderCategory": "entry",
            "type": "market",
            "status": "filled",
            "requestedPrice": kwargs.get("price"),
            "requestedQuantity": kwargs.get("quantity"),
            "executedQuantity": kwargs.get("quantity"),
            "executedPrice": kwargs.get("price", 50000.0), # Usar un precio por defecto si no se proporciona
            "cumulativeQuoteQty": kwargs.get("quantity", 1.0) * kwargs.get("price", 50000.0),
            "commissions": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    mock.execute_market_order = AsyncMock(side_effect=mock_execute_market_order)

    # Configurar get_account_info para evitar RuntimeWarning
    mock.get_account_info = AsyncMock(return_value={"canTrade": True, "canWithdraw": True, "canDeposit": True})
    
    return mock

@pytest_asyncio.fixture
async def credential_service_fixture(mock_binance_adapter_fixture, db_engine: Any):
    """Fixture para CredentialService con dependencias reales."""
    # Crear una session_factory a partir del db_engine para CredentialService
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    service = CredentialService(
        session_factory=session_factory,
        binance_adapter=mock_binance_adapter_fixture
    )
    return service

@pytest_asyncio.fixture
async def mock_notification_service_fixture(credential_service_fixture, db_session: AsyncSession):
    """Mock para NotificationService."""
    # Para simplificar, usamos un AsyncMock completo.
    # Si se necesita comportamiento específico, se puede instanciar NotificationService
    # con sus dependencias mockeadas (credential_service_fixture, persistence_service_fixture).
    persistence_service = SupabasePersistenceService(session=db_session)
    mock = AsyncMock(spec=NotificationService)
    # Ejemplo de configuración de un método mockeado:
    # async def send_notification_mock(*args, **kwargs): return True
    # mock.send_notification = AsyncMock(side_effect=send_notification_mock)
    return mock

@pytest_asyncio.fixture
async def configuration_service_fixture(
    credential_service_fixture,
    mock_notification_service_fixture,
    db_session: AsyncSession
):
    """Fixture para ConfigurationService con dependencias mínimas."""
    persistence_service = SupabasePersistenceService(session=db_session)
    service = ConfigurationService(persistence_service=persistence_service)
    service.set_credential_service(credential_service_fixture)
    # El portfolio_service se inyectará en tiempo de ejecución o se mockeará donde sea necesario,
    # para evitar dependencias circulares en las fixtures.
    # service.set_portfolio_service(portfolio_service_fixture) 
    service.set_notification_service(mock_notification_service_fixture)
    return service

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Eliminada la fixture cleanup_db_after_each_test ya que setup_and_cleanup_db en test_reports_endpoints.py la maneja.

@pytest_asyncio.fixture
async def market_data_service_fixture(
    credential_service_fixture,
    mock_binance_adapter_fixture,
    db_engine: Any # Cambiar a db_engine para crear session_factory
):
    """Fixture para MarketDataService con dependencias reales."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    service = MarketDataService(
        credential_service=credential_service_fixture,
        binance_adapter=mock_binance_adapter_fixture,
        session_factory=session_factory # Pasar session_factory
    )
    yield service
    await service.close() # Asegurar que se cierre el servicio y sus websockets si los tuviera

@pytest_asyncio.fixture
async def portfolio_service_fixture(market_data_service_fixture, db_engine: Any):
    """Fixture para PortfolioService con dependencias."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    service = PortfolioService(
        market_data_service=market_data_service_fixture,
        session_factory=session_factory # Pasar session_factory
    )
    # Inicializar el portafolio para el usuario fijo de test
    await service.initialize_portfolio(FIXED_USER_ID)
    return service

@pytest.fixture
def real_order_execution_service_fixture(mock_binance_adapter_fixture):
    """Fixture para OrderExecutionService (real) con BinanceAdapter mockeado."""
    return OrderExecutionService(binance_adapter=mock_binance_adapter_fixture)

@pytest.fixture
def paper_order_execution_service_fixture():
    """Fixture para PaperOrderExecutionService."""
    return PaperOrderExecutionService(initial_capital=Decimal("10000.0"))

@pytest.fixture
def unified_order_execution_service_fixture(
    real_order_execution_service_fixture,
    paper_order_execution_service_fixture
):
    """Fixture para UnifiedOrderExecutionService."""
    mock = AsyncMock(spec=UnifiedOrderExecutionService)

    async def mock_execute_market_order(
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        trading_mode: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        oco_order_list_id: Optional[str] = None
    ) -> TradeOrderDetails:
        # Simular una orden ejecutada exitosamente
        return TradeOrderDetails(
            orderId_internal=uuid4(),
            orderId_exchange=str(uuid4()), # Proporcionar un valor por defecto
            clientOrderId_exchange=str(uuid4()), # Proporcionar un valor por defecto
            orderCategory=OrderCategory.ENTRY,
            type='market',
            status=OrderStatus.FILLED.value, # Asegurar que el estado sea 'filled'
            requestedPrice=Decimal("30000.0"),
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=Decimal("30000.0"),
            cumulativeQuoteQty=quantity * Decimal("30000.0"),
            commissions=[],
            commission=Decimal("0.0"),
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={"mock_response": "filled"},
            ocoOrderListId=oco_order_list_id
        )
    
    mock.execute_market_order.side_effect = mock_execute_market_order
    
    return mock

@pytest_asyncio.fixture
async def ai_orchestrator_fixture(market_data_service_fixture):
    """Fixture para AIOrchestrator."""
    # Asegurar que GEMINI_API_KEY esté disponible en el entorno de test
    # Si no, mockear ChatGoogleGenerativeAI
    if not app_settings.GEMINI_API_KEY:
        with patch('ultibot_backend.services.ai_orchestrator_service.ChatGoogleGenerativeAI', new_callable=AsyncMock) as mock_llm:
            # Configurar el mock_llm si es necesario para devolver respuestas simuladas
            mock_llm_instance = mock_llm.return_value
            # Ejemplo: mock_llm_instance.ainvoke.return_value = AsyncMock(content="...") 
            service = AIOrchestrator(market_data_service=market_data_service_fixture)
    else:
        service = AIOrchestrator(market_data_service=market_data_service_fixture)
    return service

@pytest_asyncio.fixture
async def trading_engine_fixture(
    market_data_service_fixture,
    unified_order_execution_service_fixture,
    credential_service_fixture,
    mock_notification_service_fixture,
    mock_strategy_service_integration, # Usar el mock existente para StrategyService
    configuration_service_fixture,
    portfolio_service_fixture,
    ai_orchestrator_fixture,
    db_session: AsyncSession # Añadir db_session para inicializar PersistenceService
):
    """Fixture completa para TradingEngine con todas las dependencias."""
    persistence_service = SupabasePersistenceService(session=db_session)
    engine = TradingEngine(
        persistence_service=persistence_service, # Usar la fixture real de persistencia
        market_data_service=market_data_service_fixture,
        unified_order_execution_service=unified_order_execution_service_fixture,
        credential_service=credential_service_fixture,
        notification_service=mock_notification_service_fixture,
        strategy_service=mock_strategy_service_integration,
        configuration_service=configuration_service_fixture,
        portfolio_service=portfolio_service_fixture,
        ai_orchestrator=ai_orchestrator_fixture
    )
    return engine
