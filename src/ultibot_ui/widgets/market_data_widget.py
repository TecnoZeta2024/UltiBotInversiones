import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, Coroutine
from uuid import UUID
import random
from datetime import datetime
from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter, QMessageBox, QAbstractItemView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal as pyqtSignal
from PySide6.QtGui import QColor, QFont

import qasync

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from shared.data_types import UserConfiguration
from ultibot_backend.core.domain_models.user_configuration_models import RiskProfile, Theme
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)

ALL_AVAILABLE_PAIRS_EXAMPLE = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "XRPUSDT", "SOLUSDT", 
    "DOTUSDT", "DOGEUSDT", "SHIBUSDT", "MATICUSDT", "LTCUSDT",
    "BNBUSDT", "LINKUSDT", "AVAXUSDT", "TRXUSDT", "ATOMUSDT"
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
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
    
    def __init__(self, user_id: Optional[UUID], api_client: UltiBotAPIClient, main_window: Optional[BaseMainWindow], main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.main_window = main_window # Guardar referencia a MainWindow
        self.main_event_loop = main_event_loop # Guardar la referencia al bucle de eventos
        self.selected_pairs: List[str] = [] 
        self.all_available_pairs: List[str] = []

        self._init_ui()
        self._setup_timers()

        self.user_config_fetched.connect(self._handle_user_config_result)
        self.tickers_data_fetched.connect(self._handle_tickers_data_result)
        self.config_saved.connect(self._handle_config_saved_result)
        self.market_data_api_error.connect(self._handle_market_data_api_error)
        # La inicialización ahora es controlada por el componente padre (ej. MainWindow)
        # self.load_initial_configuration()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        title_label = QLabel("Datos de Mercado")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
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
        # Normalizar los favorite_pairs a un formato sin barra si vienen con ella
        normalized_favorite_pairs = [pair.replace("/", "") for pair in (config.favorite_pairs or ["BTCUSDT", "ETHUSDT"])]
        self.selected_pairs = normalized_favorite_pairs
        self.all_available_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE
        
        update_interval_seconds = 30
        if config.mcp_server_preferences:
            market_pref = next((p for p in config.mcp_server_preferences 
                                if p.query_frequency_seconds and ('market' in p.id.lower() or 'ccxt' in p.id.lower() or 'mobula' in p.id.lower())), 
                               None)
            if market_pref and market_pref.query_frequency_seconds is not None:
                update_interval_seconds = market_pref.query_frequency_seconds
                logger.info(f"Intervalo de actualización de UI configurado desde MCP '{market_pref.id}': {update_interval_seconds}s")

        update_interval_ms = update_interval_seconds * 1000
        
        self.tickers_timer.start(update_interval_ms)
        logger.info(f"Configuración cargada: Pares seleccionados: {self.selected_pairs}, Intervalo de actualización: {update_interval_ms}ms")
        self.update_tickers_data()

    async def initialize_widget_data(self):
        """
        Inicia la carga de datos iniciales para este widget de forma asíncrona.
        Este método debe ser awaitable por el componente padre después de la inicialización.
        """
        logger.info("Iniciando la carga de datos asíncrona para MarketDataWidget...")
        if self.main_event_loop and self.main_event_loop.is_running():
            await self._load_initial_configuration_async()
        else:
            logger.error("No se puede iniciar la carga de datos: el bucle de eventos no está disponible o no está en ejecución.")

    async def _load_initial_configuration_async(self):
        try:
            config_data = await self.api_client.get_user_configuration()
            # Pydantic ya no se usa aquí para la validación, se asume que la API devuelve el formato correcto
            self.user_config_fetched.emit(UserConfiguration(**config_data))
        except Exception as e:
            self.market_data_api_error.emit(str(e))

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
        self.main_event_loop.create_task(self._update_tickers_data_async())

    async def _update_tickers_data_async(self):
        try:
            tickers_data = await self.api_client.get_market_data(self.selected_pairs)
            self.tickers_data_fetched.emit(tickers_data)
        except Exception as e:
            self.market_data_api_error.emit(str(e))

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
        self.main_event_loop.create_task(self._save_widget_configuration_async())

    async def _save_widget_configuration_async(self):
        try:
            config_data = await self.api_client.get_user_configuration()
            current_config = UserConfiguration(**config_data)
            current_config.favorite_pairs = self.selected_pairs
            
            updated_config_data = await self.api_client.update_user_configuration(current_config.model_dump(mode='json'))
            self.config_saved.emit(UserConfiguration(**updated_config_data))
        except Exception as e:
            self.market_data_api_error.emit(f"Error al guardar la configuración: {e}")

    def _handle_market_data_api_error(self, message: str):
        logger.error(f"MarketDataWidget: Error de API: {message}")
        QMessageBox.warning(self, "Error de API en Datos de Mercado", message)

    def cleanup(self):
        """Detiene el temporizador de actualización."""
        logger.info("MarketDataWidget: Iniciando limpieza.")
        if hasattr(self, 'tickers_timer') and self.tickers_timer.isActive():
            self.tickers_timer.stop()
        # Los hilos de los workers son gestionados por MainWindow.
        logger.info("MarketDataWidget: Limpieza completada.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    class MockAPIClient(UltiBotAPIClient):
        async def get_user_configuration(self) -> UserConfiguration:
            await asyncio.sleep(0.1)
            return UserConfiguration(
                id=str(UUID("123e4567-e89b-12d3-a456-426614174000")), # Asignar un ID si es necesario
                user_id=str(UUID("123e4567-e89b-12d3-a456-426614174000")),
                favoritePairs=["BTC/USDT", "ETH/USDT"],
                telegramChatId=None,
                notificationPreferences=[],
                enableTelegramNotifications=True,
                defaultPaperTradingCapital=Decimal("10000.00"),
                paperTradingActive=True,
                paperTradingAssets=[],
                watchlists=[],
                riskProfile=RiskProfile.MODERATE,
                riskProfileSettings=None,
                realTradingSettings=None,
                aiStrategyConfigurations=[],
                aiAnalysisConfidenceThresholds=None,
                mcpServerPreferences=[],
                selectedTheme=Theme.DARK,
                dashboardLayoutProfiles={},
                activeDashboardLayoutProfileId=None,
                dashboardLayoutConfig={},
                cloudSyncPreferences=None,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
        
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
        # Pasar None para main_window en el contexto de prueba
        widget = MarketDataWidget(user_id=test_user_id, api_client=mock_api_client, main_window=None, main_event_loop=loop)
        
        await widget.initialize_widget_data() # Ahora es awaitable
        widget.show()
        # No es necesario 'pass' aquí

    if __name__ == "__main__":
        try:
            qasync.run(main_async)
        except KeyboardInterrupt:
            logger.info("Aplicación de prueba cerrada.")
