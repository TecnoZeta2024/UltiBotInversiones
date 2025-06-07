from typing import Optional, List, Dict, Any 
from uuid import UUID

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.shared.data_types import PortfolioSnapshot, MarketData, Notification, Kline, Ticker

class UIMarketDataService:
    def __init__(self, api_client: UltiBotAPIClient):
        self.api_client = api_client

    async def fetch_portfolio_summary(self, user_id: UUID, trading_mode: str) -> Optional[PortfolioSnapshot]:
        """
        Fetches the portfolio summary for a given user and trading mode.
        """
        return await self.api_client.get_portfolio_snapshot(user_id, trading_mode)

    async def fetch_historical_market_data(
        self, symbol: str, interval: str, limit: int = 200
    ) -> Optional[List[Kline]]:
        """
        Fetches historical kline data for a given asset and interval.
        """
        return await self.api_client.get_candlestick_data(symbol, interval, limit)

    async def fetch_notification_history(self, limit: int = 20, offset: int = 0) -> Optional[List[Notification]]:
        """
        Fetches the notification history.
        """
        return await self.api_client.get_notification_history(limit, offset)

    async def fetch_tickers_data(self, symbols: List[str]) -> Optional[Dict[str, Ticker]]:
        """
        Fetches current ticker data for a list of symbols.
        """
        return await self.api_client.get_tickers_data(symbols)

    async def close_services(self):
        """
        Placeholder for any cleanup if needed.
        """
        print("UIMarketDataService closed.")
