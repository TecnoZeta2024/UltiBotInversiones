import asyncio
import pytest
import pytest_asyncio
import logging
import sys
import os
from cryptography.fernet import Fernet
from typing import AsyncGenerator, Optional, Any, Dict, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Configuración Inicial Obligatoria ---

@pytest.fixture(scope='session', autouse=True)
def set_test_environment():
    """
    Fixture para configurar el entorno de prueba antes de que se ejecuten los tests.
    Se ejecuta automáticamente una vez por sesión.
    """
    os.environ['TESTING'] = 'True'
    
    valid_key = Fernet.generate_key()
    os.environ['CREDENTIAL_ENCRYPTION_KEY'] = valid_key.decode('utf-8')
    
    # Usar una base de datos SQLite en memoria para los tests
    database_url = "sqlite+aiosqlite:///:memory:"
    os.environ['DATABASE_URL'] = database_url
    
    logger.info(f"Entorno de prueba configurado. DATABASE_URL: {database_url}")
    
    # Añadir 'src' al sys.path para asegurar que los módulos de la aplicación sean importables.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    
    yield
    
    # Limpieza después de que todos los tests hayan terminado (opcional)
    del os.environ['TESTING']
    del os.environ['CREDENTIAL_ENCRYPTION_KEY']
    del os.environ['DATABASE_URL']

# --- Importaciones de la Aplicación (Después de la Configuración) ---
from ultibot_backend.main import app as fastapi_app
from ultibot_backend.dependencies import (
    get_persistence_service, get_strategy_service, get_performance_service,
    get_config_service, get_credential_service, get_market_data_service,
    get_portfolio_service, get_notification_service, get_trading_engine_service,
    get_ai_orchestrator_service, get_unified_order_execution_service
)
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
    """Crea un motor de BD SQLite en memoria para toda la sesión."""
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        # Crear tablas
        await conn.execute(text("""
            CREATE TABLE user_configurations (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL UNIQUE, telegram_chat_id TEXT,
                notification_preferences TEXT, enable_telegram_notifications BOOLEAN,
                default_paper_trading_capital REAL, paper_trading_active BOOLEAN,
                paper_trading_assets TEXT, watchlists TEXT, favorite_pairs TEXT,
                risk_profile TEXT, risk_profile_settings TEXT, real_trading_settings TEXT,
                ai_strategy_configurations TEXT, ai_analysis_confidence_thresholds TEXT,
                mcp_server_preferences TEXT, selected_theme TEXT, dashboard_layout_profiles TEXT,
                active_dashboard_layout_profile_id TEXT, dashboard_layout_config TEXT,
                cloud_sync_preferences TEXT, created_at TEXT, updated_at TEXT
            );
        """))
        await conn.execute(text("""
            CREATE TABLE trades (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, data TEXT NOT NULL,
                position_status TEXT, mode TEXT, symbol TEXT, created_at TEXT,
                updated_at TEXT, closed_at TEXT
            );
        """))
        await conn.execute(text("""
            CREATE TABLE portfolio_snapshots (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, timestamp TEXT NOT NULL,
                data TEXT NOT NULL
            );
        """))
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Proporciona una sesión de BD transaccional para cada test."""
    async with db_engine.connect() as connection:
        async with connection.begin() as transaction:
            async_session = AsyncSession(bind=connection)
            yield async_session
            await transaction.rollback()
            await async_session.close()

@pytest_asyncio.fixture
async def persistence_service_fixture(db_session: AsyncSession) -> SupabasePersistenceService:
    """
    Proporciona una instancia de SupabasePersistenceService que utiliza la sesión
    de base de datos de prueba.
    """
    return SupabasePersistenceService(session=db_session)


@pytest.fixture(scope="session")
def event_loop():
    """Asegura un único event loop por sesión."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_strategy_service_integration():
    """Mock para el servicio de estrategias con métodos asíncronos definidos."""
    service = MagicMock(spec=StrategyService)
    service.strategy_requires_ai_analysis = AsyncMock(return_value=True)
    service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    service.get_ai_configuration_for_strategy = AsyncMock()
    service.get_effective_confidence_thresholds_for_strategy = AsyncMock()
    service.get_active_strategies = AsyncMock()
    return service

