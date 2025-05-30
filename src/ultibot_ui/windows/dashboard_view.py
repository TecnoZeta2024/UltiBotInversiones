from uuid import UUID

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
from PySide6.QtCore import Qt

# Services (UI Layer)
from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.services.ui_config_service import UIConfigService

# Widgets
from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.notification_widget import NotificationWidget


class DashboardView(QWidget):
    def __init__(self, user_id: UUID, market_data_service: UIMarketDataService, config_service: UIConfigService, parent: QWidget | None = None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service

        self.setWindowTitle(f"UltiBot Dashboard - User: {str(self.user_id)[:8]}...") # Show partial user_id
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # --- Top Area: Market Data Widget ---
        # This widget shows overall market tickers, favorite pairs, etc.
        self.market_data_widget = MarketDataWidget(self.user_id, self.market_data_service, self.config_service)

        # --- Center Area: Portfolio and Charts ---
        # This will be split horizontally: Portfolio on the left, Charts on the right.
        self.portfolio_widget = PortfolioWidget(self.user_id, self.market_data_service)
        self.chart_widget = ChartWidget(self.user_id, self.market_data_service) # UserID might not be directly used by chart for now

        center_splitter = QSplitter(Qt.Orientation.Horizontal)
        center_splitter.addWidget(self.portfolio_widget)
        center_splitter.addWidget(self.chart_widget)
        # Set initial relative sizes for portfolio and chart areas
        # These are proportions, not fixed pixels, so they adapt to window size.
        center_splitter.setStretchFactor(0, 1) # Portfolio widget takes 1 part
        center_splitter.setStretchFactor(1, 2) # Chart widget takes 2 parts (larger)
        # Or, set initial sizes (can be adjusted by user)
        # center_splitter.setSizes([300, 600]) # Example initial pixel sizes


        # --- Bottom Area: Notifications ---
        # This widget will display user notifications.
        self.notification_widget = NotificationWidget(self.user_id, self.market_data_service) # UIMarketDataService has notification fetching

        # --- Main Vertical Splitter ---
        # This splitter will divide the dashboard vertically:
        # Top: MarketDataWidget
        # Middle: CenterSplitter (Portfolio + Charts)
        # Bottom: NotificationWidget

        # We can have a top-level splitter for MarketDataWidget vs the rest
        # And another one for (Portfolio+Charts) vs Notifications

        # Let's try:
        # Top: MarketDataWidget
        # Bottom_Half: Splitter ( (Portfolio + Chart_Widget) + Notification_Widget )

        # Main layout structure:
        # MarketDataWidget (top_zone)
        # MainContentSplitter (vertical)
        #   -> CenterSplitter (Portfolio | Chart) (center_zone)
        #   -> NotificationWidget (bottom_zone)

        main_content_splitter = QSplitter(Qt.Orientation.Vertical)
        main_content_splitter.addWidget(center_splitter) # Portfolio and Charts
        main_content_splitter.addWidget(self.notification_widget) # Notifications

        # Set initial relative sizes for main content areas
        main_content_splitter.setStretchFactor(0, 3) # Portfolio/Charts area takes 3 parts
        main_content_splitter.setStretchFactor(1, 1) # Notifications area takes 1 part
        # main_content_splitter.setSizes([600, 200]) # Example initial pixel sizes


        # Add Market Data Widget and the Main Content Splitter to the main layout
        main_layout.addWidget(self.market_data_widget, 1) # Give it some stretch factor
        main_layout.addWidget(main_content_splitter, 3)  # Give more stretch to the main content

        # Set initial window size (optional, can be done by MainWindow)
        # self.resize(1200, 800)


    def cleanup(self):
        """
        Clean up resources used by child widgets.
        This might involve stopping timers, closing websocket connections (if any), etc.
        """
        print("Cleaning up DashboardView and its child widgets...")
        if hasattr(self.market_data_widget, 'cleanup') and callable(getattr(self.market_data_widget, 'cleanup')):
            self.market_data_widget.cleanup()
        if hasattr(self.portfolio_widget, 'cleanup') and callable(getattr(self.portfolio_widget, 'cleanup')):
            self.portfolio_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup') and callable(getattr(self.chart_widget, 'cleanup')):
            self.chart_widget.cleanup()
        if hasattr(self.notification_widget, 'cleanup') and callable(getattr(self.notification_widget, 'cleanup')):
            self.notification_widget.cleanup()
        print("DashboardView cleanup finished.")

    def showEvent(self, event):
        """Adjust splitter sizes after the window is shown and sized."""
        super().showEvent(event)
        # It's often better to set stretch factors or use layouts that manage sizes.
        # Setting fixed sizes in showEvent can be tricky if the window is resized later by user.
        # However, for initial setup:
        # self.center_splitter.setSizes([self.width() // 3, 2 * self.width() // 3])
        # self.main_content_splitter.setSizes([ (self.height() * 3) // 4, self.height() // 4])
        # Using stretch factors in _setup_ui is generally more robust.
        # No explicit size setting here if stretch factors are used.

# Example Usage (for testing DashboardView itself)
if __name__ == '__main__':
    import sys
    import qasync
    from PySide6.QtWidgets import QApplication
    from src.ultibot_ui.services.api_client import ApiClient # For mock services

    # --- Mock Services ---
    class MockDashboardApiClient(ApiClient):
        # Implement mock methods for all endpoints used by the child widgets
        # For simplicity, we can reuse the mocks from individual widget tests if they are compatible
        # or create more specific ones here.

        # MarketDataWidget needs: get_user_configuration, save_user_configuration, get_tickers_data
        async def get_user_configuration(self, user_id: UUID) -> dict | None:
            print(f"[MockDashboard] get_user_configuration for {user_id}")
            return {"favoritePairs": ["BTC-USD", "ETH-USD"]}

        async def save_user_configuration(self, user_id: UUID, config_data: dict) -> bool:
            print(f"[MockDashboard] save_user_configuration for {user_id}: {config_data}")
            return True

        async def get_tickers_data(self, symbols: list[str]) -> dict | None:
            print(f"[MockDashboard] get_tickers_data for {symbols}")
            data = {}
            for sym in symbols:
                price = 20000 + sum(ord(c) for c in sym) % 5000 # pseudo-random price
                change = (sum(ord(c) for c in sym) % 10) - 5
                data[sym] = {"lastPrice": f"{price:.2f}", "priceChangePercent": f"{change:.2f}", "quoteVolume": f"{price*100:.0f}"}
            return data

        # PortfolioWidget needs: get_portfolio_summary
        async def get_portfolio_summary(self, user_id: UUID) -> PortfolioSnapshot | None:
            from src.ultibot_ui.models import AssetHolding, PortfolioSnapshot # Local import for clarity
            from datetime import datetime
            print(f"[MockDashboard] get_portfolio_summary for {user_id}")
            holdings = [
                AssetHolding(asset_id="BTC-USD", quantity=0.5, average_purchase_price=30000.00, current_value=32500.00),
                AssetHolding(asset_id="ETH-USD", quantity=10.0, average_purchase_price=2000.00, current_value=22000.00),
            ]
            return PortfolioSnapshot(
                snapshot_id=uuid.uuid4(), timestamp=datetime.now(), user_id=user_id,
                holdings=holdings, total_value=54500.00, cash_balance=1234.56
            )

        # ChartWidget needs: get_market_historical_data
        async def get_market_historical_data(self, asset_id: str, interval: str) -> MarketData | None:
            from src.ultibot_ui.models import Kline, MarketData # Local import
            from datetime import datetime
            import numpy as np
            print(f"[MockDashboard] get_market_historical_data for {asset_id} ({interval})")
            klines_list = []
            current_time = datetime.now().timestamp() * 1000
            price = 100.0
            for i in range(50):
                open_p = price + np.random.uniform(-1,1)
                high_p = max(open_p, price + np.random.uniform(0,2))
                low_p = min(open_p, price - np.random.uniform(0,2))
                close_p = np.random.uniform(low_p, high_p)
                kline_ts = int(current_time - (50 - i) * (60000 * (["1m","5m","1h","1d"].index(interval if interval in ["1m","5m","1h","1d"] else "1m") +1 )))
                klines_list.append(Kline(timestamp=kline_ts, open=open_p, high=high_p, low=low_p, close=close_p, volume=np.random.uniform(100,1000)))
                price = close_p
            return MarketData(asset_id=asset_id, interval=interval, klines=klines_list)

        # NotificationWidget needs: get_notification_history
        async def get_notification_history(self, user_id: UUID) -> list[Notification] | None:
            from src.ultibot_ui.models import Notification # Local import
            from datetime import datetime
            print(f"[MockDashboard] get_notification_history for {user_id}")
            return [
                Notification(notification_id=uuid.uuid4(), user_id=user_id, message="Welcome to UltiBot Dashboard!", timestamp=datetime.now(), read_status=False, type="INFO"),
                Notification(notification_id=uuid.uuid4(), user_id=user_id, message="BTC price alert triggered.", timestamp=datetime.now(), read_status=True, type="PRICE_ALERT"),
            ]

        async def close(self): # Ensure mock client has a close method
            print("[MockDashboard] ApiClient closed.")


    async def main_async_dashboard():
        app = QApplication.instance() or QApplication(sys.argv)

        # Setup mock services
        mock_api_client = MockDashboardApiClient()
        market_data_service = UIMarketDataService(api_client=mock_api_client)
        config_service = UIConfigService(api_client=mock_api_client) # UIConfigService also uses ApiClient

        test_user_id = uuid.uuid4()
        config_service.set_user_id(test_user_id) # Important for UIConfigService operations

        dashboard_view = DashboardView(user_id=test_user_id, market_data_service=market_data_service, config_service=config_service)
        dashboard_view.resize(1600, 900) # Set a larger default size for the dashboard
        dashboard_view.show()

        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        try:
            await loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            dashboard_view.cleanup() # Call cleanup on the dashboard
            await mock_api_client.close() # Close the mock client

    if __name__ == "__main__":
        try:
            qasync.run(main_async_dashboard())
        except RuntimeError as e:
            if "another loop is running" not in str(e).lower():
                 raise
        except KeyboardInterrupt:
            print("DashboardView test application terminated.")
        print("Exiting DashboardView example.")
