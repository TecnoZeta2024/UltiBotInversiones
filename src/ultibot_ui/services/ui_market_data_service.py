from typing import Optional, List, Dict, Any # Added Dict, Any
from uuid import UUID

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.models import PortfolioSnapshot, MarketData, Notification, Kline # Added Kline

class UIMarketDataService:
    def __init__(self, api_client: UltiBotAPIClient):
        self.api_client = api_client
        # Removed: self.backend_market_data_service = backend_market_data_service
        # Removed: self.websocket_clients = {}
        # Removed: self.websocket_thread = None
        # Removed: self.stop_event = threading.Event()
        # Removed: self.message_queue = queue.Queue()

    async def fetch_portfolio_summary(self, user_id: UUID) -> Optional[PortfolioSnapshot]:
        """
        Fetches the portfolio summary for a given user.
        """
        return await self.api_client.get_portfolio_summary(user_id)

    async def fetch_historical_market_data(
        self, asset_id: str, interval: str
    ) -> Optional[MarketData]:
        """
        Fetches historical market data for a given asset and interval.
        (Note: 'symbol' in original plan changed to 'asset_id' to match ApiClient and models)
        """
        return await self.api_client.get_market_historical_data(asset_id, interval)

    async def fetch_notification_history(self, user_id: UUID) -> Optional[List[Notification]]:
        """
        Fetches the notification history for a given user.
        """
        return await self.api_client.get_notification_history(user_id)

    async def fetch_tickers_data(self, symbols: List[str]) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Fetches current ticker data for a list of symbols.
        """
        return await self.api_client.get_tickers_data(symbols)

    # Removed get_market_data_rest as it's replaced by fetch_historical_market_data (for klines)
    # and fetch_tickers_data (for current prices).
    # Removed subscribe_to_market_data_websocket, unsubscribe_from_market_data_websocket
    # as WebSocket handling is deferred and not part of ApiClient for now.
    # Removed _start_websocket_thread, _process_websocket_messages, _handle_websocket_message
    # Removed get_all_binance_symbols as its source (direct Binance call or other backend service)
    # would now be through ApiClient if it were a defined backend endpoint.
    # If a generic "get_tradable_assets" endpoint exists, a new method could be added.

    # Example of how a method for fetching all available symbols/assets might look if
    # there was a corresponding ApiClient method and backend endpoint:
    # async def get_available_assets(self) -> Optional[List[SomeAssetInfoModel]]:
    #     return await self.api_client.get_available_assets_list()

    async def close_services(self):
        """
        Placeholder for any cleanup if needed.
        The ApiClient's close method should be called separately by the application manager.
        """
        # self.stop_event.set()
        # if self.websocket_thread and self.websocket_thread.is_alive():
        #     self.websocket_thread.join()
        # for ws_client in self.websocket_clients.values():
        #     if ws_client:
        #         await ws_client.close() # Assuming ws_client has an async close
        print("UIMarketDataService closed (if any stateful resources were managed here).")

# Note: The original MockUIMarketDataService and its methods like get_all_binance_symbols
# and the WebSocket logic were significantly different. This refactoring assumes that
# REST API calls via ApiClient are the primary mode of data fetching for now.
# If WebSockets are reintroduced, they'll need a dedicated client and integration strategy.
