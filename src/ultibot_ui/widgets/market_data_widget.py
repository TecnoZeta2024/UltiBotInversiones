import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Coroutine
from uuid import UUID
import random

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter, QMessageBox, QAbstractItemView, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont

import qasync

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.workers import ApiWorker
from shared.data_types import UserConfiguration

logger = logging.getLogger(__name__)

ALL_AVAILABLE_PAIRS_EXAMPLE = [
    "BTC/USDT", "ETH/USDT", "ADA/USDT", "XRP/USDT", "SOL/USDT", 
    "DOT/USDT", "DOGE/USDT", "SHIB/USDT", "MATIC/USDT", "LTC/USDT",
    "BNB/USDT", "LINK/USDT", "AVAX/USDT", "TRX/USDT", "ATOM/USDT"
]

class PairConfigurationDialog(QDialog):
    def __init__(self, available_pairs: List[str], selected_pairs: List[str], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Pares de Trading")
        self.setMinimumSize(400, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar par...")
        self.search_input.textChanged.connect(self.filter_pairs)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        self._original_list_items: List[QListWidgetItem] = []
        for pair_text in sorted(list(set(available_pairs))):
            item = QListWidgetItem(pair_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if pair_text in selected_pairs else Qt.CheckState.Unchecked)
            self._original_list_items.append(item)
        
        self.filter_pairs("") # Populate the list initially
        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox()
        self.button_box.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def filter_pairs(self, text: str):
        text_lower = text.lower().strip()
        self.list_widget.clear()
        for item_original in self._original_list_items:
            if text_lower in item_original.text().lower():
                new_item = item_original.clone()
                self.list_widget.addItem(new_item)

    def get_selected_pairs(self) -> List[str]:
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

class MarketDataWidget(QWidget):
    user_config_fetched = pyqtSignal(UserConfiguration)
    tickers_data_fetched = pyqtSignal(dict)
    config_saved = pyqtSignal(UserConfiguration)
    market_data_api_error = pyqtSignal(str)
    
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.selected_pairs: List[str] = [] 
        self.all_available_pairs: List[str] = [] 
        self.active_api_workers: List[Any] = []

        self._init_ui()
        self._setup_timers()

        self.user_config_fetched.connect(self._handle_user_config_result)
        self.tickers_data_fetched.connect(self._handle_tickers_data_result)
        self.config_saved.connect(self._handle_config_saved_result)
        self.market_data_api_error.connect(self._handle_market_data_api_error)
        self.load_initial_configuration()

    def _run_api_worker_and_await_result(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine]) -> asyncio.Future:
        qasync_loop = asyncio.get_event_loop()
        future = qasync_loop.create_future()

        worker = ApiWorker(coroutine_factory=coroutine_factory, api_client=self.api_client)
        thread = QThread()
        self.active_api_workers.append((worker, thread))

        worker.moveToThread(thread)

        def _on_result(result):
            if not future.done():
                qasync_loop.call_soon_threadsafe(future.set_result, result)
        def _on_error(error_msg):
            if not future.done():
                qasync_loop.call_soon_threadsafe(future.set_exception, Exception(error_msg))
        
        worker.result_ready.connect(_on_result)
        worker.error_occurred.connect(_on_error)
        
        thread.started.connect(worker.run)

        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_api_workers.remove((worker, thread)) if (worker, thread) in self.active_api_workers else None)

        thread.start()
        return future

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        title_label = QLabel("Datos de Mercado")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.configure_pairs_button = QPushButton("Configurar Pares")
        self.configure_pairs_button.clicked.connect(self.show_pair_configuration_dialog)
        layout.addWidget(self.configure_pairs_button)

        self.tickers_table = QTableWidget()
        self.tickers_table.setColumnCount(5) 
        self.tickers_table.setHorizontalHeaderLabels(["Símbolo", "Precio", "Cambio 24h (%)", "Volumen 24h", "Tendencia"])
        header = self.tickers_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tickers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tickers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tickers_table.setAlternatingRowColors(True)
        layout.addWidget(self.tickers_table)

    def _setup_timers(self):
        self.tickers_timer = QTimer(self)
        self.tickers_timer.timeout.connect(self.update_tickers_data)

    def _handle_user_config_result(self, config: UserConfiguration):
        self.selected_pairs = config.favoritePairs or ["BTC/USDT", "ETH/USDT"]
        self.all_available_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE
        
        update_interval_seconds = 30
        if config.mcpServerPreferences:
            market_pref = next((p for p in config.mcpServerPreferences 
                                if p.queryFrequencySeconds and ('market' in p.id.lower() or 'ccxt' in p.id.lower() or 'mobula' in p.id.lower())), 
                               None)
            if market_pref and market_pref.queryFrequencySeconds is not None:
                update_interval_seconds = market_pref.queryFrequencySeconds
                logger.info(f"Intervalo de actualización de UI configurado desde MCP '{market_pref.id}': {update_interval_seconds}s")

        update_interval_ms = update_interval_seconds * 1000
        
        self.tickers_timer.start(update_interval_ms)
        logger.info(f"Configuración cargada: Pares seleccionados: {self.selected_pairs}, Intervalo de actualización: {update_interval_ms}ms")
        self.update_tickers_data()

    def load_initial_configuration(self):
        logger.info("Cargando configuración inicial para MarketDataWidget...")
        future = self._run_api_worker_and_await_result(
            lambda api_client: api_client.get_user_configuration()
        )
        future.add_done_callback(
            lambda f: self.user_config_fetched.emit(f.result()) if not f.exception() else self.market_data_api_error.emit(str(f.exception()))
        )

    def _handle_tickers_data_result(self, tickers_data: Dict[str, Any]):
        if not self.selected_pairs:
            self.tickers_table.setRowCount(0)
            return

        self.tickers_table.setRowCount(len(self.selected_pairs))
        for row, symbol in enumerate(self.selected_pairs):
            data = tickers_data.get(symbol, {})
            price = data.get("lastPrice", "N/A")
            change_24h_str = data.get("priceChangePercent", "N/A")
            volume_24h = data.get("quoteVolume", "N/A")

            self.tickers_table.setItem(row, 0, QTableWidgetItem(symbol))
            self.tickers_table.setItem(row, 1, QTableWidgetItem(str(price)))
            
            item_change = QTableWidgetItem(f"{change_24h_str}%" if change_24h_str != "N/A" else "N/A")
            try:
                change_val = float(change_24h_str)
                if change_val > 0:
                    item_change.setForeground(QColor("green"))
                elif change_val < 0:
                    item_change.setForeground(QColor("red"))
            except (ValueError, TypeError):
                pass
            self.tickers_table.setItem(row, 2, item_change)
            
            self.tickers_table.setItem(row, 3, QTableWidgetItem(str(volume_24h)))
            self.tickers_table.setItem(row, 4, QTableWidgetItem("N/D"))

        self.tickers_table.resizeColumnsToContents()

    def update_tickers_data(self):
        if not self.selected_pairs:
            return
        future = self._run_api_worker_and_await_result(
            lambda api_client: api_client.get_market_data(self.selected_pairs)
        )
        future.add_done_callback(
            lambda f: self.tickers_data_fetched.emit(f.result()) if not f.exception() else self.market_data_api_error.emit(str(f.exception()))
        )

    def show_pair_configuration_dialog(self):
        dialog = PairConfigurationDialog(self.all_available_pairs, self.selected_pairs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_selected_pairs = dialog.get_selected_pairs()
            if set(new_selected_pairs) != set(self.selected_pairs):
                self.selected_pairs = new_selected_pairs
                self.save_widget_configuration()
                self.update_tickers_data()

    def _handle_config_saved_result(self, config: UserConfiguration):
        logger.info("Configuración de MarketDataWidget guardada exitosamente.")

    def save_widget_configuration(self):
        future_get_config = self._run_api_worker_and_await_result(
            lambda api_client: api_client.get_user_configuration()
        )

        def on_get_config_done(f):
            if f.exception():
                self.market_data_api_error.emit(f"Error al obtener config para guardar: {f.exception()}")
                return
            
            current_config: UserConfiguration = f.result()
            current_config.favoritePairs = self.selected_pairs
            
            future_update = self._run_api_worker_and_await_result(
                lambda api_client: api_client.update_user_configuration(current_config)
            )
            future_update.add_done_callback(
                lambda f_update: self.config_saved.emit(f_update.result()) if not f_update.exception() else self.market_data_api_error.emit(f"Error al guardar config: {f_update.exception()}")
            )

        future_get_config.add_done_callback(on_get_config_done)

    def _handle_market_data_api_error(self, message: str):
        logger.error(f"MarketDataWidget: Error de API: {message}")
        QMessageBox.warning(self, "Error de API en Datos de Mercado", message)

    def cleanup(self):
        if hasattr(self, 'tickers_timer') and self.tickers_timer.isActive():
            self.tickers_timer.stop()
        for worker, thread in self.active_api_workers[:]:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
        self.active_api_workers.clear()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    class MockAPIClient(UltiBotAPIClient):
        async def get_user_configuration(self) -> UserConfiguration:
            await asyncio.sleep(0.1)
            return UserConfiguration(user_id=UUID("123e4567-e89b-12d3-a456-426614174000"), favoritePairs=["BTC/USDT", "ETH/USDT"])
        
        async def update_user_configuration(self, config: UserConfiguration) -> UserConfiguration:
            await asyncio.sleep(0.1)
            return config

        async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
            mock_data = {}
            for symbol in symbols:
                mock_data[symbol] = {
                    "lastPrice": str(round(random.uniform(20000, 60000), 2)),
                    "priceChangePercent": str(round(random.uniform(-5, 5), 2)),
                    "quoteVolume": str(round(random.uniform(1000, 100000), 2))
                }
            await asyncio.sleep(0.1)
            return mock_data

    async def main_async():
        app = QApplication.instance() or QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        test_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_api_client = MockAPIClient(base_url="http://mock")
        widget = MarketDataWidget(user_id=test_user_id, api_client=mock_api_client)
        
        widget.load_initial_configuration()
        widget.show()
        pass

    if __name__ == "__main__":
        try:
            qasync.run(main_async)
        except KeyboardInterrupt:
            logger.info("Aplicación de prueba cerrada.")

