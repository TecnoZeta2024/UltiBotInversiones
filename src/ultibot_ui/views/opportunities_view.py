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
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class OpportunitiesView(QWidget):
    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        logger.info("OpportunitiesView: __init__ called.")
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        self.is_active = False
        self.current_opportunities: List[Opportunity] = []
        logger.debug("OpportunitiesView initialized.")

        self._setup_ui()

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
        self.opportunities_table.itemSelectionChanged.connect(self._on_opportunity_selected)

        table_layout.addWidget(self.opportunities_table)
        main_layout.addWidget(table_container_frame, 1)
        self._apply_shadow_effect(table_container_frame)

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(30_000)
        self._auto_refresh_timer.timeout.connect(self._fetch_opportunities)

    def enter_view(self):
        """Se llama cuando la vista se vuelve activa."""
        logger.info("OpportunitiesView: Entrando a la vista.")
        self.is_active = True
        self._auto_refresh_timer.start()
        self._fetch_opportunities()

    def leave_view(self):
        """Se llama cuando la vista se vuelve inactiva."""
        logger.info("OpportunitiesView: Saliendo de la vista.")
        self.is_active = False
        self._auto_refresh_timer.stop()

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
        
        async def safe_get_opportunities():
            try:
                return await self.api_client.get_ai_opportunities()
            except APIError as e:
                logger.error(f"APIError in OpportunitiesView: {e}", exc_info=True)
                return e

        coroutine_factory = lambda _: safe_get_opportunities()
        self.main_window.submit_task(coroutine_factory, self._handle_opportunities_result, self._handle_opportunities_error)

    @qasync.asyncSlot()
    async def _on_opportunity_selected(self):
        selected_items = self.opportunities_table.selectedItems()
        if not selected_items:
            return

        selected_row = selected_items[0].row()
        if selected_row >= len(self.current_opportunities):
            return
            
        opportunity = self.current_opportunities[selected_row]
        symbol = opportunity.symbol.replace("/", "")
        logger.info(f"Opportunity selected: {symbol}. Fetching historical data.")
        self.main_window.set_status_message(f"Loading historical data for {symbol}...")

        try:
            # Fetch historical data from the new endpoint
            # Assuming '1h' interval and 500 data points for now
            historical_data = await self.api_client.get_market_history(symbol, "1h", 500)
            
            # Assuming main_window has a method to update a chart
            if hasattr(self.main_window, 'update_chart_data'):
                self.main_window.update_chart_data(symbol, historical_data)
                self.main_window.set_status_message(f"Displayed historical data for {symbol}.")
            else:
                logger.warning("main_window does not have 'update_chart_data' method.")
                self.main_window.set_status_message("Chart display function not available.")

        except APIError as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            self.main_window.set_status_message(f"Error loading data for {symbol}: {e.message}")
            QMessageBox.warning(self, "Data Error", f"Could not load historical data for {symbol}.\nDetails: {e.message}")
        except Exception as e:
            logger.critical(f"An unexpected error occurred while fetching historical data for {symbol}: {e}", exc_info=True)
            self.main_window.set_status_message(f"Critical error loading data for {symbol}.")


    @qasync.asyncSlot(object)
    async def _handle_opportunities_result(self, data: object):
        if not self.is_active:
            logger.info("OpportunitiesView no está activa, ignorando resultado.")
            return
        
        if isinstance(data, Exception):
            await self._handle_opportunities_error(str(data))
            return

        if not isinstance(data, list):
            error_msg = f"Invalid data format: Expected list, got {type(data).__name__}"
            logger.error(f"OpportunitiesView: {error_msg}")
            await self._handle_opportunities_error(error_msg)
            return

        try:
            self.current_opportunities = [Opportunity(**opp) for opp in data]
        except (TypeError, ValueError) as e:
            error_msg = f"Data parsing error: {e}"
            logger.error(f"OpportunitiesView: {error_msg}")
            await self._handle_opportunities_error(error_msg)
            return

        logger.info(f"Received {len(self.current_opportunities)} opportunities.")
        self.status_label.setText(f"Loaded {len(self.current_opportunities)} opportunities.")
        self.refresh_button.setEnabled(True)
        self.opportunities_table.setRowCount(0)

        if not self.current_opportunities:
            self.opportunities_table.setRowCount(1)
            placeholder_item = QTableWidgetItem("No opportunities to display.")
            placeholder_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opportunities_table.setItem(0, 0, placeholder_item)
            self.opportunities_table.setSpan(0, 0, 1, self.opportunities_table.columnCount())
            self.status_label.setText("No high-confidence opportunities found.")
            self.last_updated_label.setText(f"Last updated: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}")
            return

        self.opportunities_table.setRowCount(len(self.current_opportunities))
        for row, opp in enumerate(self.current_opportunities):
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

    @qasync.asyncSlot(str)
    async def _handle_opportunities_error(self, error_message: str):
        if not self.is_active:
            logger.info("OpportunitiesView no está activa, ignorando error.")
            return
            
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
        self.leave_view()
        logger.info("OpportunitiesView cleanup finished.")
