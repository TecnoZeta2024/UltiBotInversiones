"""Módulo de ventana principal de UltiBotInversiones.

Este módulo contiene la implementación de la ventana principal de la aplicación,
proporcionando la interfaz de usuario principal con navegación lateral y vistas
intercambiables para diferentes funcionalidades del bot de trading.
"""

import logging
from uuid import UUID

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QWidget,
    QAction # Added for menu actions
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
from src.ultibot_ui.main import ApiWorker, apply_application_style # Import the new style function


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones.

    Proporciona la interfaz de usuario principal con navegación lateral,
    barra de estado y vistas intercambiables para las diferentes
    funcionalidades del sistema de trading.
    """

    def __init__(
        self,
        user_id: UUID,
        api_client: UltiBotAPIClient, # Changed: Pass api_client
        parent=None,
    ):
        """Inicializa la ventana principal con el cliente API.

        Args:
            user_id: Identificador único del usuario
            api_client: Cliente para interactuar con el backend API.
            parent: Widget padre opcional
        """
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client # Use the passed-in api_client

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

        self._create_menu_bar() # Added menu bar setup
        self._create_status_bar()
        self._setup_central_widget()

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

    def _schedule_initial_load(self):
        """Programa la carga inicial del estado de Paper Trading y Real Trading.

        Utiliza ApiWorker para ejecutar llamadas API de forma no bloqueante.
        """
        # Remove direct asyncio.create_task usage. Will use ApiWorker.
        logging.info("Programando carga inicial de estados de trading con ApiWorker.")
        self._load_initial_paper_trading_status_worker()
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
        """Creates the main menu bar with theme switching options."""
        menu_bar = self.menuBar()

        # View Menu (or Settings/Preferences Menu)
        view_menu = menu_bar.addMenu("&View")

        # Theme Submenu or Direct Actions
        theme_menu = view_menu.addMenu("Switch &Theme")

        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self._apply_theme_selection("dark"))
        theme_menu.addAction(dark_theme_action)

        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(lambda: self._apply_theme_selection("light"))
        theme_menu.addAction(light_theme_action)

    def _apply_theme_selection(self, theme_name: str):
        """Applies the selected theme by calling the centralized function."""
        logger.info(f"MainWindow: User selected {theme_name} theme.")
        apply_application_style(theme_name) # Call the function imported from main.py
        # Note: If specific widgets need to be explicitly repainted or updated
        # after a theme change, that logic could be added here (e.g., custom plot redraws).
        # For QSS, Qt generally handles repaint, but complex custom widgets might need a hint.
        # self.update(); # Force a repaint of the window and its children if needed.


    async def _load_initial_paper_trading_status(self):
        """Carga el estado inicial del modo Paper Trading y actualiza la UI.

        Esta función ahora inicia un ApiWorker para obtener la configuración del usuario.
        """
        logging.info("Iniciando ApiWorker para _load_initial_paper_trading_status.")

        # Ensure user_id is string for API calls if needed by client, though get_user_configuration might not need it.
        # The current api_client.get_user_configuration takes no args.
        worker = ApiWorker(self.api_client.get_user_configuration())
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_paper_trading_status_result)
        worker.error_occurred.connect(self._handle_paper_trading_status_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_threads.remove(thread))
        thread.start()

    def _handle_paper_trading_status_result(self, result: dict): # Type hint result as dict (from JSON)
        """Maneja el resultado exitoso de la carga del estado de Paper Trading."""
        try:
            # Assuming result is a dict similar to UserConfiguration or parts of it
            is_active = result.get("paperTradingActive", False) # Adapt key if necessary
            self._update_paper_trading_status_label(is_active)
            logging.info(f"Estado de Paper Trading cargado: {'Activo' if is_active else 'Inactivo'}")
        except Exception as e:
            self._handle_paper_trading_status_error(f"Error al procesar resultado de Paper Trading: {e}")
        finally:
            self._paper_trading_status_loaded = True
            self._check_initialization_complete()

    def _handle_paper_trading_status_error(self, error_message: str):
        """Maneja errores durante la carga del estado de Paper Trading."""
        self.paper_trading_status_label.setText("Modo: Error")
        self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.statusBar.showMessage(f"Error al cargar modo Paper: {error_message}")
        logging.error(f"Error al cargar el estado inicial del Paper Trading: {error_message}")
        self._paper_trading_status_loaded = True # Mark as loaded even on error to not block init indefinitely
        self._check_initialization_complete()

    def _load_initial_real_trading_status_worker(self):
        """Carga el estado inicial del modo de Operativa Real Limitada usando ApiWorker."""
        logging.info("Iniciando ApiWorker para _load_initial_real_trading_status.")

        worker = ApiWorker(self.api_client.get_real_trading_mode_status())
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_real_trading_status_result)
        worker.error_occurred.connect(self._handle_real_trading_status_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_threads.remove(thread))
        thread.start()

    def _handle_real_trading_status_result(self, status_data: dict): # Type hint
        """Maneja el resultado exitoso de la carga del estado de Real Trading."""
        try:
            self._update_real_trading_status_label(
                status_data.get("isActive", False),
                status_data.get("executedCount", 0),
                status_data.get("limit", 5) # Default limit if not provided
            )
            logging.info(f"Estado de Real Trading cargado: {'Activo' if status_data.get('isActive') else 'Inactivo'}")
        except Exception as e:
            self._handle_real_trading_status_error(f"Error al procesar resultado de Real Trading: {e}")
        finally:
            self._real_trading_status_loaded = True
            self._check_initialization_complete()

    def _handle_real_trading_status_error(self, error_message: str):
        """Maneja errores durante la carga del estado de Real Trading."""
        self.real_trading_status_label.setText("Modo Real: Error")
        self.real_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
        self.statusBar.showMessage(f"Error al cargar modo Real: {error_message}")
        logging.error(f"Error al cargar el estado inicial del Real Trading: {error_message}")
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


    def _setup_central_widget(self):
        """Configura el widget central con la navegación lateral y las vistas."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # No margins for a clean look
        main_layout.setSpacing(0) # No spacing between sidebar and content

        # Sidebar Navigation
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200)  # Ancho fijo para la barra lateral
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        # Content Area (StackedWidget)
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Añadir vistas al stacked widget
        # DashboardView constructor needs to be updated to accept api_client
        self.dashboard_view = DashboardView(
            user_id=self.user_id,
            api_client=self.api_client
            # Removed old services: market_data_service, config_service,
            # notification_service, persistence_service
        )
        self.stacked_widget.addWidget(self.dashboard_view)  # Índice 0

        # Replace placeholder with OpportunitiesView
        self.opportunities_view = OpportunitiesView(self.user_id, self.api_client)
        self.stacked_widget.addWidget(self.opportunities_view)  # Índice 1

        # self.strategies_view = QLabel("Vista de Estrategias (Placeholder)")
        # self.strategies_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.strategy_management_view = StrategyManagementView(api_client=self.api_client, parent=self) # Pasar api_client
        self.stacked_widget.addWidget(self.strategy_management_view)  # Índice 2

        # New PortfolioView
        self.portfolio_view = PortfolioView(self.user_id, self.api_client)
        self.stacked_widget.addWidget(self.portfolio_view) # Index 3

        # Vista de historial con el widget de paper trading report
        self.history_view = HistoryView(self.user_id)
        self.stacked_widget.addWidget(self.history_view)  # Índice 4

        self.settings_view = SettingsView(str(self.user_id), self.api_client)
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

    def _switch_view(self, view_name):
        """Cambia a la vista especificada.

        Args:
            view_name: Nombre de la vista a mostrar

        """
        index = self.view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)

    def closeEvent(self, event):
        """Maneja el evento de cierre de la ventana principal.

        Asegura que los recursos de los widgets hijos se limpien apropiadamente
        antes de cerrar la aplicación.

        Args:
            event: Evento de cierre de Qt

        """
        print("MainWindow: closeEvent triggered.")
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
