import httpx
import hmac
import hashlib
import time
from typing import List, Dict, Any, Optional
from injector import inject
from datetime import datetime, timezone
from decimal import Decimal

from ..core.ports import IMarketDataProvider, IOrderExecutionPort, ICredentialService
from ..app_config import AppSettings
from ..core.exceptions import ExternalAPIError, CredentialError
from ..core.domain_models.trading import TickerData, KlineData, Order, OrderType, OrderSide, OrderStatus
from shared.data_types import ServiceName

class BinanceAPIError(ExternalAPIError):
    """Exception for errors related to the Binance API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, "Binance", status_code, response_data)

class BinanceAdapter(IMarketDataProvider, IOrderExecutionPort):
    """
    Adapter for fetching market data and executing orders on Binance.
    """
    @inject
    def __init__(self, config: AppSettings, credential_service: ICredentialService):
        self._base_url = "https://api.binance.com/api/v3"
        self._credential_service = credential_service
        self._client: Optional[httpx.AsyncClient] = None
        self._api_key: Optional[str] = None
        self._api_secret: Optional[str] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            creds = await self._credential_service.get_first_decrypted_credential_by_service(ServiceName.BINANCE_SPOT)
            if not creds or not creds.encrypted_api_key or not creds.encrypted_api_secret:
                raise CredentialError("Binance API credentials are not configured.")
            self._api_key = creds.encrypted_api_key
            self._api_secret = creds.encrypted_api_secret
            self._client = httpx.AsyncClient(
                headers={"X-MBX-APIKEY": self._api_key}
            )
        return self._client

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        if not self._api_secret:
            raise CredentialError("API secret is not available for signature generation.")
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(self._api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    async def get_ticker(self, symbol: str) -> TickerData:
        client = await self._get_client()
        try:
            response = await client.get(f"{self._base_url}/ticker/24hr", params={"symbol": symbol})
            response.raise_for_status()
            data = response.json()
            return TickerData(
                symbol=data["symbol"],
                price=Decimal(data["lastPrice"]),
                volume=Decimal(data["volume"]),
                price_change_24h=Decimal(data["priceChange"]) if "priceChange" in data else None,
                price_change_percent_24h=Decimal(data["priceChangePercent"]) if "priceChangePercent" in data else None,
                timestamp=datetime.fromtimestamp(data["closeTime"] / 1000, tz=timezone.utc)
            )
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error fetching ticker data for {symbol}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error for {symbol}: {e}") from e
        except KeyError as e:
            raise BinanceAPIError(f"Missing data key in ticker response for {symbol}: {e}. Response: {data}", response_data=data) from e

    async def get_klines(self, symbol: str, interval: str) -> List[KlineData]:
        client = await self._get_client()
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000
        }
        try:
            response = await client.get(f"{self._base_url}/klines", params=params)
            response.raise_for_status()
            klines_data = response.json()
            return [
                KlineData(
                    open_time=datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
                    open_price=Decimal(kline[1]),
                    high_price=Decimal(kline[2]),
                    low_price=Decimal(kline[3]),
                    close_price=Decimal(kline[4]),
                    volume=Decimal(kline[5]),
                    close_time=datetime.fromtimestamp(kline[6] / 1000, tz=timezone.utc),
                    symbol=symbol,
                    interval=interval
                )
                for kline in klines_data
            ]
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error fetching klines for {symbol}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error for {symbol}: {e}") from e
        except IndexError as e:
            raise BinanceAPIError(f"Invalid klines data structure for {symbol}: {e}. Response: {klines_data}", response_data=klines_data) from e

    async def get_all_symbols(self) -> List[str]:
        client = await self._get_client()
        try:
            response = await client.get(f"{self._base_url}/exchangeInfo")
            response.raise_for_status()
            exchange_info = response.json()
            return [s["symbol"] for s in exchange_info["symbols"] if s["status"] == "TRADING"]
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error fetching all symbols: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error fetching all symbols: {e}") from e

    async def execute_order(self, symbol: str, order_type: OrderType, side: OrderSide, quantity: Decimal, price: Optional[Decimal] = None) -> Order:
        client = await self._get_client()
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": f"{quantity:.8f}".rstrip('0').rstrip('.'),
            "timestamp": int(time.time() * 1000)
        }
        if order_type == OrderType.LIMIT:
            if price is None:
                raise ValueError("Price is required for LIMIT orders.")
            params["price"] = f"{price:.8f}".rstrip('0').rstrip('.')
            params["timeInForce"] = "GTC"

        params["signature"] = self._generate_signature(params)

        try:
            response = await client.post(f"{self._base_url}/order", params=params)
            response.raise_for_status()
            data = response.json()
            return Order(
                id=str(data['orderId']),
                symbol=data['symbol'],
                side=OrderSide(data['side']),
                type=OrderType(data['type']),
                quantity=Decimal(data['origQty']),
                price=Decimal(data['price']) if Decimal(data['price']) > 0 else None,
                status=OrderStatus(data['status']),
                created_at=datetime.fromtimestamp(data['transactTime'] / 1000, tz=timezone.utc)
            )
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error executing order for {symbol}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error executing order for {symbol}: {e}") from e

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        client = await self._get_client()
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000)
        }
        params["signature"] = self._generate_signature(params)

        try:
            response = await client.delete(f"{self._base_url}/order", params=params)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400 and e.response.json().get('code') == -2011:
                return False
            raise BinanceAPIError(f"Error cancelling order {order_id}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error cancelling order {order_id}: {e}") from e

    async def verify_credentials(self, api_key: str, api_secret: str) -> bool:
        # Temporary client for verification
        temp_client = httpx.AsyncClient(headers={"X-MBX-APIKEY": api_key})
        try:
            params = {"timestamp": int(time.time() * 1000)}
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            params["signature"] = signature
            
            response = await temp_client.get(f"{self._base_url}/account", params=params)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False
        finally:
            await temp_client.aclose()

    async def get_account_permissions(self, api_key: str, api_secret: str) -> Dict[str, bool]:
        temp_client = httpx.AsyncClient(headers={"X-MBX-APIKEY": api_key})
        try:
            params = {"timestamp": int(time.time() * 1000)}
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            params["signature"] = signature

            response = await temp_client.get(f"{self._base_url}/account", params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "can_trade": data.get("canTrade", False),
                "can_withdraw": data.get("canWithdraw", False),
                "can_deposit": data.get("canDeposit", False)
            }
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError("Failed to get account permissions", status_code=e.response.status_code, response_data=e.response.json()) from e
        finally:
            await temp_client.aclose()

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
