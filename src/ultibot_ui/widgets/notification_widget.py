import asyncio
import uuid # For UUID type hinting and example
from typing import Optional, List
from datetime import datetime # For formatting notification timestamps

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QApplication # Added QApplication for example
)
from PySide6.QtCore import Qt, QSize, QTimer # Added QTimer, QSize
from PySide6.QtGui import QFont, QColor # For styling items

from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService # Using this service for now
from src.ultibot_ui.models import Notification # Assuming Notification model is correctly defined

class NotificationWidget(QWidget):
    def __init__(self, user_id: uuid.UUID, data_service: UIMarketDataService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        # Assuming UIMarketDataService has fetch_notification_history method
        self.data_service = data_service

        self._init_ui()
        asyncio.create_task(self.refresh_notifications())

        # Auto-refresh timer
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(lambda: asyncio.create_task(self.refresh_notifications()))
        self.auto_refresh_timer.start(120000) # Refresh every 120 seconds (2 minutes)


    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Title Label
        title_label = QLabel("Notifications")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Notification List
        self.notification_list_widget = QListWidget()
        # self.notification_list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection) # Optional
        layout.addWidget(self.notification_list_widget)

        # Refresh Button
        self.refresh_button = QPushButton("Refresh Notifications")
        self.refresh_button.clicked.connect(lambda: asyncio.create_task(self.refresh_notifications()))
        layout.addWidget(self.refresh_button)

        # Status Label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    async def refresh_notifications(self):
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Loading notifications...")
        try:
            # Assuming fetch_notification_history is available on the passed data_service
            notifications_data: Optional[List[Notification]] = await self.data_service.fetch_notification_history(self.user_id)

            if notifications_data is not None:
                self.update_notification_list(notifications_data)
                count = len(notifications_data)
                self.status_label.setText(f"{count} notification{'s' if count != 1 else ''} loaded.")
            else:
                self.notification_list_widget.clear()
                self.status_label.setText("Error loading notifications or no data received.")
        except Exception as e:
            self.notification_list_widget.clear()
            self.status_label.setText(f"Error loading notifications: {e}")
        finally:
            self.refresh_button.setEnabled(True)

    def update_notification_list(self, notifications: List[Notification]):
        self.notification_list_widget.clear()

        if not notifications:
            self.status_label.setText("No notifications found.")
            # Optionally, add a placeholder item:
            # placeholder_item = QListWidgetItem("No notifications.")
            # placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags) # Make it non-selectable
            # self.notification_list_widget.addItem(placeholder_item)
            return

        for notif_model in sorted(notifications, key=lambda n: n.timestamp, reverse=True): # Display newest first
            # Model fields: notification_id, user_id, message, timestamp, read_status, type

            # Format the display text for the list item
            # Using strftime for timestamp. Ensure notif_model.timestamp is a datetime object.
            ts_str = notif_model.timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(notif_model.timestamp, datetime) else str(notif_model.timestamp)

            # Example: "ALERT [2023-01-01 10:00:00]: Price of BTC reached $50000"
            # item_text = f"[{notif_model.type.upper()}] {ts_str}\n{notif_model.message}"
            # For simplicity, just message and timestamp for now
            item_text = f"{ts_str}\n{notif_model.message}"

            list_item = QListWidgetItem(item_text)
            list_item.setToolTip(notif_model.message) # Full message on hover

            # Styling based on read_status or type (example)
            item_font = list_item.font()
            if not notif_model.read_status:
                item_font.setBold(True)
                list_item.setFont(item_font)
                # list_item.setBackground(QColor("#e0e0ff")) # Light blue for unread, if desired

            if "alert" in notif_model.type.lower() or "error" in notif_model.type.lower():
                list_item.setForeground(QColor("red"))
            elif "warning" in notif_model.type.lower():
                list_item.setForeground(QColor("orange"))
            elif "success" in notif_model.type.lower() or "confirmation" in notif_model.type.lower():
                 list_item.setForeground(QColor("green"))


            # To make items taller to accommodate two lines of text easily:
            list_item.setSizeHint(QSize(0, 50)) # Width 0 means use default, height 50 pixels

            self.notification_list_widget.addItem(list_item)

    def cleanup(self):
        self.auto_refresh_timer.stop()
        print("NotificationWidget timer stopped.")

# --- Example Usage ---
if __name__ == '__main__':
    import sys
    import qasync # Required for asyncio integration
    from src.ultibot_ui.services.api_client import ApiClient # For UIMarketDataService

    # --- Mocking Services and Models ---
    class MockNotificationApiClient(ApiClient): # Inherit from actual for structure
        async def get_notification_history(self, user_id: uuid.UUID) -> Optional[List[Notification]]:
            print(f"MockNotificationApiClient: Fetching notifications for user {user_id}")
            await asyncio.sleep(0.5)

            # Sample notification data based on the Pydantic model
            # Notification: notification_id, user_id, message, timestamp, read_status, type
            mock_notifications = [
                Notification(
                    notification_id=uuid.uuid4(), user_id=user_id,
                    message="Your trade order for BTC-USD (0.1 BTC @ $50000) has been executed.",
                    timestamp=datetime.now().replace(hour=10, minute=30), read_status=False, type="TRADE_CONFIRMATION"
                ),
                Notification(
                    notification_id=uuid.uuid4(), user_id=user_id,
                    message="ETH price reached your alert threshold of $4000.",
                    timestamp=datetime.now().replace(hour=9, minute=15), read_status=True, type="PRICE_ALERT"
                ),
                Notification(
                    notification_id=uuid.uuid4(), user_id=user_id,
                    message="Scheduled maintenance upcoming in 2 hours.",
                    timestamp=datetime.now().replace(hour=8, minute=0), read_status=False, type="SYSTEM_INFO"
                ),
                 Notification(
                    notification_id=uuid.uuid4(), user_id=user_id,
                    message="This is a very long notification message designed to test the tooltip functionality and how text wrapping or truncation might appear in the QListWidgetItem. If it's too long it should be picked up by the tooltip.",
                    timestamp=datetime.now().replace(hour=7, minute=0), read_status=True, type="INFO"
                ),
            ]
            if user_id == uuid.UUID("00000000-0000-0000-0000-000000000002"): # Specific user for testing
                return mock_notifications
            return [] # Return empty list for other users or on error

    async def main_async_notifications():
        app = QApplication.instance() or QApplication(sys.argv)

        mock_api_client = MockNotificationApiClient()
        # UIMarketDataService is used here as per the plan, assuming it has fetch_notification_history
        data_service = UIMarketDataService(api_client=mock_api_client)

        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000002")

        notification_widget = NotificationWidget(user_id=test_user_id, data_service=data_service)
        notification_widget.setWindowTitle("Notification Widget Test")
        notification_widget.resize(400, 500)
        notification_widget.show()

        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        try:
            await loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            notification_widget.cleanup() # Test cleanup
            if hasattr(mock_api_client, 'close'):
                 await mock_api_client.close()

    if __name__ == "__main__":
        try:
            qasync.run(main_async_notifications())
        except RuntimeError as e:
            if "another loop is running" not in str(e).lower():
                 raise
        except KeyboardInterrupt:
            print("Notification test application terminated.")
        print("Exiting notification example.")
