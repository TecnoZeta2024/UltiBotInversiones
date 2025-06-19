import logging
import asyncio
import os
import asyncpg
from functools import lru_cache
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession # Importar AsyncSession

from fastapi import Request, Depends # Importar Depends
from ultibot_backend.services.order_execution_service import PaperOrderExecutionService
from ultibot_backend.adapters.binance_adapter import BinanceAdapter
from ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService as PersistenceService
from ultibot_backend.services.ai_orchestrator_service import AIOrchestrator as AIOrchestratorService
from ultibot_backend.services.config_service import ConfigurationService
from ultibot_backend.services.credential_service import CredentialService
from ultibot_backend.services.market_data_service import MarketDataService
from ultibot_backend.services.notification_service import NotificationService
from ultibot_backend.services.order_execution_service import OrderExecutionService
from ultibot_backend.services.performance_service import PerformanceService
from ultibot_backend.services.portfolio_service import PortfolioService
from ultibot_backend.services.strategy_service import StrategyService
from ultibot_backend.services.trading_engine_service import TradingEngine as TradingEngineService
from ultibot_backend.services.trading_report_service import TradingReportService
from ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService

logger = logging.getLogger(__name__)

# Nueva función para obtener la sesión de la base de datos
# Esta función será sobrescrita en los tests para inyectar la sesión de la fixture
async def get_db_session() -> AsyncSession:
    # En un entorno de producción, esto debería obtener una sesión del pool
    # Para los tests, será sobrescrita por la fixture db_session
    raise NotImplementedError("get_db_session debe ser implementado o sobrescrito")

class DependencyContainer:
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        # self.persistence_service: Optional[PersistenceService] = None # Eliminado
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

    async def initialize_services(self):
        logger.info("Initializing dependency container...")
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Level 0: No service dependencies
        # La inicialización de persistence_service se moverá a get_persistence_service
        self.binance_adapter = BinanceAdapter()
        self.paper_order_execution_service = PaperOrderExecutionService()

        # Level 1: Depend on Level 0
        # persistence_service se inyectará directamente en los servicios que lo necesiten
        # a través de get_persistence_service
        self.credential_service = CredentialService(
            persistence_service=await get_persistence_service(Request), # Esto es un placeholder, se inyectará en runtime
            binance_adapter=self.binance_adapter
        )
        self.trading_report_service = TradingReportService(await get_persistence_service(Request)) # Placeholder
        self.order_execution_service = OrderExecutionService(
            binance_adapter=self.binance_adapter
        )

        # Level 2: Depend on Level 1
        self.mobula_adapter = MobulaAdapter(
            credential_service=self.credential_service,
            http_client=self.http_client
        )
        self.notification_service = NotificationService(
            credential_service=self.credential_service,
            persistence_service=await get_persistence_service(Request) # Placeholder
        )
        self.market_data_service = MarketDataService(
            credential_service=self.credential_service,
            binance_adapter=self.binance_adapter,
            persistence_service=await get_persistence_service(Request) # Placeholder
        )
        self.unified_order_execution_service = UnifiedOrderExecutionService(
            real_execution_service=self.order_execution_service,
            paper_execution_service=self.paper_order_execution_service
        )

        # Level 3: Depend on Level 2
        self.ai_orchestrator_service = AIOrchestratorService(
            market_data_service=self.market_data_service
        )
        self.portfolio_service = PortfolioService(
            persistence_service=await get_persistence_service(Request), # Placeholder
            market_data_service=self.market_data_service
        )

        # Level 4: Depend on previous levels
        self.config_service = ConfigurationService(
            persistence_service=await get_persistence_service(Request) # Placeholder
        )
        self.config_service.set_credential_service(self.credential_service)
        self.config_service.set_portfolio_service(self.portfolio_service)
        self.config_service.set_notification_service(self.notification_service)

        # Level 5: Depend on previous levels
        self.strategy_service = StrategyService(
            persistence_service=await get_persistence_service(Request), # Placeholder
            configuration_service=self.config_service
        )

        # Level 6: Depend on previous levels (including StrategyService)
        self.performance_service = PerformanceService(
            persistence_service=await get_persistence_service(Request), # Placeholder
            strategy_service=self.strategy_service
        )

        # Level 7: The main engine, depends on almost everything
        self.trading_engine_service = TradingEngineService(
            persistence_service=await get_persistence_service(Request), # Placeholder
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
        # La gestión del pool/engine de la BD se hará a través de get_db_session o lifespan
        # if self.persistence_service:
        #     if self.persistence_service._pool:
        #         await self.persistence_service._pool.close()
        #     elif self.persistence_service._engine:
        #         await self.persistence_service._engine.dispose()
        if self.binance_adapter:
            await self.binance_adapter.close()
        logger.info("Dependency container shut down.")


_global_container: Optional[DependencyContainer] = None

def get_container(request: Request) -> DependencyContainer:
    global _global_container
    if hasattr(request.app.state, 'container') and request.app.state.container is not None:
        return request.app.state.container
    else:
        # Esto es una solución de contingencia para entornos de prueba donde el lifespan
        # de FastAPI podría no inicializar app.state.container correctamente.
        # En producción, el lifespan siempre debería inicializarlo.
        if _global_container is None:
            logger.warning("DependencyContainer no encontrado en app.state. Inicializando contenedor global para tests.")
            _global_container = DependencyContainer()
            # Ejecutar inicialización de servicios si es la primera vez que se accede globalmente
            # Esto es un hack y debería ser manejado por el lifespan en un entorno real.
            # Esto es crucial para que los servicios estén listos para su uso en tests
            # que no pasan por el lifespan completo de FastAPI.
            try:
                # Ejecutar initialize_services en un loop de eventos si no hay uno corriendo
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_global_container.initialize_services())
                else:
                    loop.run_until_complete(_global_container.initialize_services())
            except RuntimeError:
                # Si no hay un loop de eventos, crear uno temporalmente
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(_global_container.initialize_services())
                new_loop.close()
            logger.info("Contenedor global de contingencia inicializado y servicios cargados.")
        return _global_container


