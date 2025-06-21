import aiosqlite # Asegurar que el driver asíncrono se cargue temprano
import asyncio
import pytest
import pytest_asyncio
import logging
import gc
import sys
import os
import shutil
import time
import sqlite3
import re
from cryptography.fernet import Fernet
from decimal import Decimal
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional, Any, Dict, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from ultibot_backend.core.domain_models.base import Base # Importar Base
# Importar explícitamente todos los módulos que contienen modelos ORM para asegurar que se registren con Base.metadata
from ultibot_backend.core.domain_models import orm_models
from ultibot_backend.core.domain_models import trade_models
from ultibot_backend.core.domain_models import market_data_models
from ultibot_backend.core.domain_models import api_credential_models # Importar el nuevo módulo de credenciales
from ultibot_backend.core.domain_models.user_configuration_models import UserConfiguration # Importar UserConfiguration

# Configurar logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # Cambiar a DEBUG para ver mensajes detallados

class MockUserConfigPersistence:
    """
    Mock en memoria para SupabasePersistenceService, enfocado en UserConfiguration.
    """
    def __init__(self):
        self._user_configs: Dict[str, UserConfiguration] = {}
        self.get_trades_with_filters = AsyncMock(return_value=[])
        self.upsert_user_configuration = AsyncMock(side_effect=self._real_upsert_user_configuration) # Mockear con side_effect

    async def get_user_configuration(self, user_id: str) -> Optional[UserConfiguration]:
        return self._user_configs.get(user_id)

    async def _real_upsert_user_configuration(self, config: UserConfiguration):
        self._user_configs[str(config.user_id)] = config
        return config

# --- Configuración Inicial Obligatoria ---

@pytest_asyncio.fixture(scope='session', autouse=True)
async def set_test_environment():
    """
    Fixture para configurar el entorno de prueba básico (variables de entorno, etc.).
    Se ejecuta automáticamente una vez por sesión. La gestión de la BD se mueve a db_engine.
    """
    os.environ['TESTING'] = 'True'
    
    valid_key = Fernet.generate_key()
    os.environ['CREDENTIAL_ENCRYPTION_KEY'] = valid_key.decode('utf-8')
    
    # Añadir 'src' al sys.path para asegurar que los módulos de la aplicación sean importables.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    
    yield
    
    # Limpieza de variables de entorno
    del os.environ['TESTING']
    del os.environ['CREDENTIAL_ENCRYPTION_KEY']
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']

