import logging
import asyncio
import os
from functools import lru_cache
from typing import Optional, Callable, Any, cast # Importar Any y cast
import httpx
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Importar la Base y los modelos para la creación de tablas
from core.domain_models.base import Base
from core.domain_models import orm_models

from fastapi import Request, Depends
from services.order_execution_service import PaperOrderExecutionService
from adapters.binance_adapter import BinanceAdapter
from adapters.mobula_adapter import MobulaAdapter
from adapters.persistence_service import SupabasePersistenceService as PersistenceService
from adapters.redis_cache import RedisCache # Importar RedisCache
from services.ai_orchestrator_service import AIOrchestrator as AIOrchestratorService
from services.config_service import ConfigurationService
from services.credential_service import CredentialService
from services.market_data_service import MarketDataService
from services.notification_service import NotificationService
from services.order_execution_service import OrderExecutionService
from services.performance_service import PerformanceService
from services.portfolio_service import PortfolioService
from services.strategy_service import StrategyService
from services.trading_engine_service import TradingEngine as TradingEngineService
from services.trading_report_service import TradingReportService
from services.unified_order_execution_service import UnifiedOrderExecutionService

logger = logging.getLogger(__name__)

# Global variables for database connection
_db_engine = None
_session_factory: Optional[Callable[..., AsyncSession]] = None

