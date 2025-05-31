import httpx
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import ValidationError

# Assuming models.py is in the same directory or src.ultibot_ui is in PYTHONPATH
from src.ultibot_ui.models import PortfolioSnapshot, MarketData, Notification, Kline # Added Kline for MarketData

class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1/"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    def _show_loading(self, message: str):
        print(f"Loading: {message}")

    def _hide_loading(self):
        print("Loading finished.")

    def _show_error(self, message: str):
        print(f"Error: {message}")

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None, # Added for POST/PUT requests
    ) -> Optional[Any]:
        self._show_loading(f"Fetching {endpoint}...")
        try:
            response = await self.client.request(
                method, self.base_url + endpoint, params=params, json=json_data
            )
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx
            return response.json()
        except httpx.RequestError as e:
            self._show_error(f"Request error for {endpoint}: {e}")
            return None
        except httpx.HTTPStatusError as e:
            self._show_error(
                f"HTTP status error for {endpoint}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e: # Catch any other unexpected errors
            self._show_error(f"An unexpected error occurred for {endpoint}: {e}")
            return None
        finally:
            self._hide_loading()

    async def get_portfolio_summary(self, user_id: UUID) -> Optional[PortfolioSnapshot]:
        # Assuming user_id might be part of auth or path, not query param here as per current spec
        # If it were a query param: params={"user_id": str(user_id)}
        data = await self._request("GET", f"portfolio/summary/{user_id}") # Adjusted to include user_id in path
        if data:
            try:
                return PortfolioSnapshot.parse_obj(data)
            except ValidationError as e:
                self._show_error(f"Portfolio summary validation error: {e}")
                return None
        return None

    async def get_market_historical_data(
        self, asset_id: str, interval: str
    ) -> Optional[MarketData]:
        # The MarketData model expects asset_id and interval, so we pass them to it.
        # The API endpoint likely returns a list of klines directly.
        params = {"asset_id": asset_id, "interval": interval}
        raw_klines_data = await self._request("GET", "market/historical-data", params=params)
        if raw_klines_data:
            try:
                # Assuming the endpoint returns a list of kline arrays/objects
                # and MarketData model expects a list of Kline model instances.
                # Also, our MarketData model includes asset_id and interval.
                return MarketData.parse_obj({
                    "asset_id": asset_id,
                    "interval": interval,
                    "klines": raw_klines_data # Assumes raw_klines_data is List[Dict] or List[List]
                })
            except ValidationError as e:
                self._show_error(f"Market data validation error for {asset_id}: {e}")
                return None
        return None

    async def get_notification_history(self, user_id: UUID) -> Optional[List[Notification]]:
        # Assuming user_id might be part of auth or path.
        # If it were a query param: params={"user_id": str(user_id)}
        data = await self._request("GET", f"notifications/history/{user_id}") # Adjusted to include user_id in path
        if data and isinstance(data, list):
            try:
                return [Notification.parse_obj(item) for item in data]
            except ValidationError as e:
                self._show_error(f"Notification history validation error: {e}")
                return None
        elif data:
            self._show_error("Notification history was not a list.")
        return None

    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict]:
        """Fetches user configuration data."""
        # Example endpoint, adjust as necessary
        data = await self._request("GET", f"users/{user_id}/configuration")
        if data and isinstance(data, dict):
            return data
        elif data:
            self._show_error("User configuration was not a dictionary.")
        return None

    async def save_user_configuration(self, user_id: UUID, config_data: Dict) -> bool:
        """Saves user configuration data."""
        # Example endpoint, adjust as necessary
        response_data = await self._request(
            "POST", f"users/{user_id}/configuration", json_data=config_data
        )
        # Assuming backend returns a success message or the saved config
        # For simplicity, returning True if request didn't explicitly fail (returned None)
        return response_data is not None

    async def get_tickers_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches current ticker data for a list of symbols.
        Example endpoint: /market/tickers?symbols=BTC-USD,ETH-USD
        Simulated response structure: {'SYMBOL': {'lastPrice': X, 'priceChangePercent': Y, 'quoteVolume': Z}}
        """
        if not symbols:
            return {}
        params = {"symbols": ",".join(symbols)}
        data = await self._request("GET", "market/tickers", params=params)
        if data and isinstance(data, dict):
            return data
        # Simulate data if API call fails for now, to allow UI development
        # In a real scenario, proper error handling or returning None is better.
        # self._show_error("Failed to fetch tickers data or data was not a dict, returning simulated data.")
        # simulated_data = {
        #     symbol: {"lastPrice": "N/A", "priceChangePercent": "N/A", "quoteVolume": "N/A", "error": "No data"}
        #     for symbol in symbols
        # }
        # return simulated_data
        return None # Return None if actual API call fails or returns unexpected data

    async def close(self):
        """Closes the underlying httpx client."""
        await self.client.aclose()
        print("ApiClient closed.")

# Example Usage (Optional - for testing purposes)
async def main():
    client = ApiClient()

    # Mock user_id for testing
    test_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    print("\n--- Testing Get Portfolio Summary ---")
    # This will likely fail if the backend isn't running or if the user_id isn't valid
    portfolio = await client.get_portfolio_summary(user_id=test_user_id)
    if portfolio:
        print(f"Portfolio: {portfolio.total_value}, Cash: {portfolio.cash_balance}")
        for holding in portfolio.holdings:
            print(f"  Holding: {holding.asset_id}, Qty: {holding.quantity}")

    print("\n--- Testing Get Market Historical Data ---")
    # This will likely fail if the backend isn't running
    market_data = await client.get_market_historical_data(asset_id="BTC-USD", interval="1h")
    if market_data:
        print(f"Market Data for {market_data.asset_id} ({market_data.interval}):")
        if market_data.klines:
            print(f"  First Kline: {market_data.klines[0]}")
            print(f"  Number of Klines: {len(market_data.klines)}")
        else:
            print("  No klines data received.")

    print("\n--- Testing Get Notification History ---")
    # This will likely fail if the backend isn't running or if the user_id isn't valid
    notifications = await client.get_notification_history(user_id=test_user_id)
    if notifications:
        print("Notifications:")
        for notif in notifications:
            print(f"  [{notif.timestamp}] {notif.message} (Read: {notif.read_status})")

    await client.close()

if __name__ == "__main__":
    import asyncio
    # To run this example:
    # 1. Make sure your backend API is running at http://localhost:8000/api/v1/
    # 2. You might need to adjust the example calls based on actual available data.
    # asyncio.run(main()) # Commented out as it requires a running event loop and backend
    print("ApiClient structure defined. Uncomment asyncio.run(main()) and run with a backend for testing.")
