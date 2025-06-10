"""Módulo de ventana principal de UltiBotInversiones.

Este módulo contiene la implementación de la ventana principal de la aplicación,
proporcionando la interfaz de usuario principal con navegación lateral y vistas
intercambiables para diferentes funcionalidades del bot de trading.
"""

import asyncio
import logging
from typing import Optional, Callable, Coroutine
from uuid import UUID

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QAction,
    QTextEdit,
    QVBoxLayout,
    QMenuBar,
    QWidget
)

from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget
from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.history_view import HistoryView
from src.ultibot_ui.windows.settings_view import SettingsView
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.services.ui_strategy_service import UIStrategyService
from src.ultibot_ui.views.strategies_view import StrategiesView
from src.ultibot_ui.views.opportunities_view import OpportunitiesView
from src.ultibot_ui.views.portfolio_view import PortfolioView
from src.ultibot_ui.workers import ApiWorker
from src.ultibot_ui.services.trading_mode_state import TradingModeStateManager, TradingMode

logger = logging.getLogger(__name__)

class RunnableApiWorker(QRunnable):
    """
    Wrapper QRunnable para un ApiWorker para ser usado con QThreadPool.
    Conecta las señales del worker a los callbacks apropiados.
    """
    def __init__(self, worker: ApiWorker, on_success: Callable, on_error: Callable):
        super().__init__()
        self.worker = worker
        # Conectar señales a los callbacks proporcionados
        self.worker.result_ready.connect(on_success)
        self.worker.error_occurred.connect(on_error)

    @pyqtSlot()
    def run(self):
        """Ejecuta el método run del ApiWorker."""
        self.worker.run()


