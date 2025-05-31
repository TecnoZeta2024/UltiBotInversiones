import asyncio # Added for api_client.close()
from PySide6.QtWidgets import QMainWindow, QStatusBar, QLabel, QWidget, QHBoxLayout, QStackedWidget, QPushButton
from PySide6.QtCore import Qt
from uuid import UUID

from src.ultibot_ui.windows.dashboard_view import DashboardView # Corrected path
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget # Corrected path

# Updated service imports
from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.services.ui_config_service import UIConfigService
from src.ultibot_ui.services.api_client import ApiClient # Added ApiClient

class MainWindow(QMainWindow):
    def __init__(self, user_id: UUID,
                 market_data_service: UIMarketDataService,
                 config_service: UIConfigService,
                 api_client: ApiClient): # Added api_client
        super().__init__()
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.api_client = api_client # Store api_client

        self.setWindowTitle("UltiBot Dashboard") # Updated title
        self.setGeometry(100, 100, 1600, 900) # Adjusted default size

        self._create_status_bar()
        self._setup_central_widget()

    def _create_status_bar(self):
        self.statusBar = QStatusBar() # Corrected: QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

        # Example: Connection status label (can be updated by services)
        self.connection_status_label = QLabel("Connection: OK") # Placeholder
        self.statusBar.addPermanentWidget(self.connection_status_label)

    def _setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins for a clean look
        main_layout.setSpacing(0) # No spacing between sidebar and content

        # Sidebar Navigation
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(180) # Slightly narrower sidebar
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        # Content Area (StackedWidget)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- Initialize Views ---
        # Dashboard View
        self.dashboard_view = DashboardView(self.user_id, self.market_data_service, self.config_service)
        self.stacked_widget.addWidget(self.dashboard_view)

        # Placeholder views for other sections
        self.opportunities_view = QLabel("Opportunities View (Placeholder)")
        self.opportunities_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.opportunities_view)

        self.strategies_view = QLabel("Strategies View (Placeholder)")
        self.strategies_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.strategies_view)

        self.trading_history_view = QLabel("Trading History View (Placeholder)")
        self.trading_history_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.trading_history_view)

        self.settings_view = QLabel("Settings View (Placeholder)")
        self.settings_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.settings_view)

        # View mapping for navigation
        self.view_map = {
            "dashboard": 0,
            "opportunities": 1,
            "strategies": 2,
            "history": 3, # Corrected from trading_history_view variable name to key "history"
            "settings": 4,
        }

        # Set initial view to Dashboard
        # Ensure sidebar button is checked (if sidebar has checkable buttons)
        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button: # This relies on objectName being set in SidebarNavigationWidget
            dashboard_button.setChecked(True)
        self.stacked_widget.setCurrentIndex(self.view_map["dashboard"])


    def _switch_view(self, view_name: str):
        index = self.view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
            self.statusBar.showMessage(f"{view_name.capitalize()} view active")
        else:
            self.statusBar.showMessage(f"Error: View '{view_name}' not found.")

    def closeEvent(self, event):
        """Handle the window close event."""
        print("Closing application via MainWindow closeEvent...")

        # Cleanup child widgets (like DashboardView and its children)
        if hasattr(self, 'dashboard_view') and self.dashboard_view is not None:
            if hasattr(self.dashboard_view, 'cleanup') and callable(getattr(self.dashboard_view, 'cleanup')):
                print("Calling dashboard_view.cleanup()...")
                self.dashboard_view.cleanup()

        # Close the ApiClient
        if hasattr(self, 'api_client') and self.api_client is not None:
            print("Closing API client from MainWindow...")
            # Running an async function from a synchronous method like closeEvent
            # can be tricky. qasync might handle tasks created here, but it's often
            # better if the application's main async shutdown orchestrates this.
            # However, creating a task is a common approach.
            if asyncio.get_event_loop().is_running():
                 asyncio.create_task(self.api_client.close())
            else:
                 # If loop not running, try to run it to completion for this task.
                 # This is less ideal. Best if qasync manages loop until all tasks are done.
                 try:
                    asyncio.run(self.api_client.close()) # This might fail if loop is closed/closing
                 except RuntimeError as e:
                    print(f"RuntimeError during api_client.close() in closeEvent: {e}. May already be closing.")

        super().closeEvent(event)
