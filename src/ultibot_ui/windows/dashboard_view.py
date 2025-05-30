from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
from PyQt5.QtCore import Qt
from uuid import UUID # Importar UUID

from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget # Importar el nuevo widget
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService

class DashboardView(QWidget):
    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService):
        super().__init__()
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Zona Superior: Resumen de Datos de Mercado (MarketDataWidget)
        self.market_data_widget = MarketDataWidget(self.user_id, self.market_data_service, self.config_service)
        main_layout.addWidget(self.market_data_widget)

        # Zona Central (con QSplitter horizontal)
        center_splitter = QSplitter(Qt.Horizontal)
        center_splitter.setContentsMargins(0, 0, 0, 0)
        center_splitter.setChildrenCollapsible(False)

        # Panel Izquierdo (Placeholder para Estado del Portafolio)
        portfolio_area = QLabel("Panel Izquierdo: Estado del Portafolio")
        portfolio_area.setAlignment(Qt.AlignCenter)
        portfolio_area.setStyleSheet("background-color: #1E1E1E; padding: 10px;")
        center_splitter.addWidget(portfolio_area)

        # Panel Derecho (Placeholder para Gráficos Financieros)
        charts_area = QLabel("Panel Derecho: Visualización de Gráficos Financieros")
        charts_area.setAlignment(Qt.AlignCenter)
        charts_area.setStyleSheet("background-color: #252526; padding: 10px;")
        center_splitter.addWidget(charts_area)

        main_layout.addWidget(center_splitter)

        # Zona Inferior (con QSplitter vertical)
        bottom_splitter = QSplitter(Qt.Vertical)
        bottom_splitter.setContentsMargins(0, 0, 0, 0)
        bottom_splitter.setChildrenCollapsible(False)

        # Placeholder para el Centro de Notificaciones
        notifications_area = QLabel("Área Inferior: Centro de Notificaciones del Sistema")
        notifications_area.setAlignment(Qt.AlignCenter)
        notifications_area.setStyleSheet("background-color: #2D2D2D; padding: 10px;")
        bottom_splitter.addWidget(notifications_area)

        # Añadir el splitter inferior al layout principal
        main_layout.addWidget(bottom_splitter)

        # Establecer tamaños iniciales para los splitters (opcional, para una mejor visualización inicial)
        # Estos valores pueden necesitar ajuste o ser dinámicos
        # center_splitter.setSizes([self.width() // 3, 2 * self.width() // 3]) # Esto causará un error si se llama antes de que el widget tenga un tamaño
        # bottom_splitter.setSizes([self.height() // 4]) # Esto también causará un error
