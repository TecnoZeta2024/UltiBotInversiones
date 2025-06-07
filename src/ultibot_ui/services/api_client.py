import logging
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID
import httpx
from datetime import datetime

from src.shared.data_types import (
    UserConfiguration,
    Notification,
    Trade,
    PerformanceMetrics,
    AiStrategyConfiguration,
    Opportunity,
    Kline,
    RealTradingSettings,
    PortfolioSnapshot,
)

logger = logging.getLogger(__name__)

class APIError(Exception):
    def __init__(self, status_code: Optional[int], message: str, response_json: Optional[Dict] = None):
        self.status_code = status_code
        self.message = message
        self.response_json = response_json
        super().__init__(f"Error de API ({status_code}): {message}")

class UltiBotAPIClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        if token:
            self._client.headers["Authorization"] = f"Bearer {token}"

    async def aclose(self):
        """Cierra el cliente HTTP de forma segura."""
        if not self._client.is_closed:
            logger.info("Cerrando httpx.AsyncClient...")
            await self._client.aclose()
            logger.info("httpx.AsyncClient cerrado.")

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        logger.debug(f"APIClient: _make_request invocado para {method} {endpoint}")
        if self._client.is_closed:
            raise APIError(status_code=None, message="El cliente API está cerrado. No se pueden hacer peticiones.")
        try:
            request_headers = kwargs.pop("headers", {})
            response = await self._client.request(method, endpoint, headers=request_headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code} para {method} {e.request.url}: {e.response.text}")
            response_data = e.response.json() if e.response.content else {}
            raise APIError(
                status_code=e.response.status_code,
                message=response_data.get("detail", e.response.text),
                response_json=response_data,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Error de petición para {method} {e.request.url}: {str(e)}")
            raise APIError(status_code=None, message=f"Fallo al conectar con la API: {str(e)}") from e

    async def get_user_configuration(self) -> UserConfiguration:
        logger.info("Obteniendo configuración de usuario.")
        data = await self._make_request("GET", "/api/v1/config")
        return UserConfiguration(**data)

    async def update_user_configuration(self, config: UserConfiguration) -> UserConfiguration:
        logger.info(f"Actualizando configuración para el usuario: {config.id}")
        data = await self._make_request("PATCH", "/api/v1/config", json=config.model_dump(mode="json"))
        return UserConfiguration(**data)

    async def create_trade(self, symbol: str, side: str, quantity: float, trading_mode: str, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> Dict[str, Any]:
        """Crea una nueva orden de mercado (trade)."""
        logger.info(f"Creando una nueva orden: {side} {quantity} {symbol} en modo {trading_mode}")
        payload = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "trading_mode": trading_mode,
        }
        headers = {}
        if trading_mode == 'real' and api_key and api_secret:
            headers["X-API-Key"] = api_key
            headers["X-API-Secret"] = api_secret
            
        return await self._make_request("POST", "/api/v1/trades", json=payload, headers=headers)

    async def get_trades(
        self, trading_mode: Literal["paper", "real", "both"] = "both", limit: int = 100, offset: int = 0, **kwargs
    ) -> List[Trade]:
        params = {"trading_mode": trading_mode, "limit": limit, "offset": offset}
        params.update(kwargs)
        
        if 'date_from' in params and isinstance(params['date_from'], datetime):
            params['date_from'] = params['date_from'].date().isoformat()
        if 'date_to' in params and isinstance(params['date_to'], datetime):
            params['date_to'] = params['date_to'].date().isoformat()

        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        data = await self._make_request("GET", "/api/v1/trades", params=params)
        return [Trade(**item) for item in data]

    async def get_trading_performance(self, trading_mode: Literal["paper", "real"], **kwargs) -> PerformanceMetrics:
        params = {"trading_mode": trading_mode}
        params.update(kwargs)

        if 'date_from' in params and isinstance(params['date_from'], datetime):
            params['date_from'] = params['date_from'].date().isoformat()
        if 'date_to' in params and isinstance(params['date_to'], datetime):
            params['date_to'] = params['date_to'].date().isoformat()

        logger.info(f"Obteniendo métricas de desempeño, modo: {trading_mode} con filtros: {params}")
        data = await self._make_request("GET", "/api/v1/performance/metrics", params=params)
        return PerformanceMetrics(**data)

    async def get_notification_history(self, limit: int = 20, offset: int = 0) -> List[Notification]:
        params = {"limit": limit, "offset": offset}
        logger.info(f"Obteniendo historial de notificaciones con paginación: {params}")
        data = await self._make_request("GET", "/api/v1/notifications", params=params)
        return [Notification(**item) for item in data]

    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        logger.info(f"Obteniendo datos de mercado para los símbolos: {symbols}")
        data = await self._make_request("POST", "/api/v1/market/data", json={"symbols": symbols})
        return data

    async def get_candlestick_data(self, symbol: str, interval: str, limit: int = 200) -> List[Kline]:
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        logger.info(f"Obteniendo datos de velas para {symbol} ({interval}) con parámetros: {params}")
        data = await self._make_request("GET", "/api/v1/market/klines", params=params)
        return [Kline(**item) for item in data]

    async def get_strategies(self) -> List[AiStrategyConfiguration]:
        logger.info("Obteniendo estrategias de trading.")
        data = await self._make_request("GET", "/api/v1/strategies")
        return [AiStrategyConfiguration(**item) for item in data]

    async def get_strategy_details(self, strategy_id: str) -> AiStrategyConfiguration:
        logger.info(f"Obteniendo detalles para la estrategia: {strategy_id}")
        data = await self._make_request("GET", f"/api/v1/strategies/{strategy_id}")
        return AiStrategyConfiguration(**data)

    async def update_strategy_activation_status(self, strategy_id: str, mode: str, active: bool) -> None:
        logger.info(f"Actualizando estado de activación para estrategia {strategy_id}, modo {mode} a {active}")
        payload = {"mode": mode, "active": active}
        await self._make_request("PATCH", f"/api/v1/strategies/{strategy_id}/activation", json=payload)

    async def delete_strategy(self, strategy_id: str) -> None:
        logger.info(f"Eliminando estrategia: {strategy_id}")
        await self._make_request("DELETE", f"/api/v1/strategies/{strategy_id}")

    async def get_opportunities(self) -> List[Opportunity]:
        logger.info("Obteniendo oportunidades de trading.")
        data = await self._make_request("GET", "/api/v1/opportunities")
        return [Opportunity(**item) for item in data]

    async def get_gemini_opportunities(self) -> List[Opportunity]:
        logger.info("Obteniendo oportunidades de trading de Gemini.")
        data = await self._make_request("GET", "/api/v1/opportunities/candidates")
        return [Opportunity(**item) for item in data]

    async def get_real_trading_mode_status(self) -> RealTradingSettings:
        logger.info("Obteniendo estado del modo de trading real.")
        data = await self._make_request("GET", "/api/v1/config/real-trading-mode/status")
        return RealTradingSettings(**data)

    async def get_real_trading_candidates(self) -> List[Opportunity]:
        logger.info("Obteniendo candidatos para trading real.")
        data = await self._make_request("GET", "/api/v1/opportunities/candidates")
        return [Opportunity(**item) for item in data]

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> PortfolioSnapshot:
        logger.info(f"Obteniendo snapshot del portafolio para {user_id}, modo: {trading_mode}")
        params = {"user_id": str(user_id), "trading_mode": trading_mode}
        data = await self._make_request("GET", "/api/v1/portfolio/snapshot", params=params)
        return PortfolioSnapshot(**data)