async def get_persistence_service(
    db_session: AsyncSession = Depends(get_db_session) # Inyectar la sesión de la BD
) -> PersistenceService:
    return PersistenceService(session=db_session)


async def get_credential_service(request: Request) -> CredentialService:
    container = get_container(request)
    assert container.credential_service is not None, "CredentialService not initialized"
    return container.credential_service


async def get_notification_service(request: Request) -> NotificationService:
    container = get_container(request)
    assert container.notification_service is not None, "NotificationService not initialized"
    return container.notification_service


async def get_config_service(request: Request) -> ConfigurationService:
    container = get_container(request)
    assert container.config_service is not None, "ConfigurationService not initialized"
    return container.config_service


async def get_market_data_service(request: Request) -> MarketDataService:
    container = get_container(request)
    assert container.market_data_service is not None, "MarketDataService not initialized"
    return container.market_data_service


async def get_portfolio_service(request: Request) -> PortfolioService:
    container = get_container(request)
    assert container.portfolio_service is not None, "PortfolioService not initialized"
    return container.portfolio_service


async def get_strategy_service(request: Request) -> StrategyService:
    container = get_container(request)
    assert container.strategy_service is not None, "StrategyService not initialized"
    return container.strategy_service


async def get_order_execution_service(request: Request) -> OrderExecutionService:
    container = get_container(request)
    assert container.order_execution_service is not None, "OrderExecutionService not initialized"
    return container.order_execution_service


async def get_unified_order_execution_service(request: Request) -> UnifiedOrderExecutionService:
    container = get_container(request)
    assert container.unified_order_execution_service is not None, "UnifiedOrderExecutionService not initialized"
    return container.unified_order_execution_service


async def get_trading_engine_service(request: Request) -> TradingEngineService:
    container = get_container(request)
    assert container.trading_engine_service is not None, "TradingEngineService not initialized"
    return container.trading_engine_service


async def get_trading_report_service(request: Request) -> TradingReportService:
    container = get_container(request)
    assert container.trading_report_service is not None, "TradingReportService not initialized"
    return container.trading_report_service


async def get_performance_service(request: Request) -> PerformanceService:
    container = get_container(request)
    assert container.performance_service is not None, "PerformanceService not initialized"
    return container.performance_service


async def get_ai_orchestrator_service(request: Request) -> AIOrchestratorService:
    container = get_container(request)
    assert container.ai_orchestrator_service is not None, "AIOrchestratorService not initialized"
    return container.ai_orchestrator_service
