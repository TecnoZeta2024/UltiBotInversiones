import sys
import asyncio
import logging
from typing import List, Dict, Any, Optional, Set, Callable, Coroutine
from uuid import UUID
import random # Para datos de ejemplo

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter, QMessageBox, QAbstractItemView, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QThread # Importar QThread
from PyQt5.QtGui import QColor, QFont

import qasync # Necesario para el bloque de prueba

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

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
            if item_original is not None and isinstance(item_original, QListWidgetItem): # Asegurar que item_original no sea None y sea QListWidgetItem
                item_text = item_original.text()
                if item_text is not None and isinstance(item_text, str): # Asegurar que item_text no sea None y sea str
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
    user_config_fetched = pyqtSignal(dict)
    tickers_data_fetched = pyqtSignal(list)
    config_saved = pyqtSignal(dict)
    market_data_api_error = pyqtSignal(str)
    
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.selected_pairs: List[str] = [] 
        self.all_available_pairs: List[str] = [] 
        self.active_api_workers = [] # Para mantener referencia a los workers y threads

        self._init_ui()
        self._setup_timers()

        # Conectar señales a manejadores
        self.user_config_fetched.connect(self._handle_user_config_result)
        self.tickers_data_fetched.connect(self._handle_tickers_data_result)
        self.config_saved.connect(self._handle_config_saved_result)
        self.market_data_api_error.connect(self._handle_market_data_api_error)

    def _run_api_worker_and_await_result(self, coro: Coroutine) -> Any:
        """
        Ejecuta una corutina en un ApiWorker y espera su resultado.
        Retorna un Future que se puede await.
        """
        from src.ultibot_ui.main import ApiWorker # Importar localmente
        import qasync # Importar qasync para obtener el bucle de eventos

        qasync_loop = asyncio.get_event_loop()
        future = qasync_loop.create_future()

        worker = ApiWorker(coroutine_factory=lambda: coro, qasync_loop=qasync_loop)
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
        self.tickers_timer.timeout.connect(self._start_update_tickers_data_task)

    def _handle_user_config_result(self, config: Dict[str, Any]):
        """Manejador para el resultado de la configuración de usuario."""
        self.selected_pairs = config.get("market_data_widget", {}).get("selected_pairs", ["BTC/USDT", "ETH/USDT"])
        self.all_available_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE # Usar la constante global por ahora
        update_interval_ms = config.get("market_data_widget", {}).get("update_interval_ms", 30000) 
        self.tickers_timer.start(update_interval_ms)
        logger.info(f"Configuración cargada: Pares seleccionados: {self.selected_pairs}, Intervalo: {update_interval_ms}ms")
        self._start_update_tickers_data_task() # Iniciar la actualización de tickers

    def load_initial_configuration(self):
        logger.info("Cargando configuración inicial para MarketDataWidget...")
        try:
            coro = self.api_client.get_user_configuration()
            self._run_api_worker_and_await_result(coro).add_done_callback(
                lambda f: self.user_config_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("load_initial_configuration: Llamada a get_user_configuration programada.")
        except Exception as e:
            logger.error(f"load_initial_configuration: Error inesperado al programar la carga de configuración: {e}", exc_info=True)
            self.market_data_api_error.emit(f"Error al programar carga de configuración: {e}")

    def _start_update_tickers_data_task(self):
        """Inicia la tarea asíncrona de actualización de datos de tickers."""
        self.update_tickers_data()

    def _handle_tickers_data_result(self, tickers_data_list: List[Dict[str, Any]]):
        """Manejador para el resultado de los datos de tickers."""
        if not self.selected_pairs:
            logger.info("No hay pares seleccionados para actualizar datos de tickers.")
            self.tickers_table.setRowCount(0)
            return

        self.tickers_table.setRowCount(len(tickers_data_list))
        for row, data in enumerate(tickers_data_list):
            if not isinstance(data, dict):
                logger.warning(f"Formato de datos de ticker inesperado: {data}")
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
        logger.info("Datos de tickers actualizados en la tabla.")

    def update_tickers_data(self):
        logger.info(f"Actualizando datos de tickers para: {self.selected_pairs} (refactorizado)")
        try:
            if not self.selected_pairs:
                logger.info("No hay pares seleccionados para actualizar datos de tickers.")
                self.tickers_table.setRowCount(0)
                return

            coro = self.api_client.get_ticker_data(self.user_id, self.selected_pairs)
            self._run_api_worker_and_await_result(coro).add_done_callback(
                lambda f: self.tickers_data_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("update_tickers_data: Llamada a get_ticker_data programada.")
        except Exception as e:
            logger.error(f"update_tickers_data: Error inesperado al programar la actualización de tickers: {e}", exc_info=True)
            self.market_data_api_error.emit(f"Error al programar actualización de tickers: {e}")

    def show_pair_configuration_dialog(self):
        dialog = PairConfigurationDialog(self.all_available_pairs, self.selected_pairs, self)
        if dialog.exec() == QDialog.Accepted: # type: ignore
            new_selected_pairs = dialog.get_selected_pairs()
            if set(new_selected_pairs) != set(self.selected_pairs):
                self.selected_pairs = new_selected_pairs
                logger.info(f"Pares de trading actualizados: {self.selected_pairs}")
                self.save_widget_configuration() # Llamada refactorizada
                self.update_tickers_data() # Llamada refactorizada

    def _handle_config_saved_result(self, config_data: Dict[str, Any]):
        """Manejador para el resultado de guardar la configuración."""
        logger.info("Configuración de MarketDataWidget guardada exitosamente (manejador de señal).")
        # Podrías añadir una notificación visual aquí si es necesario

    def save_widget_configuration(self):
        logger.info(f"Guardando configuración de MarketDataWidget: {self.selected_pairs} (refactorizado)")
        try:
            # Primero obtener la configuración actual
            coro_get = self.api_client.get_user_configuration()
            future_get_config = self._run_api_worker_and_await_result(coro_get)

            def on_get_config_done(f):
                if f.exception():
                    self.market_data_api_error.emit(f"Error al obtener config para guardar: {f.exception()}")
                    return
                
                current_config = f.result()
                if "market_data_widget" not in current_config:
                    current_config["market_data_widget"] = {}
                current_config["market_data_widget"]["selected_pairs"] = self.selected_pairs
                
                # Luego actualizar la configuración
                coro_update = self.api_client.update_user_configuration({"market_data_widget": current_config["market_data_widget"]})
                self._run_api_worker_and_await_result(coro_update).add_done_callback(
                    lambda f_update: self.config_saved.emit(f_update.result()) if not f_update.exception() else self.market_data_api_error.emit(f"Error al guardar config: {f_update.exception()}")
                )
                logger.info("save_widget_configuration: Llamada a update_user_configuration programada.")

            future_get_config.add_done_callback(on_get_config_done)
            logger.info("save_widget_configuration: Llamada a get_user_configuration programada para guardar.")

        except Exception as e:
            logger.error(f"save_widget_configuration: Error inesperado al programar el guardado de configuración: {e}", exc_info=True)
            self.market_data_api_error.emit(f"Error al programar guardado de configuración: {e}")

    def _handle_market_data_api_error(self, message: str):
        """Manejador general para errores de API en MarketDataWidget."""
        logger.error(f"MarketDataWidget: Error de API general: {message}")
        QMessageBox.warning(self, "Error de API en Datos de Mercado", message)

    def cleanup(self):
        logger.info("Limpiando MarketDataWidget...")
        if self.tickers_timer and self.tickers_timer.isActive():
            self.tickers_timer.stop()
        
        # Limpiar workers y threads activos
        for worker, thread in self.active_api_workers[:]:
            if thread.isRunning():
                logger.info(f"MarketDataWidget: Cleaning up active ApiWorker thread {thread.objectName()}.")
                thread.quit()
                if not thread.wait(2000): # Esperar un máximo de 2 segundos
                    logger.warning(f"MarketDataWidget: Thread {thread.objectName()} did not finish in time. Terminating.")
                    thread.terminate()
                    thread.wait()
            if (worker, thread) in self.active_api_workers:
                self.active_api_workers.remove((worker, thread))
        logger.info(f"MarketDataWidget: All active ApiWorkers ({len(self.active_api_workers)} remaining) processed for cleanup.")
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

        async def get_ticker_data(self, user_id: UUID, symbols: List[str]) -> List[Dict[str, Any]]: # Añadir user_id
            logger.info(f"MockAPIClient: get_ticker_data llamada para {symbols} (user_id: {user_id})")
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
        widget.load_initial_configuration() # Llamada refactorizada
        widget.show()

        with loop:
            loop.run_forever()

    app_instance = QApplication(sys.argv)
    event_loop = qasync.QEventLoop(app_instance)
    asyncio.set_event_loop(event_loop)
    
    try:
        event_loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        logger.info("Aplicación de prueba cerrada por el usuario.")
    finally:
        if event_loop.is_running():
            event_loop.stop()
        logger.info("Loop de eventos detenido.")
