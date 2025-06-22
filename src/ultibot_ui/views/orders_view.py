import logging
from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QLineEdit, 
                               QComboBox, QHBoxLayout)

from ultibot_ui.workers import OrdersWorker
# Asumiendo que el api_client se encuentra en esta ruta, siguiendo el patrón de otras vistas.
from ultibot_ui.services.api_client import UltiBotAPIClient

logger = logging.getLogger(__name__)

class OrdersView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Órdenes")
        self.all_orders = []  # Para mantener una copia de todas las órdenes
        
        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Historial de Órdenes")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self._setup_filters()
        
        self.orders_table = QTableWidget()
        self._layout.addWidget(self.orders_table)
        
        self.setLayout(self._layout)
        
        self._setup_table()
        self._setup_worker(api_client)
        
        logger.info("OrdersView initialized.")

    def _setup_filters(self):
        """Configura los widgets de filtrado."""
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por Símbolo...")
        self.search_input.textChanged.connect(self._filter_table)
        filter_layout.addWidget(self.search_input)
        
        self.side_filter_combo = QComboBox()
        self.side_filter_combo.addItems(["Todos", "BUY", "SELL"])
        self.side_filter_combo.currentTextChanged.connect(self._filter_table)
        filter_layout.addWidget(self.side_filter_combo)
        
        self._layout.addLayout(filter_layout)

    def _setup_table(self):
        """Configura la tabla de órdenes."""
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels([
            "Fecha", "Símbolo", "Tipo", "Lado", 
            "Precio", "Cantidad", "Estado"
        ])
        header = self.orders_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.orders_table.setSortingEnabled(True)

    def _setup_worker(self, api_client: UltiBotAPIClient):
        """Inicializa y conecta el worker de datos."""
        self.worker_thread = QThread()
        self.orders_worker = OrdersWorker(api_client)
        self.orders_worker.moveToThread(self.worker_thread)

        # Conectar señales y slots
        self.worker_thread.started.connect(self.orders_worker.run)
        self.orders_worker.finished.connect(self.worker_thread.quit)
        self.orders_worker.finished.connect(self.orders_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.orders_worker.orders_ready.connect(self.update_orders_table)
        self.orders_worker.error_occurred.connect(self._on_error)

        self.worker_thread.start()
        logger.info("Hilo de OrdersWorker iniciado.")

    @Slot(list)
    def update_orders_table(self, orders: list):
        """Puebla la tabla con los datos de las órdenes."""
        logger.info(f"Actualizando tabla de órdenes con {len(orders)} órdenes.")
        self.all_orders = orders  # Guardar la lista completa
        self.orders_table.setSortingEnabled(False)
        self.orders_table.setRowCount(0)

        for row, order in enumerate(self.all_orders):
            self.orders_table.insertRow(row)
            self.orders_table.setItem(row, 0, QTableWidgetItem(order.get('date', '')))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('symbol', '')))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('type', '')))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order.get('side', '')))
            self.orders_table.setItem(row, 4, QTableWidgetItem(str(order.get('price', 0.0))))
            self.orders_table.setItem(row, 5, QTableWidgetItem(str(order.get('amount', 0.0))))
            self.orders_table.setItem(row, 6, QTableWidgetItem(order.get('status', '')))
        
        self.orders_table.setSortingEnabled(True)
        logger.info("Tabla de órdenes actualizada.")
        self._filter_table() # Aplicar filtro inicial

    def _filter_table(self):
        """Filtra la tabla de órdenes basado en los controles de búsqueda."""
        search_text = self.search_input.text().lower()
        side_filter = self.side_filter_combo.currentText()

        for row in range(self.orders_table.rowCount()):
            symbol_item = self.orders_table.item(row, 1)
            side_item = self.orders_table.item(row, 3)

            symbol_match = search_text in symbol_item.text().lower() if symbol_item else False
            
            side_match = (side_filter == "Todos" or 
                          (side_item and side_item.text() == side_filter))

            if symbol_match and side_match:
                self.orders_table.setRowHidden(row, False)
            else:
                self.orders_table.setRowHidden(row, True)

    @Slot(str)
    def _on_error(self, error_message: str):
        """Maneja los errores provenientes del worker."""
        logger.error(f"Ocurrió un error en OrdersWorker: {error_message}")

    def closeEvent(self, event):
        """Asegura que el hilo del worker se cierre correctamente."""
        logger.info("Cerrando OrdersView y deteniendo el hilo del worker.")
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        super().closeEvent(event)
