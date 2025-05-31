import asyncio
import uuid # For UUID type hinting and example
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PySide6.QtCore import Qt, Signal as pyqtSignal, QTimer # Added QTimer

from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.models import PortfolioSnapshot, AssetHolding # Assuming models are correctly defined

# For example usage and potential styling
from PySide6.QtGui import QColor
from PySide6.QtCore import QDateTime


class PortfolioWidget(QWidget):
    # data_updated = pyqtSignal(PortfolioSnapshot) # Example if needed for external updates

    def __init__(self, user_id: uuid.UUID, market_data_service: UIMarketDataService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service

        self._init_ui()
        asyncio.create_task(self.refresh_data())

        # Auto-refresh timer
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_data()))
        self.auto_refresh_timer.start(60000) # Refresh every 60 seconds

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Title Label
        title_label = QLabel("Portfolio Overview")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Consider making title_label font larger if desired
        # font = title_label.font()
        # font.setPointSize(16)
        # title_label.setFont(font)
        layout.addWidget(title_label)

        # Summary Labels
        self.total_value_label = QLabel("Total Portfolio Value: N/A")
        layout.addWidget(self.total_value_label)

        self.cash_balance_label = QLabel("Cash Balance: N/A") # Modified from "Total Cash Balance" for brevity
        layout.addWidget(self.cash_balance_label)

        # Assets Table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(4)
        self.assets_table.setHorizontalHeaderLabels(["Asset", "Quantity", "Avg. Price", "Current Value"]) # Changed "Current Price" to "Avg. Price" to match AssetHolding
        self.assets_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.assets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.assets_table)

        # Refresh Button
        self.refresh_button = QPushButton("Refresh Portfolio")
        self.refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh_data()))
        layout.addWidget(self.refresh_button)

        # Status Label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Apply some basic styling (optional)
        # self._apply_styles()

    async def refresh_data(self):
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Loading portfolio...")
        try:
            portfolio_snapshot: Optional[PortfolioSnapshot] = await self.market_data_service.fetch_portfolio_summary(self.user_id)

            if portfolio_snapshot:
                self.update_ui(portfolio_snapshot)
                self.status_label.setText(f"Portfolio updated: {QDateTime.currentDateTime().toString()}")
            else:
                self.total_value_label.setText("Total Portfolio Value: Error")
                self.cash_balance_label.setText("Cash Balance: Error")
                self.assets_table.setRowCount(0) # Clear table
                self.status_label.setText("Error loading portfolio. Service returned no data.")
        except Exception as e:
            self.total_value_label.setText("Total Portfolio Value: Error")
            self.cash_balance_label.setText("Cash Balance: Error")
            self.assets_table.setRowCount(0)
            self.status_label.setText(f"Error loading portfolio: {e}")
        finally:
            self.refresh_button.setEnabled(True)

    def update_ui(self, snapshot: PortfolioSnapshot):
        # Using model field names as defined in models.py
        # Assuming PortfolioSnapshot has: total_value, cash_balance, holdings, timestamp
        # Assuming AssetHolding has: asset_id, quantity, average_purchase_price, current_value

        self.total_value_label.setText(f"Total Portfolio Value: {snapshot.total_value:.2f}") # Removed currency for now, can be added if available in model
        self.cash_balance_label.setText(f"Cash Balance: {snapshot.cash_balance:.2f}")

        self.assets_table.setRowCount(len(snapshot.holdings))
        for i, holding in enumerate(snapshot.holdings):
            self.assets_table.setItem(i, 0, QTableWidgetItem(holding.asset_id))
            self.assets_table.setItem(i, 1, QTableWidgetItem(f"{holding.quantity:.8f}"))

            avg_price_str = f"{holding.average_purchase_price:.2f}" if holding.average_purchase_price is not None else "N/A"
            self.assets_table.setItem(i, 2, QTableWidgetItem(avg_price_str))

            current_value_str = f"{holding.current_value:.2f}" if holding.current_value is not None else "N/A"
            self.assets_table.setItem(i, 3, QTableWidgetItem(current_value_str))

        # Update status with snapshot timestamp
        self.status_label.setText(f"Portfolio as of: {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        self.auto_refresh_timer.stop()
        print("PortfolioWidget timer stopped.")

    def _apply_styles(self):
        # Example basic styling (can be expanded)
        self.setStyleSheet("""
            QLabel { font-size: 14px; }
            QPushButton { padding: 5px; font-size: 14px; }
            QTableWidget { font-size: 13px; }
            QHeaderView::section { background-color: #4a4a4a; color: white; padding: 4px; border: 1px solid #6c6c6c; }
        """)
        # For dark theme table items (if not handled by overall app theme)
        # self.assets_table.setStyleSheet("QTableWidgetItem { color: #cccccc; background-color: #3a3a3a; }")


# Example Usage (requires qasync for running asyncio with PySide6/PyQt)
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    import qasync # Required for asyncio integration with Qt

    # --- Mocking Services and Models ---
    from src.ultibot_ui.services.api_client import ApiClient # For UIMarketDataService

    class MockApiClient(ApiClient): # Use the actual ApiClient for structure
        async def get_portfolio_summary(self, user_id: uuid.UUID) -> Optional[PortfolioSnapshot]:
            print(f"MockApiClient: Fetching portfolio for user {user_id}")
            await asyncio.sleep(1) # Simulate network delay
            if user_id == uuid.UUID("00000000-0000-0000-0000-000000000001"): # Known user
                holdings = [
                    AssetHolding(asset_id="BTC", quantity=0.5, average_purchase_price=30000.00, current_value=32500.00),
                    AssetHolding(asset_id="ETH", quantity=10.0, average_purchase_price=2000.00, current_value=22000.00),
                    AssetHolding(asset_id="USDT", quantity=1000.0, average_purchase_price=1.00, current_value=1000.00), # Cash-like asset
                ]
                return PortfolioSnapshot(
                    snapshot_id=uuid.uuid4(),
                    timestamp=QDateTime.currentDateTime().toPython(), # Use Python datetime
                    user_id=user_id,
                    holdings=holdings,
                    total_value=55500.00, # Sum of current_value
                    cash_balance=1000.00 # Could be one of the holdings or separate
                )
            return None

    # --- Main Application Setup ---
    async def main_async():
        app = QApplication.instance() or QApplication(sys.argv)

        # Create mock services
        mock_api_client = MockApiClient() # No base_url needed if methods are overridden
        market_data_service = UIMarketDataService(api_client=mock_api_client)

        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        portfolio_widget = PortfolioWidget(user_id=test_user_id, market_data_service=market_data_service)
        portfolio_widget.setWindowTitle("Portfolio Widget Test")
        portfolio_widget.resize(600, 400)
        portfolio_widget.show()

        # qasync event loop
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        try:
            await loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            portfolio_widget.cleanup() # Test cleanup
            if hasattr(mock_api_client, 'close'): # If ApiClient has a close method
                 await mock_api_client.close()


    if __name__ == "__main__":
        # It's often better to run qasync.run outside the main_async for cleaner setup
        # However, for a single widget test, this structure works.
        try:
            qasync.run(main_async())
        except RuntimeError as e:
            if "another loop is running" in str(e).lower():
                print("Asyncio loop already running. This can happen in some environments (e.g. Spyder).")
            else:
                raise
        except KeyboardInterrupt:
            print("Test application terminated.")
        print("Exiting example.")
