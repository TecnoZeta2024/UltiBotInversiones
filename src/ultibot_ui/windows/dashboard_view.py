import logging
from typing import Optional, List, Dict, Any, Callable, Coroutine
from uuid import UUID
import asyncio

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from src.shared.data_types import Trade
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.notification_widget import NotificationWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget

logger = logging.getLogger(__name__)

class DashboardView(QWidget):
    """
    Vista principal del dashboard que integra varios widgets para mostrar
    información clave de trading.
    """
    initialization_complete = pyqtSignal(bool)

    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        self._is_initialized = False
        self._pending_tasks = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.setLayout(self.main_layout)

        self._setup_ui()
        self._initialize_async_components()

    def _setup_ui(self):
        """Configura la interfaz de usuario básica del dashboard usando tarjetas."""
        self.portfolio_widget = PortfolioWidget(self.user_id, self.main_window, self.api_client, self.loop, self)
        self.chart_widget = ChartWidget(self.main_window, self.api_client, self.loop, self)
        self.notification_widget = NotificationWidget(self.user_id, self.main_window, self.api_client, self.loop, self)

        portfolio_card = QFrame()
        portfolio_card.setProperty("class", "card")
        portfolio_layout = QVBoxLayout(portfolio_card)
        portfolio_layout.addWidget(self.portfolio_widget)
        self.main_layout.addWidget(portfolio_card, 1) # Añadir stretch factor

        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(self.chart_widget)
        self.main_layout.addWidget(chart_card, 1) # Añadir stretch factor

        notification_card = QFrame()
        notification_card.setProperty("class", "card")
        notification_layout = QVBoxLayout(notification_card)
        notification_layout.addWidget(self.notification_widget)
        self.main_layout.addWidget(notification_card, 1) # Añadir stretch factor

    def _initialize_async_components(self):
        """Inicia la carga de datos asíncrona para los componentes del dashboard."""
        logger.info("DashboardView: _initialize_async_components INVOCADO")
        self._pending_tasks = 1

        coroutine_factory = lambda client: client.get_trades(trading_mode="both")
        
        self.main_window.submit_task(
            coroutine_factory,
            self._on_performance_loaded,
            self._on_load_error("desempeño de estrategias")
        )

    def _check_initialization_complete(self):
        """Verifica si todas las tareas de inicialización han finalizado."""
        self._pending_tasks -= 1
        if self._pending_tasks <= 0 and not self._is_initialized:
            self._is_initialized = True
            self.initialization_complete.emit(True)
            logger.info("DashboardView: Inicialización de componentes asíncronos completada.")
            
            self.portfolio_widget.refresh_data()
            # self.chart_widget.enter_view() # No existe, se carga al iniciar
            # self.notification_widget.enter_view() # No existe

    def _on_performance_loaded(self, trades: List[Trade]):
        """Maneja la carga exitosa de datos de desempeño."""
        logger.info(f"DashboardView: {len(trades)} trades cargados para el análisis de desempeño.")
        self._check_initialization_complete()

    def _on_load_error(self, component_name: str) -> Callable[[str], None]:
        """Crea un manejador de errores para un componente específico."""
        def handler(error_msg: str):
            logger.error(f"DashboardView: Error al cargar {component_name}: {error_msg}", exc_info=True)
            self._check_initialization_complete()
        return handler

    def cleanup(self):
        """Detiene todos los hilos y tareas activas."""
        logger.info("DashboardView: Iniciando limpieza de tareas.")
        
        if hasattr(self.portfolio_widget, 'cleanup'): self.portfolio_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup'): self.chart_widget.cleanup()
        if hasattr(self.notification_widget, 'cleanup'): self.notification_widget.cleanup()

        logger.info("DashboardView: Limpieza completada.")
