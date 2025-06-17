import logging
from functools import lru_cache
from typing import Optional
import httpx

from fastapi import Request
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


class DependencyContainer:
    def __init__(self):
        self.http_client: Optional[httpx.AsyncClient] = None
        self.persistence_service: Optional[PersistenceService] = None
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
        self.persistence_service = PersistenceService()
        await self.persistence_service.connect()
        self.binance_adapter = BinanceAdapter()
        self.paper_order_execution_service = PaperOrderExecutionService()

        # Level 1: Depend on Level 0
        self.credential_service = CredentialService(
            persistence_service=self.persistence_service,
            binance_adapter=self.binance_adapter
        )
        self.trading_report_service = TradingReportService(self.persistence_service)
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

        # Level 3: Depend on Level 2
        self.ai_orchestrator_service = AIOrchestratorService(
            market_data_service=self.market_data_service
        )
        self.portfolio_service = PortfolioService(
            persistence_service=self.persistence_service,
            market_data_service=self.market_data_service
        )

        # Level 4: Depend on previous levels
        self.config_service = ConfigurationService(
            persistence_service=self.persistence_service
        )
        self.config_service.set_credential_service(self.credential_service)
        self.config_service.set_portfolio_service(self.portfolio_service)
        self.config_service.set_notification_service(self.notification_service)

        # Level 5: Depend on previous levels
        self.strategy_service = StrategyService(
            persistence_service=self.persistence_service,
            configuration_service=self.config_service
        )

        # Level 6: Depend on previous levels (including StrategyService)
        self.performance_service = PerformanceService(
            persistence_service=self.persistence_service,
            strategy_service=self.strategy_service
        )

        # Level 7: The main engine, depends on almost everything
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
        if self.persistence_service:
            await self.persistence_service.disconnect()
        if self.binance_adapter:
            await self.binance_adapter.close()
        logger.info("Dependency container shut down.")


def get_container(request: Request) -> DependencyContainer:
    return request.app.state.container


async def get_persistence_service(request: Request) -> PersistenceService:
    container = get_container(request)
    assert container.persistence_service is not None, "PersistenceService not initialized"
    return container.persistence_service


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

