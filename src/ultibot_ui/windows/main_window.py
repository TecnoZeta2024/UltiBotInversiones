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
    QComboBox, # Added QComboBox (from subtask 2)
)

from src.shared.data_types import UserConfiguration
# Import TradingMode and TradingModeService (from subtask 2)
from src.ultibot_ui.services import TradingMode, TradingModeService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget
from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.history_view import HistoryView
from src.ultibot_ui.windows.settings_view import SettingsView
from src.ultibot_ui.services.api_client import UltiBotAPIClient # Importar UltiBotAPIClient
from src.ultibot_ui.views.strategy_management_view import StrategyManagementView # Importar StrategyManagementView


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación UltiBotInversiones.

    Proporciona la interfaz de usuario principal con navegación lateral,
    barra de estado y vistas intercambiables para las diferentes
    funcionalidades del sistema de trading.
    """

    def __init__(
        self,
        user_id: UUID,
        market_data_service: MarketDataService,
        config_service: ConfigService,
        notification_service: NotificationService,
        persistence_service: SupabasePersistenceService,
        parent=None,
    ):
        """Inicializa la ventana principal con los servicios requeridos.

        Args:
            user_id: Identificador único del usuario
            market_data_service: Servicio de datos de mercado
            config_service: Servicio de configuración
            notification_service: Servicio de notificaciones
            persistence_service: Servicio de persistencia de datos
            parent: Widget padre opcional

        """
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.notification_service = notification_service
        self.persistence_service = persistence_service

        # Inicializar el cliente API para el frontend
        self.api_client = UltiBotAPIClient()

        # Variables para rastrear el estado de inicialización
        self._initialization_complete = False

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1200, 800)

        # Instantiate TradingModeService (from subtask 5)
        self.trading_mode_service = TradingModeService()

        self._create_status_bar() # mode_switcher_combo is created here
        self._setup_central_widget() # dashboard_view is created here, needs trading_mode_service

        # Connect signals for mode_switcher_combo and trading_mode_service (from subtask 5)
        self.mode_switcher_combo.currentIndexChanged.connect(self._handle_mode_switch_selection)
        self.trading_mode_service.mode_changed.connect(self._update_mode_switcher_ui)
        
        # Set initial state of the combo box (from subtask 5)
        self._update_mode_switcher_ui(self.trading_mode_service.get_current_mode())

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

        Utiliza qasync para ejecutar código asíncrono de forma segura
        en el contexto de Qt.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            # Crear tareas para cargar ambos estados iniciales
            task_paper = loop.create_task(self._load_initial_paper_trading_status())
            task_real = loop.create_task(self._load_initial_real_trading_status())
            
            # Configurar callback para marcar la inicialización como completa después de ambas tareas
            async def wait_for_all_initial_loads():
                await asyncio.gather(task_paper, task_real)
                self._initialization_complete = True
                logging.info("Inicialización completa de los estados de trading.")

            loop.create_task(wait_for_all_initial_loads())

        except Exception as e:
            logging.error(f"Error al programar carga inicial: {e}", exc_info=True)
            self.paper_trading_status_label.setText("Modo: Error de Inicialización")
            self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.real_trading_status_label.setText("Modo Real: Error")
            self.real_trading_status_label.setStyleSheet("font-weight: bold; color: red;")


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

    async def _load_initial_paper_trading_status(self):
        """Carga el estado inicial del modo Paper Trading y actualiza la UI.

        Esta función se ejecuta de forma asíncrona para obtener la configuración
        del usuario y actualizar el estado del modo Paper Trading en la interfaz.
        """
        try:
            user_config = await self.config_service.get_user_configuration(str(self.user_id)) # Convert UUID to str
            self._update_paper_trading_status_label(
                user_config.paperTradingActive or False
            )
        except Exception as e:
            self.paper_trading_status_label.setText("Modo: Error")
            self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.statusBar.showMessage(f"Error al cargar modo Paper: {e}")
            logging.error(
                f"Error al cargar el estado inicial del Paper Trading: {e}",
                exc_info=True,
            )

    async def _load_initial_real_trading_status(self):
        """Carga el estado inicial del modo de Operativa Real Limitada y actualiza la UI."""
        try:
            status_data = await self.api_client.get_real_trading_mode_status()
            self._update_real_trading_status_label(
                status_data.get("isActive", False),
                status_data.get("executedCount", 0),
                status_data.get("limit", 5)
            )
        except Exception as e:
            self.real_trading_status_label.setText("Modo Real: Error")
            self.real_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.statusBar.showMessage(f"Error al cargar modo Real: {e}")
            logging.error(
                f"Error al cargar el estado inicial del Real Trading: {e}",
                exc_info=True,
            )

    def _update_paper_trading_status_display(self, config: UserConfiguration):
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
        self.dashboard_view = DashboardView(
            self.user_id,
            self.market_data_service,
            self.config_service,
            self.notification_service,
            self.persistence_service,
            self.api_client,
            self.trading_mode_service, # Pass TradingModeService (from subtask 5)
        )
        self.stacked_widget.addWidget(self.dashboard_view)  # Índice 0

        # Placeholder para otras vistas
        self.opportunities_view = QLabel("Vista de Oportunidades (Placeholder)")
        self.opportunities_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.opportunities_view)  # Índice 1

        # self.strategies_view = QLabel("Vista de Estrategias (Placeholder)") # Reemplazado
        # self.strategies_view.setAlignment(Qt.AlignmentFlag.AlignCenter) # Reemplazado
        self.strategy_management_view = StrategyManagementView(api_client=self.api_client, parent=self) # Pasar api_client
        self.stacked_widget.addWidget(self.strategy_management_view)  # Índice 2

        # Vista de historial con el widget de paper trading report
        self.history_view = HistoryView(self.user_id)
        self.stacked_widget.addWidget(self.history_view)  # Índice 3

        self.settings_view = SettingsView(str(self.user_id), self.api_client) # Pasar api_client
        self.stacked_widget.addWidget(self.settings_view)  # Índice 4

        # View mapping for navigation
        self.view_map = {
            "dashboard": 0,
            "opportunities": 1,
            "strategies": 2,
            "history": 3, # Corrected from trading_history_view variable name to key "history"
            "settings": 4,
        }

        # Set initial view to Dashboard
        # Ensure sidebar button is checked (if sidebar has checkable buttons)
        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button: # This relies on objectName being set in SidebarNavigationWidget
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

    # Handler methods for TradingModeService and QComboBox (from subtask 5)
    def _handle_mode_switch_selection(self, index: int):
        """
        Handles the selection change in the trading mode QComboBox.
        Updates the TradingModeService with the new mode.
        """
        selected_mode_enum = self.mode_switcher_combo.itemData(index)
        logger.debug(f"MainWindow._handle_mode_switch_selection: QComboBox index {index}, selected mode {selected_mode_enum}")
        if isinstance(selected_mode_enum, TradingMode):
            self.trading_mode_service.set_mode(selected_mode_enum)
        else:
            logging.warning(f"Invalid data type from mode_switcher_combo: {type(selected_mode_enum)}")

    def _update_mode_switcher_ui(self, new_mode: TradingMode):
        """
        Updates the QComboBox selection when the TradingModeService reports a mode change.
        """
        logger.debug(f"MainWindow._update_mode_switcher_ui: Updating QComboBox for mode {new_mode}")
        for i in range(self.mode_switcher_combo.count()):
            if self.mode_switcher_combo.itemData(i) == new_mode:
                self.mode_switcher_combo.blockSignals(True)
                self.mode_switcher_combo.setCurrentIndex(i)
                self.mode_switcher_combo.blockSignals(False)
                logging.debug(f"Mode switcher UI set to index {i} for mode {new_mode}") # Added specific log for when index is set
                return
        logging.warning(f"Mode {new_mode} not found in mode_switcher_combo.")

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

        super().closeEvent(event)  # Aceptar el evento de cierre
