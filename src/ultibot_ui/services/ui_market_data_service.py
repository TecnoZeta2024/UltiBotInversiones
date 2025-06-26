from typing import Optional, List, Dict, Any 
from uuid import UUID

from ultibot_ui.services.api_client import UltiBotAPIClient
from shared.data_types import PortfolioSnapshot, MarketData, Notification, Kline, Ticker

class UIMarketDataService:
    def __init__(self, api_client: UltiBotAPIClient):
        self.api_client = api_client

    async def fetch_portfolio_summary(self, user_id: UUID) -> Optional[PortfolioSnapshot]:
        """
        Fetches the portfolio summary for a given user.
        """
        snapshot_data = await self.api_client.get_portfolio_snapshot(user_id)
        if snapshot_data:
            return PortfolioSnapshot.model_validate(snapshot_data)
        return None

    async def fetch_historical_market_data(
        self, symbol: str, interval: str, limit: int = 200
    ) -> Optional[List[Kline]]:
        """
        Fetches historical kline data for a given asset and interval.
        """
        klines_data = await self.api_client.get_ohlcv_data(symbol, interval, limit)
        if klines_data:
            return [Kline.model_validate(k) for k in klines_data]
        return None

    async def fetch_notification_history(self, limit: int = 20) -> Optional[List[Notification]]:
        """
        Fetches the notification history.
        """
        notifications_data = await self.api_client.get_notification_history(limit)
        if notifications_data:
            return [Notification.model_validate(n) for n in notifications_data]
        return None

    async def fetch_tickers_data(self, symbols: List[str]) -> Optional[Dict[str, Ticker]]:
        """
        Fetches current ticker data for a list of symbols.
        """
        tickers_data = await self.api_client.get_market_data(symbols)
        if tickers_data:
            # Asumiendo que get_market_data devuelve un diccionario donde las claves son símbolos
            # y los valores son los datos del ticker.
            return {symbol: Ticker.model_validate(data) for symbol, data in tickers_data.items()}
        return None

    async def close_services(self):
        """
        Placeholder for any cleanup if needed.
        """
        print("UIMarketDataService closed.")
