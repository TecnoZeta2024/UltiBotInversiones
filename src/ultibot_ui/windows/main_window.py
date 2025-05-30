from PyQt5.QtWidgets import QMainWindow, QStatusBar, QLabel, QWidget, QHBoxLayout, QStackedWidget, QPushButton
from PyQt5.QtCore import Qt
from uuid import UUID # Importar UUID

from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.settings_view import SettingsView # Importar SettingsView
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget

import logging # Importar logging
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QLabel, QWidget, QHBoxLayout, QStackedWidget, QPushButton
from PyQt5.QtCore import Qt
from uuid import UUID # Importar UUID

from src.ultibot_ui.windows.dashboard_view import DashboardView
from src.ultibot_ui.windows.settings_view import SettingsView # Importar SettingsView
from src.ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.shared.data_types import UserConfiguration # Importar UserConfiguration

class MainWindow(QMainWindow):
    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService, notification_service: NotificationService, parent=None): # Añadir notification_service
        super().__init__(parent)
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.notification_service = notification_service # Guardar la referencia al servicio de notificaciones

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self._create_status_bar()
        self._setup_central_widget()
        # Conectar la señal de cambio de configuración de SettingsView
        self.settings_view.config_changed.connect(self._update_paper_trading_status_display)
        # Cargar el estado inicial del paper trading al iniciar la ventana
        import asyncio
        asyncio.create_task(self._load_initial_paper_trading_status())

    def _create_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Etiqueta para el estado de conexión general
        self.connection_status_label = QLabel("Estado de Conexión: Desconectado")
        self.statusBar.addPermanentWidget(self.connection_status_label)

        # Etiqueta para el modo Paper Trading
        self.paper_trading_status_label = QLabel("Modo: Real")
        self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: green;") # Estilo inicial
        self.statusBar.addPermanentWidget(self.paper_trading_status_label)

        self.statusBar.showMessage("Listo")

    async def _load_initial_paper_trading_status(self):
        """Carga el estado inicial del modo Paper Trading y actualiza la UI."""
        try:
            user_config = await self.config_service.load_user_configuration(self.user_id)
            self._update_paper_trading_status_label(user_config.paperTradingActive or False)
        except Exception as e:
            self.paper_trading_status_label.setText("Modo: Error")
            self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: red;")
            self.statusBar.showMessage(f"Error al cargar modo: {e}")
            logging.error(f"Error al cargar el estado inicial del Paper Trading: {e}", exc_info=True)

    def _update_paper_trading_status_display(self, config: UserConfiguration):
        """Actualiza la visualización del modo Paper Trading en la barra de estado."""
        self._update_paper_trading_status_label(config.paperTradingActive or False)
        self.statusBar.showMessage("Configuración de Paper Trading actualizada.")

    def _update_paper_trading_status_label(self, is_paper_trading_active: bool):
        """Actualiza el texto y estilo de la etiqueta del modo Paper Trading."""
        if is_paper_trading_active:
            self.paper_trading_status_label.setText("Modo: PAPER TRADING")
            self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: orange;")
        else:
            self.paper_trading_status_label.setText("Modo: Real")
            self.paper_trading_status_label.setStyleSheet("font-weight: bold; color: green;")

    def _setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar de navegación
        self.sidebar = SidebarNavigationWidget()
        self.sidebar.setFixedWidth(200) # Ancho fijo para la barra lateral
        self.sidebar.navigation_requested.connect(self._switch_view)
        main_layout.addWidget(self.sidebar)

        # Contenedor de vistas principales
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Añadir vistas al stacked widget
        self.dashboard_view = DashboardView(self.user_id, self.market_data_service, self.config_service, self.notification_service) # Pasar notification_service
        self.stacked_widget.addWidget(self.dashboard_view) # Índice 0

        # Placeholder para otras vistas
        self.opportunities_view = QLabel("Vista de Oportunidades (Placeholder)")
        self.opportunities_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.opportunities_view) # Índice 1

        self.strategies_view = QLabel("Vista de Estrategias (Placeholder)")
        self.strategies_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.strategies_view) # Índice 2

        self.history_view = QLabel("Vista de Historial (Placeholder)")
        self.history_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.history_view) # Índice 3

        self.settings_view = SettingsView(str(self.user_id), self.config_service) # Instanciar SettingsView, convertir UUID a str
        self.stacked_widget.addWidget(self.settings_view) # Índice 4

        # Mapeo de nombres a índices del stacked widget
        self.view_map = {
            "dashboard": 0,
            "opportunities": 1,
            "strategies": 2,
            "history": 3,
            "settings": 4,
        }

        # Seleccionar la vista inicial (Dashboard)
        dashboard_button = self.sidebar.findChild(QPushButton, "navButton_dashboard")
        if dashboard_button:
            dashboard_button.setChecked(True)
        self.stacked_widget.setCurrentIndex(self.view_map["dashboard"])


    def _switch_view(self, view_name):
        index = self.view_map.get(view_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
