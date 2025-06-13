"""
Adaptador para la API de Mobula.

Este adaptador se encarga de obtener datos de mercado y de activos
desde el proveedor de datos Mobula.
"""

import logging
from typing import Dict, Any, List, Optional
import httpx

from ..core.exceptions import DataProviderError

logger = logging.getLogger(__name__)

class MobulaAdapter:
    """
    Adaptador para interactuar con la API de Mobula.
    """

    def __init__(self, api_key: str):
        """
        Inicializa el adaptador de Mobula.

        Args:
            api_key: La clave de API para autenticarse con Mobula.
        """
        if not api_key:
            raise ValueError("La clave de API de Mobula es obligatoria.")
        
        self.api_key = api_key
        self.base_url = "https://api.mobula.io/api/1"

    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de mercado para un símbolo específico.

        Args:
            symbol: El símbolo del activo (ej. BTC).

        Returns:
            Un diccionario con los datos de mercado o None si no se encuentra.
        
        Raises:
            DataProviderError: Si ocurre un error al contactar la API.
        """
        url = f"{self.base_url}/market/data"
        params = {"symbol": symbol}
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers, timeout=15.0)
                response.raise_for_status()
                data = response.json()
                
                if data and "data" in data:
                    logger.info(f"Datos de mercado obtenidos para {symbol} desde Mobula.")
                    return data["data"]
                
                logger.warning(f"No se encontraron datos de mercado para {symbol} en Mobula.")
                return None

        except httpx.HTTPStatusError as e:
            error_message = f"Error de estado HTTP al obtener datos de Mobula: {e.response.status_code}"
            logger.error(error_message)
            raise DataProviderError(error_message) from e
        except httpx.RequestError as e:
            error_message = f"Error de red al conectar con la API de Mobula: {e}"
            logger.error(error_message)
            raise DataProviderError(error_message) from e
        except Exception as e:
            error_message = f"Un error inesperado ocurrió con el adaptador de Mobula: {e}"
            logger.error(error_message)
            raise DataProviderError(error_message) from e

def create_mobula_adapter(api_key: str) -> "MobulaAdapter":
    """
    Factory function para crear una instancia de MobulaAdapter.

    Args:
        api_key: La clave de API de Mobula.

    Returns:
        Una instancia de MobulaAdapter.
    """
    return MobulaAdapter(api_key=api_key)
