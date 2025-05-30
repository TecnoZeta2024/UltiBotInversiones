from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
from PyQt5.QtCore import Qt
from uuid import UUID # Importar UUID
import asyncio # Importar asyncio para iniciar tareas asíncronas

from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget
from src.ultibot_ui.widgets.chart_widget import ChartWidget # Importar ChartWidget
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
        
        # Iniciar la carga y suscripción de pares para market_data_widget
        asyncio.create_task(self.market_data_widget.load_and_subscribe_pairs())

        # Zona Central (con QSplitter horizontal)
        center_splitter = QSplitter(Qt.Orientation.Horizontal) # Usar Qt.Orientation
        center_splitter.setContentsMargins(0, 0, 0, 0)
        center_splitter.setChildrenCollapsible(False)

        # Panel Izquierdo (Placeholder para Estado del Portafolio)
        portfolio_area = QLabel("Panel Izquierdo: Estado del Portafolio")
        portfolio_area.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        portfolio_area.setStyleSheet("background-color: #1E1E1E; padding: 10px;")
        center_splitter.addWidget(portfolio_area)

        # Panel Derecho (Gráficos Financieros - ChartWidget)
        self.chart_widget = ChartWidget(self.user_id, self.market_data_service) # Pasar market_data_service
        center_splitter.addWidget(self.chart_widget)

        # Conectar señales del ChartWidget para solicitar datos al backend
        self.chart_widget.symbol_selected.connect(self._handle_chart_symbol_selection)
        self.chart_widget.interval_selected.connect(self._handle_chart_interval_selection)

        main_layout.addWidget(center_splitter)

        # Zona Inferior (con QSplitter vertical)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical) # Usar Qt.Orientation
        bottom_splitter.setContentsMargins(0, 0, 0, 0)
        bottom_splitter.setChildrenCollapsible(False)

        # Placeholder para el Centro de Notificaciones
        notifications_area = QLabel("Área Inferior: Centro de Notificaciones del Sistema")
        notifications_area.setAlignment(Qt.AlignmentFlag.AlignCenter) # Usar Qt.AlignmentFlag
        notifications_area.setStyleSheet("background-color: #2D2D2D; padding: 10px;")
        bottom_splitter.addWidget(notifications_area)

        # Añadir el splitter inferior al layout principal
        main_layout.addWidget(bottom_splitter)

        # Establecer tamaños iniciales para los splitters (opcional, para una mejor visualización inicial)
        # Estos valores pueden necesitar ajuste o ser dinámicos
        center_splitter.setSizes([self.width() // 3, 2 * self.width() // 3])
        # bottom_splitter.setSizes([self.height() // 4]) # No se puede usar self.height() aquí directamente

    def _handle_chart_symbol_selection(self, symbol: str):
        """Slot síncrono para la señal symbol_selected del ChartWidget."""
        print(f"Dashboard: Símbolo de gráfico seleccionado: {symbol}")
        asyncio.create_task(self._fetch_and_update_chart_data())

    def _handle_chart_interval_selection(self, interval: str):
        """Slot síncrono para la señal interval_selected del ChartWidget."""
        print(f"Dashboard: Temporalidad de gráfico seleccionada: {interval}")
        asyncio.create_task(self._fetch_and_update_chart_data())

    async def _fetch_and_update_chart_data(self):
        """
        Obtiene los datos de velas del backend y los pasa al ChartWidget.
        """
        if self.chart_widget.current_symbol and self.chart_widget.current_interval:
            try:
                candlestick_data = await self.market_data_service.get_candlestick_data(
                    user_id=self.user_id,
                    symbol=self.chart_widget.current_symbol,
                    interval=self.chart_widget.current_interval,
                    limit=200 # Cantidad de velas a mostrar
                )
                self.chart_widget.set_candlestick_data(candlestick_data)
            except Exception as e:
                print(f"Error al obtener datos de velas para el gráfico: {e}")
                self.chart_widget.set_candlestick_data([]) # Limpiar el gráfico en caso de error
                self.chart_widget.chart_area.setText(f"Error al cargar datos: {e}")
