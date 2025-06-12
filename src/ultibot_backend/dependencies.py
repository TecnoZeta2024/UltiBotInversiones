"""
Módulo de Inyección de Dependencias para la aplicación FastAPI.

Utiliza un enfoque de contenedor manual para instanciar y cablear los componentes
de la aplicación (adaptadores, servicios, etc.) siguiendo los principios de la
Arquitectura Hexagonal y la Inversión de Control.
"""

import os
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importación de Puertos (Interfaces)
from src.ultibot_backend.core.ports import (
    IMarketDataProvider,
    IPromptRepository,
    IPromptManager,
    IMCPToolHub,
    IAIModelAdapter,
    IAIOrchestrator,
    IPersistencePort
)

# Importación de Adaptadores (Implementaciones)
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.prompt_persistence_adapter import PromptPersistenceAdapter
from src.ultibot_backend.adapters.gemini_adapter import GeminiAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService

# Importación de Servicios (Lógica de Aplicación)
from src.ultibot_backend.services.tool_hub_service import ToolHubService
from src.ultibot_backend.services.prompt_manager_service import PromptManagerService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.services.market_scan_service import MarketScanService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.trading_engine_service import TradingEngine

# --- Contenedor de Dependencias ---

@lru_cache(maxsize=None)
def get_settings():
    """Retorna un diccionario con las configuraciones de la aplicación."""
    return {
        "mobula_api_key": os.getenv("MOBULA_API_KEY"),
        "binance_api_key": os.getenv("BINANCE_API_KEY"),
        "binance_api_secret": os.getenv("BINANCE_API_SECRET"),
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
    }

# --- Proveedores de Adaptadores ---

def get_binance_adapter() -> BinanceAdapter:
    settings = get_settings()
    return BinanceAdapter(
        api_key=settings["binance_api_key"],
        api_secret=settings["binance_api_secret"]
    )

def get_mobula_adapter() -> MobulaAdapter:
    settings = get_settings()
    return MobulaAdapter(api_key=settings["mobula_api_key"])

def get_prompt_persistence_adapter() -> IPromptRepository:
    settings = get_settings()
    return PromptPersistenceAdapter(
        supabase_url=settings["supabase_url"],
        supabase_key=settings["supabase_key"]
    )

def get_gemini_adapter() -> IAIModelAdapter:
    settings = get_settings()
    return GeminiAdapter(api_key=settings["gemini_api_key"])

def get_persistence_service() -> SupabasePersistenceService:
    """Proveedor del servicio de persistencia de Supabase."""
    return SupabasePersistenceService()

# --- Proveedores de Servicios ---

def get_tool_hub_service(
    mobula_adapter: MobulaAdapter = Depends(get_mobula_adapter),
    binance_adapter: BinanceAdapter = Depends(get_binance_adapter)
) -> IMCPToolHub:
    return ToolHubService(
        mobula_adapter=mobula_adapter,
        binance_adapter=binance_adapter
    )

def get_prompt_manager_service(
    prompt_repo: IPromptRepository = Depends(get_prompt_persistence_adapter)
) -> IPromptManager:
    return PromptManagerService(prompt_repository=prompt_repo)

def get_ai_orchestrator_service(
    gemini_adapter: IAIModelAdapter = Depends(get_gemini_adapter),
    tool_hub: IMCPToolHub = Depends(get_tool_hub_service),
    prompt_manager: IPromptManager = Depends(get_prompt_manager_service)
) -> IAIOrchestrator:
    return AIOrchestratorService(
        gemini_adapter=gemini_adapter,
        tool_hub=tool_hub,
        prompt_manager=prompt_manager
    )

def get_credential_service(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    binance_adapter: BinanceAdapter = Depends(get_binance_adapter)
) -> CredentialService:
    return CredentialService(
        persistence_service=persistence_service,
        binance_adapter=binance_adapter
    )

def get_notification_service(
    credential_service: CredentialService = Depends(get_credential_service),
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> NotificationService:
    return NotificationService(
        credential_service=credential_service,
        persistence_service=persistence_service
    )

def get_configuration_service(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    notification_service: NotificationService = Depends(get_notification_service),
    credential_service: CredentialService = Depends(get_credential_service)
) -> ConfigurationService:
    return ConfigurationService(
        persistence_service=persistence_service,
        notification_service=notification_service,
        portfolio_service=None,  # Placeholder - se agregará cuando exista
        credential_service=credential_service
    )

def get_market_scan_service(
    binance_adapter: BinanceAdapter = Depends(get_binance_adapter),
    mobula_adapter: MobulaAdapter = Depends(get_mobula_adapter),
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> MarketScanService:
    return MarketScanService(
        binance_adapter=binance_adapter,
        mobula_adapter=mobula_adapter,
        persistence_service=persistence_service
    )

def get_market_data_service(
    credential_service: CredentialService = Depends(get_credential_service),
    binance_adapter: BinanceAdapter = Depends(get_binance_adapter),
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> MarketDataService:
    return MarketDataService(
        credential_service=credential_service,
        binance_adapter=binance_adapter,
        persistence_service=persistence_service
    )

def get_strategy_service(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> StrategyService:
    return StrategyService(persistence_service=persistence_service)

def get_performance_service(
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service),
    strategy_service: StrategyService = Depends(get_strategy_service)
) -> PerformanceService:
    return PerformanceService(
        persistence_service=persistence_service,
        strategy_service=strategy_service
    )

def get_portfolio_service(
    market_data_service: MarketDataService = Depends(get_market_data_service),
    persistence_service: SupabasePersistenceService = Depends(get_persistence_service)
) -> PortfolioService:
    return PortfolioService(
        market_data_service=market_data_service,
        persistence_service=persistence_service
    )

def get_trading_engine_service() -> TradingEngine:
    return TradingEngine()

# --- Dependencias para Endpoints de FastAPI ---

# Se pueden usar directamente en los endpoints con Depends()
# Ejemplo: async def my_endpoint(orchestrator: IAIOrchestrator = Depends(get_ai_orchestrator_service)):
#              ...

# Alias para mayor claridad en los endpoints
AIOrchestratorDep = Annotated[IAIOrchestrator, Depends(get_ai_orchestrator_service)]
PromptManagerDep = Annotated[IPromptManager, Depends(get_prompt_manager_service)]
ConfigurationServiceDep = Annotated[ConfigurationService, Depends(get_configuration_service)]
MarketScanServiceDep = Annotated[MarketScanService, Depends(get_market_scan_service)]
MarketDataServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
PersistenceServiceDep = Annotated[IPersistencePort, Depends(get_persistence_service)]
PerformanceServiceDep = Annotated[PerformanceService, Depends(get_performance_service)]
PortfolioDep = Annotated[PortfolioService, Depends(get_portfolio_service)]
TradingEngineDep = Annotated[TradingEngine, Depends(get_trading_engine_service)]
