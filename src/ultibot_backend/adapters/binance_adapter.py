import hmac
import hashlib
import time
import httpx
import os # Importar os
import json # Importar json
import asyncio # Importar asyncio
import websockets # Importar websockets
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from src.ultibot_backend.core.exceptions import BinanceAPIError, ExternalAPIError
from src.shared.data_types import AssetBalance

class BinanceAdapter:
    """
    Adaptador para interactuar con la API de Binance.
    """
    BASE_URL = "https://api.binance.com"
    RETRY_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 1

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=self.BASE_URL, timeout=10.0)
        self._explicitly_closed = False # Flag para indicar si el adaptador ha sido cerrado explícitamente

    def _sign_request(self, api_key: str, api_secret: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Firma los parámetros de la solicitud con HMAC SHA256.
        """
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        m = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        params['signature'] = m.hexdigest()
        return params

    async def _make_request(self, method: str, endpoint: str, api_key: str, api_secret: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Any:
        """
        Realiza una solicitud a la API de Binance con reintentos y manejo de errores.
        """
        if self._explicitly_closed:
            raise RuntimeError("BinanceAdapter ha sido cerrado y no puede realizar nuevas solicitudes.")

        if params is None:
            params = {}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params = self._sign_request(api_key, api_secret, params)

        headers = {"X-MBX-APIKEY": api_key}

        for attempt in range(self.RETRY_ATTEMPTS):
            try:
                if method == "GET":
                    response = await self.client.get(endpoint, params=params, headers=headers)
                elif method == "POST":
                    response = await self.client.post(endpoint, params=params, headers=headers)
                elif method == "DELETE":
                    response = await self.client.delete(endpoint, params=params, headers=headers)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")

                response.raise_for_status()  # Lanza httpx.HTTPStatusError para códigos de estado 4xx/5xx
                return response.json()

            except httpx.HTTPStatusError as e:
                error_message = f"Error de estado HTTP de Binance API: {e.response.status_code} - {e.response.text}"
                response_data = e.response.json() if e.response.text else {}
                if e.response.status_code in [400, 401, 403, 404, 405, 406, 418, 429]: # Errores de cliente o rate limit
                    raise BinanceAPIError(
                        message=error_message,
                        status_code=e.response.status_code,
                        response_data=response_data,
                        original_exception=e
                    )
                elif e.response.status_code in [500, 502, 503, 504]: # Errores de servidor, potencialmente reintentables
                    if attempt < self.RETRY_ATTEMPTS - 1:
                        print(f"Advertencia: Error de servidor de Binance ({e.response.status_code}). Reintentando en {self.RETRY_DELAY_SECONDS}s...")
                        await asyncio.sleep(self.RETRY_DELAY_SECONDS)
                    else:
                        raise BinanceAPIError(
                            message=error_message,
                            status_code=e.response.status_code,
                            response_data=response_data,
                            original_exception=e
                        )
                else:
                    raise BinanceAPIError(
                        message=error_message,
                        status_code=e.response.status_code,
                        response_data=response_data,
                        original_exception=e
                    )
            except httpx.RequestError as e:
                error_message = f"Error de red o solicitud al interactuar con Binance API: {e}"
                if attempt < self.RETRY_ATTEMPTS - 1:
                    print(f"Advertencia: Error de red de Binance. Reintentando en {self.RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(self.RETRY_DELAY_SECONDS)
                else:
                    raise BinanceAPIError(
                        message=error_message,
                        status_code=None,
                        response_data={},
                        original_exception=e
                    )
            except Exception as e:
                raise ExternalAPIError(
                    message=f"Error inesperado al interactuar con Binance API: {e}",
                    service_name="BINANCE",
                    original_exception=e
                )
        
        # Esto no debería ser alcanzado si las excepciones se manejan correctamente
        raise BinanceAPIError("Fallo desconocido al realizar la solicitud a Binance API.")

    async def get_account_info(self, api_key: str, api_secret: str) -> Dict[str, Any]:
        """
        Obtiene la información de la cuenta de Binance, incluyendo balances y permisos.
        Endpoint: GET /api/v3/account
        """
        endpoint = "/api/v3/account"
        try:
            response_data = await self._make_request("GET", endpoint, api_key, api_secret, signed=True)
            return response_data
        except BinanceAPIError as e:
            raise e
        except Exception as e:
            raise BinanceAPIError(f"Error al obtener información de la cuenta de Binance: {e}", original_exception=e)

    async def get_spot_balances(self, api_key: str, api_secret: str) -> List[AssetBalance]:
        """
        Obtiene los balances de la cuenta de Spot de Binance.
        """
        account_info = await self.get_account_info(api_key, api_secret)
        balances_data = account_info.get("balances", [])
        
        asset_balances: List[AssetBalance] = []
        for balance in balances_data:
            try:
                free = float(balance.get("free", 0))
                locked = float(balance.get("locked", 0))
                total = free + locked
                if total > 0: # Solo incluir activos con balance > 0
                    asset_balances.append(AssetBalance(
                        asset=balance.get("asset"),
                        free=free,
                        locked=locked,
                        total=total
                    ))
            except ValueError as e:
                print(f"Advertencia: No se pudo parsear el balance para el activo {balance.get('asset')}: {e}")
        return asset_balances

    async def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene los datos de ticker de 24 horas para un símbolo específico.
        Endpoint: GET /api/v3/ticker/24hr
        """
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        try:
            response_data = await self._make_request("GET", endpoint, "", "", params=params, signed=False)
            return response_data
        except BinanceAPIError as e:
            raise e
        except Exception as e:
            raise BinanceAPIError(f"Error al obtener ticker 24hr para {symbol}: {e}", original_exception=e)

    async def get_all_tickers_24hr(self) -> List[Dict[str, Any]]:
        """
        Obtiene los datos de ticker de 24 horas para todos los símbolos.
        Endpoint: GET /api/v3/ticker/24hr
        """
        endpoint = "/api/v3/ticker/24hr"
        try:
            response_data = await self._make_request("GET", endpoint, "", "", signed=False)
            return response_data
        except BinanceAPIError as e:
            raise e
        except Exception as e:
            raise BinanceAPIError(f"Error al obtener todos los tickers 24hr: {e}", original_exception=e)

    async def get_klines(self, symbol: str, interval: str, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: int = 500) -> List[List[Any]]:
        """
        Obtiene datos históricos de velas (OHLCV) para un símbolo y temporalidad dados.
        Endpoint: GET /api/v3/klines
        Parámetros:
            symbol (str): El par de trading (ej. "BTCUSDT").
            interval (str): La temporalidad de las velas (ej. "1m", "5m", "1h", "1d").
            start_time (int, optional): Timestamp en milisegundos para el inicio del rango.
            end_time (int, optional): Timestamp en milisegundos para el fin del rango.
            limit (int): Número de velas a retornar (máximo 1000).
        """
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response_data = await self._make_request("GET", endpoint, "", "", params=params, signed=False)
            return response_data
        except BinanceAPIError as e:
            raise e
        except Exception as e:
            raise BinanceAPIError(f"Error al obtener klines para {symbol} con intervalo {interval}: {e}", original_exception=e)

    async def _connect_websocket(self, stream_url: str, callback: Callable):
        """
        Establece una conexión WebSocket y procesa los mensajes entrantes.
        """
        try:
            async with websockets.connect(stream_url) as ws:
                print(f"Conectado a WebSocket: {stream_url}")
                while True:
                    try:
                        message = await ws.recv()
                        data = json.loads(message)
                        await callback(data)
                    except websockets.exceptions.ConnectionClosedOK:
                        print(f"Conexión WebSocket cerrada normalmente para {stream_url}.")
                        break
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"Error de conexión WebSocket para {stream_url}: {e}")
                        break
                    except json.JSONDecodeError:
                        print(f"Error al decodificar JSON del mensaje WebSocket: {message}")
                    except Exception as e:
                        print(f"Error inesperado al procesar mensaje WebSocket: {e}")
        except Exception as e:
            print(f"Error al conectar al WebSocket {stream_url}: {e}")
            raise ExternalAPIError(
                message=f"Error al conectar al WebSocket de Binance: {e}",
                service_name="BINANCE_WEBSOCKET",
                original_exception=e
            )

    async def subscribe_to_ticker_stream(self, symbol: str, callback: Callable):
        """
        Suscribe a un stream de ticker de 24 horas para un símbolo específico.
        Stream: <symbol>@ticker
        """
        stream_url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@ticker"
        print(f"Intentando conectar a WebSocket para {symbol} en {stream_url}")
        # Ejecutar el WebSocket en una tarea separada para no bloquear el main loop
        asyncio.create_task(self._connect_websocket(stream_url, callback))

    async def close(self):
        """Cierra el cliente HTTP y marca el adaptador como cerrado."""
        if not self._explicitly_closed:
            await self.client.aclose()
            self._explicitly_closed = True
            print("BinanceAdapter: Cliente HTTP cerrado y adaptador marcado como cerrado.")
        else:
            print("BinanceAdapter: Ya estaba cerrado.")

