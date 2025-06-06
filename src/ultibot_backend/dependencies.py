from fastapi import Request
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.ultibot_backend.services.trading_report_service import TradingReportService
from src.ultibot_backend.services.trading_engine_service import TradingEngine
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService

def get_service(request: Request, service_name: str):
    return getattr(request.app.state, service_name)

def get_persistence_service(request: Request) -> SupabasePersistenceService:
    return request.app.state.persistence_service

def get_credential_service(request: Request) -> CredentialService:
    return request.app.state.credential_service

def get_market_data_service(request: Request) -> MarketDataService:
    return request.app.state.market_data_service

def get_portfolio_service(request: Request) -> PortfolioService:
    return request.app.state.portfolio_service

def get_notification_service(request: Request) -> NotificationService:
    return request.app.state.notification_service

def get_config_service(request: Request) -> ConfigurationService:
    return request.app.state.configuration_service

def get_unified_order_execution_service(request: Request) -> UnifiedOrderExecutionService:
    return request.app.state.unified_order_execution_service

def get_strategy_service(request: Request) -> StrategyService:
    return request.app.state.strategy_service

def get_performance_service(request: Request) -> PerformanceService:
    return request.app.state.performance_service

def get_trading_report_service(request: Request) -> TradingReportService:
    return request.app.state.trading_report_service

def get_trading_engine_service(request: Request) -> TradingEngine:
    return request.app.state.trading_engine
