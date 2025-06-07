import logging
from typing import List, Optional, Dict, Set, Callable, Any
from uuid import UUID
from fastapi import Depends

from src.shared.data_types import AssetBalance, ServiceName, BinanceConnectionStatus
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import BinanceAPIError, CredentialError, UltiBotError, ExternalAPIError, MarketDataError
from src.ultibot_backend.app_config import settings
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Servicio para obtener datos de mercado, incluyendo balances de exchanges y streams en tiempo real.
    """
    def __init__(self, 
                 credential_service: CredentialService, 
                 binance_adapter: BinanceAdapter
                 ):
        self.credential_service = credential_service
        self.binance_adapter = binance_adapter
        self._active_websocket_tasks: Dict[str, asyncio.Task] = {}
        self._closed = False
        self._invalid_symbols_cache: Set[str] = set()
        self._cache_expiration = {}

    async def get_binance_connection_status(self) -> BinanceConnectionStatus:
        """
        Verifica el estado de la conexión con Binance y devuelve un objeto BinanceConnectionStatus.
        """
        status_message = "Conexión con Binance no verificada."
        is_connected = False
        last_verified_at = None
        status_code = None
        account_permissions = None

        try:
            binance_credential = await self.credential_service.get_credential(
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default"
            )

            if not binance_credential:
                status_message = "Credenciales de Binance no encontradas. Por favor, configúrelas."
                logger.warning(status_message)
                return BinanceConnectionStatus(
                    is_connected=False,
                    status_message=status_message,
                    status_code="CREDENTIALS_NOT_FOUND",
                    last_verified_at=None,
                    account_permissions=None
                )
            
            is_connected = await self.credential_service.verify_credential(binance_credential)
            
            last_verified_at = binance_credential.last_verified_at
            account_permissions = binance_credential.permissions

            if not is_connected:
                status_message = "Fallo en la verificación de conexión con Binance. Revise sus credenciales y permisos."
                status_code = "VERIFICATION_FAILED"
                logger.error(status_message)
            else:
                status_message = "Conexión con Binance exitosa."
                logger.info(status_message)

        except CredentialError as e:
            status_message = f"Error al acceder a las credenciales de Binance: {e}"
            status_code = "CREDENTIAL_ERROR"
            logger.error(status_message, exc_info=True)
        except BinanceAPIError as e:
            status_message = f"Error de la API de Binance: {e}"
            status_code = e.code if e.code else "BINANCE_API_ERROR"
            logger.error(status_message, exc_info=True)
        except Exception as e:
            status_message = f"Error inesperado al verificar conexión con Binance: {e}"
            status_code = "UNEXPECTED_ERROR"
            logger.critical(status_message, exc_info=True)
        
        return BinanceConnectionStatus(
            is_connected=is_connected,
            last_verified_at=last_verified_at,
            status_message=status_message,
            status_code=status_code,
            account_permissions=account_permissions
        )

    async def get_binance_spot_balances(self) -> List[AssetBalance]:
        """
        Obtiene los balances de Spot de Binance para el usuario.
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se pueden obtener balances.")
            return []
        binance_credential = await self.credential_service.get_credential(
            service_name=ServiceName.BINANCE_SPOT,
            credential_label="default"
        )

        if not binance_credential:
            raise CredentialError("Credenciales de Binance no encontradas para obtener balances.")

        decrypted_api_key = binance_credential.encrypted_api_key
        decrypted_api_secret = binance_credential.encrypted_api_secret

        if not decrypted_api_key or not decrypted_api_secret:
            logger.error("Credenciales de Binance inválidas o ausentes.")
            raise CredentialError("Las credenciales de Binance (API Key o Secret) no están disponibles o no son válidas.")
        try:
            balances = await self.binance_adapter.get_spot_balances(decrypted_api_key, decrypted_api_secret)
            logger.info("Balances de Binance obtenidos.")
            return balances
        except BinanceAPIError as e:
            logger.error(f"Error de la API de Binance al obtener balances: {e}")
            raise UltiBotError(f"No se pudieron obtener los balances de Binance: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener balances de Binance: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener balances de Binance: {e}")

    async def get_market_data_rest(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Obtiene datos de mercado (precio actual, cambio 24h, volumen 24h) para una lista de símbolos
        usando la API REST de Binance.
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se pueden obtener datos de mercado REST.")
            return {s: {"error": "Servicio cerrado"} for s in symbols}
            
        current_time = datetime.now().timestamp()
        expired_symbols = [symbol for symbol, expiry_time in self._cache_expiration.items() if current_time > expiry_time]
        for symbol in expired_symbols:
            if symbol in self._invalid_symbols_cache:
                self._invalid_symbols_cache.remove(symbol)
                del self._cache_expiration[symbol]
                
        market_data = {}
        for original_symbol in symbols:
            try:
                if original_symbol in self._invalid_symbols_cache:
                    logger.debug(f"Símbolo inválido (en caché): {original_symbol}. Saltando solicitud a Binance API.")
                    market_data[original_symbol] = {"error": "Símbolo inválido (caché)"}
                    continue
                
                binance_formatted_symbol = self.binance_adapter.normalize_symbol(original_symbol)
                
                ticker_data = await self.binance_adapter.get_ticker_24hr(binance_formatted_symbol)
                market_data[original_symbol] = {
                    "lastPrice": float(ticker_data.get("lastPrice", 0)),
                    "priceChangePercent": float(ticker_data.get("priceChangePercent", 0)),
                    "quoteVolume": float(ticker_data.get("quoteVolume", 0))
                }
                logger.info(f"Datos REST de {original_symbol} (consultado como {binance_formatted_symbol}) obtenidos.")
            except ValueError as ve:
                logger.error(f"Símbolo inválido recibido: {original_symbol} - {ve}")
                market_data[original_symbol] = {"error": f"Símbolo inválido: {ve}"}
                self._invalid_symbols_cache.add(original_symbol)
                self._cache_expiration[original_symbol] = current_time + 86400
            except BinanceAPIError as e:
                error_msg = str(e)
                if "Invalid symbol" in error_msg:
                    logger.warning(f"Símbolo inválido detectado: {original_symbol}. Agregando a caché.")
                    self._invalid_symbols_cache.add(original_symbol)
                    current_time = datetime.now().timestamp()
                    self._cache_expiration[original_symbol] = current_time + 86400
                else:
                    logger.error(f"Error al obtener datos REST de {original_symbol}: {e}")
                market_data[original_symbol] = {"error": error_msg}
            except Exception as e:
                logger.critical(f"Error inesperado al obtener datos REST de {original_symbol}: {e}", exc_info=True)
                market_data[original_symbol] = {"error": "Error inesperado"}
        return market_data

    async def get_latest_price(self, symbol: str) -> float:
        """
        Obtiene el último precio conocido para un símbolo específico.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se puede obtener el último precio para {symbol}.")
            raise MarketDataError(f"MarketDataService cerrado. No se puede obtener el precio para {symbol}.")
        try:
            ticker_data = await self.binance_adapter.get_ticker_24hr(symbol)
            last_price = float(ticker_data.get("lastPrice", 0))
            if last_price == 0:
                raise MarketDataError(f"Precio 'lastPrice' no encontrado o es cero para el símbolo {symbol}.")
            logger.info(f"Último precio de {symbol}: {last_price}")
            return last_price
        except BinanceAPIError as e:
            logger.error(f"Error de la API de Binance al obtener el último precio para {symbol}: {e}")
            raise MarketDataError(f"Fallo al obtener el último precio de Binance para {symbol}: {e}") from e
        except Exception as e:
            logger.critical(f"Error inesperado al obtener el último precio para {symbol}: {e}", exc_info=True)
            raise MarketDataError(f"Error inesperado al obtener el último precio para {symbol}: {e}") from e

    async def subscribe_to_market_data_websocket(self, symbol: str, callback: Callable):
        """
        Suscribe a un stream de ticker de 24 horas para un símbolo específico vía WebSocket.
        """
        if symbol in self._active_websocket_tasks:
            logger.warning(f"Ya suscrito al stream de WebSocket para {symbol}. Ignorando solicitud.")
            return

        logger.info(f"Suscribiéndose al stream de WebSocket para {symbol}.")
        try:
            task = asyncio.create_task(self.binance_adapter.subscribe_to_ticker_stream(symbol, callback))
            self._active_websocket_tasks[symbol] = task
        except ExternalAPIError as e:
            logger.error(f"Error al suscribirse al WebSocket para {symbol}: {e}")
            raise UltiBotError(f"No se pudo suscribir al stream de WebSocket para {symbol}: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al suscribirse al WebSocket para {symbol}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al suscribirse al stream de WebSocket para {symbol}: {e}")

    async def unsubscribe_from_market_data_websocket(self, symbol: str):
        """
        Cancela la suscripción a un stream de WebSocket para un símbolo específico.
        """
        if symbol in self._active_websocket_tasks:
            task = self._active_websocket_tasks.pop(symbol)
            task.cancel()
            try:
                await task
                logger.info(f"Suscripción a WebSocket para {symbol} cancelada exitosamente.")
            except asyncio.CancelledError:
                logger.info(f"Tarea de WebSocket para {symbol} cancelada.")
            except Exception as e:
                logger.error(f"Error al cancelar la tarea de WebSocket para {symbol}: {e}")
        else:
            logger.warning(f"No hay una suscripción activa a WebSocket para {symbol}.")

    async def get_candlestick_data(self, symbol: str, interval: str, limit: int = 200, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene datos históricos de velas (OHLCV) para un par y temporalidad dados.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se pueden obtener datos de velas para {symbol}-{interval}.")
            return []
        try:
            klines_data = await self.binance_adapter.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            processed_data = []
            for kline in klines_data:
                processed_data.append({
                    "open_time": kline[0],
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "close_time": kline[6],
                    "quote_asset_volume": float(kline[7]),
                    "number_of_trades": kline[8],
                    "taker_buy_base_asset_volume": float(kline[9]),
                    "taker_buy_quote_asset_volume": float(kline[10])
                })
            logger.info(f"Datos de velas para {symbol}-{interval} obtenidos y procesados.")
            return processed_data
        except BinanceAPIError as e:
            logger.error(f"Error al obtener datos de velas para {symbol}-{interval}: {e}")
            raise UltiBotError(f"No se pudieron obtener los datos de velas de Binance para {symbol}-{interval}: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener datos de velas para {symbol}-{interval}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener datos de velas de Binance para {symbol}-{interval}: {e}")

    async def close(self):
        """
        Cierra el cliente HTTP y cancela todas las tareas WebSocket activas.
        """
        if self._closed:
            return
        
        self._closed = True
        logger.info("MarketDataService: Iniciando cierre...")

        for symbol, task in list(self._active_websocket_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"MarketDataService: Tarea de WebSocket para {symbol} cancelada durante el cierre.")
            except Exception as e:
                logger.error(f"MarketDataService: Error al cancelar la tarea de WebSocket para {symbol} durante el cierre: {e}")
        self._active_websocket_tasks.clear()
        
        await self.binance_adapter.close()
        logger.info("MarketDataService: Cierre completado.")
