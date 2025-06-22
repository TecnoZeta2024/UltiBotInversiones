import logging
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QPushButton)
from typing import List, Dict, Any

from ultibot_ui.workers import StrategiesWorker
from ultibot_ui.services.api_client import UltiBotAPIClient

logger = logging.getLogger(__name__)

class StrategiesView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trading Strategies")
        self.api_client = api_client # Usar la instancia de api_client
        
        self._layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Configured Trading Strategies")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._layout.addWidget(self.title_label)
        
        self.strategies_table_widget = QTableWidget()
        self._layout.addWidget(self.strategies_table_widget)
        
        self.setLayout(self._layout)
        
        self._setup_table()
        self.load_strategies()

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
            
            # For now, we only populate the name. Other columns will be filled later.
            self.strategies_table_widget.setItem(row, 0, QTableWidgetItem(name))
            # Placeholder for other columns
            self.strategies_table_widget.setItem(row, 1, QTableWidgetItem("N/A"))
            self.strategies_table_widget.setItem(row, 2, QTableWidgetItem("N/A"))
            self.strategies_table_widget.setItem(row, 3, QTableWidgetItem("N/A"))

            self._add_action_buttons(row, strategy)
        
        logger.info(f"Strategies view updated with {len(strategies)} strategies.")
        self.strategies_table_widget.resizeColumnsToContents()

    def _add_action_buttons(self, row: int, strategy: Dict[str, Any]):
        """Adds action buttons to a specific row in the table."""
        buttons_widget = QWidget()
        layout = QHBoxLayout(buttons_widget)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # TODO: Connect these buttons to actual functionality
        toggle_button = QPushButton("Activar")
        details_button = QPushButton("Detalles")

        layout.addWidget(toggle_button)
        layout.addWidget(details_button)
        
        buttons_widget.setLayout(layout)
        self.strategies_table_widget.setCellWidget(row, 4, buttons_widget)

    def load_strategies(self):
        """
        Initializes and runs the worker to load strategies data.
        """
        logger.info("Starting StrategiesWorker...")
        self.worker_thread = QThread()
        # El worker ahora se crea con la instancia de api_client.
        self.worker = StrategiesWorker(self.api_client) # Pasar api_client
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.strategies_ready.connect(self.update_strategies)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        # Clean up thread when worker is done
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.worker_thread.start()

    def on_worker_error(self, error_message: str):
        """Handles errors reported by the worker."""
        logger.error(f"An error occurred in StrategiesWorker: {error_message}")
        QMessageBox.critical(self, "Error", f"Failed to load strategies:\n{error_message}")
