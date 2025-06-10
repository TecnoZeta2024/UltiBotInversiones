import asyncio
import logging
from uuid import UUID
from typing import List, Dict, Any, Coroutine, Callable
import qasync

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QAbstractItemView, QFrame, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, QTimer, QDateTime
from PyQt5.QtGui import QColor

from src.shared.data_types import Opportunity
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class OpportunitiesView(QWidget):
    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        logger.info("OpportunitiesView: __init__ called.")
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        logger.debug("OpportunitiesView initialized.")

        self._setup_ui()
        self._load_initial_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        title_frame = QFrame()
        title_frame.setObjectName("viewHeaderFrame")
        title_frame_layout = QHBoxLayout(title_frame)
        title_frame_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("High-Confidence Trading Opportunities")
        title_label.setObjectName("viewTitleLabel")
        title_frame_layout.addWidget(title_label)
        title_frame_layout.addStretch()
        main_layout.addWidget(title_frame)

        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(10)
        controls_layout.setContentsMargins(0, 6, 0, 6)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("statusLabel")
        controls_layout.addWidget(self.status_label)
        controls_layout.addStretch()
        self.refresh_button = QPushButton("Refresh Opportunities")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self._fetch_opportunities)
        controls_layout.addWidget(self.refresh_button)

        self.last_updated_label = QLabel("Last updated: --")
        controls_layout.addWidget(self.last_updated_label)
        main_layout.addWidget(controls_frame)

        table_container_frame = QFrame()
        table_container_frame.setObjectName("tableContainerFrame")
        table_layout = QVBoxLayout(table_container_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.opportunities_table = QTableWidget()
        self.opportunities_table.setObjectName("opportunitiesTable")
        self.opportunities_table.setColumnCount(7)
        self.opportunities_table.setHorizontalHeaderLabels([
            "Symbol", "Side", "Entry Price", "Score", "Strategy", "Exchange", "Timestamp"
        ])
        header = self.opportunities_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vheader = self.opportunities_table.verticalHeader()
        if vheader:
            vheader.setVisible(False)
        self.opportunities_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.opportunities_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.opportunities_table.setAlternatingRowColors(True)

        table_layout.addWidget(self.opportunities_table)
        main_layout.addWidget(table_container_frame, 1)
        self._apply_shadow_effect(table_container_frame)

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(30_000)
        self._auto_refresh_timer.timeout.connect(self._fetch_opportunities)
        self._auto_refresh_timer.start()

    def _load_initial_data(self):
        logger.info("OpportunitiesView: _load_initial_data called.")
        QTimer.singleShot(100, self._fetch_opportunities)

    def _apply_shadow_effect(self, widget: QWidget, color_hex: str = "#000000", blur_radius: int = 10, x_offset: int = 0, y_offset: int = 1):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(color_hex))
        shadow.setOffset(x_offset, y_offset)
        widget.setGraphicsEffect(shadow)

    @qasync.asyncSlot()
    async def _fetch_opportunities(self):
        logger.info("Fetching Gemini IA opportunities.")
        self.status_label.setText("Loading opportunities...")
        self.refresh_button.setEnabled(False)
        self.opportunities_table.setRowCount(0)
        
        coro_factory = lambda api_client: api_client.get_ai_opportunities()
        await self._start_api_worker(coro_factory)

    async def _start_api_worker(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine]):
        logger.debug("Creating ApiWorker.")
        
        worker = ApiWorker(
            api_client=self.api_client, 
            coroutine_factory=coroutine_factory,
            loop=self.loop
        )
        thread = QThread()
        if hasattr(self.main_window, 'add_thread') and callable(getattr(self.main_window, 'add_thread')):
            self.main_window.add_thread(thread)
        else:
            logger.warning("OpportunitiesView: self.main_window does not have add_thread. Thread not tracked by main_window.")
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_opportunities_result)
        worker.error_occurred.connect(self._handle_opportunities_error)
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        
        thread.start()

    @qasync.asyncSlot()
    async def _handle_opportunities_result(self, data: object):
        if not isinstance(data, list):
            error_msg = f"Invalid data format: Expected list, got {type(data).__name__}"
            logger.error(f"OpportunitiesView: {error_msg}")
            await self._handle_opportunities_error(error_msg)
            return

        try:
            opportunities = [Opportunity(**opp) for opp in data]
        except (TypeError, ValueError) as e:
            error_msg = f"Data parsing error: {e}"
            logger.error(f"OpportunitiesView: {error_msg}")
            await self._handle_opportunities_error(error_msg)
            return

        logger.info(f"Received {len(opportunities)} opportunities.")
        self.status_label.setText(f"Loaded {len(opportunities)} opportunities.")
        self.refresh_button.setEnabled(True)
        self.opportunities_table.setRowCount(0)

        if not opportunities:
            self.opportunities_table.setRowCount(1)
            placeholder_item = QTableWidgetItem("No opportunities to display.")
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opportunities_table.setItem(0, 0, placeholder_item)
            self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())
            self.status_label.setText("No high-confidence opportunities found.")
            self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")
            return

        self.opportunities_table.setRowCount(len(opportunities))
        for row, opp in enumerate(opportunities):
            symbol = opp.symbol.replace("/", "") if opp.symbol else "N/A"
            side = opp.predicted_direction or "N/A"
            entry_price = opp.predicted_price_target
            confidence_score = opp.confidence_score
            strategy_id = "AI"
            exchange = opp.exchange or "N/A"
            timestamp = opp.created_at.strftime('%Y-%m-%d %H:%M:%S') if opp.created_at else "N/A"

            self.opportunities_table.setItem(row, 0, QTableWidgetItem(symbol))
            
            side_item = QTableWidgetItem(side)
            if side == "UP":
                side_item.setForeground(QColor("lightgreen"))
            elif side == "DOWN":
                side_item.setForeground(QColor("lightcoral"))
            self.opportunities_table.setItem(row, 1, side_item)

            entry_price_str = f"{entry_price:,.2f}" if isinstance(entry_price, (int, float)) else "N/A"
            self.opportunities_table.setItem(row, 2, QTableWidgetItem(entry_price_str))

            score_str = f"{confidence_score:.2f}" if isinstance(confidence_score, float) else "N/A"
            score_item = QTableWidgetItem(score_str)
            if isinstance(confidence_score, float):
                if confidence_score >= 0.9: score_item.setForeground(QColor("lightgreen"))
                elif confidence_score >= 0.7: score_item.setForeground(QColor("yellow"))
                else: score_item.setForeground(QColor("orange"))
            self.opportunities_table.setItem(row, 3, score_item)

            self.opportunities_table.setItem(row, 4, QTableWidgetItem(strategy_id))
            self.opportunities_table.setItem(row, 5, QTableWidgetItem(exchange))
            self.opportunities_table.setItem(row, 6, QTableWidgetItem(timestamp))

        self.opportunities_table.resizeColumnsToContents()
        self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")

    @qasync.asyncSlot()
    async def _handle_opportunities_error(self, error_message: str):
        logger.error(f"Error fetching opportunities: {error_message}")
        self.status_label.setText("Failed to load opportunities.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Opportunities Error", f"Could not load trading opportunities.\nDetails: {error_message}")
        
        self.opportunities_table.setRowCount(1)
        error_item = QTableWidgetItem(f"Error loading data: {error_message}")
        error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.opportunities_table.setItem(0, 0, error_item)
        self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())

    def cleanup(self):
        logger.info("Cleaning up OpportunitiesView...")
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.stop()
        logger.info("OpportunitiesView cleanup finished.")

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    
    print("To test this view, please run it as part of the main application.")
