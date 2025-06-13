"""
Módulo de Inyección de Dependencias para la aplicación FastAPI.

Utiliza un enfoque de contenedor manual para instanciar y cablear los componentes
de la aplicación (adaptadores, servicios, etc.) siguiendo los principios de la
Arquitectura Hexagonal y la Inversión de Control. El grafo de dependencias se
resuelve en el siguiente orden:
1. Configuración (AppSettings).
2. Puertos primarios sin dependencias complejas (ej. Persistencia).
3. Servicios base que implementan puertos (ej. CredentialService).
4. Adaptadores que dependen de servicios/puertos base.
5. Servicios de aplicación que orquestan la lógica de negocio.
"""

from typing import Annotated
from fastapi import Depends
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Importación de Configuración ---
from src.ultibot_backend.app_config import get_app_settings, AppSettings

# --- Importación de Puertos (Interfaces) ---
from src.ultibot_backend.core.ports import (
    IPromptRepository,
    IPromptManager,
    IMCPToolHub,
    IAIModelAdapter,
    IAIOrchestrator,
    IPersistencePort,
    IOrderExecutionPort,
    ICredentialService,
    IMarketDataProvider,
    INotificationPort,
    IPortfolioManager
)

# --- Importación de Adaptadores (Implementaciones) ---
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.prompt_persistence_adapter import PromptPersistenceAdapter
from src.ultibot_backend.adapters.gemini_adapter import GeminiAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.adapters.telegram_adapter import TelegramAdapter

# --- Importación de Servicios (Lógica de Aplicación) ---
from src.ultibot_backend.services.tool_hub_service import ToolHubService
from src.ultibot_backend.services.prompt_manager_service import PromptManagerService
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestratorService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.trading_engine_service import TradingEngine

# --- Contenedor de Dependencias ---

# Nivel 0: Configuración
def get_settings() -> AppSettings:
    """Proveedor de la configuración de la aplicación."""
    return get_app_settings()

# Nivel 1: Puertos y Servicios Base (Sin dependencias complejas)
def get_persistence_service(settings: AppSettings = Depends(get_settings)) -> IPersistencePort:
    """
    Proveedor del servicio de persistencia.
    Implementa: IPersistencePort.
    """
    return SupabasePersistenceService(app_settings=settings)

def get_credential_service(
    persistence_port: IPersistencePort = Depends(get_persistence_service)
) -> ICredentialService:
    """
    Proveedor del servicio de credenciales.
    Implementa: ICredentialService.
    """
    return CredentialService(persistence_port=persistence_port)

# Nivel 2: Adaptadores (Implementaciones de puertos que dependen de servicios base)
def get_binance_adapter(
    credential_service: ICredentialService = Depends(get_credential_service),
    app_settings: AppSettings = Depends(get_settings)
) -> BinanceAdapter:
    """
    Proveedor del adaptador de Binance.
    Implementa: IOrderExecutionPort y IMarketDataProvider.
    """
    return BinanceAdapter(credential_service=credential_service, app_settings=app_settings)

def get_telegram_adapter(
    credential_service: ICredentialService = Depends(get_credential_service),
    app_settings: AppSettings = Depends(get_settings)
) -> INotificationPort:
    """
    Proveedor del adaptador de Telegram.
    Implementa: INotificationPort.
    """
    return TelegramAdapter(credential_service=credential_service, app_settings=app_settings)

def get_mobula_adapter(settings: AppSettings = Depends(get_settings)) -> MobulaAdapter:
    """Proveedor del adaptador de Mobula para datos de mercado alternativos."""
    api_key = settings.mobula_api_key
    if not api_key:
        raise ValueError("Mobula API key is not configured.")
    return MobulaAdapter(api_key=api_key)

def get_prompt_persistence_adapter(settings: AppSettings = Depends(get_settings)) -> IPromptRepository:
    """Proveedor del adaptador de persistencia para prompts de IA."""
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase URL and Key must be configured.")
    return PromptPersistenceAdapter(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_key
    )

def get_gemini_adapter(settings: AppSettings = Depends(get_settings)) -> IAIModelAdapter:
    """Proveedor del adaptador para el modelo de IA de Gemini."""
    if not settings.gemini_api_key:
        raise ValueError("Gemini API key is not configured.")
    return GeminiAdapter(api_key=settings.gemini_api_key)

