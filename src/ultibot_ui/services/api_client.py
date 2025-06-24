import logging
import json
from decimal import Decimal
from typing import Any, Dict, Optional, List, Union
from uuid import UUID
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
    _instance: Optional["UltiBotAPIClient"] = None
    _client: Optional[httpx.AsyncClient] = None
    _base_url: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(UltiBotAPIClient, cls).__new__(cls)
            cls._instance._base_url = kwargs.get('base_url') # Guardar base_url para inicialización perezosa
            cls._instance._client = None # Asegurar que no se inicialice aquí
        return cls._instance

    def __init__(self, base_url: str):
        # El __init__ se llama cada vez que se instancia, pero solo queremos configurar el base_url una vez
        if self._base_url is None:
            self._base_url = base_url
        logger.debug(f"APIClient singleton: base URL establecida en {self._base_url}")

    @property
    def base_url(self) -> str:
        """Retorna la URL base del cliente API."""
        if self._base_url is None:
            raise RuntimeError("Base URL not set for UltiBotAPIClient.")
        return self._base_url

    async def initialize_client(self):
        """Inicializa el cliente httpx de forma asíncrona."""
        if self._client is None or self._client.is_closed:
            if self._base_url is None:
                raise RuntimeError("Base URL not set for UltiBotAPIClient.")
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)
            logger.debug(f"APIClient httpx client inicializado con base URL: {self._base_url}")
        else:
            logger.debug("APIClient httpx client ya está inicializado.")

    def _convert_decimals_to_floats(self, obj: Any) -> Any:
        """
        Convierte recursivamente objetos Decimal a float en diccionarios y listas.
        """
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals_to_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_floats(elem) for elem in obj]
        return obj

    async def close(self):
        """Cierra el cliente httpx."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("APIClient httpx client closed.")

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=lambda retry_state: logger.warning(
            f"Fallo de conexión, reintentando en {retry_state.idle_for:.2f}s... "
            f"(Intento {retry_state.attempt_number}) para {retry_state.args[1]}"
        )
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        # Asegurar que el cliente esté inicializado antes de cada solicitud
        await self.initialize_client()
        
        # Asegurar que self._client no es None después de la inicialización
        if self._client is None:
            raise RuntimeError("HTTP client failed to initialize.")

        url = f"{self._base_url}{endpoint}"
        try:
            logger.debug(f"APIClient: _make_request invocado para {method} {endpoint}")
            
            response = await self._client.request(method, endpoint, **kwargs)
            
            logger.info(f"HTTP Request: {method} {self._base_url}{endpoint} \"HTTP/{response.http_version} {response.status_code} {response.reason_phrase}\"")

            response.raise_for_status()
            
            # Decodificar la respuesta JSON y convertir Decimal a float
            json_response = response.json()
            processed_response = self._convert_decimals_to_floats(json_response)
            
            logger.debug(f"Response content (processed): {processed_response}")
            return processed_response
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP {e.response.status_code} para {method} {url}: {e.response.text}")
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except json.JSONDecodeError:
                error_detail = e.response.text
            raise APIError(
                message=error_detail,
                status_code=e.response.status_code
            ) from e
        except httpx.RequestError as e:
            logger.warning(f"Error de red para {method} {url}: {e}. Re-lanzando para posible reintento.")
            raise  # Re-lanza la excepción original para que tenacity la capture

    async def get_user_configuration(self) -> Dict[str, Any]:
        logger.info("Obteniendo configuración de usuario.")
        return await self._make_request("GET", "/api/v1/config")

    async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str) -> Dict[str, Any]:
        logger.info(f"Obteniendo snapshot del portafolio para {user_id}, modo: {trading_mode}")
        endpoint = f"/api/v1/portfolio/snapshot/{str(user_id)}"
        params = {"trading_mode": trading_mode}
        return await self._make_request("GET", endpoint, params=params)

    async def get_trades(self, trading_mode: str, status: str = 'open', limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"trading_mode": trading_mode, "limit": limit, "offset": offset, "status": status}
        logger.info(f"Obteniendo trades, modo: {trading_mode}, filtros: {params}")
        return await self._make_request("GET", "/api/v1/trades", params=params)

    async def get_ohlcv_data(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {"symbol": symbol, "timeframe": timeframe, "limit": limit}
        return await self._make_request("GET", "/api/v1/market/ohlcv", params=params)

    async def get_ai_opportunities(self) -> List[Dict[str, Any]]:
        return await self._make_request("GET", "/api/v1/opportunities/ai")

    async def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtiene el historial de notificaciones."""
        logger.info(f"Obteniendo historial de notificaciones, límite: {limit}")
        return await self._make_request("GET", "/api/v1/notifications", params={"limit": limit})

    async def execute_market_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una orden de mercado."""
        trading_mode = order_data.get("trading_mode")
        if trading_mode == "real" and not ("api_key" in order_data and "api_secret" in order_data):
            logger.error("Intento de orden real sin credenciales.")
            raise ValueError("API key y secret son requeridos para operaciones en modo real.")
        
        logger.info(f"Ejecutando orden de mercado en modo {trading_mode} para el símbolo {order_data.get('symbol')}.")
        return await self._make_request("POST", "/api/v1/trading/market-order", json=order_data)

    async def get_open_trades_by_mode(self, user_id: UUID, trading_mode: str) -> List[Dict[str, Any]]:
        """Obtiene las operaciones abiertas filtradas por modo de trading."""
        logger.info(f"Obteniendo trades abiertos para {user_id} en modo {trading_mode}.")
        return await self._make_request(
            "GET",
            f"/api/v1/trades/trades/{user_id}/open",
            params={"trading_mode": trading_mode}
        )

    async def create_order(self, symbol: str, order_type: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Crea una nueva orden."""
        order_data = {
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
        }
        if price is not None:
            order_data["price"] = price
        
        logger.info(f"Enviando nueva orden: {order_data}")
        return await self._make_request("POST", "/api/v1/orders/", json=order_data)
