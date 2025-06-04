import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Callable
from uuid import UUID
import random # Para datos de ejemplo

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter, QMessageBox, QAbstractItemView, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor, QFont

import qasync # Necesario para el bloque de prueba

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
# from src.shared.data_types import NotificationLevel # No se usa directamente aquí, se eliminó la señal

logger = logging.getLogger(__name__)

# Ejemplo de pares disponibles, esto debería venir de la configuración o una API
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

        # Campo de búsqueda/filtro
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar par...")
        self.search_input.textChanged.connect(self.filter_pairs)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        
        # Guardamos los items originales para poder restaurarlos al filtrar
        self._original_list_items: List[QListWidgetItem] = []
        for pair_text in sorted(list(set(available_pairs))):
            item = QListWidgetItem(pair_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable) # type: ignore
            item.setCheckState(Qt.Checked if pair_text in selected_pairs else Qt.Unchecked) # type: ignore
            self._original_list_items.append(item)
            self.list_widget.addItem(item) # Añadir al QListWidget visible
        
        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def filter_pairs(self, text: str):
        text_lower = text.lower().strip()
        self.list_widget.clear() # Limpiar la lista visible
        for item_original in self._original_list_items:
            if item_original is not None: # Asegurar que item_original no sea None
                item_text = item_original.text()
                if item_text: # Asegurar que item_text (resultado de .text()) no sea None
                    if text_lower in item_text.lower(): 
                        self.list_widget.addItem(item_original) # Añadir solo los que coinciden

    def get_selected_pairs(self) -> List[str]:
        selected = []
        # Iterar sobre los items actualmente visibles en el QListWidget
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked: # type: ignore
                selected.append(item.text())
        return selected

