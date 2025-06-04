"""
UltiBot Backend Main Application

Este módulo inicializa y configura la aplicación FastAPI del backend UltiBot,
incluyendo todos los servicios, adaptadores y endpoints necesarios.

Para ejecutar correctamente la aplicación, use desde la raíz del proyecto:
    uvicorn src.ultibot_backend.main:app --reload (para desarrollo)
O asegúrese de que el directorio raíz del proyecto esté en PYTHONPATH.
"""

from __future__ import annotations

import asyncio
import logging
import logging.handlers # Añadido para RotatingFileHandler
import sys
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

# Solución para Windows ProactorEventLoop con psycopg - DEBE SER LO PRIMERO
if sys.platform == "win32":
    try:
        import win32api # Intenta importar win32api para verificar si el entorno es compatible
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except ImportError:
        logging.warning("win32api no encontrado. No se pudo establecer WindowsSelectorEventLoopPolicy. Esto puede causar problemas en Windows.")

from fastapi import FastAPI, Request

# Importaciones organizadas: stdlib, third-party, local
from langchain_google_genai import ChatGoogleGenerativeAI

from .adapters.binance_adapter import BinanceAdapter
from .adapters.mobula_adapter import MobulaAdapter
from .adapters.persistence_service import SupabasePersistenceService
from .app_config import settings
from .services.ai_orchestrator_service import AIOrchestrator
from .services.config_service import ConfigService
from .services.configuration_service import ConfigurationService
from .services.credential_service import CredentialService
from .services.market_data_service import MarketDataService
from .services.notification_service import NotificationService
from .services.order_execution_service import (
    OrderExecutionService,
    PaperOrderExecutionService,
)
from .services.performance_service import PerformanceService
from .services.portfolio_service import PortfolioService
from .services.strategy_service import StrategyService
from .services.trading_engine_service import TradingEngine
from .services.trading_report_service import TradingReportService # Nueva importación
from .services.unified_order_execution_service import UnifiedOrderExecutionService
from ..shared.data_types import ServiceName, UserConfiguration
from . import dependencies as deps # Importar el nuevo módulo de dependencias

# Configuración de logging con RotatingFileHandler
import os # Necesario para os.path.join y os.makedirs
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = os.path.join(log_dir, "backend.log")

# Estimar maxBytes para ~500 líneas (500 líneas * 200 bytes/línea = 100KB)
# backupCount=0 significa que cuando el log alcance maxBytes, se rota y el viejo se descarta.
backend_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=100000,  # Aproximadamente 100KB
    backupCount=0,    # No mantener archivos de backup, solo el actual (se rota/sobrescribe)
    encoding='utf-8'
)
backend_handler.setLevel(logging.INFO) # Mantener el nivel INFO como estaba en basicConfig
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
backend_handler.setFormatter(formatter)

# Configurar el logger raíz
root_logger_backend = logging.getLogger()
if root_logger_backend.hasHandlers():
    for h_existente in root_logger_backend.handlers[:]:
        root_logger_backend.removeHandler(h_existente)
        
root_logger_backend.addHandler(backend_handler)
root_logger_backend.setLevel(logging.INFO) # Nivel INFO para el logger raíz del backend

logger = logging.getLogger(__name__)
logger.info("Logging configurado con RotatingFileHandler para escribir en logs/backend.log (max ~100KB).")

# FIXED_USER_ID se accede a través de settings
from .app_config import settings

# Variables globales para servicios (se inicializan en lifespan)
credential_service: Optional[CredentialService] = None
notification_service: Optional[NotificationService] = None
binance_adapter: Optional[BinanceAdapter] = None
market_data_service: Optional[MarketDataService] = None
persistence_service: Optional[SupabasePersistenceService] = None
portfolio_service: Optional[PortfolioService] = None
config_service: Optional[ConfigService] = None
order_execution_service: Optional[OrderExecutionService] = None
paper_order_execution_service: Optional[PaperOrderExecutionService] = None
unified_order_execution_service: Optional[UnifiedOrderExecutionService] = None
trading_engine_service: Optional[TradingEngine] = None
strategy_service: Optional[StrategyService] = None
performance_service: Optional[PerformanceService] = None
trading_report_service: Optional[TradingReportService] = None # Nueva variable global
ai_orchestrator: Optional[AIOrchestrator] = None
mobula_adapter: Optional[MobulaAdapter] = None
llm_provider: Optional[ChatGoogleGenerativeAI] = None
user_configuration: Optional[UserConfiguration] = None


