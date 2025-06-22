import os
import logging

logger = logging.getLogger(__name__)

def get_api_base_url() -> str:
    """
    Obtiene la URL base para la API del backend desde las variables de entorno.
    """
    # La URL por defecto apunta al servicio backend definido en docker-compose.yml
    # o al que se ejecuta localmente.
    default_url = "http://localhost:8000"
    api_url = os.getenv("ULTIBOT_API_URL", default_url)
    logger.debug(f"API base URL is set to: {api_url}")
    return api_url
