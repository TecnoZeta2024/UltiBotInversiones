import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from typing import Any

# Solución para Windows ProactorEventLoop con psycopg/asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.ultibot_backend.api.v1.endpoints import (
    capital_management, config, market_data, notifications, opportunities,
    performance, portfolio, reports, strategies, trades, trading
)
from src.ultibot_backend.dependencies import get_container
from src.ultibot_backend.core.exceptions import UltiBotError

# Configuración del logging
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = 'logs/backend.log'
os.makedirs(os.path.dirname(log_file), exist_ok=True)
# Redirigir stdout y stderr a un archivo de log separado para Uvicorn
uvicorn_log_file = 'logs/backend_stdout.log'
try:
    uvicorn_log_stream = open(uvicorn_log_file, 'a')
    sys.stdout = uvicorn_log_stream
    sys.stderr = uvicorn_log_stream
except Exception as e:
    logging.error(f"No se pudo abrir el archivo de log para stdout/stderr: {e}")


handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=1)
handler.setFormatter(log_formatter)
# Capturar todo desde el nivel DEBUG hacia arriba
logging.basicConfig(level=logging.DEBUG, handlers=[handler])
logger = logging.getLogger(__name__)
logger.info(f"Logging configurado con RotatingFileHandler para escribir en {log_file} (max ~100KB).")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para manejar el ciclo de vida de la aplicación.
    """
    logger.info("Iniciando UltiBot Backend...")
    container = get_container()
    app.state.container = container
    try:
        await container.initialize_services()
        logger.info("Contenedor de dependencias inicializado.")
        
    except Exception as e:
        logger.critical(f"Error fatal durante el arranque de la aplicación: {e}", exc_info=True)
        raise

    logger.info("Aplicación iniciada correctamente.")
    yield
    
    logger.info("Apagando UltiBot Backend...")
    await container.shutdown()
    logger.info("Recursos liberados y aplicación apagada.")

app = FastAPI(
    title="UltiBot Backend",
    description="El backend para la plataforma de trading algorítmico UltiBotInversiones.",
    version="1.0.0",
    lifespan=lifespan
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Middleware: Solicitud entrante: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Middleware: Solicitud procesada: {request.method} {request.url.path} - Status: {response.status_code}")
    return response

@app.exception_handler(UltiBotError)
async def ultibot_exception_handler(request: Request, exc: UltiBotError):
    logger.error(f"Error de UltiBot: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Excepción no controlada: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocurrió un error interno inesperado en el servidor."},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro explícito de cada router desde su módulo
api_prefix = "/api/v1"
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
app.include_router(capital_management.router, prefix=f"{api_prefix}/capital", tags=["capital_management"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
