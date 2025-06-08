import logging
from typing import Any, Dict, Optional, List
from uuid import UUID
import httpx

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

class UltiBotAPIClient:
    """Cliente para interactuar con la API del backend de UltiBot."""

    def __init__(self, base_url: str, client: httpx.AsyncClient):
        self._base_url = base_url
        self._client = client
        logger.debug(f"API base URL set to: {self._base_url}")

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self._base_url}{endpoint}"
        try:
            logger.debug(f"APIClient: _make_request invocado para {method} {endpoint}")
            response = await self._client.request(method, url, **kwargs)
            
            logger.info(f"HTTP Request: {method} {url} \"HTTP/{response.http_version} {response.status_code} {response.reason_phrase}\"")

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code} para {method} {url}: {e.response.text}")
            raise APIError(
                message=e.response.json().get("detail", e.response.text),
                status_code=e.response.status_code
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Error de red para {method} {url}: {e}")
            raise APIError(f"Error de conexión: {e}") from e

    async def get_user_configuration(self) -> Dict[str, Any]:
        logger.info("Obteniendo configuración de usuario.")
        return await self._make_request("GET", "/api/v1/config")

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Dict[str, Any]:
        logger.info(f"Obteniendo snapshot del portafolio para {user_id}, modo: {trading_mode}")
        params = {"user_id": str(user_id), "trading_mode": trading_mode}
        return await self._make_request("GET", "/api/v1/portfolio/snapshot", params=params)

    async def get_trades(self, trading_mode: str, status: str = 'open', limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"trading_mode": trading_mode, "limit": limit, "offset": offset, "status": status}
        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", "/api/v1/trades", params=params)

    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"symbol": symbol, "timeframe": timeframe, "limit": limit}
        return await self._make_request("GET", "/api/v1/market/ohlcv", params=params)

    async def get_ai_opportunities(self) -> List[Dict[str, Any]]:
        return await self._make_request("GET", "/api/v1/opportunities/ai")
