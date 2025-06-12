"""
Punto de entrada principal para la aplicación de backend FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from asgi_correlation_id import CorrelationIdMiddleware

from src.ultibot_backend.api.v1.router import api_router
from src.ultibot_backend.app_config import (
    get_app_settings,
    get_uvicorn_config,
    setup_logging,
)

# Configuración inicial
config = get_app_settings()
setup_logging(config)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para la vida de la aplicación.
    Se ejecuta al iniciar y al apagar.
    """
    logger.info("Iniciando UltiBot Backend...")
    # Las dependencias ahora se manejan por endpoint con Depends(),
    # no se necesita un inyector global en el estado de la app.
    yield
    logger.info("Apagando UltiBot Backend...")

def create_app() -> FastAPI:
    """
    Crea y configura la instancia de la aplicación FastAPI.
    """
    app = FastAPI(
        title=config.PROJECT_NAME,
        version=config.VERSION,
        description=config.DESCRIPTION,
        lifespan=lifespan,
    )

    # Middlewares
    app.add_middleware(CorrelationIdMiddleware)

    # Incluir routers de la API
    app.include_router(api_router, prefix=config.API_V1_STR)

    logger.info("Aplicación FastAPI creada y configurada.")
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn_config = get_uvicorn_config()
    
    logger.info(
        f"Iniciando servidor Uvicorn en "
        f"{uvicorn_config.host}:{uvicorn_config.port}"
    )
    
    uvicorn.run(
        "src.ultibot_backend.main:app",
        host=uvicorn_config.host,
        port=uvicorn_config.port,
        reload=uvicorn_config.reload,
        log_level=uvicorn_config.log_level.lower(),
    )
