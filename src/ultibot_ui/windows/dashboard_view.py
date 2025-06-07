import logging
from typing import Optional, List, Dict, Any, Callable, Coroutine
from uuid import UUID
import asyncio

from PyQt5.QtCore import pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from src.shared.data_types import Trade
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.notification_widget import NotificationWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class DashboardView(QWidget):
    """
    Vista principal del dashboard que integra varios widgets para mostrar
    información clave de trading.
    """
    initialization_complete = pyqtSignal(bool)

    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, qasync_loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.qasync_loop = qasync_loop
        self.active_workers: Dict[str, QThread] = {}
        self._is_initialized = False
        self._pending_tasks = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        self._setup_ui()
        self._initialize_async_components()

    def _setup_ui(self):
        """Configura la interfaz de usuario básica del dashboard."""
        backend_url = self.api_client.base_url
        
        self.portfolio_widget = PortfolioWidget(self.user_id, backend_url, self)
        self.chart_widget = ChartWidget(backend_url, self)
        
        if self.qasync_loop:
            self.notification_widget = NotificationWidget(self.api_client, self.user_id, self.qasync_loop, self)
        else:
            self.notification_widget = QLabel("Error: Notification widget could not be loaded.")
            logger.error("DashboardView: qasync_loop no está disponible para NotificationWidget.")

        self.main_layout.addWidget(self.portfolio_widget)
        self.main_layout.addWidget(self.chart_widget)
        self.main_layout.addWidget(self.notification_widget)

    def _start_api_worker(
        self,
        coroutine_factory: Callable[[UltiBotAPIClient], Coroutine],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
        worker_id: str,
    ):
        """Inicia un ApiWorker en un hilo separado para ejecutar una corutina."""
        if worker_id in self.active_workers and self.active_workers[worker_id].isRunning():
            logger.warning(f"Worker con ID '{worker_id}' ya está en ejecución. Se omite la nueva solicitud.")
            return

        worker = ApiWorker(
            base_url=self.api_client.base_url,
            coroutine_factory=coroutine_factory
        )
        thread = QThread()
        self.active_workers[worker_id] = thread

        worker.moveToThread(thread)
        
        worker.result_ready.connect(on_success)
        worker.error_occurred.connect(lambda e: on_error(Exception(e)))

        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        thread.started.connect(worker.run)
        thread.start()

    def _initialize_async_components(self):
        """Inicia la carga de datos asíncrona para los componentes del dashboard."""
        logger.info("DashboardView: _initialize_async_components INVOCADO")
        self._pending_tasks = 1

        self._start_api_worker(
            coroutine_factory=lambda api: api.get_trades(trading_mode="both"),
            on_success=self._on_performance_loaded,
            on_error=self._on_load_error("desempeño de estrategias"),
            worker_id="load_performance",
        )

    def _check_initialization_complete(self):
        """Verifica si todas las tareas de inicialización han finalizado."""
        self._pending_tasks -= 1
        if self._pending_tasks <= 0 and not self._is_initialized:
            self._is_initialized = True
            self.initialization_complete.emit(True)
            logger.info("DashboardView: Inicialización de componentes asíncronos completada.")

    def _on_performance_loaded(self, trades: List[Trade]):
        """Maneja la carga exitosa de datos de desempeño."""
        logger.info(f"DashboardView: {len(trades)} trades cargados para el análisis de desempeño.")
        self._check_initialization_complete()

    def _on_load_error(self, component_name: str) -> Callable[[Exception], None]:
        """Crea un manejador de errores para un componente específico."""
        def handler(error: Exception):
            logger.error(f"DashboardView: Error al cargar {component_name}: {error}", exc_info=True)
            self._check_initialization_complete()
        return handler

    def cleanup(self):
        """Detiene todos los hilos y tareas activas."""
        logger.info("DashboardView: Iniciando limpieza de tareas.")
        
        if isinstance(self.portfolio_widget, PortfolioWidget): self.portfolio_widget.cleanup()
        if isinstance(self.chart_widget, ChartWidget): self.chart_widget.cleanup()
        if isinstance(self.notification_widget, NotificationWidget): self.notification_widget.cleanup()

        for worker_id, thread in self.active_workers.items():
            if thread.isRunning():
                logger.info(f"DashboardView: Deteniendo worker {worker_id}")
                thread.quit()
                if not thread.wait(2000):
                    logger.warning(f"DashboardView: El hilo para {worker_id} no terminó a tiempo. Forzando terminación.")
                    thread.terminate()
                    thread.wait()
        self.active_workers.clear()
        logger.info("DashboardView: Limpieza completada.")
