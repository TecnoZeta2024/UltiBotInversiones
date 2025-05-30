import sys
import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QApplication, QLineEdit, QPushButton, QDialog,
    QDialogButtonBox, QCompleter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QColor, QFont
from typing import List, Dict, Any, Optional, Set # Importar tipos de typing
from datetime import datetime # Importar datetime
from uuid import UUID # Importar UUID

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService

class MarketDataWidget(QWidget):
    """
    Widget para la visualización de datos de mercado en tiempo real.
    Muestra una tabla con pares de criptomonedas, precio actual, cambio 24h y volumen 24h.
    """
    data_updated = pyqtSignal(dict) # Señal para notificar actualizaciones de datos

    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.market_data = {} # Almacena los datos de mercado actuales
        self.favorite_pairs = [] # Lista de pares favoritos
        self._rest_update_timer = QTimer(self)
        self._websocket_tasks: Set[str] = set() # Para mantener un registro de los símbolos suscritos
        self.init_ui()
        self.load_and_subscribe_pairs()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Título del widget
        title_label = QLabel("Resumen de Datos de Mercado")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Tabla para mostrar los datos de mercado
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(["Símbolo", "Precio Actual", "Cambio 24h (%)", "Volumen 24h"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setVisible(False) # No hay un enum para esto, es un booleano
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers) # Hacer la tabla de solo lectura
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

        # Botón para configurar pares favoritos (AC1)
        self.configure_button = QPushButton("Configurar Pares Favoritos")
        self.configure_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.configure_button.clicked.connect(self.open_pair_configuration_dialog)
        main_layout.addWidget(self.configure_button, alignment=Qt.AlignRight)

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
            symbol_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 0, symbol_item)
            # Inicializar las otras celdas con N/A o --
            for col in range(1, 4):
                item = QTableWidgetItem("N/A")
                item.setTextAlignment(Qt.AlignCenter)
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
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setForeground(QColor("#dc3545")) # Rojo para errores
                        self.table_widget.setItem(row, col, item)
                else:
                    # Precio Actual
                    price_item = QTableWidgetItem(f"{data['lastPrice']:.8f}")
                    price_item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row, 1, price_item)

                    # Cambio 24h
                    change_percent = data['priceChangePercent']
                    change_item = QTableWidgetItem(f"{change_percent:.2f}%")
                    change_item.setTextAlignment(Qt.AlignCenter)
                    if change_percent > 0:
                        change_item.setForeground(QColor("#28a745")) # Verde
                    elif change_percent < 0:
                        change_item.setForeground(QColor("#dc3545")) # Rojo
                    else:
                        change_item.setForeground(QColor("#f0f0f0")) # Blanco/gris
                    self.table_widget.setItem(row, 2, change_item)

                    # Volumen 24h
                    volume_item = QTableWidgetItem(f"{data['quoteVolume']:.2f}")
                    volume_item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row, 3, volume_item)
            else:
                # Si no hay datos para un par, mostrar N/A
                for col in range(1, 4):
                    item = QTableWidgetItem("N/A")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row, col, item)

    async def load_and_subscribe_pairs(self):
        """Carga los pares favoritos del usuario y suscribe a los streams de datos."""
        try:
            user_config = await self.config_service.load_user_configuration(self.user_id)
            if user_config.favoritePairs:
                self.set_favorite_pairs(user_config.favoritePairs)
            else:
                self.set_favorite_pairs([]) # Asegurarse de que la lista esté vacía si no hay favoritos

            # Iniciar la actualización REST periódica
            self._rest_update_timer.timeout.connect(lambda: asyncio.create_task(self._fetch_rest_data()))
            self._rest_update_timer.start(10000) # Actualizar cada 10 segundos (configurable)
            await self._fetch_rest_data() # Primera carga inmediata

            # Suscribirse a WebSockets para los pares favoritos
            await self._subscribe_to_websockets()

        except Exception as e:
            print(f"Error al cargar y suscribir pares favoritos: {e}")
            # Manejar el error en la UI, quizás mostrando un mensaje

    async def _fetch_rest_data(self):
        """Obtiene datos de mercado vía REST API para los pares favoritos."""
        if not self.favorite_pairs:
            return

        try:
            rest_data = await self.market_data_service.get_market_data_rest(self.user_id, self.favorite_pairs)
            # Fusionar los datos REST con los datos existentes (que pueden incluir actualizaciones de WS)
            for symbol, data in rest_data.items():
                self.market_data[symbol] = {**self.market_data.get(symbol, {}), **data}
            self.data_updated.emit(self.market_data)
        except Exception as e:
            print(f"Error al obtener datos REST de mercado: {e}")
            # Marcar los pares con error en la UI si es necesario

    async def _subscribe_to_websockets(self):
        """Suscribe a los streams de WebSocket para los pares favoritos."""
        # Cancelar suscripciones WS existentes que ya no son favoritas
        for symbol in list(self._websocket_tasks):
            if symbol not in self.favorite_pairs:
                await self.market_data_service.unsubscribe_from_market_data_websocket(symbol)
                self._websocket_tasks.remove(symbol)

        # Suscribirse a nuevos pares favoritos
        for pair in self.favorite_pairs:
            if pair not in self._websocket_tasks:
                try:
                    await self.market_data_service.subscribe_to_market_data_websocket(
                        self.user_id, pair, self._handle_websocket_data
                    )
                    self._websocket_tasks.add(pair) # Marcar como suscrito
                except Exception as e:
                    print(f"Error al suscribirse a WebSocket para {pair}: {e}")
                    # Marcar el par con error en la UI

    async def _handle_websocket_data(self, data: Dict[str, Any]):
        """Maneja los datos recibidos del stream de WebSocket."""
        event_type = data.get('e')
        if event_type == '24hrTicker':
            symbol = data.get('s')
            last_price = float(data.get('c', 0))
            price_change_percent = float(data.get('P', 0))
            quote_volume = float(data.get('q', 0))

            # Actualizar solo los campos que vienen del WebSocket (principalmente precio)
            current_data = self.market_data.get(symbol, {})
            current_data['lastPrice'] = last_price
            current_data['priceChangePercent'] = price_change_percent
            current_data['quoteVolume'] = quote_volume
            self.market_data[symbol] = current_data
            self.data_updated.emit(self.market_data)
        # else:
            # print(f"Datos WS no reconocidos: {data}")

    def open_pair_configuration_dialog(self):
        """Abre un diálogo para configurar los pares favoritos."""
        dialog = PairConfigurationDialog(self.favorite_pairs, self)
        if dialog.exec_() == QDialog.Accepted:
            new_pairs = dialog.get_selected_pairs()
            self.set_favorite_pairs(new_pairs)
            # Guardar los nuevos pares en el backend
            asyncio.create_task(self._save_favorite_pairs(new_pairs))
            # Re-suscribir a los WebSockets con la nueva lista
            asyncio.create_task(self._subscribe_to_websockets())
            asyncio.create_task(self._fetch_rest_data()) # Actualizar datos REST inmediatamente

    async def _save_favorite_pairs(self, pairs: List[str]):
        """Guarda la lista de pares favoritos en la configuración del usuario."""
        try:
            user_config = await self.config_service.load_user_configuration(self.user_id)
            user_config.favoritePairs = pairs
            await self.config_service.save_user_configuration(self.user_id, user_config)
            print(f"Pares favoritos guardados: {pairs}")
        except Exception as e:
            print(f"Error al guardar pares favoritos: {e}")


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
        completer.setCaseSensitivity(Qt.CaseInsensitive)
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
        self.selected_pairs_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.SectionResizeMode.Stretch)
        self.selected_pairs_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.SectionResizeMode.ResizeToContents)
        self.selected_pairs_list.verticalHeader().setVisible(False)
        self.selected_pairs_list.setEditTriggers(QTableWidget.NoEditTriggers)
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
            symbol_item.setTextAlignment(Qt.AlignCenter)
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
    loop = asyncio.get_event_loop()
    
    # Crear instancias de los servicios mockeados
    mock_market_data_service = MockMarketDataService()
    mock_config_service = MockConfigService()
    test_user_id = UUID("00000000-0000-0000-0000-000000000001")

    # Ejemplo de uso del MarketDataWidget
    main_window = QWidget()
    main_layout = QVBoxLayout()
    main_window.setLayout(main_layout)

    market_data_widget = MarketDataWidget(test_user_id, mock_market_data_service, mock_config_service)
    main_layout.addWidget(market_data_widget)

    # Iniciar la carga y suscripción de pares en una tarea de asyncio
    asyncio.create_task(market_data_widget.load_and_subscribe_pairs())

    # Para que el loop de asyncio se ejecute junto con el de Qt,
    # necesitamos un mecanismo que "bombee" los eventos de asyncio.
    # Esto es lo que qasync hace automáticamente. Aquí, lo simulamos con un QTimer.
    async def run_async_tasks():
        await asyncio.sleep(0.01) # Pequeña pausa para permitir que el loop de Qt procese eventos

    timer_async = QTimer()
    timer_async.timeout.connect(lambda: asyncio.create_task(run_async_tasks()))
    timer_async.start(10) # Ejecutar cada 10ms para mantener el loop de asyncio activo

    main_window.show()
    sys.exit(app.exec_())
