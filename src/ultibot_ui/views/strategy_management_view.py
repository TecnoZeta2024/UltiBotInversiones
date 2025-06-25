from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
from PySide6.QtCore import QEventLoop, QTimer, QThread # Importar QThread
import asyncio
import logging
from typing import Optional, List

from ultibot_ui.services.ui_strategy_service import UIStrategyService
from ultibot_ui.workers import ApiWorker # Importar ApiWorker
from ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow para type hinting

logger = logging.getLogger(__name__)

class StrategyManagementView(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.strategy_service = UIStrategyService(api_client)
        self.active_threads: List[QThread] = [] # Lista para rastrear hilos
        self.main_window: Optional[BaseMainWindow] = None # Referencia a MainWindow
        self.init_ui()
        self.strategy_service.strategies_updated.connect(self.display_strategies)
        self.strategy_service.error_occurred.connect(self.display_error)

    def set_main_window(self, main_window: BaseMainWindow):
        """Establece la referencia a la ventana principal."""
        self.main_window = main_window

    def init_ui(self):
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)

        title_label = QLabel("Strategy Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._layout.addWidget(title_label)

        self.strategy_list_widget = QListWidget()
        self._layout.addWidget(self.strategy_list_widget)

        self.status_label = QLabel("")
        self._layout.addWidget(self.status_label)

    def load_strategies(self):
        # Usar ApiWorker para ejecutar la corutina de forma segura en el bucle de eventos principal
        coro_factory = lambda api_client: self.strategy_service.fetch_strategies(api_client)
        
        worker = ApiWorker(api_client=self.api_client, coroutine_factory=coro_factory)
        thread = QThread()
        thread.setObjectName("StrategyManagementWorkerThread")
        worker.moveToThread(thread)

        worker.result_ready.connect(self.display_strategies)
        worker.error_occurred.connect(self.display_error)
        
        # Conectar la señal finished del worker para que el hilo se cierre
        worker.finished.connect(thread.quit)
        
        # Conectar la señal finished del hilo para limpiar el worker y el hilo
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        # Añadir el hilo a la lista de hilos activos de la vista y de la ventana principal
        self.active_threads.append(thread)
        if self.main_window:
            self.main_window.add_thread(thread)
        
        thread.start()

    def display_strategies(self, strategies):
        self.strategy_list_widget.clear()
        if not strategies:
            self.status_label.setText("No hay estrategias disponibles.")
            return
        for strat in strategies:
            item = QListWidgetItem(f"{strat.get('name', 'Sin Nombre')} (ID: {strat.get('id', '-')})")
            self.strategy_list_widget.addItem(item)
        self.status_label.setText(f"{len(strategies)} estrategias cargadas.")

    def display_error(self, error_msg):
        self.status_label.setText(f"Error al cargar estrategias: {error_msg}")

    def cleanup(self):
        """Detiene todos los hilos activos gestionados por StrategyManagementView."""
        logger.info(f"StrategyManagementView: Cleaning up. Stopping {len(self.active_threads)} active threads...")
        for thread in self.active_threads[:]: # Iterar sobre una copia para permitir la modificación de la lista
            if thread.isRunning():
                logger.info(f"StrategyManagementView: Quitting and waiting for thread {thread.objectName() or 'unnamed'}...")
                thread.quit()
                if not thread.wait(5000): # Esperar hasta 5 segundos
                    logger.warning(f"StrategyManagementView: Thread {thread.objectName() or 'unnamed'} did not terminate gracefully.")
            try:
                thread.finished.disconnect() # Desconectar para evitar errores si ya está desconectado
            except TypeError:
                pass
            thread.deleteLater() # Asegurarse de que el objeto QThread sea eliminado
        self.active_threads.clear()
        logger.info("StrategyManagementView: Cleanup complete.")
