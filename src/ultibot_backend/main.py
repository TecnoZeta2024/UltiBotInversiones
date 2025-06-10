import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.config import dictConfig
from typing import Any
import uuid

# Solución para Windows ProactorEventLoop con psycopg/asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from asgi_correlation_id import CorrelationIdMiddleware, correlation_id, CorrelationIdFilter

from src.ultibot_backend.api.v1.endpoints import (
    config, market_data, market_configuration, notifications, opportunities,
    performance, portfolio, reports, strategies, trades, trading, trading_mode
)
from src.ultibot_backend.dependencies import get_container
from src.ultibot_backend.core.exceptions import UltiBotError

# --- Nueva Configuración de Logging ---
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Filtro para añadir correlation_id si no existe
class UuidCorrelationIdFilter(CorrelationIdFilter):
    def __init__(self, name: str = "", uuid_length: int = 32):
        super().__init__(name=name, uuid_length=uuid_length)
        self.uuid_length = uuid_length

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            cid = correlation_id.get()
            record.correlation_id = cid or uuid.uuid4().hex[:self.uuid_length]
        return True

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": UuidCorrelationIdFilter,
            "uuid_length": 12,
        },
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(threadName)s - %(filename)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "filters": ["correlation_id"],
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "ultibot_backend": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("ultibot_backend")
logger.info("Logging configurado exitosamente usando dictConfig.")
# --- Fin de la Nueva Configuración de Logging ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para manejar el ciclo de vida de la aplicación.
    """
    logger.info("Iniciando UltiBot Backend...")
    container = get_container()
    app.state.container = container
    try:
        logger.info("LIFESPAN: Inicializando contenedor de dependencias...")
        await container.initialize_services()
        logger.info("LIFESPAN: Contenedor de dependencias inicializado.")
        
    except Exception as e:
        logger.critical(f"LIFESPAN: Error fatal durante el arranque de la aplicación: {e}", exc_info=True)
        # Es crucial relanzar la excepción para que uvicorn sepa que el arranque falló.
        raise

    logger.info("LIFESPAN: Aplicación iniciada correctamente, cediendo el control (yield).")
    yield
    
    logger.info("LIFESPAN: Apagando UltiBot Backend...")
    await container.shutdown()
    logger.info("LIFESPAN: Recursos liberados y aplicación apagada.")

app = FastAPI(
    title="UltiBot Backend",
    description="El backend para la plataforma de trading algorítmico UltiBotInversiones.",
    version="1.0.0",
    lifespan=lifespan
)

# Añadir middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Middleware: Solicitud entrante: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Middleware: Solicitud procesada: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

@app.exception_handler(UltiBotError)
async def ultibot_exception_handler(request: Request, exc: UltiBotError):
    logger.error(f"Error de UltiBot: {exc.message} en {request.method} {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(f"Excepción no controlada en {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

# Registro explícito de cada router desde su módulo
api_prefix = "/api/v1"
logger.info("Registrando routers de la API...")
app.include_router(config.router, prefix=api_prefix, tags=["configuration"])
app.include_router(notifications.router, prefix=f"{api_prefix}/notifications", tags=["notifications"])
app.include_router(reports.router, prefix=f"{api_prefix}/reports", tags=["reports"])
app.include_router(portfolio.router, prefix=f"{api_prefix}/portfolio", tags=["portfolio"])
app.include_router(trades.router, prefix=f"{api_prefix}/trades", tags=["trades"])
app.include_router(performance.router, prefix=f"{api_prefix}/performance", tags=["performance"])
app.include_router(opportunities.router, prefix=f"{api_prefix}/opportunities", tags=["opportunities"])
app.include_router(strategies.router, prefix=f"{api_prefix}/strategies", tags=["strategies"])
app.include_router(trading.router, prefix=f"{api_prefix}/trading", tags=["trading"])
app.include_router(market_data.router, prefix=f"{api_prefix}/market", tags=["market_data"])
app.include_router(market_configuration.router, prefix=api_prefix, tags=["market_configuration"])
app.include_router(trading_mode.router, prefix=api_prefix, tags=["trading_mode"])
logger.info("Todos los routers han sido registrados.")


@app.get("/health", tags=["health"])
def health_check():
    """Endpoint de salud para verificar que la aplicación está en funcionamiento."""
    logger.debug("Health check solicitado.")
    return {"status": "ok"}