@pytest_asyncio.fixture
async def client(
    persistence_service_fixture,
    mock_strategy_service_integration,
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
    Proporciona un TestClient para interactuar con la aplicación, con todas las
    dependencias inyectadas.
    """
    # PerformanceService depende de Persistence y Strategy
    mocked_performance_service = PerformanceService(
        persistence_service=persistence_service_fixture,
        strategy_service=mock_strategy_service_integration
    )

    dependency_overrides = {
        get_persistence_service: lambda: persistence_service_fixture,
        get_strategy_service: lambda: mock_strategy_service_integration,
        get_performance_service: lambda: mocked_performance_service,
        get_config_service: lambda: configuration_service_fixture,
        get_credential_service: lambda: credential_service_fixture,
        get_market_data_service: lambda: market_data_service_fixture,
        get_portfolio_service: lambda: portfolio_service_fixture,
        get_notification_service: lambda: mock_notification_service_fixture,
        get_unified_order_execution_service: lambda: unified_order_execution_service_fixture,
        get_ai_orchestrator_service: lambda: ai_orchestrator_fixture,
        get_trading_engine_service: lambda: trading_engine_fixture,
    }

    fastapi_app.dependency_overrides = dependency_overrides

    with TestClient(fastapi_app) as c:
        yield c

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
async def credential_service_fixture(persistence_service_fixture, mock_binance_adapter_fixture):
    """Fixture para CredentialService con dependencias reales."""
    service = CredentialService(
        persistence_service=persistence_service_fixture,
        binance_adapter=mock_binance_adapter_fixture
    )
    return service

@pytest_asyncio.fixture
async def mock_notification_service_fixture(credential_service_fixture, persistence_service_fixture):
    """Mock para NotificationService."""
    # Para simplificar, usamos un AsyncMock completo.
    # Si se necesita comportamiento específico, se puede instanciar NotificationService
    # con sus dependencias mockeadas (credential_service_fixture, persistence_service_fixture).
    mock = AsyncMock(spec=NotificationService)
    # Ejemplo de configuración de un método mockeado:
    # async def send_notification_mock(*args, **kwargs): return True
    # mock.send_notification = AsyncMock(side_effect=send_notification_mock)
    return mock

@pytest_asyncio.fixture
async def configuration_service_fixture(
    persistence_service_fixture,
    credential_service_fixture,
    portfolio_service_fixture, # Añadido
    mock_notification_service_fixture
):
    """Fixture para ConfigurationService con dependencias."""
    service = ConfigurationService(persistence_service=persistence_service_fixture)
    service.set_credential_service(credential_service_fixture)
    service.set_portfolio_service(portfolio_service_fixture) # Añadido
    service.set_notification_service(mock_notification_service_fixture)

    # Es crucial cargar la configuración para que esté disponible en los tests.
    # Esto simula lo que haría la aplicación al inicio.
    try:
        await service.get_user_configuration()
    except Exception as e:
        # Esto puede ocurrir si los mocks no están completamente configurados para _load_config_from_db
        # Por ejemplo, si get_user_configuration en el mock de persistencia no devuelve lo esperado.
        print(f"Advertencia: Error al cargar la configuración inicial en fixture: {e}")
        # Intentar establecer una configuración por defecto en memoria si la carga falla
        # service._user_configuration = service.get_default_configuration() # Esto es una medida de contingencia
    return service

# Para la v1.0, se puede asumir un user_id fijo como en el backend
FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

# Eliminada la fixture cleanup_db_after_each_test ya que setup_and_cleanup_db en test_reports_endpoints.py la maneja.

@pytest_asyncio.fixture
async def market_data_service_fixture(
    credential_service_fixture,
    mock_binance_adapter_fixture,
    persistence_service_fixture
):
    """Fixture para MarketDataService con dependencias reales."""
    service = MarketDataService(
        credential_service=credential_service_fixture,
        binance_adapter=mock_binance_adapter_fixture,
        persistence_service=persistence_service_fixture
    )
    yield service
    await service.close() # Asegurar que se cierre el servicio y sus websockets si los tuviera

@pytest_asyncio.fixture
async def portfolio_service_fixture(market_data_service_fixture, persistence_service_fixture):
    """Fixture para PortfolioService con dependencias."""
    service = PortfolioService(
        market_data_service=market_data_service_fixture,
        persistence_service=persistence_service_fixture
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
    return PaperOrderExecutionService(initial_capital=10000.0)

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
        quantity: float,
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
            requestedPrice=30000.0,
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=30000.0,
            cumulativeQuoteQty=quantity * 30000.0,
            commissions=[],
            commission=0.0,
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
    persistence_service_fixture, # Usar la fixture real de persistencia
    market_data_service_fixture,
    unified_order_execution_service_fixture,
    credential_service_fixture,
    mock_notification_service_fixture,
    mock_strategy_service_integration, # Usar el mock existente para StrategyService
    configuration_service_fixture,
    portfolio_service_fixture,
    ai_orchestrator_fixture
):
    """Fixture completa para TradingEngine con todas las dependencias."""
    engine = TradingEngine(
        persistence_service=persistence_service_fixture, # Usar la fixture real de persistencia
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