# Las funciones get_..._service ahora están en dependencies.py

async def initialize_services() -> None:
    """
    Inicializa todos los servicios necesarios para la aplicación.
    
    Raises:
        Exception: Si falla la inicialización de algún servicio crítico.
    """
    global credential_service, notification_service, binance_adapter, market_data_service
    global persistence_service, portfolio_service, config_service, order_execution_service
    global paper_order_execution_service, unified_order_execution_service, trading_engine_service
    global strategy_service, performance_service, trading_report_service, ai_orchestrator, mobula_adapter # trading_report_service añadido
    global llm_provider, user_configuration
    
    logger.info("Iniciando UltiBot Backend...")
    
    try:
        # Obtener clave de encriptación desde configuración
        effective_encryption_key = settings.CREDENTIAL_ENCRYPTION_KEY
        if not effective_encryption_key:
            logger.error("CREDENTIAL_ENCRYPTION_KEY no está configurada")
            raise ValueError("CREDENTIAL_ENCRYPTION_KEY es requerida")

        # 1. Inicializar servicios base
        logger.info("Inicializando servicios base...")
        global persistence_service, credential_service, binance_adapter # Asegurar que las globales se actualizan
        persistence_service = SupabasePersistenceService()
        await persistence_service.connect()
        deps.set_persistence_service(persistence_service)
        
        # BinanceAdapter debe estar inicializado antes de CredentialService si se va a pasar
        binance_adapter = BinanceAdapter()
        deps.set_binance_adapter(binance_adapter) # Asegurar que se establece en deps si otros lo usan desde ahí
        
        credential_service = CredentialService(
            persistence_service=persistence_service,
            binance_adapter=binance_adapter
        )
        deps.set_credential_service(credential_service)
        
        # 2. Inicializar servicios dependientes
        logger.info("Inicializando servicios dependientes...")
        global market_data_service, portfolio_service # Asegurar que las globales se actualizan
        market_data_service = MarketDataService(
            credential_service=credential_service,
            binance_adapter=binance_adapter
        )
        deps.set_market_data_service(market_data_service)
        
        portfolio_service = PortfolioService(
            market_data_service=market_data_service,
            persistence_service=persistence_service
        )
        deps.set_portfolio_service(portfolio_service)
        
        # 3. Inicializar configuración (con dependency injection pattern)
        global config_service, notification_service # Asegurar que las globales se actualizan
        config_service = ConfigService(
            persistence_service=persistence_service,
            credential_service=credential_service,
            portfolio_service=portfolio_service
        )
        deps.set_config_service(config_service)
        
        notification_service = NotificationService(
            credential_service=credential_service,
            persistence_service=persistence_service,
            config_service=config_service
        )
        deps.set_notification_service(notification_service)
        
        # Inyectar notification_service en config_service
        config_service.set_notification_service(notification_service)
        
        # 4. Inicializar servicios de trading
        logger.info("Inicializando servicios de trading...")
        global order_execution_service, paper_order_execution_service, unified_order_execution_service # Asegurar
        global strategy_service, configuration_service # Asegurar
        order_execution_service = OrderExecutionService(binance_adapter=binance_adapter)
        paper_order_execution_service = PaperOrderExecutionService()
        
        unified_order_execution_service = UnifiedOrderExecutionService(
            real_execution_service=order_execution_service,
            paper_execution_service=paper_order_execution_service
        )
        deps.set_unified_order_execution_service(unified_order_execution_service)
        
        strategy_service = StrategyService(persistence_service=persistence_service)
        deps.set_strategy_service(strategy_service)
        
        configuration_service = ConfigurationService(persistence_service=persistence_service)
        
        # 5. Inicializar servicios avanzados
        logger.info("Inicializando servicios avanzados...")
        global performance_service # Asegurar
        if persistence_service and strategy_service:
            performance_service = PerformanceService(
                persistence_service=persistence_service,
                strategy_service=strategy_service
            )
            deps.set_performance_service(performance_service)
            logger.info("PerformanceService inicializado.")
        else:
            logger.error("No se pudo inicializar PerformanceService")
            performance_service = None
            # deps.set_performance_service(None) # Opcional, si se quiere registrar explícitamente el None
        
        # 6. Inicializar adaptadores externos
        global mobula_adapter # Asegurar
        mobula_adapter = MobulaAdapter(credential_service=credential_service)
        
        # 7. Inicializar LLM Provider
        try:
            # Usar la clave de API de Gemini si está disponible en las settings
            if settings.GEMINI_API_KEY:
                llm_provider = ChatGoogleGenerativeAI(
                    model="gemini-pro", 
                    temperature=0.7, 
                    google_api_key=settings.GEMINI_API_KEY
                )
                logger.info("LLM Provider (ChatGoogleGenerativeAI) inicializado con GEMINI_API_KEY.")
            else:
                # Si no hay GEMINI_API_KEY, intentar con credenciales por defecto (ADC)
                llm_provider = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
                logger.info("LLM Provider (ChatGoogleGenerativeAI) inicializado sin GEMINI_API_KEY explícita (usando ADC).")
            
        except Exception as e:
            logger.error(f"Error al inicializar LLM Provider: {e}")
            llm_provider = None
        
        # 8. Inicializar AI Orchestrator
        # credential_service es inicializado incondicionalmente antes.
        # Se asume que AIOrchestrator requiere credential_service y su constructor
        # lanzará una excepción si falla la inicialización.
        ai_orchestrator = AIOrchestrator() # Eliminado credential_service
        logger.info("AIOrchestrator inicializado.")

        # 8.b Inicializar TradingReportService (después de persistence_service)
        if persistence_service:
            trading_report_service = TradingReportService(persistence_service=persistence_service)
            deps.set_trading_report_service(trading_report_service)
            logger.info("TradingReportService inicializado.")
        else:
            logger.error("No se pudo inicializar TradingReportService porque persistence_service no está disponible.")
            trading_report_service = None
        
        # 9. Inicializar Trading Engine
        # Se asume que TradingEngine requiere una instancia válida de AIOrchestrator.
        trading_engine_service = TradingEngine(
            strategy_service=strategy_service,
            configuration_service=configuration_service,
            ai_orchestrator=ai_orchestrator
        )
        deps.trading_engine_instance = trading_engine_service
        
        logger.info("Todos los servicios principales inicializados.")
        
        # 10. Cargar configuración de usuario
        await load_user_configuration()
        
        # 11. Verificar credenciales de Telegram si están disponibles
        await verify_telegram_credentials()
        
    except Exception as e:
        logger.error(f"Error durante la inicialización de servicios: {e}", exc_info=True)
        raise