class TaskManager(QObject):
    """
    Gestiona un QThreadPool para ejecutar tareas ApiWorker de forma asíncrona y centralizada.
    """
    def __init__(self, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.loop = loop
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(10) # Límite razonable de hilos
        logger.info(f"TaskManager inicializado con un máximo de {self.thread_pool.maxThreadCount()} hilos.")

    def submit(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success: Callable, on_error: Callable):
        """
        Crea un ApiWorker, lo envuelve en un QRunnable y lo envía al pool de hilos.
        """
        api_worker_instance = ApiWorker(
            api_client=self.api_client,
            coroutine_factory=coroutine_factory,
            loop=self.loop
        )
        runnable_worker = RunnableApiWorker(
            worker=api_worker_instance,
            on_success=on_success,
            on_error=on_error
        )
        self.thread_pool.start(runnable_worker)
        logger.debug("Tarea ApiWorker enviada al pool de hilos.")

    def cleanup(self):
        """Limpia el pool de hilos, esperando a que las tareas terminen."""
        logger.info("Cerrando el pool de hilos del TaskManager...")
        self.thread_pool.waitForDone()
        logger.info("El pool de hilos del TaskManager ha sido cerrado.")


class MainWindow(QMainWindow, BaseMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones."""

    def __init__(
        self,
        user_id: UUID,
        api_client: UltiBotAPIClient,
        trading_mode_manager: TradingModeStateManager,
        loop: asyncio.AbstractEventLoop,
        parent: Optional[QWidget] = None,
    ):
        """Inicializa la ventana principal."""
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.loop = loop
        
        self.task_manager = TaskManager(api_client=self.api_client, loop=self.loop, parent=self)
        self.trading_mode_manager = trading_mode_manager

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1024, 600)

        self.setMenuBar(self._create_menu_bar())
        self._setup_status_bar()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        self._setup_central_widget(main_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.trading_mode_manager.trading_mode_changed.connect(self.update_trading_mode_indicator)
        self._sync_initial_trading_mode()

        logger.info("MainWindow inicializada y visible.")

    def _setup_status_bar(self):
        """Configura la barra de estado, incluyendo el indicador de modo de trading."""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        
        self.trading_mode_label = QLabel("Syncing mode...")
        self.trading_mode_label.setStyleSheet("padding: 2px 5px; border-radius: 3px;")
        status_bar.addPermanentWidget(self.trading_mode_label)
        
        status_bar.showMessage("Listo")

    def _sync_initial_trading_mode(self):
        """Inicia la sincronización del modo de trading con el backend."""
        self.submit_task(
            lambda client: self.trading_mode_manager.sync_with_backend(),
            on_success=lambda: logger.info("Initial trading mode synced successfully."),
            on_error=lambda err: logger.error(f"Failed to sync initial trading mode: {err}")
        )

    @pyqtSlot(str)
    def update_trading_mode_indicator(self, mode_str: str):
        """Actualiza el indicador visual del modo de trading en la barra de estado."""
        try:
            mode = TradingMode(mode_str)
            self.trading_mode_label.setText(f"MODE: {mode.display_name}")
            self.trading_mode_label.setStyleSheet(
                f"background-color: {mode.color}; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold;"
            )
            logger.info(f"Trading mode indicator updated to {mode.value}")
        except ValueError:
            logger.error(f"Invalid mode string received: {mode_str}")
            self.trading_mode_label.setText("Mode: Unknown")
            self.trading_mode_label.setStyleSheet("background-color: #777; color: white;")

    def submit_task(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success: Callable, on_error: Callable):
        """
        Delega la ejecución de una factoría de corutinas al gestor de tareas central.
        """
        self.task_manager.submit(coroutine_factory, on_success, on_error)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        return self.loop

    def _create_menu_bar(self) -> QMenuBar:
        """Crea y devuelve la barra de menú principal."""
        menu_bar = QMenuBar(self)
        # ... (código del menú sin cambios)
        return menu_bar

    def _log_debug(self, msg: str):
        """Agrega un mensaje al logger."""
        logger.info(msg)

    def _setup_central_widget(self, main_layout: QHBoxLayout):
        """Configura el widget central con navegación y vistas."""
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)

        # Inicialización de vistas
        self.dashboard_view = DashboardView(self.user_id, self, self.api_client, self.trading_mode_manager, self.loop)
        self.stacked_widget.addWidget(self.dashboard_view)

        self.opportunities_view = OpportunitiesView(self.user_id, self, self.api_client, self.loop)
        self.stacked_widget.addWidget(self.opportunities_view)

        self.strategies_view = StrategiesView(self.user_id, self, self.api_client, self.trading_mode_manager, self.loop)
        self.stacked_widget.addWidget(self.strategies_view)

        self.portfolio_view = PortfolioView(self.user_id, self.api_client, self.trading_mode_manager, self.loop, self)
        self.stacked_widget.addWidget(self.portfolio_view)

        self.history_view = HistoryView(self.user_id, self, self.api_client, self.loop)
        self.stacked_widget.addWidget(self.history_view)

        self.settings_view = SettingsView(str(self.user_id), self.api_client, self.loop, self)
        self.stacked_widget.addWidget(self.settings_view)

        self.view_map = {
            "dashboard": 0, "opportunities": 1, "strategies": 2,
            "portfolio": 3, "history": 4, "settings": 5,
        }

        self.strategy_service = UIStrategyService(self.api_client, self, self.loop)
        self.strategy_service.strategies_updated.connect(self.strategies_view.update_strategies_list)
        self.strategy_service.error_occurred.connect(lambda msg: self._log_debug(f"[STRATEGY_SVC_ERR] {msg}"))
        
        self._fetch_strategies()

        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button:
            dashboard_button.setChecked(True)
        self.stacked_widget.setCurrentIndex(self.view_map["dashboard"])
        self._log_debug("Central widget y vistas configuradas.")

    def _fetch_strategies(self):
        """Inicia la obtención de estrategias."""
        self.strategy_service.fetch_strategies()
        self._log_debug("MainWindow: Iniciada la obtención de estrategias.")

    def _switch_view(self, view_name: str):
        """Cambia a la vista especificada."""
        index = self.view_map.get(view_name)
        if index is not None:
            current_widget = self.stacked_widget.widget(self.stacked_widget.currentIndex())
            if hasattr(current_widget, 'leave_view'):
                current_widget.leave_view()

            self.stacked_widget.setCurrentIndex(index)
            view_widget = self.stacked_widget.widget(index)
            if hasattr(view_widget, 'enter_view'):
                view_widget.enter_view()

    def cleanup(self):
        """Limpia los recursos de la ventana."""
        self._log_debug("Limpiando recursos de MainWindow...")
        for i in range(self.stacked_widget.count()):
            view_widget = self.stacked_widget.widget(i)
            if hasattr(view_widget, "cleanup"):
                view_widget.cleanup()
        self.task_manager.cleanup()
        self._log_debug("Limpieza de MainWindow finalizada.")

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.cleanup()
        super().closeEvent(event)
