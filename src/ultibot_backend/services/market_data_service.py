import logging
from typing import List, Optional, Dict, Set, Callable, Any
from uuid import UUID

from src.shared.data_types import AssetBalance, ServiceName, BinanceConnectionStatus
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.core.exceptions import BinanceAPIError, CredentialError, UltiBotError, ExternalAPIError
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Servicio para obtener datos de mercado, incluyendo balances de exchanges y streams en tiempo real.
    """
    def __init__(self, credential_service: CredentialService, binance_adapter: BinanceAdapter):
        self.credential_service = credential_service
        self.binance_adapter = binance_adapter
        self._active_websocket_tasks: Dict[str, asyncio.Task] = {} # Para mantener un registro de las tareas WebSocket
        self._closed = False # Flag para indicar si el servicio ha sido cerrado

    async def get_binance_connection_status(self, user_id: UUID) -> BinanceConnectionStatus:
        """
        Verifica el estado de la conexión con Binance y devuelve un objeto BinanceConnectionStatus.
        """
        status_message = "Conexión con Binance no verificada."
        is_connected = False
        last_verified_at = None
        status_code = None
        account_permissions = None

        try:
            # Intentar obtener la credencial de Binance Spot
            binance_credential = await self.credential_service.get_credential(
                user_id=user_id,
                service_name=ServiceName.BINANCE_SPOT,
                credential_label="default" # Asumimos una etiqueta por defecto para la credencial principal
            )

            if not binance_credential:
                status_message = "Credenciales de Binance no encontradas. Por favor, configúrelas."
                logger.warning(f"Usuario {user_id}: {status_message}")
                return BinanceConnectionStatus(
                    is_connected=False,
                    status_message=status_message,
                    status_code="CREDENTIALS_NOT_FOUND",
                    last_verified_at=None, # Añadir explícitamente None
                    account_permissions=None # Añadir explícitamente None
                )
            
            # La verificación de la credencial ya actualiza su estado en la BD
            is_connected = await self.credential_service.verify_credential(binance_credential)
            
            # Después de verify_credential, binance_credential.last_verified_at y .permissions ya deberían estar actualizados
            last_verified_at = binance_credential.last_verified_at
            account_permissions = binance_credential.permissions

            if not is_connected:
                status_message = "Fallo en la verificación de conexión con Binance. Revise sus credenciales y permisos."
                status_code = "VERIFICATION_FAILED"
                logger.error(f"Usuario {user_id}: {status_message}")
            else:
                status_message = "Conexión con Binance exitosa."
                logger.info(f"Usuario {user_id}: {status_message}")

        except CredentialError as e:
            status_message = f"Error al acceder a las credenciales de Binance: {e}"
            status_code = "CREDENTIAL_ERROR"
            logger.error(f"Usuario {user_id}: {status_message}", exc_info=True)
        except BinanceAPIError as e:
            status_message = f"Error de la API de Binance: {e}"
            status_code = e.code if e.code else "BINANCE_API_ERROR"
            logger.error(f"Usuario {user_id}: {status_message}", exc_info=True)
        except Exception as e:
            status_message = f"Error inesperado al verificar conexión con Binance: {e}"
            status_code = "UNEXPECTED_ERROR"
            logger.critical(f"Usuario {user_id}: {status_message}", exc_info=True)
        
        return BinanceConnectionStatus(
            is_connected=is_connected,
            last_verified_at=last_verified_at,
            status_message=status_message,
            status_code=status_code,
            account_permissions=account_permissions
        )

    async def get_binance_spot_balances(self, user_id: UUID) -> List[AssetBalance]:
        """
        Obtiene los balances de Spot de Binance para un usuario.
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se pueden obtener balances.")
            return []
        binance_credential = await self.credential_service.get_credential(
            user_id=user_id,
            service_name=ServiceName.BINANCE_SPOT,
            credential_label="default"
        )

        if not binance_credential:
            raise CredentialError("Credenciales de Binance no encontradas para obtener balances.")

        # Las credenciales ya están desencriptadas en el objeto binance_credential
        # si get_credential no lanzó un error.
        decrypted_api_key = binance_credential.encrypted_api_key
        decrypted_api_secret = binance_credential.encrypted_api_secret

        # Aunque get_credential ya lanza CredentialError si la desencriptación falla,
        # añadimos una comprobación explícita aquí para mayor robustez y claridad.
        if decrypted_api_key is None or decrypted_api_secret is None:
            raise CredentialError("Las credenciales de Binance (API Key o Secret) no están disponibles o no son válidas.")

        try:
            balances = await self.binance_adapter.get_spot_balances(decrypted_api_key, decrypted_api_secret)
            logger.info(f"Balances de Binance obtenidos para el usuario {user_id}.")
            return balances
        except BinanceAPIError as e:
            logger.error(f"Error al obtener balances de Binance para el usuario {user_id}: {e}")
            raise UltiBotError(f"No se pudieron obtener los balances de Binance: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener balances de Binance para el usuario {user_id}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener balances de Binance: {e}")

    async def get_market_data_rest(self, user_id: UUID, symbols: List[str]) -> Dict[str, Any]:
        """
        Obtiene datos de mercado (precio actual, cambio 24h, volumen 24h) para una lista de símbolos
        usando la API REST de Binance.
        """
        if self._closed:
            logger.warning("MarketDataService está cerrado. No se pueden obtener datos de mercado REST.")
            return {s: {"error": "Servicio cerrado"} for s in symbols}
        market_data = {}
        for symbol in symbols:
            try:
                # Los endpoints de ticker 24hr no requieren API Key ni Secret
                ticker_data = await self.binance_adapter.get_ticker_24hr(symbol)
                market_data[symbol] = {
                    "lastPrice": float(ticker_data.get("lastPrice", 0)),
                    "priceChangePercent": float(ticker_data.get("priceChangePercent", 0)),
                    "quoteVolume": float(ticker_data.get("quoteVolume", 0))
                }
                logger.info(f"Datos REST de {symbol} obtenidos para el usuario {user_id}.")
            except BinanceAPIError as e:
                logger.error(f"Error al obtener datos REST de {symbol} para el usuario {user_id}: {e}")
                market_data[symbol] = {"error": str(e)}
            except Exception as e:
                logger.critical(f"Error inesperado al obtener datos REST de {symbol} para el usuario {user_id}: {e}", exc_info=True)
                market_data[symbol] = {"error": "Error inesperado"}
        return market_data

    async def subscribe_to_market_data_websocket(self, user_id: UUID, symbol: str, callback: Callable):
        """
        Suscribe a un stream de ticker de 24 horas para un símbolo específico vía WebSocket.
        La función de callback recibirá los datos del ticker en tiempo real.
        """
        if symbol in self._active_websocket_tasks:
            logger.warning(f"Usuario {user_id}: Ya suscrito al stream de WebSocket para {symbol}. Ignorando solicitud.")
            return

        logger.info(f"Usuario {user_id}: Suscribiéndose al stream de WebSocket para {symbol}.")
        try:
            # La API Key y Secret no son necesarios para streams públicos de WebSocket
            task = asyncio.create_task(self.binance_adapter.subscribe_to_ticker_stream(symbol, callback))
            self._active_websocket_tasks[symbol] = task
        except ExternalAPIError as e:
            logger.error(f"Usuario {user_id}: Error al suscribirse al WebSocket para {symbol}: {e}")
            raise UltiBotError(f"No se pudo suscribir al stream de WebSocket para {symbol}: {e}")
        except Exception as e:
            logger.critical(f"Usuario {user_id}: Error inesperado al suscribirse al WebSocket para {symbol}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al suscribirse al stream de WebSocket para {symbol}: {e}")

    async def unsubscribe_from_market_data_websocket(self, symbol: str):
        """
        Cancela la suscripción a un stream de WebSocket para un símbolo específico.
        """
        if symbol in self._active_websocket_tasks:
            task = self._active_websocket_tasks.pop(symbol)
            task.cancel()
            try:
                await task # Esperar a que la tarea se cancele
                logger.info(f"Suscripción a WebSocket para {symbol} cancelada exitosamente.")
            except asyncio.CancelledError:
                logger.info(f"Tarea de WebSocket para {symbol} cancelada.")
            except Exception as e:
                logger.error(f"Error al cancelar la tarea de WebSocket para {symbol}: {e}")
        else:
            logger.warning(f"No hay una suscripción activa a WebSocket para {symbol}.")

    async def get_candlestick_data(self, user_id: UUID, symbol: str, interval: str, limit: int = 200, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene datos históricos de velas (OHLCV) para un par y temporalidad dados,
        procesándolos para ser consumidos por el frontend.
        """
        if self._closed:
            logger.warning(f"MarketDataService está cerrado. No se pueden obtener datos de velas para {symbol}-{interval}.")
            return []
        try:
            # No se requieren credenciales para este endpoint público
            klines_data = await self.binance_adapter.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )

            processed_data = []
            for kline in klines_data:
                # Formato de kline:
                # [
                #   1499040000000,      // Open time
                #   "0.01634790",       // Open
                #   "0.80000000",       // High
                #   "0.01575800",       // Low
                #   "0.01577100",       // Close
                #   "148976.11427815",  // Volume
                #   1499644799999,      // Close time
                #   "2434.19055334",    // Quote asset volume
                #   308,                // Number of trades
                #   "1756.87402397",    // Taker buy base asset volume
                #   "28.46694368",      // Taker buy quote asset volume
                #   "1792.34210000"     // Ignore
                # ]
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
            logger.info(f"Datos de velas para {symbol}-{interval} obtenidos y procesados para el usuario {user_id}.")
            return processed_data
        except BinanceAPIError as e:
            logger.error(f"Error al obtener datos de velas para {symbol}-{interval} para el usuario {user_id}: {e}")
            raise UltiBotError(f"No se pudieron obtener los datos de velas de Binance para {symbol}-{interval}: {e}")
        except Exception as e:
            logger.critical(f"Error inesperado al obtener datos de velas para {symbol}-{interval} para el usuario {user_id}: {e}", exc_info=True)
            raise UltiBotError(f"Error inesperado al obtener datos de velas de Binance para {symbol}-{interval}: {e}")

    async def close(self):
        """
        Cierra el cliente HTTP y cancela todas las tareas WebSocket activas.
        """
        if self._closed:
            return # Ya está cerrado o en proceso de cierre
        
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

# Ejemplo de uso (para pruebas locales)
async def main():
    # Configurar un logger básico para el ejemplo
    logging.basicConfig(level=logging.INFO)

    # Necesitarás configurar la variable de entorno CREDENTIAL_ENCRYPTION_KEY
    # y tener una credencial de Binance en tu base de datos Supabase para que esto funcione.
    # Para pruebas, puedes simular el CredentialService y BinanceAdapter.

    # Ejemplo de inicialización de servicios (simplificado para el ejemplo)
    # En una aplicación real, estos serían inyectados por un framework (FastAPI Depends)
    from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
    from src.ultibot_backend.app_config import settings # Asegúrate de que settings esté configurado

    # Configurar una URL de BD de prueba o mockear SupabasePersistenceService
    # settings.DATABASE_URL = "postgresql://..." 

    # persistence_service = SupabasePersistenceService() # No es necesario para este ejemplo
    # await persistence_service.connect() # No es necesario para este ejemplo

    credential_service = CredentialService()
    binance_adapter = BinanceAdapter() 

    market_data_service = MarketDataService(credential_service, binance_adapter)

    # ID de usuario de prueba (debe coincidir con el user_id de la credencial en la BD)
    test_user_id = UUID("a1b2c3d4-e5f6-7890-1234-567890abcdef") 

    try:
        print("Verificando estado de conexión con Binance...")
        status = await market_data_service.get_binance_connection_status(test_user_id)
        print(f"Estado de conexión: {status.is_connected}, Mensaje: {status.status_message}, Permisos: {status.account_permissions}")

        if status.is_connected:
            print("\nObteniendo balances de Spot de Binance...")
            try:
                balances = await market_data_service.get_binance_spot_balances(test_user_id)
                for balance in balances:
                    print(f"  {balance.asset}: Free={balance.free}, Locked={balance.locked}, Total={balance.total}")
            except UltiBotError as e:
                print(f"Error al obtener balances: {e}")
        else:
            print("No se pueden obtener balances sin una conexión exitosa a Binance.")

        print("\nObteniendo datos de mercado REST para BTCUSDT y ETHUSDT...")
        symbols_to_fetch = ["BTCUSDT", "ETHUSDT"]
        rest_data = await market_data_service.get_market_data_rest(test_user_id, symbols_to_fetch)
        for symbol, data in rest_data.items():
            if "error" in data:
                print(f"  Error para {symbol}: {data['error']}")
            else:
                print(f"  {symbol}: Precio={data['lastPrice']}, Cambio 24h={data['priceChangePercent']}%, Volumen={data['quoteVolume']}")

        # Función de callback para el stream de WebSocket
        async def handle_ws_data(data: Dict[str, Any]):
            event_type = data.get('e')
            if event_type == '24hrTicker':
                symbol = data.get('s')
                last_price = data.get('c')
                price_change_percent = data.get('P')
                quote_volume = data.get('q')
                print(f"  WS Ticker Update: {symbol} - Precio: {last_price}, Cambio 24h: {price_change_percent}%, Volumen: {quote_volume}")
            else:
                print(f"  WS Raw Data: {data}")

        print("\nSuscribiéndose al stream de WebSocket para BTCUSDT y ETHUSDT...")
        await market_data_service.subscribe_to_market_data_websocket(test_user_id, "BTCUSDT", handle_ws_data)
        await market_data_service.subscribe_to_market_data_websocket(test_user_id, "ETHUSDT", handle_ws_data)

        print("Manteniendo la conexión WebSocket abierta por 45 segundos. Presiona Ctrl+C para salir.")
        await asyncio.sleep(45)

        print("\nCancelando suscripción a ETHUSDT...")
        await market_data_service.unsubscribe_from_market_data_websocket("ETHUSDT")
        print("Esperando 15 segundos más para ver si BTCUSDT sigue recibiendo datos...")
        await asyncio.sleep(15)

    except UltiBotError as e:
        print(f"Error de UltiBot: {e}")
    except Exception as e:
        print(f"Error inesperado en el main: {e}")
    finally:
        print("\nCerrando servicios...")
        await market_data_service.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
