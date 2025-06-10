import logging
from functools import lru_cache
from typing import Optional, Union

import httpx
from src.ultibot_backend.app_config import settings
from src.ultibot_backend.services.order_execution_service import OrderExecutionService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService as PersistenceService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.trading_engine_service import TradingEngineService
from src.ultibot_backend.services.trading_report_service import TradingReportService

# New imports for paper trading
from src.ultibot_backend.services.trading_mode_service import TradingModeService, get_trading_mode_service, TradingMode
from src.ultibot_backend.services.simulated_portfolio_service import SimulatedPortfolioService, get_simulated_portfolio_service
from src.ultibot_backend.services.simulated_order_execution_service import SimulatedOrderExecutionService


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
        self.config_service: Optional[ConfigurationService] = None
        self.strategy_service: Optional[StrategyService] = None
        self.trading_engine_service: Optional[TradingEngineService] = None
        
        # Paper trading services
        self.trading_mode_service: Optional[TradingModeService] = None
        self.simulated_portfolio_service: Optional[SimulatedPortfolioService] = None
        self.simulated_order_execution_service: Optional[SimulatedOrderExecutionService] = None


    async def initialize_services(self):
        logger.info("Initializing dependency container...")
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Level 0: No service dependencies
        self.persistence_service = PersistenceService()
        await self.persistence_service.connect()
        
        binance_api_key = settings.BINANCE_API_KEY or ""
        binance_api_secret = settings.BINANCE_API_SECRET or ""

        self.binance_adapter = BinanceAdapter(
            api_key=binance_api_key,
            api_secret=binance_api_secret,
            http_client=self.http_client
        )
        
        self.ai_orchestrator_service = AIOrchestratorService(
            app_settings=settings
        )
        
        # Initialize trading mode and simulation services
        self.trading_mode_service = get_trading_mode_service()
        self.simulated_portfolio_service = get_simulated_portfolio_service()
        self.simulated_order_execution_service = SimulatedOrderExecutionService(
            simulated_portfolio_service=self.simulated_portfolio_service
        )

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

        # Level 3: Depend on Level 2
        self.portfolio_service = PortfolioService(
            persistence_service=self.persistence_service,
            market_data_service=self.market_data_service
        )

        # Level 4: Depend on previous levels
        self.config_service = ConfigurationService(
            persistence_service=self.persistence_service,
            credential_service=self.credential_service,
            portfolio_service=self.portfolio_service,
            notification_service=self.notification_service
        )

        # Level 5: Depend on previous levels
        self.strategy_service = StrategyService(
            persistence_service=self.persistence_service
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
            order_execution_service=self.get_active_order_execution_service(), # Dynamic dependency
            credential_service=self.credential_service,
            notification_service=self.notification_service,
            strategy_service=self.strategy_service,
            configuration_service=self.config_service,
            portfolio_service=self.portfolio_service,
            ai_orchestrator=self.ai_orchestrator_service,
            app_settings=settings
        )
        logger.info("Dependency container initialized successfully.")

    def get_active_order_execution_service(self) -> Union[OrderExecutionService, SimulatedOrderExecutionService]:
        """
        Returns the active order execution service based on the current trading mode.
        """
        if self.trading_mode_service.get_mode() == TradingMode.LIVE:
            assert self.order_execution_service is not None
            return self.order_execution_service
        else:
            assert self.simulated_order_execution_service is not None
            return self.simulated_order_execution_service

    async def shutdown(self):
        logger.info("Shutting down dependency container...")
        if self.http_client:
            await self.http_client.aclose()
        if self.persistence_service:
            await self.persistence_service.disconnect()
        if self.binance_adapter:
            await self.binance_adapter.close()
        logger.info("Dependency container shut down.")


@lru_cache()
def get_container() -> DependencyContainer:
    return DependencyContainer()

# Existing providers... (no changes needed for them)

async def get_persistence_service() -> PersistenceService:
    container = get_container()
    assert container.persistence_service is not None
    return container.persistence_service


async def get_credential_service() -> CredentialService:
    container = get_container()
    assert container.credential_service is not None
    return container.credential_service


async def get_notification_service() -> NotificationService:
    container = get_container()
    assert container.notification_service is not None
    return container.notification_service


async def get_config_service() -> ConfigurationService:
    container = get_container()
    assert container.config_service is not None
    return container.config_service


async def get_market_data_service() -> MarketDataService:
    container = get_container()
    assert container.market_data_service is not None
    return container.market_data_service


async def get_portfolio_service() -> PortfolioService:
    container = get_container()
    assert container.portfolio_service is not None
    return container.portfolio_service


async def get_strategy_service() -> StrategyService:
    container = get_container()
    assert container.strategy_service is not None
    return container.strategy_service

# New dynamic provider for order execution
def get_active_order_execution_service() -> Union[OrderExecutionService, SimulatedOrderExecutionService]:
    container = get_container()
    return container.get_active_order_execution_service()


async def get_trading_engine_service() -> TradingEngineService:
    container = get_container()
    assert container.trading_engine_service is not None
    return container.trading_engine_service


async def get_trading_report_service() -> TradingReportService:
    container = get_container()
    assert container.trading_report_service is not None
    return container.trading_report_service


async def get_performance_service() -> PerformanceService:
    container = get_container()
    assert container.performance_service is not None
    return container.performance_service


async def get_ai_orchestrator_service() -> AIOrchestratorService:
    container = get_container()
    assert container.ai_orchestrator_service is not None
    return container.ai_orchestrator_service
