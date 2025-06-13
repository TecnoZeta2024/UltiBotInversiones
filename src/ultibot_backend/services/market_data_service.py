import logging
from typing import List, Optional, Dict, Set, Callable, Any
from uuid import UUID
from fastapi import Depends
from datetime import timedelta

from shared.data_types import AssetBalance, ServiceName, BinanceConnectionStatus, MarketData
from ..core.ports import IMarketDataProvider, ICredentialService, IPersistencePort
from ..core.exceptions import BinanceAPIError, CredentialError, UltiBotError, ExternalAPIError, MarketDataError
from ..app_config import AppSettings
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Servicio para obtener datos de mercado, incluyendo balances de exchanges y streams en tiempo real.
    """
    def __init__(self, 
                 credential_service: ICredentialService, 
                 market_data_provider: IMarketDataProvider,
                 persistence_port: IPersistencePort,
                 app_settings: AppSettings
                 ):
        self.credential_service = credential_service
        self.market_data_provider = market_data_provider
        self.persistence_port = persistence_port
        self.app_settings = app_settings
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
        
        # La lógica para obtener credenciales y desencriptarlas debe estar en el CredentialService
        # Aquí asumimos que el market_data_provider ya tiene acceso a las credenciales necesarias
        # a través de la inyección de dependencias o un método específico.
        try:
            balances = await self.market_data_provider.get_spot_balances()
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
        usando la API REST.
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se pueden obtener datos de mercado REST.")
            return {s: {"error": "Servicio cerrado"} for s in symbols}
            
        market_data = {}
        for symbol in symbols:
            try:
                ticker_data = await self.market_data_provider.get_ticker(symbol)
                market_data[symbol] = {
                    "lastPrice": ticker_data.price,
                    "priceChangePercent": ticker_data.price_change_percent_24h,
                    "quoteVolume": ticker_data.volume_24h
                }
                logger.info(f"Datos REST de {symbol} obtenidos.")
            except Exception as e:
                logger.error(f"Error al obtener datos REST de {symbol}: {e}")
                market_data[symbol] = {"error": str(e)}
        return market_data

    async def get_latest_price(self, symbol: str) -> float:
        """
        Obtiene el último precio conocido para un símbolo específico.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se puede obtener el último precio para {symbol}.")
            raise MarketDataError(f"MarketDataService cerrado. No se puede obtener el precio para {symbol}.")
        try:
            ticker_data = await self.market_data_provider.get_ticker(symbol)
            if ticker_data.price == 0:
                raise MarketDataError(f"Precio 'lastPrice' no encontrado o es cero para el símbolo {symbol}.")
            logger.info(f"Último precio de {symbol}: {ticker_data.price}")
            return ticker_data.price
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
            task = asyncio.create_task(self.market_data_provider.subscribe_to_ticker_stream(symbol, callback))
            self._active_websocket_tasks[symbol] = task
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
            klines_data = await self.market_data_provider.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            market_data_to_save = [MarketData.from_kline(symbol, kline) for kline in klines_data]

            if market_data_to_save:
                await self.persistence_port.save_market_data(market_data_to_save)
                logger.info(f"{len(market_data_to_save)} registros de velas para {symbol}-{interval} guardados en la base de datos.")

            logger.info(f"Datos de velas para {symbol}-{interval} obtenidos y procesados.")
            return [kline.to_dict() for kline in klines_data]
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
            historical_data = await self.persistence_port.get_market_data_from_db(
                symbol=symbol,
                limit=limit
            )
            logger.info(f"Se obtuvieron {len(historical_data)} registros históricos para {symbol}-{interval} desde la base de datos.")
            return historical_data
        except Exception as e:
            logger.critical(f"Error inesperado al obtener datos históricos desde la base de datos para {symbol}-{interval}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener datos históricos para {symbol}-{interval}: {e}")

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
        
        await self.market_data_provider.close()
        logger.info("MarketDataService: Cierre completado.")