# --- Importaciones de la Aplicación (Después de la Configuración) ---
from ultibot_backend.main import app as fastapi_app
from ultibot_backend.dependencies import (
    get_persistence_service, get_strategy_service, get_performance_service,
    get_config_service, get_credential_service, get_market_data_service,
    get_portfolio_service, get_notification_service, get_trading_engine_service,
    get_ai_orchestrator_service, get_unified_order_execution_service,
    get_db_session, DependencyContainer, get_container_async
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

# Registrar adaptador global para que SQLite entienda los objetos UUID de Python.
# Esto es más robusto que usar listeners de eventos de SQLAlchemy.
sqlite3.register_adapter(UUID, str)

@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[Any, None]:
    """
    Crea un motor de BD SQLite en un archivo temporal para toda la sesión y gestiona su ciclo de vida.
    Usa un manejo manual del directorio temporal con reintentos para mayor robustez en Windows.
    """
    temp_dir = tempfile.mkdtemp()
    engine = None
    try:
        temp_db_path = Path(temp_dir) / "test_db.sqlite"
        db_uri_path = str(temp_db_path).replace('\\', '/')
        db_url = f"sqlite+aiosqlite:///{db_uri_path}"
        os.environ['DATABASE_URL'] = db_url
        
        logger.info(f"db_engine fixture: Usando DATABASE_URL: {db_url}")
        engine = create_async_engine(db_url, poolclass=NullPool)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = result.scalars().all()
            logger.info(f"Tablas creadas en la base de datos: {tables}")
            
        yield engine
        
    finally:
        if engine:
            await engine.dispose()
            logger.info("Motor de base de datos dispuesto.")
        
        # Bucle de reintento para eliminar el directorio temporal, manejando bloqueos en Windows.
        for i in range(5):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Directorio temporal {temp_dir} limpiado exitosamente.")
                break
            except PermissionError:
                logger.warning(f"Intento {i+1}/5: No se pudo eliminar {temp_dir}. Reintentando en 0.2s...")
                time.sleep(0.2)
        else:
            logger.error(f"No se pudo eliminar el directorio temporal {temp_dir} después de 5 intentos.")
            shutil.rmtree(temp_dir, ignore_errors=True) # Fallback para no bloquear la suite

@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de BD limpia para cada test, eliminando todos los
    datos de las tablas antes de cada ejecución para garantizar el aislamiento.
    Este enfoque es más robusto para backends como aiosqlite que no soportan
    completamente los SAVEPOINTS para transacciones anidadas.
    """
    # Crear una fábrica de sesiones directamente desde el motor
    TestSessionFactory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # La sesión para el test
    async_session = TestSessionFactory()

    # Limpiar todas las tablas antes del test
    async with async_session.begin():
        for table in reversed(Base.metadata.sorted_tables):
            await async_session.execute(table.delete())
    
    # Sobrescribir la dependencia de la app para que use esta misma sesión
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    fastapi_app.dependency_overrides[get_db_session] = override_get_db_session

    try:
        # Envolver la ejecución del test en una transacción.
        # Esto asegura que los datos creados en la fase de "Arrange" del test
        # sean visibles para el endpoint de la API cuando se llama en la fase "Act",
        # ya que ambos operan dentro de la misma transacción.
        # Al salir del bloque 'with', la transacción se confirma automáticamente.
        async with async_session.begin():
            yield async_session
    finally:
        # Limpiar la sobreescritura y cerrar la sesión
        fastapi_app.dependency_overrides.clear()
        await async_session.close()

@pytest_asyncio.fixture
async def persistence_service_fixture(db_session: AsyncSession) -> SupabasePersistenceService:
    """Fixture que proporciona una instancia del servicio de persistencia."""
    return SupabasePersistenceService(session=db_session)


@pytest.fixture
def mock_persistence_service_integration():
    """Mock del servicio de persistencia para integración."""
    return MockUserConfigPersistence()

@pytest.fixture
def mock_strategy_service_integration():
    """Mock para el servicio de estrategias con métodos asíncronos definidos."""
    service = MagicMock(spec=StrategyService)
    service.strategy_requires_ai_analysis = AsyncMock(return_value=True)
    service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    service.get_ai_configuration_for_strategy = AsyncMock()
    service.get_effective_confidence_thresholds_for_strategy = AsyncMock()
    service.get_active_strategies = AsyncMock()
    service.get_strategy_config = AsyncMock(return_value=None)
    return service

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP para tests.
    IMPORTANTE: Esta fixture NO configura la base de datos.
    Usar 'client_with_db' para tests de integración que la requieran.
    """
    async with AsyncClient(app=fastapi_app, base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def client_with_db(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Proporciona un AsyncClient para tests de integración que ya tiene la dependencia
    de la base de datos sobreescrita por la fixture `db_session`.
    """
    async with AsyncClient(app=fastapi_app, base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_binance_adapter_fixture():
    """Mock para el BinanceAdapter."""
    mock = AsyncMock(spec=BinanceAdapter)
    mock.get_ticker_24hr.return_value = {"lastPrice": "50000.0"}
    
    async def mock_execute_market_order(*args, **kwargs):
        return {
            "orderId_internal": "mock-order-id", "orderCategory": "entry", "type": "market",
            "status": "filled", "requestedPrice": kwargs.get("price"), "requestedQuantity": kwargs.get("quantity"),
            "executedQuantity": kwargs.get("quantity"), "executedPrice": kwargs.get("price", 50000.0),
            "cumulativeQuoteQty": kwargs.get("quantity", 1.0) * kwargs.get("price", 50000.0),
            "commissions": [], "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    mock.execute_market_order = AsyncMock(side_effect=mock_execute_market_order)
    mock.get_account_info = AsyncMock(return_value={"canTrade": True, "canWithdraw": True, "canDeposit": True})
    return mock

@pytest_asyncio.fixture
async def credential_service_fixture(mock_binance_adapter_fixture, db_engine: Any):
    """Fixture para CredentialService con dependencias correctas y mock de credenciales."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    service = CredentialService(
        session_factory=session_factory,
        binance_adapter=mock_binance_adapter_fixture
    )
    
    # Mockear el método get_credential para que devuelva una credencial válida
    mock_credential = APICredential(
        id=uuid4(),
        user_id=FIXED_USER_ID,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot",
        encrypted_api_key=service.encrypt_data("mock_api_key"),
        encrypted_api_secret=service.encrypt_data("mock_api_secret"),
        status="active", # Corregido de is_active a status
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    service.get_credential = AsyncMock(return_value=mock_credential)
    
    return service

@pytest_asyncio.fixture
async def mock_notification_service_fixture():
    """Mock para NotificationService."""
    return AsyncMock(spec=NotificationService)

@pytest_asyncio.fixture
async def configuration_service_fixture(
    credential_service_fixture,
    mock_notification_service_fixture,
    persistence_service_fixture: SupabasePersistenceService
):
    """Fixture para ConfigurationService con dependencias correctas."""
    service = ConfigurationService(persistence_service=persistence_service_fixture)
    service.set_credential_service(credential_service_fixture)
    service.set_notification_service(mock_notification_service_fixture)
    return service

FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

@pytest.fixture
def trade_factory():
    """
    Factory fixture para crear diccionarios de datos para TradeORM.
    Asegura IDs únicos y valores por defecto consistentes para inserción raw.
    """
    import json
    from ultibot_backend.core.domain_models.orm_models import TradeORM

    def _factory(data_dict: Optional[Dict] = None, **overrides):
        now = datetime.now(timezone.utc)
        
        # Datos por defecto para 'data'
        default_data_dict = {"pnl_usd": 100.0, "side": "buy"}
        if data_dict:
            default_data_dict.update(data_dict)

        trade_data = {
            "id": str(uuid4()),
            "user_id": FIXED_USER_ID, # Pasar como UUID directamente
            "data": json.dumps(default_data_dict), # Siempre serializar a JSON aquí
            "status": "closed",
            "position_status": "closed",
            "mode": "paper",
            "symbol": "BTCUSDT",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "closed_at": now.isoformat(),
        }
        trade_data.update(overrides)
        return trade_data

    return _factory

@pytest_asyncio.fixture
async def market_data_service_fixture(
    credential_service_fixture,
    mock_binance_adapter_fixture,
    persistence_service_fixture: SupabasePersistenceService
):
    """Fixture para MarketDataService con dependencias correctas."""
    service = MarketDataService(
        credential_service=credential_service_fixture,
        binance_adapter=mock_binance_adapter_fixture,
        persistence_service=persistence_service_fixture
    )
    yield service
    await service.close()

@pytest_asyncio.fixture
async def portfolio_service_fixture(market_data_service_fixture, persistence_service_fixture: SupabasePersistenceService):
    """Fixture para PortfolioService con dependencias correctas."""
    service = PortfolioService(
        market_data_service=market_data_service_fixture,
        persistence_service=persistence_service_fixture
    )
    await service.initialize_portfolio(FIXED_USER_ID)
    return service

@pytest.fixture
def real_order_execution_service_fixture(mock_binance_adapter_fixture):
    """Fixture para OrderExecutionService (real)."""
    return OrderExecutionService(binance_adapter=mock_binance_adapter_fixture)

@pytest.fixture
def paper_order_execution_service_fixture():
    """Fixture para PaperOrderExecutionService."""
    return PaperOrderExecutionService(initial_capital=Decimal("10000.0"))

@pytest_asyncio.fixture
async def unified_order_execution_service_fixture():
    """Fixture para UnifiedOrderExecutionService con mocks de ejecución de órdenes."""
    mock_service = AsyncMock(spec=UnifiedOrderExecutionService)

    async def mock_execute_market_order(
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        trading_mode: str,
        api_key: str,
        api_secret: Optional[str] = None,
        price: Optional[Decimal] = None,
    ) -> TradeOrderDetails:
        logger.info(f"Mock execute_market_order called for {symbol} {side} {quantity}")
        return TradeOrderDetails(
            orderId_internal=uuid4(),
            orderCategory=OrderCategory.ENTRY,
            type="MARKET",
            status=OrderStatus.FILLED.value,
            requestedPrice=price,
            requestedQuantity=quantity,
            executedQuantity=quantity,
            executedPrice=Decimal("30000.0") if "BTC" in symbol else Decimal("2000.0"), # Precio simulado
            orderId_exchange="mock_exchange_order_id_" + str(uuid4()),
            clientOrderId_exchange="mock_client_order_id_" + str(uuid4()),
            cumulativeQuoteQty=quantity * (Decimal("30000.0") if "BTC" in symbol else Decimal("2000.0")),
            commissions=[],
            commission=Decimal("0.001"),
            commissionAsset="USDT",
            submittedAt=datetime.now(timezone.utc),
            fillTimestamp=datetime.now(timezone.utc),
            rawResponse={"mock_response": "market_order_filled"},
            ocoOrderListId=None,
        )
    mock_service.execute_market_order.side_effect = mock_execute_market_order

    async def mock_create_oco_order(
        user_id: UUID,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        stop_price: Decimal,
        limit_price: Decimal,
        trading_mode: str,
        api_key: str,
        api_secret: Optional[str] = None,
    ) -> Any: # Retorna un objeto con ocoOrderListId
        logger.info(f"Mock create_oco_order called for {symbol} {side} TP:{price} SL:{stop_price}")
        # Simular la respuesta de Binance para una orden OCO
        return MagicMock(ocoOrderListId="mock_oco_list_id_" + str(uuid4()))

    mock_service.create_oco_order.side_effect = mock_create_oco_order
    
    return mock_service

@pytest_asyncio.fixture
async def ai_orchestrator_fixture(market_data_service_fixture):
    """Fixture para AIOrchestrator."""
    if not app_settings.GEMINI_API_KEY:
        with patch('ultibot_backend.services.ai_orchestrator_service.ChatGoogleGenerativeAI', new_callable=AsyncMock):
            return AIOrchestrator(market_data_service=market_data_service_fixture)
    return AIOrchestrator(market_data_service=market_data_service_fixture)

@pytest_asyncio.fixture
async def trading_engine_fixture(
    persistence_service_fixture,
    market_data_service_fixture,
    unified_order_execution_service_fixture,
    credential_service_fixture,
    mock_notification_service_fixture,
    mock_strategy_service_integration,
    configuration_service_fixture,
    portfolio_service_fixture,
    ai_orchestrator_fixture
):
    """Fixture completa para TradingEngine con todas las dependencias."""
    return TradingEngine(
        persistence_service=persistence_service_fixture,
        market_data_service=market_data_service_fixture,
        unified_order_execution_service=unified_order_execution_service_fixture,
        credential_service=credential_service_fixture,
        notification_service=mock_notification_service_fixture,
        strategy_service=mock_strategy_service_integration,
        configuration_service=configuration_service_fixture,
        portfolio_service=portfolio_service_fixture,
        ai_orchestrator=ai_orchestrator_fixture
    )

@pytest.fixture
def mock_user_config():
    """Mock user configuration for testing."""
    from ultibot_backend.core.domain_models.user_configuration_models import (
        UserConfiguration, RiskProfileSettings, RealTradingSettings, RiskProfile, Theme
    )
    from decimal import Decimal
    
    return UserConfiguration(
        id="test-config-id",
        user_id=str(FIXED_USER_ID),
        telegram_chat_id="test-chat-id",
        notification_preferences=[],
        enable_telegram_notifications=True,
        default_paper_trading_capital=Decimal("10000.0"),
        paper_trading_active=True,
        paper_trading_assets=[],
        watchlists=[],
        favorite_pairs=[],
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=RiskProfileSettings(
            per_trade_capital_risk_percentage=0.02,
            daily_capital_risk_percentage=0.1,
            max_drawdown_percentage=0.15
        ),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_concurrent_operations=3,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None,
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=None
        ),
        ai_strategy_configurations=[],
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=[],
        selected_theme=Theme.DARK,
        dashboard_layout_profiles={},
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config={},
        cloud_sync_preferences=None
    )

@pytest.fixture 
def mock_portfolio_snapshot():
    """Mock portfolio snapshot for testing."""
    from shared.data_types import PortfolioSnapshot, PortfolioSummary
    from decimal import Decimal
    
    return PortfolioSnapshot(
        paper_trading=PortfolioSummary(
            available_balance_usdt=Decimal("9500.0"),
            total_assets_value_usd=Decimal("500.0"),
            total_portfolio_value_usd=Decimal("10000.0"),
            assets=[],
            error_message=None
        ),
        real_trading=PortfolioSummary(
            available_balance_usdt=Decimal("4800.0"),
            total_assets_value_usd=Decimal("200.0"),
            total_portfolio_value_usd=Decimal("5000.0"),
            assets=[],
            error_message=None
        )
    )
