"""Módulo de ventana principal de UltiBotInversiones.

Este módulo contiene la implementación de la ventana principal de la aplicación,
proporcionando la interfaz de usuario principal con navegación lateral y vistas
intercambiables para diferentes funcionalidades del bot de trading.
"""

import asyncio # Añadido para la anotación de tipo AbstractEventLoop
import logging
logger = logging.getLogger(__name__)

from uuid import UUID

from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QWidget,
    QAction, # Added for menu actions
    QTextEdit, # Añadido para panel de logs
    QVBoxLayout # Cambiar QVBox por QVBoxLayout
)

from src.shared.data_types import UserConfiguration # May not be needed directly in MainWindow anymore for config
# Removed direct service imports, will use api_client
# from src.ultibot_backend.services.config_service import ConfigService
# from src.ultibot_backend.services.market_data_service import MarketDataService
# from src.ultibot_backend.services.notification_service import NotificationService
# from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget
from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.history_view import HistoryView
from src.ultibot_ui.windows.settings_view import SettingsView
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.views.strategy_management_view import StrategyManagementView
from src.ultibot_ui.views.opportunities_view import OpportunitiesView
from src.ultibot_ui.views.portfolio_view import PortfolioView


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones.

    Proporciona la interfaz de usuario principal con navegación lateral,
    barra de estado y vistas intercambiables para las diferentes
    funcionalidades del sistema de trading.
    """

    def __init__(
        self,
        user_id: UUID,
        backend_base_url: str, # Changed: Pass backend_base_url
        qasync_loop: asyncio.AbstractEventLoop, # Added qasync_loop
        parent=None,
    ):
        """Inicializa la ventana principal con la URL base del backend y el bucle qasync.

        Args:
            user_id: Identificador único del usuario
            backend_base_url: URL base del backend API.
            qasync_loop: El bucle de eventos qasync del hilo principal.
            parent: Widget padre opcional
        """
        super().__init__(parent)
        self.user_id = user_id
        self.backend_base_url = backend_base_url # Store the backend base URL
        self.qasync_loop = qasync_loop # Store the qasync loop

        # Remove old service instances
        # self.market_data_service = market_data_service
        # self.config_service = config_service
        # self.notification_service = notification_service
        # self.persistence_service = persistence_service

        # Variables para rastrear el estado de inicialización
        self._initialization_complete = False
        self._paper_trading_status_loaded = False # These flags relate to status bar, not theme
        self._real_trading_status_loaded = False
        self.active_threads = []

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1200, 800)

        # Elementos de UI añadidos
        self.debug_log_widget = QTextEdit()
        self.debug_log_widget.setReadOnly(True)
        self.debug_log_widget.setMaximumHeight(120)
        self.debug_log_widget.setStyleSheet("background-color: #222; color: #0f0; font-family: Consolas, monospace; font-size: 12px;")
        self.debug_log_widget.append("[INFO] UI inicializada. Esperando eventos...")

        # Banner visual de bienvenida
        self.banner_label = QLabel("🟢 UltiBotInversiones UI cargada correctamente")
        self.banner_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00FF8C; padding: 8px; background: #1E1E1E; border-radius: 6px;")

        self._create_menu_bar() # Added menu bar setup
        self._create_status_bar()

        # Layout vertical para banner y logs
        self._main_vbox = QVBoxLayout()
        self._main_vbox.setContentsMargins(0, 0, 0, 0)
        self._main_vbox.setSpacing(0)
        self._main_vbox.addWidget(self.banner_label)
        self._main_vbox.addWidget(self.debug_log_widget)

        # Widget central real
        self._central_content_widget = QWidget()
        self._main_vbox.addWidget(self._central_content_widget, 1)
        central_widget = QWidget()
        central_widget.setLayout(self._main_vbox)
        self.setCentralWidget(central_widget)

        # El resto de la UI se monta en _central_content_widget
        self._setup_central_widget(parent_widget=self._central_content_widget)

        # Conectar la señal de cambio de configuración de SettingsView
        self.settings_view.config_changed.connect(
            self._update_paper_trading_status_display
        )
        # Conectar la nueva señal de cambio de estado del modo real
        self.settings_view.real_trading_mode_status_changed.connect(
            self._update_real_trading_status_display
        )

        # Usar QTimer para cargar el estado inicial de forma asíncrona segura
        self._init_timer = QTimer()
        self._init_timer.singleShot(100, self._schedule_initial_load)

        self._log_debug("MainWindow inicializada y visible.")
        self.statusBar.showMessage("Ventana principal desplegada correctamente.")

    def _safe_set_future_result(self, future_instance, result_value):
        """Helper para llamar a future.set_result de forma segura desde un hilo."""
        self.qasync_loop.call_soon_threadsafe(future_instance.set_result, result_value)

    def _safe_set_future_exception(self, future_instance, exception_value):
        """Helper para llamar a future.set_exception de forma segura desde un hilo."""
        self.qasync_loop.call_soon_threadsafe(future_instance.set_exception, exception_value)

    def _schedule_initial_load(self):
        """Programa la carga inicial del estado de Paper Trading y Real Trading.

        Utiliza ApiWorker para ejecutar llamadas API de forma no bloqueante.
        """
        # Remove direct asyncio.create_task usage. Will use ApiWorker.
        logging.info("Programando carga inicial de estados de trading con ApiWorker.")
        # Estas llamadas ahora usarán el patrón con asyncio.Future
        self._load_initial_paper_trading_status()
        self._load_initial_real_trading_status_worker()

    def _check_initialization_complete(self):
        """Comprueba si todas las cargas iniciales se han completado."""
        if self._paper_trading_status_loaded and self._real_trading_status_loaded:
            self._initialization_complete = True
            logging.info("Inicialización completa de los estados de trading.")
            # Emit a signal or call a method if something needs to happen after full init.

    def _create_status_bar(self):
        """Crea y configura la barra de estado de la ventana principal."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Trading Mode Switcher ComboBox (from subtask 2)
        self.mode_switcher_combo = QComboBox()
        self.mode_switcher_combo.addItem(str(TradingMode.PAPER), TradingMode.PAPER)
        self.mode_switcher_combo.addItem(str(TradingMode.REAL), TradingMode.REAL)
        self.statusBar.addPermanentWidget(self.mode_switcher_combo)

        # Etiqueta para el estado de conexión general
        self.connection_status_label = QLabel("Estado de Conexión: Desconectado")
        self.statusBar.addPermanentWidget(self.connection_status_label)

        # Etiqueta para el modo Paper Trading
        self.paper_trading_status_label = QLabel("Modo: Real")
        self.paper_trading_status_label.setStyleSheet(
            "font-weight: bold; color: green;"
        )
        self.statusBar.addPermanentWidget(self.paper_trading_status_label)

        # Etiqueta para el modo de Operativa Real Limitada (NUEVO)
        self.real_trading_status_label = QLabel("Modo Real: Inactivo")
        self.real_trading_status_label.setStyleSheet(
            "font-weight: bold; color: gray;"
        )
        self.statusBar.addPermanentWidget(self.real_trading_status_label)

        self.statusBar.showMessage("Listo")

    def _create_menu_bar(self):
        """Creates the main menu bar with theme switching options. Si el menú no está soportado, no falla."""
        menu_bar = self.menuBar()
        if menu_bar is None:
            logger.warning("No se pudo crear la barra de menú (menuBar() es None). El entorno puede no soportar menús nativos.")
            return

        # View Menu (or Settings/Preferences Menu)
        view_menu = menu_bar.addMenu("&View") if menu_bar else None
        if view_menu is None:
            logger.warning("No se pudo crear el menú 'View'. El entorno puede no soportar menús nativos.")
            return

        # Theme Submenu or Direct Actions
        theme_menu = view_menu.addMenu("Switch &Theme") if view_menu else None
        if theme_menu is None:
            logger.warning("No se pudo crear el submenú de temas. El entorno puede no soportar menús nativos.")
            return

        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self._apply_theme_selection("dark"))
        theme_menu.addAction(dark_theme_action)

        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(lambda: self._apply_theme_selection("light"))
        theme_menu.addAction(light_theme_action)

    def _apply_theme_selection(self, theme_name: str):
        """Applies the selected theme by calling the centralized function."""
        logger.info(f"MainWindow: User selected {theme_name} theme.")
        from src.ultibot_ui.main import apply_application_style
        apply_application_style(theme_name) # Call the function imported from main.py
        # Note: If specific widgets need to be explicitly repainted or updated
        # after a theme change, that logic could be added here (e.g., custom plot redraws).
        # For QSS, Qt generally handles repaint, but complex custom widgets might need a hint.
        # self.update(); # Force a repaint of the window and its children if needed.


    def _load_initial_paper_trading_status(self): # CORREGIDO: No necesita ser async def
        """Carga el estado inicial del modo Paper Trading y actualiza la UI.

        Esta función ahora inicia un ApiWorker para obtener la configuración del usuario.
        """
        logging.info("Iniciando ApiWorker para _load_initial_paper_trading_status.")

        # Ensure user_id is string for API calls if needed by client, though get_user_configuration might not need it.
        # The current api_client.get_user_configuration takes no args.
        from src.ultibot_ui.main import ApiWorker
        if not self.qasync_loop:
            logger.error("MainWindow: qasync_loop no está disponible para _load_initial_paper_trading_status")
            self._handle_paper_trading_status_error(Exception("Error interno: Bucle de eventos no configurado."))
            return

        coroutine_factory = lambda api_client: api_client.get_user_configuration()
        future = self.qasync_loop.create_future()
        worker = ApiWorker(coroutine_factory, self.backend_base_url)
        
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        # Conectar señales del worker para establecer el resultado/excepción del futuro EN EL HILO PRINCIPAL
        worker.result_ready.connect(lambda result: self._safe_set_future_result(future, result))
        worker.error_occurred.connect(lambda err_msg: self._safe_set_future_exception(future, APIError(message=err_msg)))

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        worker.result_ready.connect(worker.deleteLater) # Worker se autodestruye
        worker.error_occurred.connect(worker.deleteLater) # Worker se autodestruye
        thread.finished.connect(thread.deleteLater) # Thread se autodestruye
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        
        thread.start()

        # Añadir un callback al futuro que se ejecutará en el hilo principal
        future.add_done_callback(
            lambda fut: self._handle_paper_trading_status_result(fut.result())
            if not fut.exception() else self._handle_paper_trading_status_error(
                fut.exception() # Pasamos la excepción directamente, el handler la convertirá a str
            )
        )

    def _handle_paper_trading_status_result(self, result: dict): # Type hint result as dict (from JSON)
        """Maneja el resultado exitoso de la carga del estado de Paper Trading."""
        try:
            is_active = result.get("paperTradingActive", False) 
            self._update_paper_trading_status_label(is_active)
            logging.info(f"Estado de Paper Trading cargado: {'Activo' if is_active else 'Inactivo'}")
        except Exception as e:
            self._handle_paper_trading_status_error(e) # Pasar la excepción directamente
        finally:
            self._paper_trading_status_loaded = True
            self._check_initialization_complete()

    def _handle_paper_trading_status_error(self, error: BaseException | None): # Aceptar BaseException | None
        """Maneja errores durante la carga del estado de Paper Trading."""
        error_message = str(error if error is not None else "Error desconocido")
        self.paper_trading_status_label.setText("Modo: Error")
        self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.statusBar.showMessage(f"Error al cargar modo Paper: {error_message}")
        logging.error(f"Error al cargar el estado inicial del Paper Trading: {error_message}")
        self._log_debug(f"[ERROR] Paper Trading: {error_message}")
        self._paper_trading_status_loaded = True # Mark as loaded even on error to not block init indefinitely
        self._check_initialization_complete()

    def _load_initial_real_trading_status_worker(self):
        """Carga el estado inicial del modo de Operativa Real Limitada usando ApiWorker."""
        logging.info("Iniciando ApiWorker para _load_initial_real_trading_status.")

        from src.ultibot_ui.main import ApiWorker
        if not self.qasync_loop:
            logger.error("MainWindow: qasync_loop no está disponible para _load_initial_real_trading_status_worker")
            self._handle_real_trading_status_error(Exception("Error interno: Bucle de eventos no configurado."))
            return

        coroutine_factory = lambda api_client: api_client.get_real_trading_mode_status()
        future = self.qasync_loop.create_future()
        worker = ApiWorker(coroutine_factory, self.backend_base_url)

        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(lambda result: self._safe_set_future_result(future, result))
        worker.error_occurred.connect(lambda err_msg: self._safe_set_future_exception(future, APIError(message=err_msg)))

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)

        thread.start()

        future.add_done_callback(
            lambda fut: self._handle_real_trading_status_result(fut.result())
            if not fut.exception() else self._handle_real_trading_status_error(
                fut.exception() # Pasamos la excepción directamente, el handler la convertirá a str
            )
        )

    def _handle_real_trading_status_result(self, status_data: dict): # Type hint
        """Maneja el resultado exitoso de la carga del estado de Real Trading."""
        try:
            is_active = status_data.get("isActive", False)
            executed_count = status_data.get("executedCount", 0)
            limit = status_data.get("limit", 5) # Default limit if not provided
            self._update_real_trading_status_label(is_active, executed_count, limit)
            logging.info(f"Estado de Real Trading cargado: {'Activo' if is_active else 'Inactivo'}")
        except Exception as e:
            self._handle_real_trading_status_error(e)
        finally:
            self._real_trading_status_loaded = True
            self._check_initialization_complete()

    def _handle_real_trading_status_error(self, error: BaseException | None): # Aceptar BaseException | None
        """Maneja errores durante la carga del estado de Real Trading."""
        error_message = str(error if error is not None else "Error desconocido")
        self.real_trading_status_label.setText("Modo Real: Error")
        self.real_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.statusBar.showMessage(f"Error al cargar modo Real: {error_message}")
        logging.error(f"Error al cargar el estado inicial del Real Trading: {error_message}")
        self._log_debug(f"[ERROR] Real Trading: {error_message}")
        self._real_trading_status_loaded = True # Mark as loaded even on error
        self._check_initialization_complete()

    def _update_paper_trading_status_display(self, config: UserConfiguration): # config might be dict now
        """Actualiza la visualización del modo Paper Trading en la barra de estado.

        Args:
            config: Configuración de usuario actualizada

        """
        self._update_paper_trading_status_label(config.paperTradingActive or False)
        self.statusBar.showMessage("Configuración de Paper Trading actualizada.")

    def _update_paper_trading_status_label(self, is_paper_trading_active: bool):
        """Actualiza el texto y estilo de la etiqueta del modo Paper Trading.

        Args:
            is_paper_trading_active: True si el modo Paper Trading está activo

        """
        if is_paper_trading_active:
            self.paper_trading_status_label.setText("Modo: PAPER TRADING")
            self.paper_trading_status_label.setStyleSheet(
                "font-weight: bold; color: orange;"
            )
        else:
            self.paper_trading_status_label.setText("Modo: Real")
            self.paper_trading_status_label.setStyleSheet(
                "font-weight: bold; color: green;"
            )

    def _update_real_trading_status_display(self, is_active: bool, executed_count: int, limit: int):
        """Actualiza la visualización del modo de Operativa Real Limitada en la barra de estado.

        Args:
            is_active: True si el modo real está activo
            executed_count: Número de operaciones reales ejecutadas
            limit: Límite de operaciones reales
        """
        if is_active:
            self.real_trading_status_label.setText(f"MODO REAL LIMITADO ACTIVO ({executed_count}/{limit})")
            self.real_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.real_trading_status_label.setText("Modo Real: Inactivo")
            self.real_trading_status_label.setStyleSheet("font-weight: bold; color: gray;")
        self.statusBar.showMessage("Estado de Operativa Real actualizado.")

    def _log_debug(self, msg: str):
        """Agrega un mensaje al panel de logs visual y al logger."""
        self.debug_log_widget.append(msg)
        logger.info(msg)

    def _setup_central_widget(self, parent_widget=None):
        """Configura el widget central con la navegación lateral y las vistas."""
        if parent_widget is None:
            parent_widget = QWidget()
        main_layout = QHBoxLayout(parent_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar Navigation
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200)  # Ancho fijo para la barra lateral
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        # Content Area (StackedWidget)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Añadir vistas al stacked widget
        # DashboardView constructor needs to be updated to accept backend_base_url
        self.dashboard_view = DashboardView(
            user_id=self.user_id,
            backend_base_url=self.backend_base_url
            # Removed old services: market_data_service, config_service,
            # notification_service, persistence_service
        )
        self.stacked_widget.addWidget(self.dashboard_view)  # Índice 0
        self.dashboard_view.initialization_complete.connect(self._on_dashboard_initialized) # Conectar señal

        # Replace placeholder with OpportunitiesView
        if not self.qasync_loop:
            logger.critical("MainWindow: qasync_loop no está disponible al crear OpportunitiesView. Esto es un error fatal.")
            # Podríamos crear un QLabel de error aquí en lugar de OpportunitiesView
            error_label = QLabel("Error Crítico: Bucle de eventos no disponible para OpportunitiesView.")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stacked_widget.addWidget(error_label)
        else:
            self.opportunities_view = OpportunitiesView(self.user_id, self.backend_base_url, self.qasync_loop)
            self.stacked_widget.addWidget(self.opportunities_view)  # Índice 1

        # self.strategies_view = QLabel("Vista de Estrategias (Placeholder)")
        # self.strategies_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.strategy_management_view = StrategyManagementView(backend_base_url=self.backend_base_url, parent=self) # Pasar backend_base_url
        self.stacked_widget.addWidget(self.strategy_management_view)  # Índice 2

        # New PortfolioView
        if not self.qasync_loop:
            logger.critical("MainWindow: qasync_loop no está disponible al crear PortfolioView. Esto es un error fatal.")
            error_label_portfolio = QLabel("Error Crítico: Bucle de eventos no disponible para PortfolioView.")
            error_label_portfolio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stacked_widget.addWidget(error_label_portfolio)
        else:
            self.portfolio_view = PortfolioView(self.user_id, self.backend_base_url, self.qasync_loop)
            self.stacked_widget.addWidget(self.portfolio_view) # Index 3

        # Vista de historial con el widget de paper trading report
        self.history_view = HistoryView(self.user_id)
        self.stacked_widget.addWidget(self.history_view)  # Índice 4

        self.settings_view = SettingsView(str(self.user_id), self.backend_base_url, self.qasync_loop) # Pasar backend_base_url
        self.stacked_widget.addWidget(self.settings_view)  # Índice 5

        # View mapping for navigation
        self.view_map = {
            "dashboard": 0,
            "opportunities": 1,
            "strategies": 2,
            "portfolio": 3, # New portfolio view
            "history": 4,
            "settings": 5,
        }

        # Update sidebar navigation items (assuming SidebarNavigationWidget needs this)
        # This might require adding a "Portfolio" button in SidebarNavigationWidget's setup
        # For now, we just ensure the map is correct. The button itself needs to be added in SidebarNavigationWidget.
        # If SidebarNavigationWidget dynamically creates buttons based on a list of view names,
        # that list would need to be updated.

        # Set initial view to Dashboard
        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button:
            dashboard_button.setChecked(True)
        self.stacked_widget.setCurrentIndex(self.view_map["dashboard"])

        self._log_debug("Central widget y vistas configuradas.")

    def _switch_view(self, view_name):
        """Cambia a la vista especificada.

        Args:
            view_name: Nombre de la vista a mostrar

        """
        index = self.view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)

    def _on_dashboard_initialized(self):
        """
        Se llama cuando DashboardView ha completado su inicialización asíncrona.
        Ahora podemos cargar las estrategias.
        """
        logger.info("MainWindow: _on_dashboard_initialized INVOCADO.") # LOG AÑADIDO
        logger.info("MainWindow: DashboardView inicializado. Cargando estrategias...")
        if hasattr(self.strategy_management_view, 'load_strategies') and callable(self.strategy_management_view.load_strategies):
            self.strategy_management_view.load_strategies()
        else:
            logger.warning("MainWindow: strategy_management_view no tiene el método load_strategies o no es llamable.")

    def closeEvent(self, event):
        self._log_debug("[INFO] MainWindow: closeEvent triggered.")
        # Llamar a métodos de limpieza en las vistas/widgets que lo necesiten
        if hasattr(self.dashboard_view, "cleanup") and callable(
            self.dashboard_view.cleanup
        ):
            print("MainWindow: Calling cleanup on dashboard_view.")
            self.dashboard_view.cleanup()

        # Limpiar la vista de historial
        if hasattr(self.history_view, "cleanup") and callable(
            self.history_view.cleanup
        ):
            print("MainWindow: Calling cleanup on history_view.")
            self.history_view.cleanup()

        # Limpiar la vista de oportunidades
        if hasattr(self.opportunities_view, "cleanup") and callable(
            self.opportunities_view.cleanup
        ):
            print("MainWindow: Calling cleanup on opportunities_view.")
            self.opportunities_view.cleanup()

        # Limpiar la vista de portafolio
        if hasattr(self.portfolio_view, "cleanup") and callable(
            self.portfolio_view.cleanup
        ):
            print("MainWindow: Calling cleanup on portfolio_view.")
            self.portfolio_view.cleanup()

        # Clean up any running QThreads
        for thread in list(self.active_threads): # Iterate over a copy
            if thread.isRunning():
                print(f"MainWindow: Stopping active QThread {thread} during closeEvent.")
                thread.quit()
                thread.wait(3000) # Wait up to 3 seconds for thread to finish

        super().closeEvent(event)  # Aceptar el evento de cierre
