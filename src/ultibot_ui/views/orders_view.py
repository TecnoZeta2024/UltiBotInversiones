import logging
import asyncio
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTableWidget, 
                               QHeaderView, QTableWidgetItem, QLineEdit, 
                               QComboBox, QHBoxLayout, QMessageBox)
from typing import Optional, List, Dict, Any # Importar List, Dict, Any
from uuid import UUID

from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)


class OrdersView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, main_event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Órdenes")
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client
        self.main_window = main_window # Guardar referencia a MainWindow
        self.main_event_loop = main_event_loop
        self.all_orders = []
        self.load_orders_task: Optional[asyncio.Task] = None
        
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
        """Establece el user_id y actualiza los widgets dependientes."""
        self.user_id = user_id
        logger.info(f"OrdersView: User ID set to {user_id}.")
        # La carga inicial de datos ahora se maneja en initialize_view_data,
        # que es llamado por MainWindow.

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

    async def initialize_view_data(self):
        """Carga las órdenes de forma asíncrona."""
        if self.user_id is None:
            logger.warning("Cannot load orders, user_id is not set.")
            return
        
        if self.load_orders_task and not self.load_orders_task.done():
            logger.info("Order loading task is already running.")
            return

        logger.info("Creating asyncio task to fetch orders.")
        
        self.load_orders_task = self.main_event_loop.create_task(self._load_orders_async())

    async def _load_orders_async(self):
        """Carga las órdenes desde la API y actualiza la tabla."""
        if not self.user_id:
            logger.error("Cannot load orders: user_id is not set.")
            return
        
        try:
            # Obtener órdenes cerradas de paper trading.
            # Asumimos que el user_id se maneja a través de la autenticación en el backend.
            orders = await self.api_client.get_trades(trading_mode='paper', status='closed', limit=500)
            self.update_orders_table(orders)
        except Exception as e:
            logger.error(f"Failed to load orders: {e}", exc_info=True)
            self._on_error(f"No se pudieron cargar las órdenes: {e}")

    @Slot(list)
    def update_orders_table(self, orders: List[Dict[str, Any]]):
        """Puebla la tabla con los datos de las órdenes."""
        logger.info(f"Actualizando tabla de órdenes con {len(orders)} órdenes.")
        self.all_orders = orders  # Guardar la lista completa
        self.orders_table.setSortingEnabled(False)
        self.orders_table.setRowCount(0)

        for row, order in enumerate(self.all_orders):
            self.orders_table.insertRow(row)
            # Asegurarse de que las claves existen y los tipos son correctos
            self.orders_table.setItem(row, 0, QTableWidgetItem(order.get('closed_at', '') or '')) # Usar closed_at para fecha
            self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('symbol', '') or ''))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('trade_type', '') or '')) # Usar trade_type
            self.orders_table.setItem(row, 3, QTableWidgetItem(order.get('side', '') or ''))
            self.orders_table.setItem(row, 4, QTableWidgetItem(str(order.get('executed_price', 0.0) or 0.0))) # Usar executed_price
            self.orders_table.setItem(row, 5, QTableWidgetItem(str(order.get('executed_quantity', 0.0) or 0.0))) # Usar executed_quantity
            self.orders_table.setItem(row, 6, QTableWidgetItem(order.get('status', '') or ''))
        
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
        """Cancela la tarea de carga de órdenes si se está ejecutando."""
        logger.info("OrdersView: Cleaning up tasks.")
        if self.load_orders_task and not self.load_orders_task.done():
            self.load_orders_task.cancel()
            logger.info("Order loading task cancelled.")
        logger.info("OrdersView: Cleanup complete.")