async def load_user_configuration() -> None:
    """Carga la configuración del usuario al inicio."""
    global user_configuration
    
    if not config_service:
        logger.error("ConfigService no inicializado al intentar cargar la configuración del usuario.")
        user_configuration = None # O manejar de otra forma
        return

    try:
        user_configuration = await config_service.get_user_configuration(
            user_id_str=str(settings.FIXED_USER_ID)
        )
        logger.info(f"Configuración de usuario cargada para {settings.FIXED_USER_ID}.")
    except Exception as e:
        logger.error(f"Error al cargar configuración de usuario: {e}", exc_info=True)
        # Asegurarse que config_service existe antes de llamar a get_default_configuration
        user_configuration = config_service.get_default_configuration(user_id=settings.FIXED_USER_ID)
        logger.warning("Se utilizará la configuración por defecto.")


async def verify_telegram_credentials() -> None:
    """Verifica las credenciales de Telegram si están disponibles."""
    if not settings.DATABASE_URL:
        logger.warning("DATABASE_URL no configurada. Omitiendo verificación de Telegram.")
        return

    if not credential_service:
        logger.error("CredentialService no inicializado al intentar verificar credenciales de Telegram.")
        return
    
    try:
        telegram_credential = await credential_service.get_credential(
            user_id=settings.FIXED_USER_ID,
            service_name=ServiceName.TELEGRAM_BOT,
            credential_label="default_telegram_bot"
        )
        
        if telegram_credential:
            logger.info(f"Credenciales de Telegram encontradas para {settings.FIXED_USER_ID}.")
            # Asegurarse que notification_service existe si es necesario para verify_credential
            if not notification_service:
                logger.warning("NotificationService no disponible para la verificación de credenciales de Telegram.")
                is_verified = False
            else:
                is_verified = await credential_service.verify_credential(
                    credential=telegram_credential,
                    notification_service=notification_service
                )
            
            if is_verified:
                logger.info("Verificación inicial de Telegram exitosa.")
            else:
                logger.warning("La verificación inicial de Telegram falló.")
        else:
            logger.info(f"No se encontraron credenciales de Telegram para {settings.FIXED_USER_ID}.")
            
    except Exception as e:
        logger.error(f"Error durante verificación de Telegram: {e}", exc_info=True)


