from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel
from PyQt5.QtCore import Qt, QTimer # Importar QTimer
from uuid import UUID # Importar UUID
import asyncio # Importar asyncio para iniciar tareas asíncronas

from src.shared.data_types import Notification # Importar Notification

from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget # Importar PortfolioWidget
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.ultibot_ui.widgets.notification_widget import NotificationWidget # Importar NotificationWidget

class DashboardView(QWidget):
    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService, notification_service: NotificationService): # Añadir notification_service
        super().__init__()
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.notification_service = notification_service # Guardar la referencia al servicio de notificaciones
        
        # Inicializar PortfolioService aquí, ya que DashboardView tiene sus dependencias
        self.portfolio_service = PortfolioService(self.market_data_service, self.config_service)
        
        self._setup_ui()
        
        # Iniciar la inicialización del portafolio de paper trading
        asyncio.create_task(self.portfolio_service.initialize_portfolio(self.user_id))
        # Iniciar la carga de notificaciones y la suscripción en tiempo real
        asyncio.create_task(self._load_and_subscribe_notifications())

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
        center_splitter = QSplitter(Qt.Orientation.Horizontal)
        center_splitter.setContentsMargins(0, 0, 0, 0)
        center_splitter.setChildrenCollapsible(False)

        # Panel Izquierdo: Estado del Portafolio (PortfolioWidget)
        self.portfolio_widget = PortfolioWidget(self.user_id, self.portfolio_service)
        center_splitter.addWidget(self.portfolio_widget)
        
        # Iniciar las actualizaciones del portfolio_widget
        self.portfolio_widget.start_updates()

        # Panel Derecho (Gráficos Financieros - ChartWidget)
        self.chart_widget = ChartWidget(self.user_id, self.market_data_service)
        center_splitter.addWidget(self.chart_widget)

        # Conectar señales del ChartWidget para solicitar datos al backend
        self.chart_widget.symbol_selected.connect(self._handle_chart_symbol_selection)
        self.chart_widget.interval_selected.connect(self._handle_chart_interval_selection)

        main_layout.addWidget(center_splitter)

        # Zona Inferior (con QSplitter vertical)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical) # Usar Qt.Orientation
        bottom_splitter.setContentsMargins(0, 0, 0, 0)
        bottom_splitter.setChildrenCollapsible(False)

        # Reemplazar con NotificationWidget
        self.notification_widget = NotificationWidget(self.notification_service, self.user_id) # Pasar notification_service y user_id
        bottom_splitter.addWidget(self.notification_widget)

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

    async def _load_and_subscribe_notifications(self):
        """
        Carga el historial de notificaciones y configura la suscripción en tiempo real.
        """
        try:
            # Cargar historial de notificaciones
            history_notifications = await self.notification_service.get_notification_history(self.user_id)
            for notification in history_notifications:
                # notification_data ya es un objeto Notification
                self.notification_widget.add_notification(notification)
            
            # TODO: Implementar suscripción a WebSockets para notificaciones en tiempo real
            # Por ahora, un polling simple como fallback
            self._notification_polling_timer = QTimer(self)
            self._notification_polling_timer.setInterval(30000) # Polling cada 30 segundos
            self._notification_polling_timer.timeout.connect(self._on_notification_polling_timeout)
            self._notification_polling_timer.start()
            print("Polling de notificaciones iniciado.")

        except Exception as e:
            print(f"Error al cargar o suscribir notificaciones: {e}")
            # Podríamos añadir una notificación de error al propio widget de notificaciones
            # o a un sistema de logs de UI.

    def _on_notification_polling_timeout(self):
        """Slot síncrono para el QTimer que inicia la tarea asíncrona de polling de notificaciones."""
        asyncio.create_task(self._fetch_new_notifications())

    async def _fetch_new_notifications(self):
        """Obtiene nuevas notificaciones del backend y las añade al widget."""
        try:
            # En una implementación real, esto podría ser un endpoint para "nuevas notificaciones desde X timestamp"
            # Por simplicidad, aquí solo cargamos el historial de nuevo, lo cual no es eficiente para "nuevas"
            # pero sirve para el propósito de demostración de polling.
            # La lógica de add_notification ya maneja duplicados.
            new_notifications = await self.notification_service.get_notification_history(self.user_id)
            for notification in new_notifications:
                self.notification_widget.add_notification(notification)
        except Exception as e:
            print(f"Error al hacer polling de nuevas notificaciones: {e}")
            # Manejar el error, quizás mostrando una notificación de error en la UI
