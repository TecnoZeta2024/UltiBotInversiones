"""
Servicio para interactuar con la API del backend de UltiBotInversiones.
"""

import logging
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Excepción personalizada para errores de API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_json: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_json = response_json

    def __str__(self):
        return f"APIError(status_code={self.status_code}, message='{self.message}', response_json={self.response_json})"

class UltiBotAPIClient:
    """
    Cliente para interactuar con la API REST del backend de UltiBotInversiones.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        import os
        if os.environ.get('RUNNING_IN_DOCKER', '').lower() == 'true':
            self.base_url = 'http://backend:8000'
        else:
            self.base_url = base_url
        self.timeout = 30.0
        self.token = token
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, headers=headers)

    async def aclose(self) -> None:
        if not self.client.is_closed:
            logger.info("Cerrando httpx.AsyncClient...")
            await self.client.aclose()
            logger.info("httpx.AsyncClient cerrado.")
        else:
            logger.info("httpx.AsyncClient ya estaba cerrado.")

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        logger.debug(f"APIClient: _make_request_invoked for {method} {endpoint}")
        url = f"{self.base_url}{endpoint}"
        request_headers = kwargs.pop("headers", {}) 
        if self.token:
            request_headers["Authorization"] = f"Bearer {self.token}"

        try:
            response = await self.client.request(method, endpoint, headers=request_headers, **kwargs)
            response.raise_for_status()

            if response.status_code == 204:
                return None
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {method} {url}: {e.response.text}")
            response_body_json = None
            try:
                response_body_json = e.response.json()
            except Exception:
                pass
            raise APIError(
                message=f"API request failed with status {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
                response_json=response_body_json
            )
        except httpx.RequestError as e:
            logger.error(f"Request error for {method} {url}: {e}")
            raise APIError(message=f"Failed to connect to API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {e}", exc_info=True)
            raise APIError(message=f"Unexpected error: {str(e)}")

    async def get_user_configuration(self) -> Dict[str, Any]:
        logger.info("Obteniendo configuración de usuario.")
        return await self._make_request("GET", "/api/v1/config")

    async def update_user_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Actualizando configuración de usuario: {config_data}")
        return await self._make_request("PATCH", "/api/v1/config", json=config_data)

    async def get_portfolio_snapshot(self, trading_mode: str = "both") -> Dict[str, Any]:
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo snapshot de portafolio, modo: {trading_mode}")
        return await self._make_request("GET", "/api/v1/portfolio/snapshot", params=params)
    
    async def get_portfolio_summary(self, trading_mode: str = "paper") -> Dict[str, Any]:
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo resumen de portafolio, modo: {trading_mode}")
        return await self._make_request("GET", "/api/v1/portfolio/summary", params=params)
    
    async def get_available_balance(self, trading_mode: str = "paper") -> Dict[str, Any]:
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo saldo disponible, modo: {trading_mode}")
        return await self._make_request("GET", "/api/v1/portfolio/balance", params=params)

    async def get_user_trades(
        self,
        trading_mode: str = "both",
        status_filter: Optional[str] = None,
        symbol_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        params = {
            "trading_mode": trading_mode,
            "limit": limit,
            "offset": offset
        }
        if status_filter:
            params["status_filter"] = status_filter
        if symbol_filter:
            params["symbol_filter"] = symbol_filter
        if date_from:
            params["date_from"] = date_from.date().isoformat()
        if date_to:
            params["date_to"] = date_to.date().isoformat()
        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", "/api/v1/trades/", params=params)

    async def get_open_trades_by_mode(self, trading_mode: str = "both") -> List[Dict[str, Any]]:
        params = {"trading_mode": trading_mode}
        logger.info(f"Obteniendo trades abiertos, modo: {trading_mode}")
        return await self._make_request("GET", "/api/v1/trades/open", params=params)

    async def get_notification_history(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        logger.info(f"Obteniendo historial de notificaciones con paginación: limit={limit}, offset={offset}")
        return await self._make_request("GET", "/api/v1/notifications/history", params=params)

    async def get_ticker_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
        if not symbols:
            return []
        params = {"symbols": ",".join(symbols)}
        logger.info(f"Obteniendo datos de ticker para símbolos: {symbols}")
        return await self._make_request("GET", "/api/v1/market/tickers", params=params)

    async def get_candlestick_data(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"symbol": symbol, "interval": interval}
        if start_time is not None:
            params["start_time"] = int(start_time.timestamp() * 1000)
        if end_time is not None:
            params["end_time"] = int(end_time.timestamp() * 1000)
        if limit is not None:
            params["limit"] = limit
        logger.info(f"Obteniendo datos de velas para {symbol} ({interval}) con parámetros: {params}")
        return await self._make_request("GET", "/api/v1/market/klines", params=params)

    async def get_real_trading_candidates(self) -> List[Dict[str, Any]]:
        logger.info("Obteniendo oportunidades de trading real pendientes de confirmación.")
        return await self._make_request("GET", "/api/v1/opportunities/real-trading-candidates")

    async def confirm_real_trade_opportunity(self, opportunity_id: UUID) -> Dict[str, Any]:
        logger.info(f"Confirmando oportunidad de trading real {opportunity_id}.")
        return await self._make_request(
            "POST",
            f"/api/v1/trading/real/confirm-opportunity/{opportunity_id}"
        )

    async def get_real_trading_mode_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del modo de operativa real limitada y el contador.
        """
        logger.info("Obteniendo estado del modo de operativa real limitada.")
        return await self._make_request("GET", "/api/v1/config/real-trading-mode/status")

    async def activate_real_trading_mode(self) -> Dict[str, Any]:
        """
        Activa el modo de operativa real limitada.
        """
        logger.info("Activando modo de operativa real limitada.")
        return await self._make_request("POST", "/api/v1/config/real-trading-mode/activate")

    async def deactivate_real_trading_mode(self) -> Dict[str, Any]:
        """
        Desactiva el modo de operativa real limitada.
        """
        logger.info("Desactivando modo de operativa real limitada.")
        return await self._make_request("POST", "/api/v1/config/real-trading-mode/deactivate")
