import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QCoreApplication # Importar QCoreApplication
from PyQt5.QtGui import QColor, QFont
from typing import List, Dict, Any, Optional, Set # Importar tipos de typing
from datetime import datetime # Importar datetime
from uuid import UUID # Importar UUID
import asyncio # Importar asyncio para el loop de eventos

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.services.ui_config_service import UIConfigService

class MarketDataWidget(QWidget):
    data_updated = pyqtSignal(dict)  # Emits the updated market_data dictionary

    def __init__(self, user_id: UUID, market_data_service: UIMarketDataService, config_service: UIConfigService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.market_data = {} # Almacena los datos de mercado actuales
        self.favorite_pairs = [] # Lista de pares favoritos
        self._rest_update_timer = QTimer(self)
        self._websocket_tasks: Set[str] = set() # Para mantener un registro de los símbolos suscritos
        self.init_ui()
        # La carga y suscripción de pares se iniciará de forma asíncrona después de la inicialización del widget
        # Esto se manejará desde el código que instancia el widget (ej. main_window o dashboard_view)

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Initial load
        asyncio.create_task(self.load_and_refresh_data())


    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Table for market data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Símbolo", "Precio Actual", "Cambio 24h (%)", "Volumen 24h"])
        horizontal_header = self.table_widget.horizontalHeader()
        if horizontal_header:
            horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # Usar ResizeMode
        
        vertical_header = self.table_widget.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)
        
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Usar EditTrigger
        self.table_widget.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #f0f0f0;
                padding: 5px;
                border: 1px solid #444;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.table_widget)

        # Buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self._on_refresh_button_clicked)
        button_layout.addWidget(self.refresh_button)

        self.configure_button = QPushButton("Configure Pairs")
        self.configure_button.clicked.connect(self.open_pair_configuration_dialog)
        main_layout.addWidget(self.configure_button, alignment=Qt.AlignmentFlag.AlignRight) # Usar AlignmentFlag

        layout.addLayout(button_layout)
        self.data_updated.connect(self.update_table)

    def set_favorite_pairs(self, pairs: List[str]):
        """Establece la lista de pares favoritos y actualiza la tabla."""
        self.favorite_pairs = pairs
        self.update_table_structure()

    def update_table_structure(self):
        """Actualiza la estructura de la tabla basada en los pares favoritos."""
        self.table_widget.setRowCount(len(self.favorite_pairs))
        for row, pair in enumerate(self.favorite_pairs):
            symbol_item = QTableWidgetItem(pair)
            symbol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
            self.table_widget.setItem(row, 0, symbol_item)
            # Inicializar las otras celdas con N/A o --
            for col in range(1, 4):
                item = QTableWidgetItem("N/A")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                self.table_widget.setItem(row, col, item)

    def update_table(self, new_data: Dict[str, Dict[str, Any]]):
        """
        Actualiza la tabla con los nuevos datos de mercado.
        new_data: {'SYMBOL': {'lastPrice': X, 'priceChangePercent': Y, 'quoteVolume': Z, 'error': '...'}}
        """
        for row, pair in enumerate(self.favorite_pairs):
            data = new_data.get(pair)
            if data:
                if "error" in data:
                    for col in range(1, 4):
                        item = QTableWidgetItem("Error")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                        item.setForeground(QColor("#dc3545")) # Rojo para errores
                        self.table_widget.setItem(row, col, item)
                else:
                    # Precio Actual
                    price_item = QTableWidgetItem(f"{data['lastPrice']:.8f}")
                    price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                    self.table_widget.setItem(row, 1, price_item)

                    # Cambio 24h
                    change_percent = data['priceChangePercent']
                    change_item = QTableWidgetItem(f"{change_percent:.2f}%")
                    change_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                    if change_percent > 0:
                        change_item.setForeground(QColor("#28a745")) # Verde
                    elif change_percent < 0:
                        change_item.setForeground(QColor("#dc3545")) # Rojo
                    else:
                        change_item.setForeground(QColor("#f0f0f0")) # Blanco/gris
                    self.table_widget.setItem(row, 2, change_item)

                    # Volumen 24h
                    volume_item = QTableWidgetItem(f"{data['quoteVolume']:.2f}")
                    volume_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                    self.table_widget.setItem(row, 3, volume_item)
            else:
                # Si no hay datos para un par, mostrar N/A
                for col in range(1, 4):
                    item = QTableWidgetItem("N/A")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
                    self.table_widget.setItem(row, col, item)

    async def load_and_subscribe_pairs(self):
        """Carga los pares favoritos del usuario y suscribe a los streams de datos."""
        try:
            user_config = await self.config_service.get_user_configuration(self.user_id) # Usar get_user_configuration
            if user_config.favoritePairs:
                self.set_favorite_pairs(user_config.favoritePairs)
            else:
                self.set_favorite_pairs([]) # Asegurarse de que la lista esté vacía si no hay favoritos

            # Iniciar la actualización REST periódica
            # Conectar el timer a un slot síncrono que inicie la tarea asíncrona
            self._rest_update_timer.timeout.connect(self._on_rest_timer_timeout)
            self._rest_update_timer.start(10000) # Actualizar cada 10 segundos (configurable)
            await self._fetch_rest_data() # Primera carga inmediata

            # Suscribirse a WebSockets para los pares favoritos
            await self._subscribe_to_websockets()

        except Exception as e:
            self.status_label.setText(f"Error during initial load: {e}")
            QMessageBox.critical(self, "Load Error", f"Failed to load initial data: {e}")
        finally:
            self.table_widget.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.configure_button.setEnabled(True)


    def _on_rest_update_timeout(self):
        if self.favorite_pairs:
            asyncio.create_task(self._fetch_rest_data())
        else:
            self.status_label.setText("No pairs to fetch. Configure pairs.")
            if self.rest_update_timer.isActive():
                self.rest_update_timer.stop()


    def _on_refresh_button_clicked(self):
        if self.favorite_pairs:
            asyncio.create_task(self._fetch_rest_data())
        else:
            QMessageBox.information(self, "No Pairs", "Please configure favorite pairs first.")


    async def _fetch_rest_data(self):
        """Fetches current ticker data for favorite pairs using UIMarketDataService."""
        if not self.favorite_pairs:
            self.status_label.setText("No favorite pairs to fetch.")
            self.market_data = {}
            self.data_updated.emit(self.market_data)
            return

        self.status_label.setText(f"Fetching data for {len(self.favorite_pairs)} pairs...")
        self.table_widget.setEnabled(False) # Disable table during update
        self.refresh_button.setEnabled(False)

        try:
            # Using the new batch ticker fetch method
            tickers_data = await self.market_data_service.fetch_tickers_data(self.favorite_pairs)

            if tickers_data is None:
                # API call failed or returned None (e.g., network error, server error)
                self.status_label.setText("Error fetching market data. Check connection or try again.")
                # Preserve old data but mark as error, or clear and show error per row
                for pair in self.favorite_pairs:
                    self.market_data[pair] = {
                        "lastPrice": "Error",
                        "priceChangePercent": "Error",
                        "quoteVolume": "Error",
                        "error": "Failed to fetch"
                    }
            else:
                # API call succeeded, update market_data
                # Ensure all favorite pairs have an entry, even if API didn't return them (maybe they are delisted)
                new_market_data = {}
                for pair in self.favorite_pairs:
                    if pair in tickers_data:
                        new_market_data[pair] = tickers_data[pair]
                    else:
                        new_market_data[pair] = {
                            "lastPrice": "N/A",
                            "priceChangePercent": "N/A",
                            "quoteVolume": "N/A",
                            "error": "Not found"
                        }
                self.market_data = new_market_data
                self.status_label.setText(f"Market data updated. Last: {QDateTime.currentDateTime().toString()}") # type: ignore

            self.data_updated.emit(self.market_data)

        except Exception as e:
            self.status_label.setText(f"An error occurred: {e}")
            # You might want to update the table to show errors for all rows
            for pair in self.favorite_pairs:
                 self.market_data[pair] = {"lastPrice": "Error", "priceChangePercent": "N/A", "quoteVolume": "N/A", "error": str(e)}
            self.data_updated.emit(self.market_data)
        finally:
            self.table_widget.setEnabled(True)
            self.refresh_button.setEnabled(True)

    def update_table(self, new_data: Dict[str, Dict[str, Any]]):
        self.table_widget.setRowCount(0) # Clear existing rows

        if not new_data and self.favorite_pairs: # Data is empty but we have pairs, likely an error state
             for i, pair_symbol in enumerate(self.favorite_pairs):
                self.table_widget.insertRow(i)
                self.table_widget.setItem(i, 0, QTableWidgetItem(pair_symbol))
                error_item = QTableWidgetItem("Error fetching")
                error_item.setForeground(Qt.GlobalColor.red) # type: ignore
                self.table_widget.setItem(i, 1, error_item)
                self.table_widget.setItem(i, 2, QTableWidgetItem("-"))
                self.table_widget.setItem(i, 3, QTableWidgetItem("-"))
             return

        for i, pair_symbol in enumerate(self.favorite_pairs): # Iterate over configured pairs to maintain order
            self.table_widget.insertRow(i)
            self.table_widget.setItem(i, 0, QTableWidgetItem(pair_symbol))

            pair_data = new_data.get(pair_symbol)
            if pair_data:
                if pair_data.get("error"):
                    price_item = QTableWidgetItem(str(pair_data.get("lastPrice", "Error"))) # Show error if available
                    price_item.setForeground(Qt.GlobalColor.red) # type: ignore
                    change_item = QTableWidgetItem(str(pair_data.get("priceChangePercent", "-")))
                    volume_item = QTableWidgetItem(str(pair_data.get("quoteVolume", "-")))
                    if pair_data.get("error") == "Not found":
                         price_item.setForeground(Qt.GlobalColor.gray) # type: ignore
                else:
                    price_item = QTableWidgetItem(str(pair_data.get("lastPrice", "N/A")))
                    change_val_str = str(pair_data.get("priceChangePercent", "0"))
                    try:
                        change_val = float(change_val_str)
                        change_item = QTableWidgetItem(f"{change_val:.2f}%")
                        if change_val > 0:
                            change_item.setForeground(Qt.GlobalColor.green) # type: ignore
                        elif change_val < 0:
                            change_item.setForeground(Qt.GlobalColor.red) # type: ignore
                        else:
                            change_item.setForeground(Qt.GlobalColor.gray) # type: ignore
                    except ValueError:
                        change_item = QTableWidgetItem(change_val_str) # Show as is if not float
                        change_item.setForeground(Qt.GlobalColor.gray) # type: ignore

                    volume_item = QTableWidgetItem(str(pair_data.get("quoteVolume", "N/A")))

                self.table_widget.setItem(i, 1, price_item)
                self.table_widget.setItem(i, 2, change_item)
                self.table_widget.setItem(i, 3, volume_item)
            else:
                # Pair was in favorite_pairs but not in new_data (should be handled by _fetch_rest_data)
                self.table_widget.setItem(i, 1, QTableWidgetItem("Waiting..."))
                self.table_widget.setItem(i, 2, QTableWidgetItem("-"))
                self.table_widget.setItem(i, 3, QTableWidgetItem("-"))


    def set_favorite_pairs(self, pairs: List[str]):
        """Updates the list of favorite pairs and refreshes the table structure."""
        self.favorite_pairs = sorted(list(set(pairs))) # Ensure unique and sorted

        # Update table structure (rows) based on new pairs
        # This will clear data, but _fetch_rest_data will be called soon after.
        self.market_data = {pair: {} for pair in self.favorite_pairs} # Reset data with new keys
        self.update_table(self.market_data) # Display empty rows for new pairs

        if not self.favorite_pairs:
            self.status_label.setText("No favorite pairs configured.")
            if self.rest_update_timer.isActive():
                self.rest_update_timer.stop()
        else:
            self.status_label.setText(f"{len(self.favorite_pairs)} pairs configured. Fetching data...")
            if not self.rest_update_timer.isActive():
                 self.rest_update_timer.start(30 * 1000) # Restart timer if it was stopped


    def open_pair_configuration_dialog(self):
        # TODO: Fetch ALL_AVAILABLE_PAIRS_EXAMPLE from config service or market data service eventually
        # For now, using the example list.
        # all_pairs = await self.market_data_service.get_all_available_symbols() or ALL_AVAILABLE_PAIRS_EXAMPLE
        all_pairs = ALL_AVAILABLE_PAIRS_EXAMPLE
        
        dialog = PairConfigurationDialog(self.favorite_pairs, all_pairs, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_pairs = dialog.get_selected_pairs()
            self.set_favorite_pairs(new_pairs)
            # Guardar los nuevos pares en el backend y re-suscribir
            asyncio.create_task(self._save_and_resubscribe_pairs(new_pairs))

    def _on_rest_timer_timeout(self):
        """Slot síncrono para el QTimer que inicia la tarea asíncrona de fetch de datos REST."""
        asyncio.create_task(self._fetch_rest_data())

    async def _save_and_resubscribe_pairs(self, new_pairs: List[str]):
        """Guarda los pares favoritos y re-suscribe a los streams."""
        await self._save_favorite_pairs(new_pairs)
        await self._subscribe_to_websockets()
        await self._fetch_rest_data() # Actualizar datos REST inmediatamente

    async def _save_favorite_pairs(self, pairs: List[str]):
        """Guarda la lista de pares favoritos en la configuración del usuario."""
        try:
            user_config = await self.config_service.get_user_configuration(self.user_id) # Usar get_user_configuration
            user_config.favoritePairs = pairs
            await self.config_service.save_user_configuration(user_config) # Eliminar user_id como argumento
            print(f"Pares favoritos guardados: {pairs}")
        except Exception as e:
            print(f"Error al guardar pares favoritos: {e}")

    def cleanup(self):
        """
        Limpia los recursos utilizados por MarketDataWidget.
        Detiene el temporizador de actualización REST y cancela las suscripciones WebSocket.
        """
        print("MarketDataWidget: cleanup called.")
        # Detener el temporizador de actualización REST
        if hasattr(self, '_rest_update_timer') and self._rest_update_timer.isActive():
            print("MarketDataWidget: Stopping REST update timer.")
            self._rest_update_timer.stop()

        # Cancelar todas las suscripciones WebSocket activas
        # Es importante hacerlo en un loop de eventos de asyncio si es posible,
        # o al menos marcar que deben ser canceladas.
        # La forma correcta de hacerlo depende de cómo se gestiona el loop de asyncio
        # en el contexto de la aplicación PyQt.
        # Por ahora, simplemente llamaremos a unsubscribe.
        # Nota: Esto podría necesitar ejecutarse en el loop de asyncio principal.
        
        # Crear una copia de la colección antes de iterar sobre ella para modificarla
        symbols_to_unsubscribe = list(self._websocket_tasks)
        if symbols_to_unsubscribe:
            print(f"MarketDataWidget: Unsubscribing from WebSockets for: {symbols_to_unsubscribe}")
            # Esta parte es asíncrona, idealmente se manejaría de forma más integrada
            # con el cierre del loop de asyncio principal de la aplicación.
            # Por ahora, creamos tareas para desuscribir.
            # Esto podría no completarse si el loop de asyncio se cierra prematuramente.
            async def unsubscribe_all():
                for symbol in symbols_to_unsubscribe:
                    try:
                        await self.market_data_service.unsubscribe_from_market_data_websocket(symbol)
                        if symbol in self._websocket_tasks: # Verificar antes de remover
                             self._websocket_tasks.remove(symbol)
                    except Exception as e:
                        print(f"MarketDataWidget: Error unsubscribing from {symbol}: {e}")
            
            # Intentar ejecutar en el loop de eventos existente si está disponible y corriendo
            try:
                loop = asyncio.get_running_loop()
                # Si el loop está corriendo, podemos crear una tarea.
                # Sin embargo, si estamos en el proceso de cierre, el loop podría no procesarla.
                # Esta es una limitación de mezclar asyncio con toolkits síncronos como Qt sin un integrador como qasync.
                # Para una limpieza más robusta, el cierre de WebSockets debería ser manejado
                # por el market_data_service.close() que se llama en main.py.
                # Aquí solo nos aseguramos de que el widget no intente usarlos más.
                # La llamada real a unsubscribe_from_market_data_websocket ya está en market_data_service.close()
                # por lo que aquí principalmente limpiamos el estado local del widget.
                print("MarketDataWidget: WebSocket cleanup will be handled by MarketDataService.close(). Clearing local tasks.")
                self._websocket_tasks.clear()

            except RuntimeError: # No running event loop
                print("MarketDataWidget: No running asyncio event loop to schedule WebSocket unsubscriptions. MarketDataService.close() should handle this.")
                self._websocket_tasks.clear() # Limpiar de todas formas el estado local

        print("MarketDataWidget: cleanup finished.")


class PairConfigurationDialog(QDialog):
    """
    Diálogo para permitir al usuario añadir/eliminar pares de criptomonedas favoritos.
    """
    def __init__(self, current_pairs: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Pares Favoritos")
        self.setGeometry(200, 200, 400, 300)
        self.setModal(True) # Hacer el diálogo modal

        self.current_pairs = set(current_pairs) # Usar un set para búsquedas rápidas
        self.all_available_pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "SOLUSDT", "DOGEUSDT"] # Simulación de pares disponibles

        self.init_ui()

    def init_ui(self):
        dialog_layout = QVBoxLayout()
        self.setLayout(dialog_layout)

        # Campo de entrada para añadir nuevos pares
        add_pair_layout = QHBoxLayout()
        self.pair_input = QLineEdit()
        self.pair_input.setPlaceholderText("Buscar o añadir par (ej. BTCUSDT)")
        
        # Autocompletado (básico, se puede mejorar con datos de la API de Binance)
        completer = QCompleter(self.all_available_pairs, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive) # Usar CaseSensitivity
        self.pair_input.setCompleter(completer)

        add_button = QPushButton("Añadir")
        add_button.clicked.connect(self.add_pair)
        add_pair_layout.addWidget(self.pair_input)
        add_pair_layout.addWidget(add_button)
        dialog_layout.addLayout(add_pair_layout)

        # Lista de pares seleccionados
        self.selected_pairs_list = QTableWidget()
        self.selected_pairs_list.setColumnCount(2)
        self.selected_pairs_list.setHorizontalHeaderLabels(["Símbolo", "Acción"])
        selected_pairs_horizontal_header = self.selected_pairs_list.horizontalHeader()
        if selected_pairs_horizontal_header:
            selected_pairs_horizontal_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Usar ResizeMode
            selected_pairs_horizontal_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Usar ResizeMode
        
        selected_pairs_vertical_header = self.selected_pairs_list.verticalHeader()
        if selected_pairs_vertical_header:
            selected_pairs_vertical_header.setVisible(False)
        
        self.selected_pairs_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Usar EditTrigger
        dialog_layout.addWidget(self.selected_pairs_list)

        self.populate_selected_pairs_list()

        # Botones de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        dialog_layout.addWidget(button_box)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #f0f0f0;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #f0f0f0;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTableWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #f0f0f0;
                padding: 5px;
                border: 1px solid #444;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

    def populate_selected_pairs_list(self):
        self.selected_pairs_list.setRowCount(0) # Limpiar la tabla
        for pair in sorted(list(self.current_pairs)):
            row_position = self.selected_pairs_list.rowCount()
            self.selected_pairs_list.insertRow(row_position)

            symbol_item = QTableWidgetItem(pair)
            symbol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) # Usar AlignmentFlag
            self.selected_pairs_list.setItem(row_position, 0, symbol_item)

            remove_button = QPushButton("Eliminar")
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    padding: 3px 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            remove_button.clicked.connect(lambda _, p=pair: self.remove_pair(p))
            self.selected_pairs_list.setCellWidget(row_position, 1, remove_button)

    def add_pair(self):
        pair = self.pair_input.text().strip().upper()
        if pair and pair not in self.current_pairs:
            # Validación básica: solo permitir pares que estén en all_available_pairs (simulado)
            if pair in self.all_available_pairs:
                self.current_pairs.add(pair)
                self.populate_selected_pairs_list()
                self.pair_input.clear()
            else:
                # Aquí se podría mostrar un mensaje de error al usuario
                print(f"Par '{pair}' no válido o no disponible.")
        elif pair in self.current_pairs:
            print(f"Par '{pair}' ya está en la lista.")

    def remove_pair(self, pair: str):
        if pair in self.current_pairs:
            self.current_pairs.remove(pair)
            self.populate_selected_pairs_list()

    def get_selected_pairs(self) -> List[str]:
        return sorted(list(self.current_pairs))


