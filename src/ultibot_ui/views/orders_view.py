import logging
import logging
from PySide6.QtCore import QThread, Slot
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QLineEdit, 
                               QComboBox, QHBoxLayout, QMessageBox, QApplication) # Importar QApplication
from typing import Optional
from uuid import UUID

from ultibot_ui.workers import OrdersWorker
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)


class OrdersView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Órdenes")
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client
        self.main_window = main_window # Guardar referencia a MainWindow
        self.all_orders = []  # Para mantener una copia de todas las órdenes
        self.worker_thread: Optional[QThread] = None
        self.orders_worker: Optional[OrdersWorker] = None
        
        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Historial de Órdenes")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self._setup_filters()
        
        self.orders_table = QTableWidget()
        self._layout.addWidget(self.orders_table)
        
        self.setLayout(self._layout)
        
        self._setup_table()
        # No llamar a _setup_worker aquí, se llamará después de set_user_id
        
        logger.info("OrdersView initialized.")

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa la carga de órdenes."""
        self.user_id = user_id
        logger.info(f"OrdersView: User ID set to {user_id}. Setting up worker.")
        self._setup_worker(self.api_client)

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
        if self.user_id is None:
            logger.warning("OrdersView: user_id no está disponible. No se puede configurar el worker de órdenes.")
            return

        self.worker_thread = QThread()
        # Obtener el bucle de eventos principal de la aplicación
        app_instance = QApplication.instance()
        if not app_instance:
            logger.error("OrdersView: No se encontró la instancia de QApplication para OrdersWorker.")
            self._on_error("Error interno: No se pudo obtener la instancia de la aplicación.")
            return
            
        main_event_loop = app_instance.property("main_event_loop")
        if not main_event_loop:
            logger.error("OrdersView: No se encontró el bucle de eventos principal de qasync para OrdersWorker.")
            self._on_error("Error interno: Bucle de eventos principal no disponible.")
            return

        self.orders_worker = OrdersWorker(api_client, self.user_id, main_event_loop) # Eliminar el parent para permitir moveToThread
        self.orders_worker.moveToThread(self.worker_thread)

        # Conectar señales y slots
        self.worker_thread.started.connect(self.orders_worker.run)
        # Conectar señales y slots
        self.orders_worker.orders_ready.connect(self.update_orders_table)
        self.orders_worker.error_occurred.connect(self._on_error)
        
        # Conectar la señal finished del worker para que el hilo se cierre
        self.orders_worker.finished.connect(self.worker_thread.quit)
        
        # Conectar la señal finished del hilo para limpiar el worker y el hilo
        self.worker_thread.finished.connect(self.orders_worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        # Añadir el hilo a la ventana principal para su seguimiento
        self.main_window.add_thread(self.worker_thread)

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
        QMessageBox.critical(self, "Error de Órdenes", f"No se pudieron cargar las órdenes:\n{error_message}")

    def cleanup(self):
        """Detiene el worker de órdenes y limpia los recursos."""
        logger.info("OrdersView: Iniciando limpieza de tareas.")
        if self.worker_thread and self.worker_thread.isRunning():
            logger.info("OrdersView: Solicitando detención del worker de órdenes.")
            self.worker_thread.quit()
            if not self.worker_thread.wait(5000): # Esperar hasta 5 segundos
                logger.warning("OrdersView: El hilo del worker de órdenes no terminó correctamente.")
        logger.info("OrdersView: Limpieza completada.")
