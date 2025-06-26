import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ultibot_ui.models import BaseMainWindow
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.services.ui_strategy_service import UIStrategyService

logger = logging.getLogger(__name__)

class StrategiesView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, main_event_loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trading Strategies")
        self.api_client = api_client
        self.main_event_loop = main_event_loop
        self.strategy_service = UIStrategyService(api_client)
        self.main_window: Optional[BaseMainWindow] = None

        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Configured Trading Strategies")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self.strategies_table_widget = QTableWidget()
        self._layout.addWidget(self.strategies_table_widget)
        
        self.setLayout(self._layout)
        
        self._setup_table()
        # self.load_strategies() # Se llamará desde MainWindow después de la inicialización

    def _setup_table(self):
        """Sets up the table columns and headers."""
        self.strategies_table_widget.setColumnCount(5)
        self.strategies_table_widget.setHorizontalHeaderLabels(["Nombre", "Estado", "P&L Total", "Nº de Operaciones", "Acciones"])
        header = self.strategies_table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

    def update_strategies(self, strategies: List[Dict[str, Any]]):
        """
        Populates the table widget with strategy information.
        """
        self.strategies_table_widget.setRowCount(0) # Clear table
        if not strategies:
            # Optionally, display a message when there are no strategies
            return

        self.strategies_table_widget.setRowCount(len(strategies))
        for row, strategy in enumerate(strategies):
            name = strategy.get('name', 'Unnamed Strategy')
            is_active_paper = strategy.get('is_active_paper_mode', False)
            is_active_real = strategy.get('is_active_real_mode', False)
            total_pnl = strategy.get('total_pnl', Decimal('0.0'))
            num_trades = strategy.get('number_of_trades', 0)

            # Nombre
            self.strategies_table_widget.setItem(row, 0, QTableWidgetItem(name))
            
            # Estado
            status_text = []
            if is_active_paper:
                status_text.append("Papel: Activa")
            else:
                status_text.append("Papel: Inactiva")
            if is_active_real:
                status_text.append("Real: Activa")
            else:
                status_text.append("Real: Inactiva")
            self.strategies_table_widget.setItem(row, 1, QTableWidgetItem(", ".join(status_text)))
            
            # P&L Total (formateado a 2 decimales)
            self.strategies_table_widget.setItem(row, 2, QTableWidgetItem(f"{total_pnl:.2f}"))
            
            # Nº de Operaciones
            self.strategies_table_widget.setItem(row, 3, QTableWidgetItem(str(num_trades)))

            self._add_action_buttons(row, strategy)
        
        logger.info(f"Strategies view updated with {len(strategies)} strategies.")
        self.strategies_table_widget.resizeColumnsToContents()

    def _add_action_buttons(self, row: int, strategy: Dict[str, Any]):
        """Adds action buttons to a specific row in the table."""
        buttons_widget = QWidget()
        layout = QHBoxLayout(buttons_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # TODO: Determinar el modo de trading desde la UI
        is_active = strategy.get('is_active_paper_mode', False)
        toggle_button = QPushButton("Desactivar" if is_active else "Activar")
        details_button = QPushButton("Detalles")

        toggle_button.clicked.connect(lambda _, s=strategy, b=toggle_button: self.on_toggle_strategy(s, b))
        details_button.clicked.connect(lambda _, s=strategy: self.on_show_details(s))

        layout.addWidget(toggle_button)
        layout.addWidget(details_button)
        
        buttons_widget.setLayout(layout)
        self.strategies_table_widget.setCellWidget(row, 4, buttons_widget)

    def on_toggle_strategy(self, strategy: Dict[str, Any], button: QPushButton):
        """Handler para activar/desactivar estrategia."""
        strategy_id = strategy.get('id')
        if not strategy_id:
            QMessageBox.warning(self, "Error", "ID de estrategia no encontrado.")
            return

        is_active = strategy.get('is_active_paper_mode', False)
        new_status = not is_active
        
        button.setEnabled(False)
        button.setText("Actualizando...")

        asyncio.create_task(self._toggle_strategy_async(strategy_id, new_status, button))

    async def _toggle_strategy_async(self, strategy_id: str, new_status: bool, button: QPushButton):
        try:
            if new_status:
                await self.strategy_service.activate_strategy(strategy_id)
                QMessageBox.information(self, "Éxito", f"Estrategia {strategy_id} activada correctamente.")
            else:
                await self.strategy_service.deactivate_strategy(strategy_id)
                QMessageBox.information(self, "Éxito", f"Estrategia {strategy_id} desactivada correctamente.")
            
            self.initialize_view_data()  # Recargar para reflejar el cambio
        except Exception as e:
            logger.error(f"Error al cambiar estado de la estrategia {strategy_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"No se pudo actualizar la estrategia {strategy_id}:\n{e}")
            # Restaurar el estado del botón en caso de error
            button.setEnabled(True)
            is_active = not new_status
            button.setText("Desactivar" if is_active else "Activar")

    def on_show_details(self, strategy: Dict[str, Any]):
        """Handler para mostrar detalles de la estrategia."""
        name = strategy.get('name', 'Sin Nombre')
        strategy_id = strategy.get('id', '-')
        QMessageBox.information(self, "Detalles de Estrategia", f"Nombre: {name}\nID: {strategy_id}\n(Más detalles próximamente)")

    def initialize_view_data(self):
        """Loads strategies data asynchronously."""
        logger.info("StrategiesView: Initializing view data (loading strategies)...")
        asyncio.create_task(self._load_strategies_async())

    async def _load_strategies_async(self):
        try:
            # Usar el servicio de UI para obtener las estrategias
            strategies = await self.strategy_service.fetch_strategies()
            self.update_strategies(strategies)
        except Exception as e:
            logger.error(f"An error occurred while loading strategies: {e}", exc_info=True)
            self.on_worker_error(str(e))

    def on_worker_error(self, error_message: str):
        """Handles errors during data loading."""
        logger.error(f"An error occurred in StrategiesView: {error_message}")
        QMessageBox.critical(self, "Error", f"Failed to load strategies:\n{error_message}")
