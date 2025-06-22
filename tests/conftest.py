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
    
    # La clave de encriptación y otras variables se cargarán desde .env.test
    # gracias a la lógica en app_config.py. No es necesario establecerla aquí.
    
    # Añadir 'src' al sys.path para asegurar que los módulos de la aplicación sean importables.
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
    
    yield
    
    # Limpieza de variables de entorno
    del os.environ['TESTING']
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']

# --- Importaciones de la Aplicación (Después de la Configuración) ---
from ultibot_backend.main import app as global_fastapi_app # Renombrar para claridad
from ultibot_backend.dependencies import (
    get_persistence_service, get_strategy_service, get_performance_service,
    get_config_service, get_credential_service, get_market_data_service,
    get_portfolio_service, get_notification_service, get_trading_engine_service,
    get_ai_orchestrator_service, get_unified_order_execution_service,
    get_db_session, DependencyContainer, get_container_async
)
from fastapi import Request, FastAPI # Importar FastAPI
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
from ultibot_backend.app_config import get_app_settings, AppSettings
from shared.data_types import APICredential, ServiceName, PerformanceMetrics
from ultibot_backend.core.domain_models.trade_models import OrderStatus, OrderCategory, TradeOrderDetails, TradeMode, TradeSide, PositionStatus
from ultibot_backend.api.v1.models.performance_models import StrategyPerformanceData, OperatingMode

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
        
        # Limpieza robusta del directorio temporal con reintentos
        max_retries = 5
        for i in range(max_retries):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Directorio temporal {temp_dir} eliminado exitosamente (intento {i+1}/{max_retries}).")
                    break
            except Exception as e:
                logger.warning(f"Intento {i+1}/{max_retries}: No se pudo eliminar el directorio temporal {temp_dir}: {e}. Reintentando en 0.1 segundos...")
                gc.collect() # Forzar recolección de basura
                await asyncio.sleep(0.1) # Pequeño retardo
        else:
            logger.error(f"Fallo al eliminar el directorio temporal {temp_dir} después de {max_retries} intentos.")

