import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
import asyncio

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFrame, QSplitter, QScrollArea, QGroupBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QFont, QColor
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice

from src.shared.data_types import PortfolioSnapshot, PortfolioAsset
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class PortfolioView(QWidget):
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.loop = loop
        self.active_threads: List[QThread] = []
        self.current_portfolio_data: Optional[PortfolioSnapshot] = None

        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)

        self._setup_ui()
        QTimer.singleShot(0, self._fetch_portfolio_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(20)
        self.setLayout(main_layout)

        header_layout = QHBoxLayout()
        title_label = QLabel("Portfolio Overview")
        title_label.setObjectName("viewTitleLabel")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.mode_indicator_label = QLabel("")
        self._update_mode_indicator_label()
        header_layout.addWidget(self.mode_indicator_label)

        self.refresh_button = QPushButton("Refresh Portfolio")
        self.refresh_button.clicked.connect(self._fetch_portfolio_data)
        header_layout.addWidget(self.refresh_button)
        main_layout.addLayout(header_layout)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        main_layout.addWidget(self.status_label)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter, 1)

        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setSpacing(15)

        summary_group = QGroupBox("Portfolio Summary")
        summary_group.setObjectName("summaryGroup")
        summary_layout = QVBoxLayout(summary_group)
        self.total_value_label = QLabel("Total Portfolio Value: N/A")
        self.total_value_label.setObjectName("dataDisplayLabel")
        self.available_balance_label = QLabel("Available Balance: N/A")
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addWidget(self.available_balance_label)
        summary_group.setFixedHeight(150)
        left_panel_layout.addWidget(summary_group)

        self.chart_group = QGroupBox("Asset Distribution")
        self.chart_group.setObjectName("assetDistributionChartGroup")
        chart_layout = QVBoxLayout(self.chart_group)
        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        chart_layout.addWidget(self.pie_chart_view)
        left_panel_layout.addWidget(self.chart_group, 1)

        content_splitter.addWidget(left_panel_widget)

        self.assets_group = QGroupBox("Detailed Asset Breakdown")
        self.assets_group.setObjectName("detailedAssetsGroup")
        assets_layout = QVBoxLayout(self.assets_group)
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(6)
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
        content_splitter.addWidget(self.assets_group)

        content_splitter.setSizes([self.width() // 3, 2 * self.width() // 3])

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
        self.assets_table.setRowCount(0)

        worker = ApiWorker(
            api_client=self.api_client,
            coroutine_factory=lambda client_in_lambda: client_in_lambda.get_portfolio_snapshot(
                user_id=self.user_id, trading_mode=self.trading_mode_manager.current_mode
            ),
            loop=self.loop
        )
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_portfolio_result)
        worker.error_occurred.connect(self._handle_portfolio_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        thread.start()

    def _handle_portfolio_result(self, portfolio_snapshot: PortfolioSnapshot):
        logger.info("PortfolioView: Portfolio snapshot data received.")
        self.status_label.setText("Portfolio data loaded successfully.")
        self.refresh_button.setEnabled(True)

        self.current_portfolio_data = portfolio_snapshot
        
        if self.trading_mode_manager.current_mode == "paper":
            mode_specific_data = portfolio_snapshot.paper_trading
        else:
            mode_specific_data = portfolio_snapshot.real_trading

        if not mode_specific_data:
            logger.warning(f"PortfolioView: No data found for mode '{self.trading_mode_manager.current_mode}' in snapshot.")
            self.total_value_label.setText("Total Portfolio Value: Data unavailable")
            self.available_balance_label.setText("Available Balance: Data unavailable")
            self.assets_table.setRowCount(0)
            self._update_pie_chart([])
            return

        self.total_value_label.setText(f"Total Portfolio Value: {mode_specific_data.total_portfolio_value_usd:,.2f} USD")
        currency_suffix = " (Virtual)" if self.trading_mode_manager.current_mode == "paper" else ""
        self.available_balance_label.setText(f"Available Balance: {mode_specific_data.available_balance_usdt:,.2f} USDT{currency_suffix}")

        assets_list = mode_specific_data.assets
        self._populate_assets_table(assets_list)
        self._update_pie_chart(assets_list)

    def _handle_portfolio_error(self, error_message: str):
        logger.error(f"PortfolioView: Error fetching portfolio data: {error_message}")
        self.status_label.setText("Failed to load portfolio data.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Portfolio Data Error",
                            f"Could not load portfolio data.\nDetails: {error_message}\n\nPlease try refreshing or check your connection.")
        self.total_value_label.setText("Total Portfolio Value: Error")
        self.available_balance_label.setText("Available Balance: Error")
        self.assets_table.setRowCount(0)
        self._update_pie_chart([])

    def _populate_assets_table(self, assets_data: List[PortfolioAsset]):
        self.assets_table.setRowCount(len(assets_data))
        for row, asset in enumerate(assets_data):
            self.assets_table.setItem(row, 0, QTableWidgetItem(asset.symbol or "N/A"))
            self.assets_table.setItem(row, 1, QTableWidgetItem(f"{asset.quantity or 0.0:,.8f}"))
            self.assets_table.setItem(row, 2, QTableWidgetItem(f"{asset.entry_price or 0.0:,.4f}"))
            self.assets_table.setItem(row, 3, QTableWidgetItem(f"{asset.current_price or 0.0:,.4f}"))
            self.assets_table.setItem(row, 4, QTableWidgetItem(f"{asset.current_value_usd or 0.0:,.2f}"))

            pnl_pct = asset.unrealized_pnl_percentage or 0.0
            pnl_item = QTableWidgetItem(f"{pnl_pct:,.2f}%")
            if pnl_pct > 0:
                pnl_item.setForeground(QColor(Qt.GlobalColor.green))
            elif pnl_pct < 0:
                pnl_item.setForeground(QColor(Qt.GlobalColor.red))
            self.assets_table.setItem(row, 5, pnl_item)

        if not assets_data and self.assets_table.rowCount() == 0:
            self.assets_table.setRowCount(1)
            placeholder_item = QTableWidgetItem("No assets to display for this mode.")
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.assets_table.setItem(0, 0, placeholder_item)
            self.assets_table.setSpan(0, 0, 1, self.assets_table.columnCount())

    def _update_pie_chart(self, assets_data: List[PortfolioAsset]):
        series = QPieSeries()
        total_portfolio_value = sum(asset.current_value_usd or 0.0 for asset in assets_data if (asset.current_value_usd or 0.0) > 0)

        if total_portfolio_value == 0:
            chart = QChart()
            chart.setTitle("Asset Distribution (No Data)")
            self.pie_chart_view.setChart(chart)
            return

        assets_data.sort(key=lambda x: x.current_value_usd or 0.0, reverse=True)
        limit = 5
        others_value = 0.0

        for i, asset in enumerate(assets_data):
            value = asset.current_value_usd or 0.0
            if value <= 0: continue

            if i < limit:
                percentage = (value / total_portfolio_value) * 100
                slice_label = f"{asset.symbol or 'N/A'}\n({percentage:.1f}%)"
                pie_slice = QPieSlice(slice_label, value)
                series.append(pie_slice)
            else:
                others_value += value

        if others_value > 0:
            percentage = (others_value / total_portfolio_value) * 100
            slice_label = f"Others\n({percentage:.1f}%)"
            series.append(slice_label, others_value)

        colors = ["#00FF8C", "#00C2FF", "#FFD700", "#FF6384", "#36A2EB", "#FF9F40"]
        for i, pie_slice in enumerate(series.slices()):
            pie_slice.setColor(QColor(colors[i % len(colors)]))
            pie_slice.setLabelVisible(True)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Asset Distribution by Value (USD)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        legend = chart.legend()
        if legend:
            legend.setVisible(True)
            legend.setAlignment(Qt.AlignmentFlag.AlignBottom)
            legend.setFont(QFont("Arial", 10))
        chart.setBackgroundVisible(False)
        chart.setTitleFont(QFont("Arial", 14, QFont.Bold))

        self.pie_chart_view.setChart(chart)

    def cleanup(self):
        logger.info("PortfolioView: Cleaning up...")
        for thread in list(self.active_threads):
            if thread.isRunning():
                thread.quit()
                thread.wait()
        self.active_threads.clear()
        if hasattr(self, 'trading_mode_manager'):
            try:
                self.trading_mode_manager.trading_mode_changed.disconnect(self._on_trading_mode_changed)
            except TypeError:
                pass
        logger.info("PortfolioView: Cleanup finished.")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    class MockApiWorker(QObject):
        result_ready = pyqtSignal(object)
        error_occurred = pyqtSignal(str)
        def __init__(self, coroutine_factory, loop): # Added loop
            super().__init__()
            self.coro_factory = coroutine_factory
        def run(self):
            try:
                mock_data = _mock_get_portfolio_snapshot("paper")
                self.result_ready.emit(mock_data)
            except Exception as e:
                self.error_occurred.emit(f"Unexpected test error: {str(e)}")

    OriginalApiWorker = ApiWorker
    ApiWorker = MockApiWorker

    def _mock_get_portfolio_snapshot(mode: str):
        return {
            "paper_trading": { "total_portfolio_value_usd": 12500.75, "available_balance_usdt": 5000.25, "assets": [{"symbol": "BTC", "quantity": 0.1, "current_value_usd": 6000.0, "unrealized_pnl_percentage": 20.0}] },
            "real_trading": { "total_portfolio_value_usd": 0, "available_balance_usdt": 0, "assets": [] }
        }

    app = QApplication(sys.argv)
    
    # Mock loop for testing purposes
    test_loop = asyncio.get_event_loop()
    
    view = PortfolioView(
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        api_client=None, # Mocked, not used in this test
        loop=test_loop
    )
    view.setWindowTitle("Portfolio View - Test")
    view.setGeometry(100, 100, 1000, 700)
    view.show()

    ApiWorker = OriginalApiWorker
    sys.exit(app.exec_())