# Nivel 3: Servicios de Aplicación (Orquestan la lógica de negocio)
def get_notification_service(
    credential_service: ICredentialService = Depends(get_credential_service),
    notification_port: INotificationPort = Depends(get_telegram_adapter)
) -> NotificationService:
    """Proveedor del servicio de notificaciones."""
    return NotificationService(
        credential_service=credential_service,
        notification_port=notification_port
    )

def get_market_data_service(
    market_data_provider: IMarketDataProvider = Depends(get_binance_adapter),
    persistence_service: IPersistencePort = Depends(get_persistence_service),
    app_settings: AppSettings = Depends(get_settings)
) -> MarketDataService:
    """Proveedor del servicio de datos de mercado."""
    return MarketDataService(
        market_data_provider=market_data_provider,
        persistence_service=persistence_service,
        app_settings=app_settings
    )

def get_portfolio_service(
    persistence_service: IPersistencePort = Depends(get_persistence_service),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    app_settings: AppSettings = Depends(get_settings)
) -> IPortfolioManager:
    """Proveedor del servicio de gestión de portafolio."""
    return PortfolioService(
        persistence_service=persistence_service,
        market_data_service=market_data_service,
        app_settings=app_settings
    )

def get_configuration_service(
    persistence_port: IPersistencePort = Depends(get_persistence_service),
    notification_port: INotificationPort = Depends(get_telegram_adapter),
    portfolio_service: IPortfolioManager = Depends(get_portfolio_service),
    credential_service: ICredentialService = Depends(get_credential_service),
    app_settings: AppSettings = Depends(get_settings)
) -> ConfigurationService:
    """Proveedor del servicio de configuración."""
    return ConfigurationService(
        persistence_port=persistence_port,
        notification_port=notification_port,
        portfolio_service=portfolio_service,
        credential_service=credential_service,
        app_settings=app_settings
    )

def get_tool_hub_service(
    mobula_adapter: MobulaAdapter = Depends(get_mobula_adapter),
    binance_adapter: BinanceAdapter = Depends(get_binance_adapter)
) -> IMCPToolHub:
    """Proveedor del hub de herramientas para la IA."""
    return ToolHubService(
        mobula_adapter=mobula_adapter,
        binance_adapter=binance_adapter
    )

def get_prompt_manager_service(
    prompt_repo: IPromptRepository = Depends(get_prompt_persistence_adapter)
) -> IPromptManager:
    """Proveedor del gestor de prompts para la IA."""
    return PromptManagerService(prompt_repository=prompt_repo)

def get_ai_orchestrator_service(
    gemini_adapter: IAIModelAdapter = Depends(get_gemini_adapter),
    tool_hub: IMCPToolHub = Depends(get_tool_hub_service),
    prompt_manager: IPromptManager = Depends(get_prompt_manager_service)
) -> IAIOrchestrator:
    """Proveedor del orquestador de IA."""
    return AIOrchestratorService(
        gemini_adapter=gemini_adapter,
        tool_hub=tool_hub,
        prompt_manager=prompt_manager
    )

def get_trading_engine_service(
    order_execution_port: IOrderExecutionPort = Depends(get_binance_adapter),
    persistence_port: IPersistencePort = Depends(get_persistence_service),
    credential_service: ICredentialService = Depends(get_credential_service),
    market_data_provider: IMarketDataProvider = Depends(get_binance_adapter),
    ai_orchestrator: IAIOrchestrator = Depends(get_ai_orchestrator_service)
) -> TradingEngine:
    """Proveedor del motor de trading, el servicio de más alto nivel."""
    return TradingEngine(
        order_execution_port=order_execution_port,
        persistence_port=persistence_port,
        credential_service=credential_service,
        market_data_provider=market_data_provider,
        ai_orchestrator=ai_orchestrator
    )

# --- Dependencias Anotadas para Endpoints de FastAPI ---
# Alias para mejorar la legibilidad y el autocompletado en los endpoints.

AIOrchestratorDep = Annotated[IAIOrchestrator, Depends(get_ai_orchestrator_service)]
ConfigurationServiceDep = Annotated[ConfigurationService, Depends(get_configuration_service)]
MarketDataServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
PersistenceServiceDep = Annotated[IPersistencePort, Depends(get_persistence_service)]
PortfolioManagerDep = Annotated[IPortfolioManager, Depends(get_portfolio_service)]
TradingEngineDep = Annotated[TradingEngine, Depends(get_trading_engine_service)]
CredentialServiceDep = Annotated[ICredentialService, Depends(get_credential_service)]