@pytest_asyncio.fixture
async def db_session(db_engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """
    Proporciona una sesión de BD transaccional y aislada para cada test.
    Cada test se ejecuta dentro de una transacción que se revierte al final.
    Esta fixture ya no necesita interactuar con la app, ya que el cliente
    se encargará de la inyección de dependencias.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()
    
    session = async_sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False
    )()
    
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()

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

@pytest.fixture
def mock_performance_service_for_endpoint():
    """
    Mock para PerformanceService para inyección en endpoints.
    Devuelve un mock limpio que puede ser configurado en cada test.
    """
    service = MagicMock(spec=PerformanceService)
    # Los métodos que serán llamados son asíncronos, así que los reemplazamos con AsyncMock.
    service.get_all_strategies_performance = AsyncMock()
    service.get_trade_performance_metrics = AsyncMock()
    return service

@pytest.fixture
def app_settings_fixture() -> AppSettings:
    """
    Returns a test-specific instance of AppSettings.
    This allows tests to override specific settings without global state pollution.
    """
    # By default, it loads from .env.test due to the logic in app_config.py
    # and the TESTING=True env var set in set_test_environment.
    return get_app_settings()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[Tuple[AsyncClient, FastAPI], Any]:
    """
    Cliente de test definitivo que garantiza un aislamiento total.
    - Devuelve una tupla (cliente, app) para permitir overrides de dependencias seguros.
    - Parchea la session factory a nivel de módulo para forzar el uso de la sesión de test.
    - Resetea el contenedor de dependencias global para cada test.
    - Crea una nueva instancia de la app para cada test.
    """
    from ultibot_backend.main import create_app
    from ultibot_backend import dependencies

    # 1. Forzar que cada test use la sesión de BD transaccional
    def get_test_session_factory():
        return lambda: db_session

    # 2. Forzar que cada test cree un nuevo contenedor de dependencias
    with patch.object(dependencies, '_global_container', None), \
         patch.object(dependencies, '_session_factory', get_test_session_factory()):
        
        app = create_app()
        
        # Limpiar cualquier override de dependencias de tests anteriores
        app.dependency_overrides.clear()

        async with AsyncClient(app=app, base_url="http://test") as c:
            yield c, app # Devolver tanto el cliente como la app
        
        # Limpieza final por si acaso
        app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def client_with_db(client: Tuple[AsyncClient, FastAPI]) -> AsyncGenerator[AsyncClient, Any]:
    """
    Proporciona un cliente HTTP asíncrono para interactuar con la aplicación FastAPI
    en un contexto de base de datos de prueba.
    """
    yield client[0] # Devuelve solo el AsyncClient de la tupla

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
    from ultibot_backend.core.domain_models.trade_models import (
        Trade, TradeOrderDetails, OrderCategory, OrderStatus, TradeSide, PositionStatus, TradeMode
    )

    def _factory(**overrides):
        now = datetime.now(timezone.utc)
        
        # Datos por defecto para el modelo Pydantic Trade
        default_trade_data = {
            "id": uuid4(),
            "user_id": FIXED_USER_ID,
            "mode": TradeMode.PAPER,
            "symbol": "BTCUSDT",
            "side": TradeSide.BUY,
            "entryOrder": TradeOrderDetails(
                orderId_internal=uuid4(),
                orderCategory=OrderCategory.ENTRY,
                type="market",
                status=OrderStatus.FILLED.value,
                requestedPrice=None,
                requestedQuantity=Decimal("1.0"),
                executedQuantity=Decimal("1.0"),
                executedPrice=Decimal("50000.0"),
                cumulativeQuoteQty=Decimal("50000.0"),
                commissions=[],
                commission=Decimal("0.0"),
                commissionAsset=None,
                timestamp=now,
                submittedAt=now,
                fillTimestamp=now,
                rawResponse={},
                ocoOrderListId=None,
                orderId_exchange=None,
                clientOrderId_exchange=None,
            ),
            "exitOrders": [],
            "positionStatus": PositionStatus.CLOSED,
            "pnl_usd": Decimal("100.0"),
            "pnl_percentage": Decimal("0.01"),
            "created_at": now,
            "opened_at": now,
            "updated_at": now,
            "closed_at": now,
        }
        
        # Aplicar overrides a los datos del modelo Pydantic
        default_trade_data.update(overrides)

        # Crear instancia del modelo Pydantic Trade
        trade_instance = Trade.model_validate(default_trade_data)

        # Construir el diccionario para TradeORM
        trade_orm_data = {
            "id": str(trade_instance.id), # Convertir a string para ORM
            "user_id": trade_instance.user_id, # UUID para ORM (GUID type handles conversion)
            "data": trade_instance.model_dump_json(), # Serializar el modelo Pydantic completo a JSON
            "position_status": trade_instance.positionStatus, # Usar el valor del enum
            "mode": trade_instance.mode, # Usar el valor del enum
            "symbol": trade_instance.symbol,
            "created_at": trade_instance.created_at,
            "updated_at": trade_instance.updated_at,
            "closed_at": trade_instance.closed_at,
        }
        return trade_orm_data

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
    ) -> Dict[str, Any]: # Retorna un diccionario, simulando una respuesta JSON
        logger.info(f"Mock create_oco_order called for {symbol} {side} TP:{price} SL:{stop_price}")
        # Simular la respuesta de Binance para una orden OCO, que es un diccionario.
        return {
            "orderListId": uuid4().int, # Usar un entero grande como en la API real
            "contingencyType": "OCO",
            "listStatusType": "EXEC_STARTED",
            "listOrderStatus": "EXECUTING",
            "listClientOrderId": "mock_oco_list_id_" + str(uuid4()),
            "transactionTime": int(datetime.now(timezone.utc).timestamp() * 1000),
            "symbol": symbol,
            "orders": [],
            "orderReports": []
        }

    mock_service.create_oco_order.side_effect = mock_create_oco_order
    
    return mock_service

@pytest_asyncio.fixture
async def ai_orchestrator_fixture(market_data_service_fixture):
    """Fixture para AIOrchestrator."""
    if not get_app_settings().GEMINI_API_KEY:
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
    """Mock user configuration for testing, using camelCase aliases."""
    from ultibot_backend.core.domain_models.user_configuration_models import (
        UserConfiguration, RiskProfileSettings, RealTradingSettings, RiskProfile, Theme
    )
    from decimal import Decimal
    
    return UserConfiguration(
        id="test-config-id",
        user_id=str(FIXED_USER_ID),
        telegramChatId="test-chat-id",
        notificationPreferences=[],
        enableTelegramNotifications=True,
        defaultPaperTradingCapital=Decimal("10000.0"),
        paperTradingActive=True,
        paperTradingAssets=[],
        watchlists=[],
        favoritePairs=[],
        riskProfile=RiskProfile.MODERATE,
        riskProfileSettings=RiskProfileSettings(
            per_trade_capital_risk_percentage=0.02,
            daily_capital_risk_percentage=0.1,
            max_drawdown_percentage=0.15
        ),
        realTradingSettings=RealTradingSettings(
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
        aiStrategyConfigurations=[],
        aiAnalysisConfidenceThresholds=None,
        mcpServerPreferences=[],
        selectedTheme=Theme.DARK,
        dashboardLayoutProfiles={},
        activeDashboardLayoutProfileId=None,
        dashboardLayoutConfig={},
        cloudSyncPreferences=None,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc)
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