if __name__ == '__main__':
    # Para ejecutar el ejemplo, necesitarás un loop de eventos de asyncio
    # que se ejecute junto con el loop de eventos de QApplication.
    # Una forma sencilla para pruebas es usar un runner como qasync,
    # pero para este ejemplo, simularemos los servicios.

    from typing import Callable # Importar Callable para el mock

    class MockMarketDataService:
        async def get_market_data_rest(self, user_id: UUID, symbols: List[str]) -> Dict[str, Any]:
            print(f"Mock: Obteniendo datos REST para {symbols}")
            mock_data = {}
            for symbol in symbols:
                mock_data[symbol] = {
                    "lastPrice": 100.0 + (datetime.now().second % 10),
                    "priceChangePercent": 0.5 + (datetime.now().second % 3 - 1),
                    "quoteVolume": 1000000.0 + (datetime.now().second * 1000)
                }
            return mock_data

        async def subscribe_to_market_data_websocket(self, user_id: UUID, symbol: str, callback: Callable):
            print(f"Mock: Suscribiéndose a WS para {symbol}")
            # En un mock, no iniciamos un WS real, solo simulamos la suscripción
            pass

        async def unsubscribe_from_market_data_websocket(self, symbol: str):
            print(f"Mock: Desuscribiéndose de WS para {symbol}")
            pass

    class MockConfigService:
        def __init__(self):
            self._config = {"favoritePairs": ["BTCUSDT", "ETHUSDT"]}

        async def load_user_configuration(self, user_id: UUID) -> Any:
            class MockUserConfig:
                def __init__(self, pairs):
                    self.favoritePairs = pairs
            return MockUserConfig(self._config["favoritePairs"])

        async def save_user_configuration(self, user_id: UUID, config: Any):
            self._config["favoritePairs"] = config.favoritePairs
            print(f"Mock: Pares favoritos guardados: {self._config['favoritePairs']}")

    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background-color: #222;
            color: #f0f0f0;
            font-family: "Segoe UI", sans-serif;
        }
        QLabel {
            color: #f0f0f0;
        }
    """)

    # Configurar el loop de eventos de asyncio para que se ejecute con el de Qt
    # Esto es una simplificación; en una aplicación real se usaría qasync
    # Asegurarse de que haya un loop de eventos de asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Crear instancias de los servicios mockeados
    mock_market_data_service = MockMarketDataService()
    mock_config_service = MockConfigService()
    test_user_id = UUID("00000000-0000-0000-0000-000000000001")

    # Ejemplo de uso del MarketDataWidget
    main_window = QWidget()
    main_layout = QVBoxLayout()
    main_window.setLayout(main_layout)

    # Ignorar los errores de Pylance para los mocks en el bloque de prueba local
    market_data_widget = MarketDataWidget(test_user_id, mock_market_data_service, mock_config_service) # type: ignore
    main_layout.addWidget(market_data_widget)

    # Iniciar la carga y suscripción de pares en una tarea de asyncio
    # Usar un QTimer para iniciar la tarea asíncrona después de que el loop de Qt esté listo
    # La lambda ahora solo inicia la tarea, no devuelve la tarea en sí.
    def _start_load_and_subscribe():
        loop.create_task(market_data_widget.load_and_subscribe_pairs())
    QTimer.singleShot(0, _start_load_and_subscribe)

    # Para que el loop de asyncio se ejecute junto con el de Qt,
    # necesitamos un mecanismo que "bombee" los eventos de asyncio.
    # Esto es lo que qasync hace automáticamente. Aquí, lo simulamos con un QTimer.
    # Este timer asegura que el loop de asyncio tenga la oportunidad de ejecutarse.
    def run_async_tasks_periodically():
        # Ejecutar el loop de asyncio por un corto período
        loop.call_soon(loop.stop)
        loop.run_forever()

    timer_async = QTimer()
    timer_async.timeout.connect(run_async_tasks_periodically)
    timer_async.start(10) # Ejecutar cada 10ms para mantener el loop de asyncio activo

    main_window.show()
    sys.exit(app.exec_())
