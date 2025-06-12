import logging
from typing import List, Optional, Dict, Set, Callable, Any
from uuid import UUID
from fastapi import Depends
from datetime import timedelta

from shared.data_types import AssetBalance, ServiceName, BinanceConnectionStatus, MarketData
from ..adapters.binance_adapter import BinanceAdapter
from .credential_service import CredentialService
from ..adapters.persistence_service import SupabasePersistenceService
from ..core.exceptions import BinanceAPIError, CredentialError, UltiBotError, ExternalAPIError, MarketDataError
from ..app_config import settings
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Servicio para obtener datos de mercado, incluyendo balances de exchanges y streams en tiempo real.
    """
    def __init__(self, 
                 credential_service: CredentialService, 
                 binance_adapter: BinanceAdapter,
                 persistence_service: SupabasePersistenceService
                 ):
        self.credential_service = credential_service
        self.binance_adapter = binance_adapter
        self.persistence_service = persistence_service
        self._active_websocket_tasks: Dict[str, asyncio.Task] = {}
        self._closed = False
        self._invalid_symbols_cache: Set[str] = set()
        self._cache_expiration = {}
        self._historical_data_tasks: Dict[str, asyncio.Task] = {}

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
        Obtiene datos históricos de velas (OHLCV) y los persiste en la base de datos.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se pueden obtener datos de velas para {symbol}-{interval}.")
            return []
        try:
            klines_data = await self.binance_adapter.get_candlestick_data(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            market_data_to_save = []
            processed_data = []
            for kline in klines_data:
                kline_dict = {
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
                }
                processed_data.append(kline_dict)
                
                market_data_to_save.append(MarketData(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                ))

            if market_data_to_save:
                await self.persistence_service.save_market_data(market_data_to_save)
                logger.info(f"{len(market_data_to_save)} registros de velas para {symbol}-{interval} guardados en la base de datos.")

            logger.info(f"Datos de velas para {symbol}-{interval} obtenidos y procesados.")
            return processed_data
        except BinanceAPIError as e:
            logger.error(f"Error al obtener datos de velas para {symbol}-{interval}: {e}")
            raise UltiBotError(f"No se pudieron obtener los datos de velas de Binance para {symbol}-{interval}: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener datos de velas para {symbol}-{interval}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener datos de velas de Binance para {symbol}-{interval}: {e}")

    async def get_historical_market_data(self, symbol: str, interval: str, limit: int = 1000) -> List[MarketData]:
        """
        Obtiene datos de mercado históricos desde la base de datos.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se pueden obtener datos históricos para {symbol}-{interval}.")
            return []
        try:
            logger.info(f"Obteniendo datos históricos para {symbol}-{interval} desde la base de datos.")
            # Aquí asumimos que el persistence_service tendrá un método para obtener los datos.
            # Este método necesita ser creado en SupabasePersistenceService.
            historical_data = await self.persistence_service.get_market_data_from_db(
                symbol=symbol,
                limit=limit
            )
            logger.info(f"Se obtuvieron {len(historical_data)} registros históricos para {symbol}-{interval} desde la base de datos.")
            return historical_data
        except Exception as e:
            logger.critical(f"Error inesperado al obtener datos históricos desde la base de datos para {symbol}-{interval}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener datos históricos para {symbol}-{interval}: {e}")


    async def fetch_and_store_historical_data(self, symbol: str, interval: str = '1h', days_back: int = 30):
        """
        Fetches historical data for a symbol going back a specified number of days
        and stores it in the database.
        
        Args:
            symbol: The trading pair symbol (e.g., 'BTCUSDT')
            interval: Candlestick interval (e.g., '1h', '4h', '1d')
            days_back: Number of days of historical data to fetch
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se pueden obtener datos históricos para {symbol}-{interval}.")
            return
        
        logger.info(f"Iniciando descarga de datos históricos para {symbol} (intervalo: {interval}, días: {days_back})")
        
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)
        
        # Determine the appropriate limit and number of iterations based on the interval
        limit_per_call = 1000  # Maximum allowed by Binance API
        total_candles_needed = days_back * 24  # Aproximación para intervalo '1h'
        
        if interval == '15m':
            total_candles_needed = days_back * 24 * 4
        elif interval == '30m':
            total_candles_needed = days_back * 24 * 2
        elif interval == '4h':
            total_candles_needed = days_back * 6
        elif interval == '1d':
            total_candles_needed = days_back
        
        iterations = (total_candles_needed + limit_per_call - 1) // limit_per_call
        
        total_candles_stored = 0
        current_end_time = end_time
        
        try:
            for _ in range(iterations):
                klines = await self.binance_adapter.get_candlestick_data(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_time,
                    end_time=current_end_time,
                    limit=limit_per_call
                )
                
                if not klines:
                    break
                
                market_data_to_save = []
                for kline in klines:
                    market_data_to_save.append(MarketData(
                        symbol=symbol,
                        timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[5])
                    ))
                
                # Save the data to the database
                if market_data_to_save:
                    await self.persistence_service.save_market_data(market_data_to_save)
                    total_candles_stored += len(market_data_to_save)
                    
                    # Update the end time for the next iteration
                    current_end_time = klines[0][0] - 1  # Use the earliest timestamp from this batch - 1ms
                
                # API Rate limiting: Sleep to prevent hitting Binance API rate limits
                await asyncio.sleep(1)
            
            logger.info(f"Completada la descarga histórica para {symbol}-{interval}. "
                        f"Se almacenaron {total_candles_stored} velas en la base de datos.")
                        
        except Exception as e:
            logger.error(f"Error al obtener datos históricos para {symbol}-{interval}: {e}", exc_info=True)
            raise

    async def start_continuous_historical_data_collection(self, symbols: List[str], intervals: List[str] = ['1h']):
        """
        Starts continuous collection of historical data for a list of symbols and intervals.
        
        Args:
            symbols: List of trading pair symbols to monitor
            intervals: List of candlestick intervals to collect
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se puede iniciar la colección de datos históricos.")
            return
            
        logger.info(f"Iniciando colección continua de datos históricos para {len(symbols)} símbolos.")
        
        # Initial historical data fetch
        for symbol in symbols:
            for interval in intervals:
                task_key = f"{symbol}_{interval}_historical"
                if task_key in self._historical_data_tasks and not self._historical_data_tasks[task_key].done():
                    logger.warning(f"Ya existe una tarea de recolección para {symbol}-{interval}. Ignorando.")
                    continue
                
                logger.info(f"Iniciando tarea de recolección de datos históricos para {symbol}-{interval}.")
                # First, fetch historical data going back 30 days
                await self.fetch_and_store_historical_data(symbol, interval, days_back=30)
                
                # Then start a continuous task to keep the data updated
                self._historical_data_tasks[task_key] = asyncio.create_task(
                    self._continuous_data_collection(symbol, interval)
                )

    async def _continuous_data_collection(self, symbol: str, interval: str):
        """
        Continuously collects recent data for a symbol at specified interval.
        This runs as a background task.
        
        Args:
            symbol: The trading pair symbol
            interval: Candlestick interval
        """
        try:
            update_frequency = 300  # 5 minutes in seconds
            
            # Adjust update frequency based on interval
            if interval == '1m':
                update_frequency = 60  # 1 minute
            elif interval == '5m':
                update_frequency = 60 * 5  # 5 minutes
            elif interval == '15m':
                update_frequency = 60 * 15  # 15 minutes
            elif interval == '30m':
                update_frequency = 60 * 30  # 30 minutes
            elif interval == '1h':
                update_frequency = 60 * 60  # 1 hour
            elif interval == '4h':
                update_frequency = 60 * 60 * 4  # 4 hours
            elif interval == '1d':
                update_frequency = 60 * 60 * 24  # 24 hours
                
            logger.info(f"Iniciando colección continua para {symbol}-{interval} (frecuencia: {update_frequency}s)")
            
            while not self._closed:
                try:
                    # Get only the last 5 candles to keep data up to date
                    klines = await self.binance_adapter.get_candlestick_data(
                        symbol=symbol,
                        interval=interval,
                        limit=5
                    )
                    
                    if klines:
                        market_data_to_save = []
                        for kline in klines:
                            market_data_to_save.append(MarketData(
                                symbol=symbol,
                                timestamp=datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
                                open=float(kline[1]),
                                high=float(kline[2]),
                                low=float(kline[3]),
                                close=float(kline[4]),
                                volume=float(kline[5])
                            ))
                        
                        # Save recent data to database with upsert logic
                        await self.persistence_service.save_market_data(market_data_to_save)
                        logger.debug(f"Actualizados {len(market_data_to_save)} puntos de datos para {symbol}-{interval}")
                        
                except Exception as e:
                    logger.error(f"Error en la colección continua de datos para {symbol}-{interval}: {e}", exc_info=True)
                
                # Sleep until next update
                await asyncio.sleep(update_frequency)
        except asyncio.CancelledError:
            logger.info(f"Tarea de colección continua cancelada para {symbol}-{interval}")
        except Exception as e:
            logger.error(f"Error fatal en la tarea de colección continua para {symbol}-{interval}: {e}", exc_info=True)

    async def stop_continuous_data_collection(self, symbol: Optional[str] = None, interval: Optional[str] = None):
        """
        Stops the continuous data collection tasks.
        
        Args:
            symbol: If provided, only stops the task for this symbol
            interval: If provided with symbol, stops the specific symbol-interval task
        """
        tasks_to_cancel = []
        
        if symbol and interval:
            task_key = f"{symbol}_{interval}_historical"
            if task_key in self._historical_data_tasks:
                tasks_to_cancel.append((task_key, self._historical_data_tasks[task_key]))
        elif symbol:
            for key, task in self._historical_data_tasks.items():
                if key.startswith(f"{symbol}_"):
                    tasks_to_cancel.append((key, task))
        else:
            tasks_to_cancel = list(self._historical_data_tasks.items())
            
        for task_key, task in tasks_to_cancel:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Tarea de colección de datos {task_key} cancelada correctamente.")
                except Exception as e:
                    logger.error(f"Error al cancelar tarea {task_key}: {e}")
                    
            del self._historical_data_tasks[task_key]
            
        if not symbol and not interval:
            self._historical_data_tasks.clear()
            
        logger.info(f"Se han detenido {len(tasks_to_cancel)} tareas de colección de datos.")

    async def close(self):
        """
        Cierra el cliente HTTP y cancela todas las tareas WebSocket activas.
        """
        if self._closed:
            return
        
        self._closed = True
        logger.info("MarketDataService: Iniciando cierre...")

        # Cancel websocket tasks
        for symbol, task in list(self._active_websocket_tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"MarketDataService: Tarea de WebSocket para {symbol} cancelada durante el cierre.")
            except Exception as e:
                logger.error(f"MarketDataService: Error al cancelar la tarea de WebSocket para {symbol} durante el cierre: {e}")
        self._active_websocket_tasks.clear()
        
        # Cancel historical data collection tasks
        await self.stop_continuous_data_collection()
        
        await self.binance_adapter.close()
        logger.info("MarketDataService: Cierre completado.")
