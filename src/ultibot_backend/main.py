import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.adapters.mobula_adapter import MobulaAdapter
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.api.v1.endpoints import (
    auth, capital_management, config, market_data, notifications, opportunities,
    performance, portfolio, reports, strategies, trades, trading
)
from src.ultibot_backend.app_config import settings
from src.ultibot_backend.security.core import get_password_hash
from src.ultibot_backend.security.schemas import UserCreate
from src.ultibot_backend.services.ai_orchestrator_service import AIOrchestrator
from src.ultibot_backend.services.configuration_service import ConfigurationService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService, PaperOrderExecutionService
from src.ultibot_backend.services.performance_service import PerformanceService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.services.trading_engine_service import TradingEngine
from src.ultibot_backend.services.trading_report_service import TradingReportService
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService

# Solución para Windows ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configuración del logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = 'logs/backend.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=1)
handler.setFormatter(log_formatter)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Logging configurado con RotatingFileHandler para escribir en {log_file} (max ~100KB).")

async def create_admin_user_on_startup():
    """Verifica y crea el usuario administrador si no existe."""
    logger.info("Verificando/creando usuario administrador en el arranque...")
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        logger.warning("ADMIN_EMAIL o ADMIN_PASSWORD no están configurados en .env. Saltando creación de usuario admin.")
        return

    db_service = SupabasePersistenceService()
    await db_service.connect()

    try:
        existing_user = await db_service.get_user_by_email(admin_email)
        if existing_user:
            logger.info(f"Usuario administrador '{admin_email}' ya existe.")
        else:
            logger.info(f"Usuario administrador '{admin_email}' no encontrado, creándolo...")
            hashed_password = get_password_hash(admin_password)
            user_in = UserCreate(
                email=admin_email,
                password=admin_password,
                is_active=True,
                is_superuser=True
            )
            await db_service.create_user(user_in=user_in, hashed_password=hashed_password)
            logger.info(f"Usuario administrador '{admin_email}' creado exitosamente.")
    except Exception as e:
        logger.error(f"Error durante la creación del usuario administrador: {e}", exc_info=True)
    finally:
        await db_service.disconnect()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para manejar el ciclo de vida de la aplicación.
    """
    logger.info("Iniciando UltiBot Backend...")
    
    await create_admin_user_on_startup()

    # Inicialización de servicios y almacenamiento en app.state
    logger.info("Inicializando servicios...")
    app.state.persistence_service = SupabasePersistenceService()
    await app.state.persistence_service.connect()
    
    app.state.binance_adapter = BinanceAdapter()
    
    app.state.credential_service = CredentialService(
        persistence_service=app.state.persistence_service,
        binance_adapter=app.state.binance_adapter
    )
    
    app.state.mobula_adapter = MobulaAdapter(credential_service=app.state.credential_service)

    app.state.configuration_service = ConfigurationService(persistence_service=app.state.persistence_service)

    app.state.market_data_service = MarketDataService(
        credential_service=app.state.credential_service,
        binance_adapter=app.state.binance_adapter
    )
    
    app.state.portfolio_service = PortfolioService(persistence_service=app.state.persistence_service)
    
    app.state.notification_service = NotificationService(
        credential_service=app.state.credential_service,
        persistence_service=app.state.persistence_service,
        config_service=app.state.configuration_service
    )

    paper_order_execution_service = PaperOrderExecutionService()
    real_order_execution_service = OrderExecutionService(binance_adapter=app.state.binance_adapter)
    
    app.state.unified_order_execution_service = UnifiedOrderExecutionService(
        paper_execution_service=paper_order_execution_service,
        real_execution_service=real_order_execution_service
    )

    app.state.performance_service = PerformanceService(persistence_service=app.state.persistence_service)
    app.state.ai_orchestrator = AIOrchestrator()
    
    app.state.strategy_service = StrategyService(
        persistence_service=app.state.persistence_service,
        configuration_service=app.state.configuration_service
    )

    app.state.trading_report_service = TradingReportService(
        persistence_service=app.state.persistence_service
    )

    app.state.trading_engine = TradingEngine(
        persistence_service=app.state.persistence_service,
        market_data_service=app.state.market_data_service,
        unified_order_execution_service=app.state.unified_order_execution_service,
        credential_service=app.state.credential_service,
        notification_service=app.state.notification_service,
        ai_orchestrator=app.state.ai_orchestrator,
        strategy_service=app.state.strategy_service,
        configuration_service=app.state.configuration_service,
        portfolio_service=app.state.portfolio_service
    )
    
    logger.info("Todos los servicios principales inicializados y almacenados en app.state.")

    logger.info("Aplicación iniciada correctamente.")
    yield
    
    # Código de limpieza al apagar
    logger.info("Apagando UltiBot Backend...")
    await app.state.persistence_service.disconnect()
    logger.info("Desconectado de la base de datos.")

app = FastAPI(
    title="UltiBot Backend",
    description="El backend para la plataforma de trading algorítmico UltiBotInversiones.",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Middleware: Solicitud entrante: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Middleware: Solicitud procesada: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

# Middleware para manejar excepciones no controladas
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Excepción no controlada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de la API
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(config.router, prefix="/api/v1", tags=["configuration"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(trades.router, prefix="/api/v1", tags=["trades"])
app.include_router(performance.router, prefix="/api/v1", tags=["performance"])
app.include_router(opportunities.router, prefix="/api/v1", tags=["opportunities"])
app.include_router(strategies.router, prefix="/api/v1", tags=["strategies"])
app.include_router(trading.router, prefix="/api/v1", tags=["trading"])
app.include_router(market_data.router, prefix="/api/v1", tags=["market_data"])
app.include_router(capital_management.router, prefix="/api/v1", tags=["capital_management"])

@app.get("/health", tags=["health"])
def health_check():
    """
    Endpoint para verificar la salud del servicio.
    """
    return {"status": "ok"}
