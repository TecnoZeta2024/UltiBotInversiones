import logging
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QPushButton)
from typing import List, Dict, Any, cast, Optional
import asyncio
from decimal import Decimal # Importar Decimal

from ultibot_ui.workers import StrategiesWorker, ApiWorker
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.services.ui_strategy_service import UIStrategyService # Importar UIStrategyService
from PySide6.QtWidgets import QApplication # Importar QApplication
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow para type hinting

logger = logging.getLogger(__name__)

class StrategiesView(QWidget):
    def __init__(self, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trading Strategies")
        self.api_client = api_client
        self.strategy_service = UIStrategyService(api_client) # Inicializar UIStrategyService
        self.thread: Optional[QThread] = None # Declarar self.thread aquí
        self.worker: Optional[StrategiesWorker] = None # Declarar self.worker aquí
        
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

        toggle_button = QPushButton("Activar")
        details_button = QPushButton("Detalles")

        # Conectar botones a funcionalidad real
        toggle_button.clicked.connect(lambda _, s=strategy: self.on_toggle_strategy(s))
        details_button.clicked.connect(lambda _, s=strategy: self.on_show_details(s))

        layout.addWidget(toggle_button)
        layout.addWidget(details_button)
        
        buttons_widget.setLayout(layout)
        self.strategies_table_widget.setCellWidget(row, 4, buttons_widget)

    def on_toggle_strategy(self, strategy: Dict[str, Any]):
        """Handler para activar/desactivar estrategia."""
        strategy_id = strategy.get('id')
        name = strategy.get('name', 'Sin Nombre')
        is_active_paper_mode = strategy.get('isActivePaperMode', False) # Asumir modo papel por ahora

        if not strategy_id:
            QMessageBox.warning(self, "Error", f"No se pudo alternar el estado de la estrategia '{name}': ID no encontrado.")
            return

        # Ejecutar la operación asíncrona en un nuevo task
        # Usar un ApiWorker para ejecutar la corutina de forma segura
        coro_factory = lambda api_client: self.strategy_service.toggle_strategy_status(
            strategy_id, is_active_paper_mode, "paper"
        )
        
        worker = ApiWorker(api_client=self.api_client, coroutine_factory=coro_factory)
        thread = QThread() # Usar QThread para el ApiWorker
        thread.setObjectName(f"ToggleStrategyWorkerThread_{strategy_id}")
        worker.moveToThread(thread)

        worker.result_ready.connect(lambda: self._on_toggle_success(strategy_id, is_active_paper_mode))
        worker.error_occurred.connect(lambda msg: self._on_toggle_error(strategy_id, msg))
        
        thread.started.connect(worker.run)
        
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        
        # Añadir el hilo a la ventana principal para su seguimiento y limpieza
        # Usar cast para ayudar a Pylance a reconocer el tipo de parent
        main_window = cast(BaseMainWindow, self.parent())
        if main_window and hasattr(main_window, 'add_thread'):
            main_window.add_thread(thread)
        
        thread.start()

    def _on_toggle_success(self, strategy_id: str, old_status: bool):
        new_status_text = "activada" if not old_status else "desactivada"
        QMessageBox.information(self, "Éxito", f"Estrategia {strategy_id} {new_status_text} correctamente.")
        self.initialize_view_data() # Recargar la lista para reflejar el cambio

    def _on_toggle_error(self, strategy_id: str, error_message: str):
        QMessageBox.critical(self, "Error", f"Error al alternar estado de estrategia {strategy_id}:\n{error_message}")
        logger.error(f"Error al alternar estado de estrategia {strategy_id}: {error_message}")

    def on_show_details(self, strategy: Dict[str, Any]):
        """Handler para mostrar detalles de la estrategia."""
        name = strategy.get('name', 'Sin Nombre')
        strategy_id = strategy.get('id', '-')
        QMessageBox.information(self, "Detalles de Estrategia", f"Nombre: {name}\nID: {strategy_id}\n(Más detalles próximamente)")

    def initialize_view_data(self):
        """
        Initializes and runs the worker to load strategies data asynchronously
        on a dedicated QThread. This method is called after MainWindow is fully
        initialized and visible.
        """
        logger.info("StrategiesView: Initializing view data (loading strategies)...")
        
        # Obtener el bucle de eventos principal de la aplicación
        app_instance = QApplication.instance()
        if not app_instance:
            logger.error("StrategiesView: No se encontró la instancia de QApplication.")
            QMessageBox.critical(self, "Error de Inicialización", "No se pudo obtener la instancia de la aplicación. La aplicación podría no funcionar correctamente.")
            return
            
        main_event_loop = app_instance.property("main_event_loop")
        if not main_event_loop:
            logger.error("StrategiesView: No se encontró el bucle de eventos principal de qasync como propiedad de la aplicación.")
            QMessageBox.critical(self, "Error de Inicialización", "No se pudo obtener el bucle de eventos principal. La aplicación podría no funcionar correctamente.")
            return

        # Crear el nuevo worker y hilo
        new_worker = StrategiesWorker(self.api_client, main_event_loop)
        new_thread = QThread() # Crear un QThread para el worker
        new_thread.setObjectName("StrategiesWorkerThread")
        new_worker.moveToThread(new_thread) # Mover el worker a su propio hilo

        # Detener el worker y hilo anteriores si existen y están corriendo
        if self.thread and self.thread.isRunning():
            logger.info("StrategiesView: Worker thread already running, stopping it.")
            if self.worker: # Asegurarse de que self.worker no sea None
                self.worker.stop() 
            self.thread.quit()
            self.thread.wait(1000) # Esperar un poco para que el hilo termine
            self.thread = None
            self.worker = None

        # Asignar el nuevo worker y hilo
        self.worker = new_worker
        self.thread = new_thread


        self.worker.strategies_ready.connect(self.update_strategies)
        self.worker.error_occurred.connect(self.on_worker_error)
        
        # Conectar las señales para la gestión del hilo
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Añadir el hilo a la ventana principal para su seguimiento y limpieza
        main_window = cast(BaseMainWindow, self.parent())
        if main_window and hasattr(main_window, 'add_thread'):
            main_window.add_thread(self.thread)
        
        self.thread.start() # Iniciar el hilo

    def on_worker_error(self, error_message: str):
        """Handles errors reported by the worker."""
        logger.error(f"An error occurred in StrategiesWorker: {error_message}")
        QMessageBox.critical(self, "Error", f"Failed to load strategies:\n{error_message}")
