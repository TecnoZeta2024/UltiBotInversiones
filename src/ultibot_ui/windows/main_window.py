from PyQt5.QtWidgets import QMainWindow, QStatusBar, QLabel, QWidget, QHBoxLayout, QStackedWidget, QPushButton
from PyQt5.QtCore import Qt
from uuid import UUID # Importar UUID

from ultibot_ui.windows.dashboard_view import DashboardView
from ultibot_ui.widgets.sidebar_navigation_widget import SidebarNavigationWidget

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService

class MainWindow(QMainWindow):
    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService):
        super().__init__()
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service

        self.setWindowTitle("UltiBotInversiones")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self._create_status_bar()
        self._setup_central_widget()

    def _create_status_bar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo")

        # Ejemplo de cómo añadir un widget a la barra de estado
        self.status_label = QLabel("Estado de Conexión: Desconectado")
        self.statusBar.addPermanentWidget(self.status_label)

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
        self.dashboard_view = DashboardView(self.user_id, self.market_data_service, self.config_service)
        self.stacked_widget.addWidget(self.dashboard_view) # Índice 0

        # Placeholder para otras vistas
        self.opportunities_view = QLabel("Vista de Oportunidades (Placeholder)")
        self.opportunities_view.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.opportunities_view) # Índice 1

        self.strategies_view = QLabel("Vista de Estrategias (Placeholder)")
        self.strategies_view.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.strategies_view) # Índice 2

        self.history_view = QLabel("Vista de Historial (Placeholder)")
        self.history_view.setAlignment(Qt.AlignCenter)
        self.stacked_widget.addWidget(self.history_view) # Índice 3

        self.settings_view = QLabel("Vista de Configuración (Placeholder)")
        self.settings_view.setAlignment(Qt.AlignCenter)
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