# Ejemplo de uso (para pruebas locales, no parte del código de producción)
async def main():
    # Asegúrate de que estas variables de entorno estén configuradas para pruebas
    # os.environ["BINANCE_API_KEY"] = "TU_API_KEY"
    # os.environ["BINANCE_API_SECRET"] = "TU_API_SECRET"

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("Por favor, configura las variables de entorno BINANCE_API_KEY y BINANCE_API_SECRET.")
        return

    binance_adapter = BinanceAdapter()
    try:
        print("Obteniendo información de la cuenta de Binance...")
        account_info = await binance_adapter.get_account_info(api_key, api_secret)
        print("Información de la cuenta:", json.dumps(account_info, indent=2))

        print("\nObteniendo balances de Spot...")
        balances = await binance_adapter.get_spot_balances(api_key, api_secret)
        for balance in balances:
            print(f"  {balance.asset}: Free={balance.free}, Locked={balance.locked}, Total={balance.total}")

        print("\nObteniendo datos de ticker 24hr para BTCUSDT...")
        try:
            btc_usdt_ticker = await binance_adapter.get_ticker_24hr("BTCUSDT")
            print("Ticker BTCUSDT:", json.dumps(btc_usdt_ticker, indent=2))
        except BinanceAPIError as e:
            print(f"Error al obtener ticker BTCUSDT: {e} (Código: {e.status_code}, Detalles: {e.response_data})")

        try:
            all_tickers = await binance_adapter.get_all_tickers_24hr()
            print(f"Total de tickers obtenidos: {len(all_tickers)}")
            # Imprimir solo los primeros 5 para no saturar la salida
            for i, ticker in enumerate(all_tickers[:5]):
                print(f"  {ticker.get('symbol')}: Price={ticker.get('lastPrice')}, Change 24h={ticker.get('priceChangePercent')}%, Volume={ticker.get('quoteVolume')}")
            if len(all_tickers) > 5:
                print("  ...")
        except BinanceAPIError as e:
            print(f"Error al obtener todos los tickers: {e} (Código: {e.status_code}, Detalles: {e.response_data})")

        # Función de callback para el stream de WebSocket
        async def handle_ticker_data(data: Dict[str, Any]):
            symbol = data.get('s')
            price = data.get('c')
            print(f"WebSocket Ticker Update: {symbol} - Last Price: {price}")

        print("\nSuscribiéndose al stream de ticker de BTCUSDT...")
        await binance_adapter.subscribe_to_ticker_stream("BTCUSDT", handle_ticker_data)

        # Mantener el evento loop corriendo por un tiempo para recibir actualizaciones de WebSocket
        print("Manteniendo la conexión WebSocket abierta por 30 segundos. Presiona Ctrl+C para salir.")
        await asyncio.sleep(30) # Esperar 30 segundos para recibir actualizaciones

    except BinanceAPIError as e:
        print(f"Error de Binance API: {e} (Código: {e.status_code}, Detalles: {e.response_data})")
    except ExternalAPIError as e:
        print(f"Error de API externa: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        await binance_adapter.close()

if __name__ == "__main__":
    asyncio.run(main())