async def cleanup_services() -> None:
    """Limpia y cierra todos los servicios."""
    logger.info("Iniciando limpieza de servicios...")
    
    cleanup_tasks = []
    
    if notification_service:
        cleanup_tasks.append(("NotificationService", notification_service.close()))
    
    if binance_adapter:
        cleanup_tasks.append(("BinanceAdapter", binance_adapter.close()))
    
    if persistence_service:
        cleanup_tasks.append(("PersistenceService", persistence_service.disconnect()))
    
    for service_name, cleanup_task in cleanup_tasks:
        try:
            await cleanup_task
            logger.info(f"{service_name} cerrado correctamente.")
        except Exception as e:
            logger.error(f"Error al cerrar {service_name}: {e}")
    
    logger.info("Limpieza de servicios completada.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación FastAPI.
    
    Args:
        app: Instancia de la aplicación FastAPI.
    """
    # Startup
    try:
        await initialize_services()
        logger.info("Aplicación iniciada correctamente.")
        yield
    except Exception as e:
        logger.error(f"Error durante el startup: {e}", exc_info=True)
        raise
    finally:
        # Shutdown
        await cleanup_services()
        logger.info("Aplicación cerrada correctamente.")


# Crear la aplicación FastAPI con lifespan
app = FastAPI(
    title="UltiBot Backend",
    description="Backend API para UltiBot - Sistema de Trading Automatizado",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware de logging de solicitudes básicas
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    logger.info(f"Middleware: Solicitud entrante: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"Middleware: Solicitud procesada: {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Middleware: Error procesando solicitud: {request.method} {request.url.path} - Error: {e}", exc_info=True)
        # Re-lanzar la excepción para que FastAPI la maneje como lo haría normalmente
        raise


@app.get("/", tags=["health"])
async def read_root():
    """Endpoint de salud básico."""
    return {
        "message": "Welcome to UltiBot Backend",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint detallado de verificación de salud."""
    try:
        # Verificar que los servicios críticos estén inicializados
        services_status = {
            "persistence_service": persistence_service is not None,
            "credential_service": credential_service is not None,
            "market_data_service": market_data_service is not None,
            "config_service": config_service is not None,
        }
        
        all_healthy = all(services_status.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "services": services_status,
            "timestamp": "2025-06-02"  # Se podría usar datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-06-02"
        }


# Incluir routers de endpoints
from .api.v1.endpoints import (
    binance_status,
    config,
    notifications,
    opportunities,
    performance,
    portfolio,
    reports,
    strategies, # <--- Añadir el router de strategies
    telegram_status,
    trades,
    gemini,  # <--- Añadir el nuevo endpoint
    trading, # <--- Añadir trading router
    market_data, # <--- Añadir market_data router
    capital_management, # <--- Añadir capital_management router
)

app.include_router(telegram_status.router, prefix="/api/v1", tags=["telegram"])
app.include_router(binance_status.router, prefix="/api/v1", tags=["binance"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
app.include_router(performance.router, prefix="/api/v1/performance", tags=["performance"])
app.include_router(opportunities.router, prefix="/api/v1", tags=["opportunities"])
app.include_router(gemini.router, prefix="/api/v1", tags=["gemini"])
app.include_router(strategies.router, prefix="/api/v1", tags=["strategies"])
app.include_router(trading.router, prefix="/api/v1", tags=["trading"])
app.include_router(market_data.router, prefix="/api/v1", tags=["market"])
app.include_router(capital_management, prefix="/api/v1/trading", tags=["capital-management"])
