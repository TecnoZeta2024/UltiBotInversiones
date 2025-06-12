import httpx
from typing import List, Dict, Any, Optional
from injector import inject
from ..core.ports import IMarketDataProvider
from ..app_config import AppSettings, get_app_settings
from ..core.exceptions import ExternalAPIError

class BinanceAPIError(ExternalAPIError):
    """Exception for errors related to the Binance API."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, "Binance", status_code, response_data)

class BinanceAdapter(IMarketDataProvider):
    """
    Adapter for fetching market data from Binance.
    """
    @inject
    def __init__(self, config: AppSettings):
        self._api_key = config.binance_api_key
        self._api_secret = config.binance_api_secret
        self._base_url = "https://api.binance.com/api/v3"
        self._client = httpx.AsyncClient(
            headers={"X-MBX-APIKEY": self._api_key}
        )

    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetches current market data for a given symbol.
        
        Args:
            symbol: The trading symbol (e.g., 'BTCUSDT').
            
        Returns:
            A dictionary containing the latest market data.
        """
        try:
            response = await self._client.get(f"{self._base_url}/ticker/24hr", params={"symbol": symbol})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error fetching market data for {symbol}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error for {symbol}: {e}") from e

    async def get_historical_data(self, symbol: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches historical k-line (candlestick) data.
        
        Args:
            symbol: The trading symbol.
            interval: The k-line interval (e.g., '1h', '4h', '1d').
            limit: The number of data points to retrieve.
            
        Returns:
            A list of dictionaries, each representing a k-line.
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        try:
            response = await self._client.get(f"{self._base_url}/klines", params=params)
            response.raise_for_status()
            # Format the response to be more developer-friendly if needed
            # [open_time, open, high, low, close, volume, close_time, ...]
            return response.json()
        except httpx.HTTPStatusError as e:
            raise BinanceAPIError(f"Error fetching historical data for {symbol}: {e}", status_code=e.response.status_code, response_data=e.response.json()) from e
        except httpx.RequestError as e:
            raise BinanceAPIError(f"Connection error for {symbol}: {e}") from e

    async def close(self):
        """Closes the underlying HTTP client."""
        await self._client.aclose()

# Example of how to use the adapter
async def main():
    config = get_app_settings()
    adapter = BinanceAdapter(config)
    try:
        # Fetch current price for BTCUSDT
        market_data = await adapter.get_market_data("BTCUSDT")
        if market_data:
            print(f"Current BTCUSDT Price: {market_data.get('lastPrice')}")

        # Fetch last 5 1-hour candles for ETHUSDT
        historical_data = await adapter.get_historical_data("ETHUSDT", "1h", 5)
        if historical_data:
            print("Last 5 1-hour candles for ETHUSDT:")
            for kline in historical_data:
                print(kline)
    finally:
        await adapter.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
