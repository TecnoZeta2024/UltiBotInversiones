import logging
from typing import Any, Dict, Optional, List
from uuid import UUID
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from src.shared.data_types import PerformanceMetrics, Trade

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Excepción personalizada para errores de la API."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"Error de API ({self.status_code}): {self.message}"
        return f"Error de API: {self.message}"

def is_connection_error(exception: BaseException) -> bool:
    """Filtro para tenacity: reintentar solo si es un error de conexión, no un error HTTP."""
    return isinstance(exception, APIError) and exception.status_code is None

class UltiBotAPIClient:
    """Cliente para interactuar con la API del backend de UltiBot."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        logger.debug(f"API client initialized with shared httpx client.")
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = endpoint
        try:
            logger.debug(f"APIClient: _make_request invocado para {method} {url}")
            print(f"Intentando conectar a: {self._client.base_url}{url}")
            
            response = await self._client.request(method, url, **kwargs)
            
            logger.info(f"HTTP Request: {method} {url} \"HTTP/{response.http_version} {response.status_code} {response.reason_phrase}\"")
            print(f"Respuesta recibida: Estado {response.status_code} {response.reason_phrase}")

            response.raise_for_status()
            data = response.json()
            logger.debug(f"Datos recibidos: {data}")
            return data
        except httpx.HTTPStatusError as e:
            error_msg = f"Error HTTP {e.response.status_code} para {method} {url}: {e.response.text}"
            logger.error(error_msg)
            print(f"ERROR API: {error_msg}")
            try:
                detail = e.response.json().get("detail", e.response.text)
            except ValueError:
                detail = e.response.text
            raise APIError(
                message=detail,
                status_code=e.response.status_code
            ) from e
        except httpx.RequestError as e:
            error_msg = f"Error de red para {method} {url}: {e}"
            logger.error(error_msg)
            print(f"ERROR DE CONEXIÓN: {error_msg}")
            raise APIError(f"Error de conexión: {e}") from e
        except Exception as e:
            error_msg = f"Error inesperado durante la petición a {url}: {str(e)}"
            logger.critical(error_msg, exc_info=True)
            print(f"ERROR CRÍTICO: {error_msg}")
            raise APIError(f"Error inesperado: {str(e)}") from e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(APIError),
        before_sleep=lambda retry_state: logger.info(f"Reintentando conexión al backend... intento {retry_state.attempt_number}")
    )
    async def get_user_configuration(self) -> Dict[str, Any]:
        logger.info("Obteniendo configuración de usuario.")
        print("Solicitando configuración de usuario al backend...")
        return await self._make_request("GET", "/api/v1/config")

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Dict[str, Any]:
        logger.info(f"Obteniendo snapshot del portafolio para {user_id}, modo: {trading_mode}")
        params = {"user_id": str(user_id), "trading_mode": trading_mode}
        return await self._make_request("GET", "/api/v1/portfolio/snapshot", params=params)

    async def get_trades(self, trading_mode: str, **kwargs) -> List[Dict[str, Any]]:
        params = {"trading_mode": trading_mode, **kwargs}
        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", "/api/v1/trades", params=params)

    async def get_trading_performance(self, trading_mode: str, **kwargs) -> Dict[str, Any]:
        params = {"trading_mode": trading_mode, **kwargs}
        return await self._make_request("GET", "/api/v1/trading/performance", params=params)

    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"symbol": symbol, "timeframe": timeframe, "limit": limit}
        return await self._make_request("GET", "/api/v1/market/ohlcv", params=params)

    async def get_ai_opportunities(self) -> List[Dict[str, Any]]:
        return await self._make_request("GET", "/api/v1/opportunities/ai")

    async def get_strategies(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de estrategias de IA disponibles."""
        return await self._make_request("GET", "/api/v1/strategies/ai")
