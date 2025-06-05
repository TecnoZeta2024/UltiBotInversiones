import logging
from uuid import UUID
from typing import List, Dict, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFrame, QSplitter, QScrollArea, QGroupBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QFont, QColor # Added QFont, QColor
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice # Import QtCharts

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager
# ApiWorker se importará localmente para evitar ciclo


logger = logging.getLogger(__name__)

class PortfolioView(QWidget):
    def __init__(self, user_id: UUID, backend_base_url: str, qasync_loop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.backend_base_url = backend_base_url
        self.qasync_loop = qasync_loop # Store the qasync_loop
        self.active_threads: List[QThread] = []
        self.current_portfolio_data: Optional[Dict[str, Any]] = None

        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)

        self._setup_ui()
        QTimer.singleShot(0, self._fetch_portfolio_data) # Load data once UI is set up

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)

        # --- Header ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Portfolio Overview")
        title_label.setObjectName("viewTitleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.mode_indicator_label = QLabel("") # Will show current trading mode
        self._update_mode_indicator_label() # Initialize
        header_layout.addWidget(self.mode_indicator_label)

        self.refresh_button = QPushButton("Refresh Portfolio")
        self.refresh_button.clicked.connect(self._fetch_portfolio_data)
        header_layout.addWidget(self.refresh_button)
        main_layout.addLayout(header_layout)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)

        # --- Main Content Splitter ---
        content_splitter = QSplitter(Qt.Orientation.Horizontal) # CORREGIDO: Qt.Orientation.Horizontal
        main_layout.addWidget(content_splitter, 1) # Give it stretch factor

        # Left Side: Summary and Pie Chart
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setSpacing(15)

        # Summary GroupBox (mock for now, can be expanded)
        summary_group = QGroupBox("Portfolio Summary")
        summary_group.setObjectName("summaryGroup") # For QSS
        summary_layout = QVBoxLayout(summary_group)
        self.total_value_label = QLabel("Total Portfolio Value: N/A")
        self.total_value_label.setObjectName("dataDisplayLabel") # For QSS
        self.available_balance_label = QLabel("Available Balance: N/A")
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addWidget(self.available_balance_label)
        summary_group.setFixedHeight(150) # Example fixed height
        left_panel_layout.addWidget(summary_group)

        # Asset Distribution Chart
        self.chart_group = QGroupBox("Asset Distribution") # Made it a class member
        self.chart_group.setObjectName("assetDistributionChartGroup")
        chart_layout = QVBoxLayout(self.chart_group)
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        chart_layout.addWidget(self.pie_chart_view)
        left_panel_layout.addWidget(self.chart_group, 1)
        # self._apply_shadow_effect(self.chart_group) # Apply shadow to chart group - TEMPORARILY COMMENTED OUT

        content_splitter.addWidget(left_panel_widget)

        # Right Side: Detailed Assets Table
        self.assets_group = QGroupBox("Detailed Asset Breakdown") # Made it a class member
        self.assets_group.setObjectName("detailedAssetsGroup")
        assets_layout = QVBoxLayout(self.assets_group)
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(6) # Symbol, Quantity, Entry Price, Current Price, Value (USD), PnL (%)
        self.assets_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg. Entry Price", "Current Price", "Current Value (USD)", "Unrealized PnL (%)"
        ])
        h_header = self.assets_table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.Stretch)
        v_header = self.assets_table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        self.assets_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assets_table.setAlternatingRowColors(True)
        assets_layout.addWidget(self.assets_table)
        content_splitter.addWidget(self.assets_group) # CORREGIDO: self.assets_group

        content_splitter.setSizes([self.width() // 3, 2 * self.width() // 3]) # Initial sizing

    def _update_mode_indicator_label(self):
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.mode_indicator_label.setText(f"Mode: {mode_info['display_name']}")
        self.mode_indicator_label.setStyleSheet(f"font-weight: bold; color: {mode_info['color']}; padding: 4px; border-radius: 4px; background-color: {mode_info['color']}22;")


    def _on_trading_mode_changed(self, new_mode: str):
        logger.info(f"PortfolioView: Trading mode changed to {new_mode}. Refreshing data.")
        self._update_mode_indicator_label()
        self._fetch_portfolio_data()

    def _fetch_portfolio_data(self):
        logger.info("PortfolioView: Fetching portfolio snapshot.")
        self.status_label.setText(f"Loading portfolio data ({self.trading_mode_manager.current_mode.title()})...")
        self.refresh_button.setEnabled(False)
        self.assets_table.setRowCount(0) # Clear table

        # Importar ApiWorker aquí para evitar import circular a nivel de módulo
        from src.ultibot_ui.main import ApiWorker
        # CORREGIDO: pasar factory (lambda), no corutina pre-creada
        worker = ApiWorker(lambda api_client: api_client.get_portfolio_snapshot(
            user_id=self.user_id, trading_mode=self.trading_mode), self.backend_base_url)
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_portfolio_result)
        worker.error_occurred.connect(self._handle_portfolio_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        thread.start()

    def _handle_portfolio_result(self, portfolio_snapshot_dict: Dict[str, Any]):
        logger.info("PortfolioView: Portfolio snapshot data received.")
        self.status_label.setText("Portfolio data loaded successfully.")
        self.refresh_button.setEnabled(True)

        self.current_portfolio_data = portfolio_snapshot_dict

        # Determine which part of the snapshot to use based on current trading mode
        mode_key = f"{self.trading_mode_manager.current_mode}_trading" # e.g., "paper_trading" or "real_trading"
        mode_specific_data = portfolio_snapshot_dict.get(mode_key, {})

        if not mode_specific_data:
            logger.warning(f"PortfolioView: No data found for mode '{self.trading_mode_manager.current_mode}' in snapshot.")
            self.total_value_label.setText("Total Portfolio Value: Data unavailable")
            self.available_balance_label.setText("Available Balance: Data unavailable")
            self.assets_table.setRowCount(0)
            self._update_pie_chart([]) # Empty data
            return

        self.total_value_label.setText(f"Total Portfolio Value: {mode_specific_data.get('total_portfolio_value_usd', 0.0):,.2f} USD")
        currency_suffix = " (Virtual)" if self.trading_mode_manager.current_mode == "paper" else ""
        self.available_balance_label.setText(f"Available Balance: {mode_specific_data.get('available_balance_usdt', 0.0):,.2f} USDT{currency_suffix}")

        assets_list = mode_specific_data.get('assets', [])
        self._populate_assets_table(assets_list)
        self._update_pie_chart(assets_list)


    def _handle_portfolio_error(self, error_message: str):
        logger.error(f"PortfolioView: Error fetching portfolio data: {error_message}")
        self.status_label.setText("Failed to load portfolio data.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Portfolio Data Error",
                            f"Could not load portfolio data.\n"
                            f"Details: {error_message}\n\n"
                            "Please try refreshing or check your connection.")
        self.total_value_label.setText("Total Portfolio Value: Error")
        self.available_balance_label.setText("Available Balance: Error")
        self.assets_table.setRowCount(0)
        self._update_pie_chart([]) # Clear chart

    def _populate_assets_table(self, assets_data: List[Dict[str, Any]]):
        self.assets_table.setRowCount(len(assets_data))
        for row, asset in enumerate(assets_data):
            self.assets_table.setItem(row, 0, QTableWidgetItem(str(asset.get("symbol", "N/A"))))
            self.assets_table.setItem(row, 1, QTableWidgetItem(f"{asset.get('quantity', 0.0):,.8f}"))
            self.assets_table.setItem(row, 2, QTableWidgetItem(f"{asset.get('entry_price', 0.0):,.4f}"))
            self.assets_table.setItem(row, 3, QTableWidgetItem(f"{asset.get('current_price', 0.0):,.4f}"))
            self.assets_table.setItem(row, 4, QTableWidgetItem(f"{asset.get('current_value_usd', 0.0):,.2f}"))

            pnl_pct = asset.get('unrealized_pnl_percentage', 0.0)
            pnl_item = QTableWidgetItem(f"{pnl_pct:,.2f}%")
            if pnl_pct > 0:
                pnl_item.setForeground(QColor(Qt.GlobalColor.green)) # CORREGIDO: QColor(Qt.GlobalColor.green)
            elif pnl_pct < 0:
                pnl_item.setForeground(QColor(Qt.GlobalColor.red))   # CORREGIDO: QColor(Qt.GlobalColor.red)
            self.assets_table.setItem(row, 5, pnl_item)

        if not assets_data:
             if self.assets_table.rowCount() == 0: # Check if it's truly empty
                self.assets_table.setRowCount(1)
                placeholder_item = QTableWidgetItem("No assets to display for this mode.")
                placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # CORREGIDO: Qt.AlignmentFlag.AlignCenter
                self.assets_table.setItem(0, 0, placeholder_item)
                self.assets_table.setSpan(0, 0, 1, self.assets_table.columnCount())


    def _update_pie_chart(self, assets_data: List[Dict[str, Any]]):
        series = QPieSeries()
        total_portfolio_value = sum(asset.get('current_value_usd', 0.0) for asset in assets_data if asset.get('current_value_usd', 0.0) > 0)

        if total_portfolio_value == 0: # No assets or all assets have zero value
            # series.append("No Assets", 1) # Show a placeholder slice
            # Alternatively, clear the chart or show a message
            chart = QChart()
            chart.setTitle("Asset Distribution (No Data)")
            # chart.addSeries(series) # Optional: show the "No Assets" slice
            self.pie_chart_view.setChart(chart)
            return

        # Group small assets into "Others" if there are many
        assets_data.sort(key=lambda x: x.get('current_value_usd', 0.0), reverse=True)
        limit = 5 # Show top 5 assets individually
        others_value = 0.0

        for i, asset in enumerate(assets_data):
            value = asset.get('current_value_usd', 0.0)
            if value <= 0: continue # Skip assets with no or negative value for pie chart

            if i < limit:
                percentage = (value / total_portfolio_value) * 100
                slice_label = f"{asset.get('symbol', 'N/A')}\n({percentage:.1f}%)"
                pie_slice = QPieSlice(slice_label, value)
                series.append(pie_slice)
            else:
                others_value += value

        if others_value > 0:
            percentage = (others_value / total_portfolio_value) * 100
            slice_label = f"Others\n({percentage:.1f}%)"
            series.append(slice_label, others_value)

        # Styling the pie chart slices (example colors)
        # TODO: Use theme accent colors
        colors = ["#00FF8C", "#00C2FF", "#FFD700", "#FF6384", "#36A2EB", "#FF9F40"] # Neon Green, Neon Blue, Gold, Pink, Blue, Orange
        for i, pie_slice in enumerate(series.slices()):
            pie_slice.setColor(QColor(colors[i % len(colors)]))
            pie_slice.setLabelVisible(True)
            # pie_slice.setLabelFont(QFont("Arial", 10)) # Set font for slice labels

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Asset Distribution by Value (USD)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations) # CORREGIDO: QChart.AnimationOption.SeriesAnimations
        legend = chart.legend()
        if legend: # CORREGIDO: Check for None
            legend.setVisible(True)
            legend.setAlignment(Qt.AlignmentFlag.AlignBottom) # CORREGIDO: Qt.AlignmentFlag.AlignBottom
            # Style legend
            legend_font = QFont("Arial", 10)
            legend.setFont(legend_font)
            # legend.setLabelColor(QColor("#E0E0E0")) # Assuming dark theme text
        chart.setBackgroundVisible(False) # Use QSS background for QChartView
        chart.setTitleFont(QFont("Arial", 14, QFont.Bold)) # Match view title style somewhat

        self.pie_chart_view.setChart(chart)


    def cleanup(self):
        logger.info("PortfolioView: Cleaning up...")
        for thread in list(self.active_threads):
            if thread.isRunning():
                thread.quit()
                thread.wait()
        self.active_threads.clear()
        if hasattr(self, 'trading_mode_manager'): # Disconnect signal
            try:
                self.trading_mode_manager.trading_mode_changed.disconnect(self._on_trading_mode_changed)
            except TypeError: # Signal not connected / already disconnected
                pass
        logger.info("PortfolioView: Cleanup finished.")

# Basic standalone test (similar to OpportunitiesView)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    from src.ultibot_ui.main import ApiWorker # CORREGIDO: Import ApiWorker for test block

    # Mock ApiWorker and UltiBotAPIClient for standalone testing
    class MockApiWorker(QObject): # Use QObject for signals if not importing full ApiWorker
        result_ready = pyqtSignal(object)
        error_occurred = pyqtSignal(str)
        def __init__(self, coro): self.coro = coro
        def run(self):
            try:
                if hasattr(self.coro, "__name__") and self.coro.__name__ == "_mock_get_portfolio_snapshot":
                    self.result_ready.emit(self.coro())
                else:
                     self.result_ready.emit({})
            except APIError as e:
                self.error_occurred.emit(str(e))
            except Exception as e:
                self.error_occurred.emit(f"Unexpected test error: {str(e)}")

    OriginalApiWorker = ApiWorker
    ApiWorker = MockApiWorker

    class MockUltiBotAPIClient:
        def __init__(self, base_url: str = ""): self.base_url = base_url
        async def get_portfolio_snapshot(self, user_id: UUID, trading_mode: str):
            return _mock_get_portfolio_snapshot(trading_mode)

    def _mock_get_portfolio_snapshot(mode: str):
        if mode == "paper":
            return {
                "paper_trading": {
                    "total_portfolio_value_usd": 12500.75,
                    "available_balance_usdt": 5000.25,
                    "assets": [
                        {"symbol": "BTC", "quantity": 0.1, "entry_price": 50000, "current_price": 60000, "current_value_usd": 6000.0, "unrealized_pnl_percentage": 20.0},
                        {"symbol": "ETH", "quantity": 2.0, "entry_price": 1500, "current_price": 2000, "current_value_usd": 4000.0, "unrealized_pnl_percentage": 33.33},
                        {"symbol": "ADA", "quantity": 5000.0, "entry_price": 0.20, "current_price": 0.25, "current_value_usd": 1250.0, "unrealized_pnl_percentage": 25.0},
                        {"symbol": "SOL", "quantity": 50.0, "entry_price": 20, "current_price": 25, "current_value_usd": 1250.0, "unrealized_pnl_percentage": 25.0},
                        {"symbol": "XRP", "quantity": 100.0, "entry_price": 0.4, "current_price": 0.5, "current_value_usd": 50.0, "unrealized_pnl_percentage": 25.0},
                        {"symbol": "DOT", "quantity": 20.0, "entry_price": 5, "current_price": 6, "current_value_usd": 120.0, "unrealized_pnl_percentage": 20.0},
                    ]
                },
                "real_trading": { # Some basic data for real mode for completeness
                    "total_portfolio_value_usd": 0, "available_balance_usdt": 0, "assets": []
                }
            }
        return {} # Default empty for other modes

    app = QApplication(sys.argv)
    # Apply a basic style for testing if needed
    # app.setStyleSheet(DARK_GLOBAL_STYLESHEET) # Assuming DARK_GLOBAL_STYLESHEET is defined or imported

    # For standalone test, qasync_loop might not be fully available or needed if ApiWorker is mocked correctly
    # For simplicity, we can pass None or a mock qasync_loop if the MockApiWorker doesn't use it.
    # However, the real ApiWorker now expects it.
    # Let's assume MockApiWorker is updated or doesn't strictly need it for this test.
    # If using a real qasync loop for testing:
    # import qasync
    # loop = qasync.QEventLoop(app)
    # asyncio.set_event_loop(loop)
    # view = PortfolioView(user_id=UUID("00000000-0000-0000-0000-000000000000"), backend_base_url="http://localhost:8000", qasync_loop=loop)

    # Simpler mock for qasync_loop for this specific test case, as MockApiWorker might not use it.
    class MockQAsyncLoop:
        def create_task(self, coro):
            pass # Mock implementation

    view = PortfolioView(user_id=UUID("00000000-0000-0000-0000-000000000000"), backend_base_url="http://localhost:8000", qasync_loop=MockQAsyncLoop()) # type: ignore
    view.setWindowTitle("Portfolio View - Test")
    view.setGeometry(100, 100, 1000, 700)
    view.show()

    ApiWorker = OriginalApiWorker
    sys.exit(app.exec_())