class MarketDataWidget(QWidget):
    # signal_add_notification = pyqtSignal(str, str, NotificationLevel) # Movido a DashboardView
    
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.selected_pairs: List[str] = [] 
        self.all_available_pairs: List[str] = [] 
        self._init_ui()
        self._setup_timers()
        # La carga inicial se hará explícitamente desde el DashboardView o MainWindow
        # asyncio.ensure_future(self.load_initial_configuration())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        title_label = QLabel("Datos de Mercado")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter) # type: ignore
        layout.addWidget(title_label)

        self.configure_pairs_button = QPushButton("Configurar Pares")
        self.configure_pairs_button.clicked.connect(self.show_pair_configuration_dialog)
        layout.addWidget(self.configure_pairs_button)

        self.tickers_table = QTableWidget()
        self.tickers_table.setColumnCount(5) 
        self.tickers_table.setHorizontalHeaderLabels(["Símbolo", "Precio", "Cambio 24h (%)", "Volumen 24h", "Tendencia"])
        self.tickers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        self.tickers_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # type: ignore
        self.tickers_table.setSelectionBehavior(QAbstractItemView.SelectRows) # type: ignore
        self.tickers_table.setAlternatingRowColors(True)
        layout.addWidget(self.tickers_table)

    def _setup_timers(self):
        self.tickers_timer = QTimer(self)
        self.tickers_timer.timeout.connect(self.update_tickers_data_slot)

    async def load_initial_configuration(self):
        logger.info("Cargando configuración inicial para MarketDataWidget...")
        try:
            config = await self.api_client.get_user_configuration()
            
            self.selected_pairs = config.get("market_data_widget", {}).get("selected_pairs", ["BTC/USDT", "ETH/USDT"])
            
            # Usar la constante global para todos los pares disponibles por ahora
            self.all_available_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE 
            
            update_interval_ms = config.get("market_data_widget", {}).get("update_interval_ms", 30000) 
            self.tickers_timer.start(update_interval_ms)
            
            logger.info(f"Configuración cargada: Pares seleccionados: {self.selected_pairs}, Intervalo: {update_interval_ms}ms")
            
            await self.update_tickers_data()

        except APIError as e:
            logger.error(f"Error de API al cargar configuración inicial: {e}")
            QMessageBox.critical(self, "Error de Configuración", f"No se pudo cargar la configuración inicial para MarketDataWidget: {e.message}")
        except Exception as e:
            logger.error(f"Error inesperado al cargar configuración inicial: {e}", exc_info=True)
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error inesperado al cargar la configuración: {str(e)}")

    def update_tickers_data_slot(self):
        asyncio.ensure_future(self.update_tickers_data())

    async def update_tickers_data(self):
        if not self.selected_pairs:
            logger.info("No hay pares seleccionados para actualizar datos de tickers.")
            self.tickers_table.setRowCount(0)
            return

        logger.info(f"Actualizando datos de tickers para: {self.selected_pairs}")
        try:
            # Pasar self.user_id a get_ticker_data
            tickers_data_list = await self.api_client.get_ticker_data(self.user_id, self.selected_pairs)
            
            self.tickers_table.setRowCount(len(tickers_data_list))
            for row, data in enumerate(tickers_data_list):
                if not isinstance(data, dict):
                    logger.warning(f"Formato de datos de ticker inesperado: {data}")
                    # Rellenar fila con N/A o mensaje de error
                    for col_idx in range(self.tickers_table.columnCount()):
                        self.tickers_table.setItem(row, col_idx, QTableWidgetItem("Error de formato"))
                    continue

                symbol = data.get("symbol", "N/A")
                price = data.get("lastPrice", "N/A") 
                change_24h_str = data.get("priceChangePercent", "N/A") 
                volume_24h = data.get("volume", "N/A") 

                self.tickers_table.setItem(row, 0, QTableWidgetItem(str(symbol)))
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
                self.tickers_table.setItem(row, 4, QTableWidgetItem("N/D")) # Tendencia

            self.tickers_table.resizeColumnsToContents()

        except APIError as e:
            logger.error(f"Error de API al actualizar datos de tickers: {e}")
            # Podríamos mostrar un mensaje en la tabla o una notificación global
            # Por ahora, solo logueamos y la tabla podría quedar desactualizada o vacía.
        except Exception as e:
            logger.error(f"Error inesperado al actualizar datos de tickers: {e}", exc_info=True)

    def show_pair_configuration_dialog(self):
        # Usar self.all_available_pairs que se cargó (o es la constante)
        dialog = PairConfigurationDialog(self.all_available_pairs, self.selected_pairs, self)
        if dialog.exec() == QDialog.Accepted: # type: ignore
            new_selected_pairs = dialog.get_selected_pairs()
            if set(new_selected_pairs) != set(self.selected_pairs):
                self.selected_pairs = new_selected_pairs
                logger.info(f"Pares de trading actualizados: {self.selected_pairs}")
                asyncio.ensure_future(self.save_widget_configuration())
                asyncio.ensure_future(self.update_tickers_data())

    async def save_widget_configuration(self):
        logger.info(f"Guardando configuración de MarketDataWidget: {self.selected_pairs}")
        try:
            current_config = await self.api_client.get_user_configuration()
            # Asegurarse de que market_data_widget existe en la config
            if "market_data_widget" not in current_config:
                current_config["market_data_widget"] = {}
            current_config["market_data_widget"]["selected_pairs"] = self.selected_pairs
            
            await self.api_client.update_user_configuration({"market_data_widget": current_config["market_data_widget"]})
            logger.info("Configuración de MarketDataWidget guardada exitosamente.")
        except APIError as e:
            logger.error(f"Error de API al guardar configuración: {e}")
            QMessageBox.warning(self, "Error al Guardar", f"No se pudo guardar la configuración de pares: {e.message}")
        except Exception as e:
            logger.error(f"Error inesperado al guardar configuración: {e}", exc_info=True)
            QMessageBox.critical(self, "Error Inesperado", f"Ocurrió un error inesperado al guardar la configuración: {str(e)}")

    def cleanup(self):
        logger.info("Limpiando MarketDataWidget...")
        if self.tickers_timer and self.tickers_timer.isActive():
            self.tickers_timer.stop()
        # Lógica de limpieza de WebSockets (actualmente comentada)
        logger.info("MarketDataWidget limpiado.")

    # --- Métodos relacionados con WebSockets (Comentados) ---
    # async def connect_websockets(self): ...
    # def handle_websocket_update(self, data: Any): ...
    # def update_ticker_in_table(self, ticker_data: TickerData): ...
    # async def disconnect_websockets(self): ...


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    class MockAPIClient:
        async def get_user_configuration(self) -> Dict[str, Any]:
            logger.info("MockAPIClient: get_user_configuration llamada")
            # Simular una configuración que podría no tener market_data_widget o selected_pairs
            return {
                "some_other_setting": "value",
                "market_data_widget": {
                    "selected_pairs": ["BTC/USDT", "ETH/USDT"],
                    "update_interval_ms": 5000 
                }
            }
        
        async def update_user_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
            logger.info(f"MockAPIClient: update_user_configuration llamada con {config_data}")
            # Simular la actualización y devolver la configuración "actualizada"
            return {"market_data_widget": config_data.get("market_data_widget", {})}

        async def get_tickers_data(self, symbols: List[str]) -> List[Dict[str, Any]]:
            logger.info(f"MockAPIClient: get_tickers_data llamada para {symbols}")
            mock_data = []
            for symbol in symbols:
                mock_data.append({
                    "symbol": symbol,
                    "lastPrice": str(round(random.uniform(20000, 60000), 2)),
                    "priceChangePercent": str(round(random.uniform(-5, 5), 2)),
                    "volume": str(round(random.uniform(1000, 100000), 2))
                })
            await asyncio.sleep(0.1) # Simular delay de red
            return mock_data

    async def main_async():
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        test_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        mock_api_client = MockAPIClient()

        widget = MarketDataWidget(user_id=test_user_id, api_client=mock_api_client) # type: ignore
        widget.setWindowTitle("Test Market Data Widget")
        widget.setGeometry(100, 100, 800, 600)
        
        # Cargar configuración inicial explícitamente
        await widget.load_initial_configuration()
        widget.show()

        with loop:
            loop.run_forever()

    # qasync.run es una forma de iniciar el loop para aplicaciones qasync.
    # Sin embargo, la estructura típica es crear el loop y luego correrlo.
    # El if __name__ == '__main__' es el punto de entrada.
    
    # app_instance = QApplication(sys.argv) # Crear la aplicación primero
    # qasync.run(main_async()) # Luego ejecutar la corutina principal con qasync.run

    # O la forma más explícita:
    app_instance = QApplication(sys.argv)
    event_loop = qasync.QEventLoop(app_instance)
    asyncio.set_event_loop(event_loop)
    
    # Iniciar la corutina principal
    # asyncio.ensure_future(main_async()) # Esto programa la corutina
    # event_loop.run_forever() # Esto inicia el loop

    # Para simplificar y asegurar que se ejecute:
    try:
        event_loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        logger.info("Aplicación de prueba cerrada por el usuario.")
    finally:
        if event_loop.is_running():
            event_loop.stop()
        # No es necesario cerrar el loop explícitamente aquí si run_until_complete lo maneja.
        logger.info("Loop de eventos detenido.")
