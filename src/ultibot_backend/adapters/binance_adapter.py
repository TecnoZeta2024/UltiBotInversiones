import asyncio
import logging
from typing import Any, AsyncGenerator, Callable, Coroutine, Dict, List, Optional
import httpx
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException as BinanceLibAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.ultibot_backend.core.exceptions import BinanceAPIError, ExternalAPIError

logger = logging.getLogger(__name__)

# Configuración de reintentos para llamadas a la API de Binance
# Reintenta en errores de conexión/timeout o errores de servidor (5xx)
binance_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout))
)

class BinanceAdapter:
    """
    Adaptador para interactuar con la API de Binance y los WebSockets.
    """

    def __init__(self, api_key: str, api_secret: str, http_client: httpx.AsyncClient):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[AsyncClient] = None
        self.bsm: Optional[BinanceSocketManager] = None
        self.http_client = http_client
        self.active_sockets: Dict[str, asyncio.Task] = {}
        self._is_closing = False

    async def initialize(self):
        """Inicializa el cliente asíncrono de Binance."""
        if not self.client:
            self.client = await AsyncClient.create(
                self.api_key, self.api_secret, http_client=self.http_client
            )
            self.bsm = BinanceSocketManager(self.client)
            logger.info("Binance AsyncClient and SocketManager initialized.")

    @binance_api_retry
    async def get_connection_status(self) -> Dict[str, Any]:
        """Verifica el estado de la conexión con la API de Binance."""
        await self.initialize()
        try:
            ping = await self.client.ping()
            return {"status": "ok", "ping": ping}
        except BinanceLibAPIError as e:
            logger.error(f"Binance API error on ping: {e}", exc_info=True)
            raise BinanceAPIError(message=e.message, status_code=e.status_code, response_data=e.response.json() if e.response else None, original_exception=e)
        except Exception as e:
            logger.error(f"Unexpected error on ping: {e}", exc_info=True)
            raise ExternalAPIError(f"An unexpected error occurred: {e}", service_name="BINANCE_ADAPTER")

    @binance_api_retry
    async def get_account_info(self) -> Dict[str, Any]:
        """Obtiene la información de la cuenta de Binance."""
        await self.initialize()
        try:
            account_info = await self.client.get_account()
            return account_info
        except BinanceLibAPIError as e:
            logger.error(f"Binance API error getting account info: {e}", exc_info=True)
            raise BinanceAPIError(message=e.message, status_code=e.status_code, response_data=e.response.json() if e.response else None, original_exception=e)

    @binance_api_retry
    async def get_all_tickers(self) -> List[Dict[str, Any]]:
        """Obtiene los precios de todos los tickers."""
        await self.initialize()
        try:
            tickers = await self.client.get_all_tickers()
            return tickers
        except BinanceLibAPIError as e:
            logger.error(f"Binance API error getting all tickers: {e}", exc_info=True)
            raise BinanceAPIError(message=e.message, status_code=e.status_code, response_data=e.response.json() if e.response else None, original_exception=e)

    @binance_api_retry
    async def get_candlestick_data(self, symbol: str, interval: str, limit: int) -> List[List[Any]]:
        """Obtiene datos de velas para un símbolo."""
        await self.initialize()
        try:
            klines = await self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            return klines
        except BinanceLibAPIError as e:
            logger.error(f"Binance API error getting klines for {symbol}: {e}", exc_info=True)
            raise BinanceAPIError(message=e.message, status_code=e.status_code, response_data=e.response.json() if e.response else None, original_exception=e)

    async def start_kline_socket(self, symbol: str, interval: str, callback: Callable[[Dict[str, Any]], Coroutine]):
        """Inicia un WebSocket para datos de velas (k-lines)."""
        await self.initialize()
        socket_key = f"{symbol.lower()}@kline_{interval}"
        if socket_key in self.active_sockets:
            logger.warning(f"Socket for {socket_key} is already active.")
            return

        async def socket_logic():
            logger.info(f"Starting kline socket for {socket_key}")
            ts = self.bsm.kline_socket(symbol, interval)
            async with ts as tscm:
                while not self._is_closing:
                    try:
                        res = await tscm.recv()
                        if res:
                            await callback(res)
                    except Exception as e:
                        logger.error(f"Error in kline socket {socket_key}: {e}", exc_info=True)
                        # En un sistema de producción, aquí podría haber lógica de reconexión.
                        await asyncio.sleep(5) # Esperar antes de reintentar
            logger.info(f"Kline socket for {socket_key} closed.")

        task = asyncio.create_task(socket_logic())
        self.active_sockets[socket_key] = task
        logger.info(f"Kline socket task for {socket_key} created.")

    async def stop_socket(self, socket_key: str):
        """Detiene un WebSocket activo."""
        if socket_key in self.active_sockets:
            task = self.active_sockets.pop(socket_key)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Socket {socket_key} cancelled successfully.")
        else:
            logger.warning(f"No active socket found for key: {socket_key}")

    async def close(self):
        """Cierra todas las conexiones y tareas."""
        if self._is_closing:
            return
        self._is_closing = True
        logger.info("Closing BinanceAdapter...")
        
        # Detener todos los sockets activos
        active_socket_keys = list(self.active_sockets.keys())
        if active_socket_keys:
            logger.info(f"Stopping {len(active_socket_keys)} active sockets...")
            await asyncio.gather(*(self.stop_socket(key) for key in active_socket_keys), return_exceptions=True)
        
        # Cerrar el cliente de Binance (que también cierra el http_client subyacente si fue creado por él)
        if self.client:
            await self.client.close_connection()
            logger.info("Binance client connection closed.")
        
        self.client = None
        self.bsm = None
        logger.info("BinanceAdapter closed.")
