"""Módulo de ventana principal de UltiBotInversiones.

Este módulo contiene la implementación de la ventana principal de la aplicación,
proporcionando la interfaz de usuario principal con navegación lateral y vistas
intercambiables para diferentes funcionalidades del bot de trading.
"""

import asyncio
import logging
from typing import Optional, List, Callable, Coroutine
from uuid import UUID

from PySide6 import QtCore, QtGui, QtWidgets

from ultibot_ui.models import BaseMainWindow, UserConfiguration
from ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget
from ultibot_ui.windows.dashboard_view import DashboardView
from ultibot_ui.windows.history_view import HistoryView
from ultibot_ui.windows.settings_view import SettingsView
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.services.ui_strategy_service import UIStrategyService
from ultibot_ui.views.strategies_view import StrategiesView
from ultibot_ui.views.opportunities_view import OpportunitiesView
from ultibot_ui.views.orders_view import OrdersView # Importar OrdersView
from ultibot_ui.views.portfolio_view import PortfolioView
from ultibot_ui.views.trading_terminal_view import TradingTerminalView
from ultibot_ui.widgets.market_data_widget import MarketDataWidget # Importar MarketDataWidget
from ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class MainWindow(QtWidgets.QMainWindow, BaseMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones."""

    def __init__(
        self,
        api_client: UltiBotAPIClient,
        parent: Optional[QtWidgets.QWidget] = None,
    ):
        """Inicializa la ventana principal."""
        super().__init__(parent)
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client # Guardar la instancia de api_client
        self.api_base_url = self.api_client.base_url # Usar la base_url del cliente inyectado
        
        self.active_threads: List[QtCore.QThread] = []

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1280, 720) # Geometría por defecto
        self.setMinimumSize(1024, 600) # Establecer un tamaño mínimo

        # Configurar el dock para el log de depuración ANTES de crear la barra de menú
        self._setup_debug_log_dock()

        self.setMenuBar(self._create_menu_bar())
        self.status_bar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Cargando configuración...") # Mensaje inicial

        self._central_content_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(self._central_content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Las vistas se inicializarán sin user_id, se actualizarán después
        self._setup_central_content(main_layout)
        
        self.setCentralWidget(self._central_content_widget)

        self._log_debug("MainWindow inicializada y visible.")
        self.status_bar.showMessage("Ventana principal desplegada correctamente.")
        self.showEvent = self.post_show_initialization # Conectar el evento showEvent

    def post_show_initialization(self, event: QtGui.QShowEvent):
        """
        Método llamado después de que la ventana principal se muestra.
        Aquí se inicializan los componentes que dependen de que la UI esté lista.
        """
        logger.info("MainWindow: Post-show initialization started.")
        # Desconectar para evitar llamadas múltiples si la ventana se muestra varias veces
        self.showEvent = lambda e: None 

        # Cargar la configuración del usuario si aún no se ha hecho
        if not self.user_id:
            self.fetch_initial_user_configuration_async() # Llamar al método público renombrado

        # Inicializar datos de las vistas que lo necesiten
        self.strategies_view.initialize_view_data()
        self.terminal_view.initialize_view_data()
        self.dashboard_view.initialize_async_components() # Asumiendo que DashboardView tiene un método similar
        # Otras vistas que necesiten inicialización tardía...

        logger.info("MainWindow: Post-show initialization finished.")
        super().showEvent(event) # Llamar al showEvent original

    def set_user_configuration(self, user_id: UUID, user_config: UserConfiguration):
        """Actualiza la ventana principal con la configuración del usuario."""
        self.user_id = user_id
        logger.info(f"User configuration set for ID: {user_id}")
        self.status_bar.showMessage(f"Configuración de usuario cargada: {user_id}", 5000)

        # Actualizar las vistas con el user_id una vez que esté disponible
        self.dashboard_view.set_user_id(user_id)
        self.market_data_widget.load_initial_configuration() # Cargar configuración inicial de MarketDataWidget
        self.opportunities_view.set_user_id(user_id)
        self.portfolio_view.set_user_id(user_id)
        self.history_view.set_user_id(user_id)
        self.orders_view.set_user_id(user_id) # Asegurarse de que OrdersView también reciba user_id
        self.settings_view.set_user_id(str(user_id)) # SettingsView espera string

        # La carga de estrategias ya no se inicia aquí, sino en _post_show_initialization
        # self._fetch_strategies_async() 

    def show_error_message(self, message: str):
        """Muestra un diálogo de error al usuario."""
        self._show_error_message(message) # Reutilizar el método privado existente

    def add_thread(self, thread: QtCore.QThread):
        """Añade un hilo a la lista de hilos activos para su seguimiento."""
        self.active_threads.append(thread)
        thread.finished.connect(lambda: self.remove_thread(thread))

    def remove_thread(self, thread: QtCore.QThread):
        """Elimina un hilo de la lista de hilos activos."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def _create_menu_bar(self) -> QtWidgets.QMenuBar:
        """Crea y devuelve la barra de menú principal."""
        menu_bar = QtWidgets.QMenuBar(self)
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("&Archivo")
        exit_action = QtGui.QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menú Ver
        view_menu = menu_bar.addMenu("&Ver")
        toggle_log_action = self.log_dock_widget.toggleViewAction()
        toggle_log_action.setText("Panel de depuración")
        view_menu.addAction(toggle_log_action)

        # Menú Ayuda
        help_menu = menu_bar.addMenu("&Ayuda")
        about_action = QtGui.QAction("Acerca de", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
        return menu_bar

    def _show_about_dialog(self):
        """Muestra el diálogo 'Acerca de'."""
        QtWidgets.QMessageBox.about(
            self,
            "Acerca de UltiBotInversiones",
            "<b>UltiBotInversiones</b><br>"
            "Versión 1.0<br><br>"
            "Una aplicación de trading algorítmico."
        )

    def _show_error_message(self, message: str):
        """Muestra un diálogo de error al usuario."""
        error_dialog = QtWidgets.QMessageBox(self)
        error_dialog.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        error_dialog.setText("Ocurrió un error")
        error_dialog.setInformativeText(message)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec()

    def _log_debug(self, msg: str):
        """Agrega un mensaje al panel de logs y al logger."""
        self.debug_log_widget.append(f"[{QtCore.QTime.currentTime().toString('HH:mm:ss')}] {msg}")
        logger.info(msg)

    def _setup_debug_log_dock(self):
        """Configura el QDockWidget para el log de depuración."""
        self.log_dock_widget = QtWidgets.QDockWidget("Log de Depuración", self)
        self.log_dock_widget.setAllowedAreas(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
        
        self.debug_log_widget = QtWidgets.QTextEdit()
        self.debug_log_widget.setReadOnly(True)
        self.debug_log_widget.setStyleSheet(
            "background-color: #222; color: #0f0; font-family: Consolas, monospace; font-size: 12px;"
        )
        self.debug_log_widget.append("[INFO] UI inicializada. Esperando eventos...")
        
        self.log_dock_widget.setWidget(self.debug_log_widget)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock_widget)
        self.log_dock_widget.setVisible(False) # Oculto por defecto

    def _setup_central_content(self, main_layout: QtWidgets.QHBoxLayout):
        """Configura el contenido central con navegación y vistas."""
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Pasar la instancia de api_client a las vistas que la necesiten
        # user_id se pasará después con set_user_configuration
        self.dashboard_view = DashboardView(
            api_client=self.api_client,
            main_window=self
        )
        self.stacked_widget.addWidget(self.dashboard_view)

        self.market_data_widget = MarketDataWidget(
            user_id=self.user_id, # user_id se establecerá después
            api_client=self.api_client,
            main_window=self
        )
        self.stacked_widget.addWidget(self.market_data_widget)

        self.opportunities_view = OpportunitiesView(
            api_client=self.api_client,
            main_window=self
        )
        self.stacked_widget.addWidget(self.opportunities_view)

        self.strategies_view = StrategiesView(api_client=self.api_client, parent=self)
        self.stacked_widget.addWidget(self.strategies_view)

        self.portfolio_view = PortfolioView(
            api_client=self.api_client
        )
        self.stacked_widget.addWidget(self.portfolio_view)

        self.history_view = HistoryView(
            api_client=self.api_client,
            main_window=self
        )
        self.stacked_widget.addWidget(self.history_view)

        self.orders_view = OrdersView(
            api_client=self.api_client,
            main_window=self
        )
        self.stacked_widget.addWidget(self.orders_view)

        self.settings_view = SettingsView(api_client=self.api_client)
        self.stacked_widget.addWidget(self.settings_view)

        self.terminal_view = TradingTerminalView(
            api_client=self.api_client,
            main_window=self # Pasar la referencia a main_window
        )
        self.stacked_widget.addWidget(self.terminal_view)
        # La señal thread_created ya no es necesaria, los hilos se añaden directamente en TradingTerminalView

        self.view_map = {
            "dashboard": {"index": 0, "shortcut": "Ctrl+1"},
            "opportunities": {"index": 1, "shortcut": "Ctrl+2"},
            "strategies": {"index": 2, "shortcut": "Ctrl+3"},
            "portfolio": {"index": 3, "shortcut": "Ctrl+4"},
            "history": {"index": 4, "shortcut": "Ctrl+5"},
            "settings": {"index": 5, "shortcut": "Ctrl+6"},
            "terminal": {"index": 6, "shortcut": "Ctrl+7"},
        }
        self._setup_shortcuts()

        # Setup strategy service
        self.strategy_service = UIStrategyService(api_client=self.api_client)
        self.strategy_service = UIStrategyService(api_client=self.api_client) # Mover inicialización aquí
        self.strategy_service.strategies_updated.connect(self.strategies_view.update_strategies)
        self.strategy_service.error_occurred.connect(self._handle_service_error)
        
        self._log_debug("Central widget y vistas configuradas.")

    def fetch_initial_user_configuration_async(self):
        """
        Obtiene la configuración inicial del usuario de forma asíncrona.
        Este método se llama si la configuración no se cargó antes.
        """
        logger.info("Fetching initial user configuration asynchronously (from MainWindow)...")
        def coroutine_factory(api_client: UltiBotAPIClient):
            return api_client.get_user_configuration()

        worker = ApiWorker(api_client=self.api_client, coroutine_factory=coroutine_factory)
        thread = QtCore.QThread()
        thread.setObjectName("InitialConfigWorkerThread")
        worker.moveToThread(thread)

        worker.result_ready.connect(lambda config_dict: self._on_initial_config_ready(config_dict))
        worker.error_occurred.connect(lambda msg: self._on_initial_config_error(msg))
        
        thread.started.connect(worker.run)
        
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        
        self.add_thread(thread)
        thread.start()

    @QtCore.Slot(object)
    def _on_initial_config_ready(self, config_dict: dict):
        """Maneja la configuración inicial del usuario una vez que está lista."""
        try:
            user_config = UserConfiguration.model_validate(config_dict)
            user_id = UUID(user_config.user_id)
            logger.info(f"Configuration received and validated for user ID: {user_id}. Updating UI.")
            self.set_user_configuration(user_id, user_config)
        except Exception as e:
            logger.critical(f"Error validating initial configuration: {e}", exc_info=True)
            self.show_error_message(f"Error al validar configuración inicial: {e}")

    @QtCore.Slot(str)
    def _on_initial_config_error(self, error_message: str):
        """Maneja errores al obtener la configuración inicial del usuario."""
        logger.critical(f"Failed to fetch initial configuration: {error_message}. Application may not function correctly.")
        self.show_error_message(f"Error al cargar configuración inicial: {error_message}")

    def _setup_shortcuts(self):
        """Configura los atajos de teclado para la navegación."""
        for view_name, view_info in self.view_map.items():
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(view_info["shortcut"]), self)
            shortcut.activated.connect(lambda name=view_name: self.sidebar.select_view(name))

    def _handle_service_error(self, message: str):
        """Maneja errores provenientes de los servicios de la UI."""
        self._log_debug(f"[SERVICE_ERROR] {message}")
        self.status_bar.showMessage(f"Error: {message}", 10000)
        self._show_error_message(
            f"No se pudo completar la operación: {message}\n\n"
            "Por favor, revise su conexión de red y el log de depuración para más detalles."
        )

    def _switch_view(self, view_name: str):
        """Cambia a la vista especificada."""
        view_info = self.view_map.get(view_name)
        if view_info is not None:
            self.stacked_widget.setCurrentIndex(view_info["index"])
            self._log_debug(f"Cambiando a la vista: {view_name}")
            # Las vistas ahora se inicializan en _post_show_initialization o cuando se establece la configuración del usuario.
            # No es necesario llamar a _fetch_strategies_async aquí.

    def cleanup(self):
        """Limpia los recursos de la ventana, asegurando el orden correcto de detención."""
        self._log_debug(f"Cleaning up MainWindow resources. Stopping {len(self.active_threads)} active threads...")

        for view_widget in [self.dashboard_view, self.opportunities_view, self.strategies_view, self.portfolio_view, self.history_view, self.settings_view, self.terminal_view]:
            if hasattr(view_widget, "cleanup"):
                try:
                    view_widget.cleanup()
                except Exception as e:
                    logger.error(f"Error during cleanup of {view_widget.__class__.__name__}: {e}", exc_info=True)

        for thread in self.active_threads[:]: 
            if thread.isRunning():
                logger.info(f"MainWindow: Quitting and waiting for thread {thread.objectName() or 'unnamed'}...")
                thread.quit()
                if not thread.wait(5000):
                    logger.warning(f"MainWindow: Thread {thread.objectName() or 'unnamed'} did not terminate gracefully.")
            try:
                thread.finished.disconnect()
            except TypeError:
                pass
            thread.deleteLater()
        
        self.active_threads.clear()
        self._log_debug("MainWindow cleanup finished.")

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana."""
        self.cleanup()
        super().closeEvent(event)