async def initialize_database():
    """Initialize the database engine and session factory."""
    global _db_engine, _session_factory
    
    if _db_engine is None:
        # Usar la URL de la base de datos de las variables de entorno
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            # Fallback a SQLite si no se proporciona DATABASE_URL (ej. para pruebas locales sin Docker)
            database_url = "sqlite+aiosqlite:///ultibot_local.db"
            logger.warning(f"DATABASE_URL no encontrada en el entorno. Usando SQLite local: {database_url}")
        else:
            logger.info(f"Usando DATABASE_URL del entorno: {database_url}")

        try:
            logger.info(f"Initializing database with URL: {database_url}")
            _db_engine = create_async_engine(
                database_url,
                echo=False,
                poolclass=NullPool if "sqlite" in database_url else None # Usar NullPool para SQLite
            )
            
            async with _db_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            _session_factory = async_sessionmaker(
                _db_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("Database tables created and session factory initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

from typing import AsyncGenerator # Importar AsyncGenerator

async def get_db_session() -> AsyncGenerator[AsyncSession, Any]:
    """
    Dependency that provides a database session, ensuring it's closed after use.
    """
    global _session_factory
    
    if _session_factory is None:
        await initialize_database()
        
    if _session_factory is None:
        raise RuntimeError("Database session factory not initialized")

    async with _session_factory() as session:
        yield session

class DependencyContainer:
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.ai_orchestrator_service: Optional[AIOrchestratorService] = None
        self.binance_adapter: Optional[BinanceAdapter] = None
        self.credential_service: Optional[CredentialService] = None
        self.mobula_adapter: Optional[MobulaAdapter] = None
        self.notification_service: Optional[NotificationService] = None
        self.performance_service: Optional[PerformanceService] = None
        self.trading_report_service: Optional[TradingReportService] = None
        self.market_data_service: Optional[MarketDataService] = None
        self.portfolio_service: Optional[PortfolioService] = None
        self.order_execution_service: Optional[OrderExecutionService] = None
        self.paper_order_execution_service: Optional[PaperOrderExecutionService] = None
        self.unified_order_execution_service: Optional[UnifiedOrderExecutionService] = None
        self.config_service: Optional[ConfigurationService] = None
        self.strategy_service: Optional[StrategyService] = None
        self.trading_engine_service: Optional[TradingEngineService] = None
        self.persistence_service: Optional[PersistenceService] = None
        self.cache: Optional[RedisCache] = None # Añadir el servicio de caché

    async def initialize_services(self):
        logger.info("Initializing dependency container...")
        
        await initialize_database()
        
        if _session_factory is None:
            raise RuntimeError("Database session factory not initialized before persistence service initialization.")
        self.persistence_service = PersistenceService(session_factory=cast(async_sessionmaker[AsyncSession], _session_factory))
        
        self.http_client = httpx.AsyncClient(timeout=30.0)

        self.cache = RedisCache() # Inicializar RedisCache
        await self.cache.initialize() # Inicializar el cliente Redis

        self.binance_adapter = BinanceAdapter()
        self.paper_order_execution_service = PaperOrderExecutionService()

        self.order_execution_service = OrderExecutionService(
            binance_adapter=self.binance_adapter
        )
        
        if _session_factory is None:
            raise RuntimeError("Database session factory not initialized before service initialization.")
        
        self.credential_service = CredentialService(
            session_factory=cast(async_sessionmaker[AsyncSession], _session_factory),
            binance_adapter=self.binance_adapter
        )
        self.trading_report_service = TradingReportService(session_factory=cast(async_sessionmaker[AsyncSession], _session_factory))

        self.mobula_adapter = MobulaAdapter(
            credential_service=self.credential_service,
            http_client=self.http_client
        )
        self.notification_service = NotificationService(
            credential_service=self.credential_service,
            persistence_service=self.persistence_service
        )
        self.market_data_service = MarketDataService(
            credential_service=self.credential_service,
            binance_adapter=self.binance_adapter,
            persistence_service=self.persistence_service
        )
        self.unified_order_execution_service = UnifiedOrderExecutionService(
            real_execution_service=self.order_execution_service,
            paper_execution_service=self.paper_order_execution_service
        )

        self.ai_orchestrator_service = AIOrchestratorService(
            market_data_service=self.market_data_service
        )
        self.portfolio_service = PortfolioService(
            persistence_service=self.persistence_service,
            market_data_service=self.market_data_service
        )

        self.config_service = ConfigurationService(
            persistence_service=self.persistence_service
        )

        self.strategy_service = StrategyService(
            persistence_service=self.persistence_service,
            configuration_service=self.config_service
        )

        self.performance_service = PerformanceService(
            strategy_service=self.strategy_service,
            persistence_service=self.persistence_service
        )

        self.trading_engine_service = TradingEngineService(
            persistence_service=self.persistence_service,
            market_data_service=self.market_data_service,
            unified_order_execution_service=self.unified_order_execution_service,
            credential_service=self.credential_service,
            notification_service=self.notification_service,
            strategy_service=self.strategy_service,
            configuration_service=self.config_service,
            portfolio_service=self.portfolio_service,
            ai_orchestrator=self.ai_orchestrator_service
        )
        logger.info("Dependency container initialized successfully.")

    async def shutdown(self):
        logger.info("Shutting down dependency container...")
        if self.http_client:
            await self.http_client.aclose()
        if self.binance_adapter:
            await self.binance_adapter.close()
        if self.cache: # Cerrar el cliente Redis
            await self.cache.close()
        logger.info("Dependency container shut down.")


_global_container: Optional[DependencyContainer] = None

async def get_container_async(request: Request) -> DependencyContainer:
    global _global_container
    if hasattr(request.app.state, 'container') and request.app.state.container is not None:
        return request.app.state.container
    else:
        if _global_container is None:
            logger.warning("DependencyContainer no encontrado en app.state. Inicializando contenedor global para tests.")
            _global_container = DependencyContainer()
            await _global_container.initialize_services()
            logger.info("Contenedor global de contingencia inicializado y servicios cargados.")
        return _global_container


async def get_persistence_service(request: Request) -> PersistenceService:
    """
    Provides the singleton PersistenceService instance from the dependency container.
    This ensures all services share the same persistence layer.
    """
    container = await get_container_async(request)
    assert container.persistence_service is not None, "PersistenceService not initialized"
    return container.persistence_service


async def get_credential_service(request: Request) -> CredentialService:
    container = await get_container_async(request)
    assert container.credential_service is not None, "CredentialService not initialized"
    return container.credential_service


async def get_notification_service(request: Request) -> NotificationService:
    container = await get_container_async(request)
    assert container.notification_service is not None, "NotificationService not initialized"
    return container.notification_service


async def get_config_service(request: Request) -> ConfigurationService:
    container = await get_container_async(request)
    assert container.config_service is not None, "ConfigurationService not initialized"
    return container.config_service


async def get_market_data_service(request: Request) -> MarketDataService:
    container = await get_container_async(request)
    assert container.market_data_service is not None, "MarketDataService not initialized"
    return container.market_data_service


async def get_portfolio_service(request: Request) -> PortfolioService:
    container = await get_container_async(request)
    assert container.portfolio_service is not None, "PortfolioService not initialized"
    return container.portfolio_service


async def get_strategy_service(request: Request) -> StrategyService:
    container = await get_container_async(request)
    assert container.strategy_service is not None, "StrategyService not initialized"
    return container.strategy_service


async def get_order_execution_service(request: Request) -> OrderExecutionService:
    container = await get_container_async(request)
    assert container.order_execution_service is not None, "OrderExecutionService not initialized"
    return container.order_execution_service


async def get_unified_order_execution_service(request: Request) -> UnifiedOrderExecutionService:
    container = await get_container_async(request)
    assert container.unified_order_execution_service is not None, "UnifiedOrderExecutionService not initialized"
    return container.unified_order_execution_service


async def get_trading_engine_service(request: Request) -> TradingEngineService:
    container = await get_container_async(request)
    assert container.trading_engine_service is not None, "TradingEngineService not initialized"
    return container.trading_engine_service


async def get_trading_report_service(request: Request) -> TradingReportService:
    container = await get_container_async(request)
    assert container.trading_report_service is not None, "TradingReportService not initialized"
    return container.trading_report_service


async def get_performance_service(request: Request) -> PerformanceService:
    container = await get_container_async(request)
    assert container.performance_service is not None, "PerformanceService not initialized"
    return container.performance_service


async def get_ai_orchestrator_service(request: Request) -> AIOrchestratorService:
    container = await get_container_async(request)
    assert container.ai_orchestrator_service is not None, "AIOrchestratorService not initialized"
    return container.ai_orchestrator_service


async def get_cache_service(request: Request) -> RedisCache:
    """
    Provides the singleton RedisCache instance from the dependency container.
    """
    container = await get_container_async(request)
    assert container.cache is not None, "RedisCache not initialized"
    return container.cache
