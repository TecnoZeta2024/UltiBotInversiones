import logging
from typing import List, Dict, Any, Optional, Callable, Coroutine
import asyncio
from uuid import UUID
import qasync

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QTimer

from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig

logger = logging.getLogger(__name__)

class StrategiesView(QWidget):
    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        self.is_active = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Configured Trading Strategies")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._fetch_strategies)
        header_layout.addWidget(self.refresh_button)
        
        self._layout.addLayout(header_layout)
        
        self.status_label = QLabel("Ready.")
        self._layout.addWidget(self.status_label)
        
        self.strategies_list_widget = QListWidget()
        self._layout.addWidget(self.strategies_list_widget)
        
        self.setLayout(self._layout)

    def enter_view(self):
        """Se llama cuando la vista se vuelve activa."""
        logger.info("StrategiesView: Entrando a la vista.")
        self.is_active = True
        self._fetch_strategies()

    def leave_view(self):
        """Se llama cuando la vista se vuelve inactiva."""
        logger.info("StrategiesView: Saliendo de la vista.")
        self.is_active = False

    @qasync.asyncSlot()
    async def _fetch_strategies(self):
        logger.info("Fetching strategies.")
        self.status_label.setText("Loading strategies...")
        self.refresh_button.setEnabled(False)
        
        coroutine_factory = lambda client: client.get_strategies()
        self.main_window.submit_task(coroutine_factory, self._handle_strategies_result, self._handle_strategies_error)

    @qasync.asyncSlot(object)
    async def _handle_strategies_result(self, data: object):
        if not self.is_active:
            logger.info("StrategiesView no está activa, ignorando resultado.")
            return

        # La respuesta de la API es un diccionario que contiene la lista de estrategias
        if not isinstance(data, dict):
            await self._handle_strategies_error(f"Invalid data format: Expected dict, got {type(data).__name__}")
            return
        
        strategies_data = data.get('strategies', [])
        
        if not isinstance(strategies_data, list):
            await self._handle_strategies_error(f"Invalid data format: 'strategies' key should be a list, got {type(strategies_data).__name__}")
            return

        logger.info(f"Received {len(strategies_data)} strategies.")
        self.status_label.setText(f"Loaded {len(strategies_data)} strategies successfully.")
        self.refresh_button.setEnabled(True)
        
        try:
            # Asumimos que la API devuelve diccionarios que se pueden convertir a nuestro modelo Pydantic
            strategies = [TradingStrategyConfig(**s_data) for s_data in strategies_data]
        except (TypeError, ValueError) as e:
            await self._handle_strategies_error(f"Data parsing error: {e}")
            return

        self.update_strategies_list(strategies)

    @qasync.asyncSlot(str)
    async def _handle_strategies_error(self, error_message: str):
        if not self.is_active:
            logger.info("StrategiesView no está activa, ignorando error.")
            return

        logger.error(f"Error fetching strategies: {error_message}")
        self.status_label.setText("Failed to load strategies.")
        self.refresh_button.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Could not load strategies: {error_message}")
        self.strategies_list_widget.clear()
        self.strategies_list_widget.addItem("Error loading strategies.")

    def update_strategies_list(self, strategies: List[TradingStrategyConfig]):
        """
        Populates the list widget with strategy information.
        """
        self.strategies_list_widget.clear()
        if not strategies:
            self.strategies_list_widget.addItem("No strategies configured.")
            return
            
        for strategy in strategies:
            status = "Active" if strategy.is_active else "Inactive"
            item_text = f"{strategy.strategy_name} ({strategy.base_strategy_type.value}) - {status}"
            list_item = QListWidgetItem(item_text)
            self.strategies_list_widget.addItem(list_item)
        
        logger.info(f"Strategies view updated with {len(strategies)} strategies.")

    def cleanup(self):
        logger.info("Cleaning up StrategiesView...")
        self.leave_view()
        logger.info("StrategiesView cleanup finished.")
