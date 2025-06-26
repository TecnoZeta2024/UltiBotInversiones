import logging
from typing import Optional, List, Dict, Any, Callable, Coroutine
from uuid import UUID
import asyncio

from PySide6.QtCore import Signal as pyqtSignal
from PySide6 import QtWidgets # Importar QtWidgets completo
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from shared.data_types import Trade
from ultibot_ui.models import BaseMainWindow
from ultibot_ui.services.api_client import UltiBotAPIClient
from ultibot_ui.widgets.chart_widget import ChartWidget
from ultibot_ui.widgets.notification_widget import NotificationWidget
from ultibot_ui.widgets.portfolio_widget import PortfolioWidget

logger = logging.getLogger(__name__)

class DashboardView(QWidget):
    """
    Vista principal del dashboard que integra varios widgets para mostrar
    información clave de trading.
    """
    initialization_complete = pyqtSignal(bool)

    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client # Usar la instancia de api_client
        self.main_window = main_window
        self.main_event_loop = main_event_loop # Guardar la referencia al bucle de eventos
        self._is_initialized = False
        self._pending_tasks = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20) # Aumentar márgenes para que las tarjetas respiren
        self.main_layout.setSpacing(20) # Aumentar espaciado entre tarjetas
        self.setLayout(self.main_layout)

        self._setup_ui()
        # No llamar a _initialize_async_components aquí, se llamará después de set_user_id

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y actualiza los widgets dependientes."""
        self.user_id = user_id
        logger.info(f"DashboardView: User ID set to {user_id}. Initializing async components.")
        
        # Actualizar widgets que dependen del user_id
        self.portfolio_widget.set_user_id(user_id)
        self.notification_widget.set_user_id(user_id)

        # La inicialización asíncrona ahora se llama desde MainWindow._post_show_initialization
        # self._initialize_async_components()

    def _setup_ui(self):
        """Configura la interfaz de usuario básica del dashboard usando tarjetas."""
        # Crear widgets sin user_id inicial, se establecerá después
        self.portfolio_widget = PortfolioWidget(self.api_client, self.main_window, self.main_event_loop, self) # Pasar api_client y main_event_loop
        self.chart_widget = ChartWidget(self.api_client, self.main_window, self.main_event_loop, self) # Pasar api_client y main_event_loop
        self.notification_widget = NotificationWidget(self.api_client, self.main_window, self.main_event_loop, self) # Pasar api_client, main_window y main_event_loop

        # Crear tarjeta para el Portfolio
        portfolio_card = QFrame()
        portfolio_card.setProperty("class", "card")
        portfolio_layout = QVBoxLayout(portfolio_card)
        portfolio_layout.addWidget(self.portfolio_widget)
        self.main_layout.addWidget(portfolio_card)

        # Crear tarjeta para el Gráfico
        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(self.chart_widget)
        self.main_layout.addWidget(chart_card)

        # Crear tarjeta para las Notificaciones
        notification_card = QFrame()
        notification_card.setProperty("class", "card")
        notification_layout = QVBoxLayout(notification_card)
        notification_layout.addWidget(self.notification_widget)
        self.main_layout.addWidget(notification_card)

    async def initialize_async_components(self):
        """Inicia la carga de datos asíncrona para los componentes del dashboard."""
        logger.info("DashboardView: initialize_async_components INVOCADO")
        await self._initialize_async()

    async def _initialize_async(self):
        """Corutina que carga los datos iniciales."""
        self._pending_tasks = 1
        try:
            trades_data = await self.api_client.get_trades(trading_mode="both")
            trades = [Trade.model_validate(t) for t in trades_data]
            await self._on_performance_loaded(trades)
        except Exception as e:
            await self._on_load_error("desempeño de estrategias")(e)

    async def _check_initialization_complete(self):
        """Verifica si todas las tareas de inicialización han finalizado."""
        self._pending_tasks -= 1
        if self._pending_tasks <= 0 and not self._is_initialized:
            self._is_initialized = True
            self.initialization_complete.emit(True)
            logger.info("DashboardView: Inicialización de componentes asíncronos completada.")
            
            # Iniciar actualizaciones de widgets clave después de la inicialización
            self.portfolio_widget.start_updates()
            await self.chart_widget.start_updates()
            self.notification_widget.start_updates()

    async def _on_performance_loaded(self, trades: List[Trade]):
        """Maneja la carga exitosa de datos de desempeño."""
        logger.info(f"DashboardView: {len(trades)} trades cargados para el análisis de desempeño.")
        await self._check_initialization_complete()

    def _on_load_error(self, component_name: str) -> Callable[[Exception], Coroutine[Any, Any, None]]:
        """Crea un manejador de errores para un componente específico."""
        async def handler(error: Exception):
            logger.error(f"DashboardView: Error al cargar {component_name}: {error}", exc_info=True)
            await self._check_initialization_complete()
        return handler

    def cleanup(self):
        """Detiene todos los hilos y tareas activas."""
        logger.info("DashboardView: Iniciando limpieza de tareas.")
        
        if hasattr(self.portfolio_widget, 'cleanup'): self.portfolio_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup'): self.chart_widget.cleanup()
        if hasattr(self.notification_widget, 'cleanup'): self.notification_widget.cleanup()

        logger.info("DashboardView: Limpieza completada.")
