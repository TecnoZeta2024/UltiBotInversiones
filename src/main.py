import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.config import dictConfig
from typing import Any, Union

# Solución para Windows ProactorEventLoop con psycopg/asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute # Importar BaseRoute desde starlette

from api.v1.endpoints import (
    config, market_data, notifications, opportunities,
    performance, portfolio, reports, strategies, trades, trading
)
from dotenv import load_dotenv
from dependencies import DependencyContainer
from core.exceptions import UltiBotError

# Cargar variables de entorno desde .env al inicio
load_dotenv()

# --- Nueva Configuración de Logging ---
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "backend_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(LOGS_DIR, "backend.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        "frontend_file_mirror": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(LOGS_DIR, "frontend.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "backend_file"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["console", "backend_file"], "level": "INFO"},
        "ultibot_backend": {"handlers": ["console", "backend_file", "frontend_file_mirror"], "level": "DEBUG", "propagate": False},
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "backend_file"],
    },
}

# La configuración de logging se aplicará dentro del lifespan
# para evitar condiciones de carrera durante la importación.
logger = logging.getLogger("ultibot_backend")
# --- Fin de la Nueva Configuración de Logging ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para manejar el ciclo de vida de la aplicación.
    Crea y gestiona una única instancia del DependencyContainer.
    """
    # Configurar el logging aquí para asegurar que se hace una sola vez
    # y en el momento adecuado.
    dictConfig(LOGGING_CONFIG)
    
    logger.info("Iniciando UltiBot Backend (lifespan)...")
    
    # Instanciar el contenedor directamente aquí
    container = DependencyContainer()
    app.state.container = container  # Adjuntar a app.state
    logger.info(f"DependencyContainer adjuntado a app.state: {app.state.container is not None}")
    
    try:
        await container.initialize_services()
        logger.info("Contenedor de dependencias inicializado en lifespan.")
        
    except Exception as e:
        logger.critical(f"Error fatal durante el arranque de la aplicación (lifespan): {e}", exc_info=True)
        raise

    logger.info("Aplicación iniciada correctamente (lifespan).")
    yield
    
    logger.info("Apagando UltiBot Backend (lifespan)...")
    if hasattr(app.state, 'container') and app.state.container:
        await app.state.container.shutdown()
        logger.info("Recursos liberados y aplicación apagada (lifespan).")
    else:
        logger.warning("No se encontró DependencyContainer en app.state durante el apagado.")

def create_app() -> FastAPI:
    """
    Factory para crear y configurar la instancia de la aplicación FastAPI.
    """
    logger.info("Creando nueva instancia de FastAPI...")
    
    app_instance = FastAPI(
        title="UltiBot Backend",
        description="El backend para la plataforma de trading algorítmico UltiBotInversiones.",
        version="1.0.0",
        lifespan=lifespan,
        debug=os.environ.get("TESTING") == "True"
    )

    @app_instance.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Middleware: Solicitud entrante: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"Middleware: Solicitud procesada: {request.method} {request.url.path} - Status: {response.status_code}")
        return response

    @app_instance.exception_handler(UltiBotError)
    async def ultibot_exception_handler(request: Request, exc: UltiBotError):
        logger.error(f"Error de UltiBot: {exc.message} en {request.method} {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app_instance.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.critical(f"Excepción no controlada en {request.method} {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error interno inesperado en el servidor."},
        )

    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registro explícito de cada router desde su módulo
    api_prefix = "/api/v1"
    logger.info("Registrando routers de la API...")
    app_instance.include_router(config.router, prefix=api_prefix, tags=["configuration"])
    app_instance.include_router(strategies.router, prefix=api_prefix, tags=["strategies"]) # Mover strategies arriba
    app_instance.include_router(notifications.router, prefix=f"{api_prefix}/notifications", tags=["notifications"])
    app_instance.include_router(reports.router, prefix=api_prefix, tags=["reports"])
    app_instance.include_router(portfolio.router, prefix=f"{api_prefix}/portfolio", tags=["portfolio"])
    app_instance.include_router(trades.router, prefix=f"{api_prefix}/trades", tags=["trades"])
    app_instance.include_router(performance.router, prefix=f"{api_prefix}/performance", tags=["performance"])
    app_instance.include_router(opportunities.router, prefix=api_prefix, tags=["opportunities"])
    app_instance.include_router(trading.router, prefix=f"{api_prefix}/trading", tags=["trading"])
    app_instance.include_router(market_data.router, prefix=f"{api_prefix}/market", tags=["market_data"])
    logger.info("Todos los routers han sido registrados.")

    # Imprimir todas las rutas registradas para depuración
    logger.info("Rutas registradas en FastAPI:")
    for route in app_instance.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods) if route.methods else "ANY"
            logger.info(f"  - Path: {route.path}, Name: {route.name}, Methods: [{methods}]")
        else:
            logger.info(f"  - Ruta no APIRoute (Tipo: {type(route).__name__})")
            
    @app_instance.get("/health", tags=["health"])
    async def health_check():
        """Endpoint de salud con validaciones de dependencias críticas"""
        logger.info("Ejecutando health check extendido")
        
        # Obtener contenedor de dependencias desde el contexto de la app
        container = app_instance.state.container
        
        # Verificar estado de componentes críticos
        health_status = {
            "status": "ok",
            "components": {
                "database": "healthy",
                "redis": "healthy",
                "binance_api": "healthy"
            },
            "message": "Todos los componentes están operativos"
        }
        
        try:
            # Verificar conexión a base de datos a través del PersistenceService
            if not await container.persistence_service.test_connection():
                health_status["components"]["database"] = "unhealthy"
                logger.warning("Health check: Base de datos no respondiendo")
            
            # Verificar conexión a Redis
            if not await container.cache.ping():
                health_status["components"]["redis"] = "unhealthy"
                logger.warning("Health check: Redis no respondiendo")
            
            # Verificar conexión a Binance
            if not await container.binance_adapter.test_connection():
                health_status["components"]["binance_api"] = "unhealthy"
                logger.warning("Health check: API de Binance no disponible")
            
            # Si algún componente falla, ajustar mensaje y status
            if any(status != "healthy" for status in health_status["components"].values()):
                health_status["status"] = "partial"
                health_status["message"] = "Algunos componentes no están disponibles"
                
        except Exception as e:
            logger.error(f"Error durante health check: {str(e)}")
            return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})
            
        logger.info(f"Health check completado: {health_status['message']}")
        return JSONResponse(content=health_status, status_code=200)
        
    return app_instance

# Crear la instancia global de la aplicación para la ejecución normal (no para tests)
app = create_app()
logger.info("Instancia global de la aplicación creada.")

if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor Uvicorn desde el punto de entrada principal...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
