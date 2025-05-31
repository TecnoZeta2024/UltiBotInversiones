import httpx
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID

from src.ultibot_backend.services.credential_service import CredentialService, ServiceName
from src.ultibot_backend.core.exceptions import MobulaAPIError # Necesitaremos definir esta excepción

logger = logging.getLogger(__name__)

MOBULA_BASE_URL = "https://api.mobula.io/api/1"

class MobulaAdapter:
    def __init__(self, credential_service: CredentialService, http_client: Optional[httpx.AsyncClient] = None):
        self.credential_service = credential_service
        self.http_client = http_client if http_client else httpx.AsyncClient(timeout=10.0)
        self._api_key: Optional[str] = None

    async def _get_api_key(self, user_id: UUID) -> Optional[str]:
        if self._api_key is None:
            try:
                # Asumimos que el usuario tiene una credencial MOBULA_API configurada
                # y que CredentialService puede encontrarla por user_id y service_name.
                cred = await self.credential_service.get_first_decrypted_credential_by_service(
                    user_id=user_id,
                    service_name=ServiceName.MOBULA_API
                )
                if cred and cred.encrypted_api_key: # encrypted_api_key contiene el valor desencriptado
                    self._api_key = cred.encrypted_api_key
                else:
                    logger.warning(f"No se encontró API key de Mobula para el usuario {user_id}")
                    return None
            except Exception as e:
                logger.error(f"Error al obtener la API key de Mobula para el usuario {user_id}: {e}", exc_info=True)
                return None
        return self._api_key

    async def get_market_data(self, user_id: UUID, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de mercado para un símbolo de activo específico desde Mobula.
        Ejemplo: precio, volumen, capitalización de mercado.
        """
        api_key = await self._get_api_key(user_id)
        if not api_key:
            raise MobulaAPIError("API key de Mobula no disponible.")

        # Mobula podría necesitar buscar por nombre o símbolo.
        # Endpoint de ejemplo: /market/data?asset=Bitcoin o /search?name=BTC
        # Para este ejemplo, usaremos un endpoint hipotético /market/data con 'symbol' como query param.
        # La API real de Mobula debe ser consultada para los endpoints correctos.
        # Este es un placeholder basado en la funcionalidad esperada.
        
        # Primero, intentemos buscar el activo para obtener su ID si es necesario, o directamente obtener datos.
        # Asumamos un endpoint /search para encontrar el activo por símbolo.
        search_url = f"{MOBULA_BASE_URL}/search"
        headers = {"Authorization": f"Bearer {api_key}"} # O "X-API-Key": api_key, según la API
        params = {"name": symbol}

        try:
            logger.debug(f"Buscando activo en Mobula: {symbol}")
            response = await self.http_client.get(search_url, params=params, headers=headers)
            response.raise_for_status()
            search_results = response.json()
            
            if not search_results or not isinstance(search_results, list) or not search_results[0].get("id"):
                # Si la búsqueda devuelve una lista de activos, tomamos el primero.
                # O si devuelve directamente los datos del activo que mejor coincide.
                # Esto es una simplificación. Una implementación real necesitaría manejar múltiples resultados.
                # Si la API devuelve directamente los datos del activo en /search, esto cambiaría.
                # Por ahora, asumimos que necesitamos un ID o que la búsqueda ya da los datos.
                # Si la API de Mobula permite obtener datos directamente por símbolo en otro endpoint, se usaría ese.
                # Ejemplo: si /market/data?symbol=BTC funciona.
                
                # Vamos a asumir que el endpoint /market/data puede tomar un 'asset' que puede ser el símbolo
                market_data_url = f"{MOBULA_BASE_URL}/market/data"
                market_params = {"asset": symbol} # o {"symbol": symbol}
                
                logger.debug(f"Obteniendo datos de mercado de Mobula para: {symbol}")
                data_response = await self.http_client.get(market_data_url, params=market_params, headers=headers)
                data_response.raise_for_status()
                asset_data = data_response.json()

                # La estructura de asset_data dependerá de la respuesta real de Mobula.
                # Ejemplo esperado: {"price": 123.45, "volume_24h": 1000000, "market_cap": 50000000, ...}
                # Asegurarse de que la respuesta contenga los datos esperados.
                if isinstance(asset_data, list) and asset_data: # Si devuelve una lista de coincidencias
                    return asset_data[0].get("market_data") if asset_data[0].get("market_data") else asset_data[0]
                elif isinstance(asset_data, dict) and asset_data.get("data"): # Si la respuesta está anidada
                     # Ejemplo de estructura Mobula: { "data": { "asset_id": { "price": X, ... } } }
                     # O { "data": { "price": X, ... } } si es un solo activo
                    if isinstance(asset_data["data"], dict) and not asset_data["data"].get("price"): # Si es un dict de activos por ID
                        # Tomar el primer activo si hay varios
                        first_asset_key = next(iter(asset_data["data"]), None)
                        if first_asset_key:
                            return asset_data["data"][first_asset_key]
                        return None
                    return asset_data["data"] # Si es un solo activo
                elif isinstance(asset_data, dict):
                    return asset_data # Si es un dict plano

                logger.warning(f"No se encontraron datos de mercado para {symbol} en Mobula o formato inesperado.")
                return None

            # Si la búsqueda fue necesaria y obtuvimos un ID:
            # asset_id = search_results[0]["id"] 
            # market_data_url = f"{MOBULA_BASE_URL}/market/data?id={asset_id}" 
            # ... y luego hacer la llamada a market_data_url

        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP de Mobula al obtener datos para {symbol}: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise MobulaAPIError(f"Error HTTP de Mobula: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Error de red al contactar Mobula para {symbol}: {e}", exc_info=True)
            raise MobulaAPIError("Error de red contactando Mobula.") from e
        except Exception as e:
            logger.error(f"Error inesperado al obtener datos de Mobula para {symbol}: {e}", exc_info=True)
            raise MobulaAPIError("Error inesperado con Mobula.") from e
        
        return None # En caso de que no se encuentre nada después de la búsqueda inicial.

    async def close(self):
        """Cierra el cliente HTTP."""
        await self.http_client.aclose()
