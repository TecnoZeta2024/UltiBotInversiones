import logging
from typing import Optional, List, Dict, Any, Callable, Coroutine
from uuid import UUID
import asyncio

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

from src.shared.data_types import Trade
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.services.trading_mode_state import TradingModeStateManager
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.notification_widget import NotificationWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget
from src.ultibot_ui.widgets.magic_card_widget import (
    MagicCardWidget, PortfolioMagicCard, TradingMagicCard
)

logger = logging.getLogger(__name__)

class DashboardView(QWidget):
    """
    Vista principal del dashboard que integra varios widgets para mostrar
    información clave de trading.
    """
    initialization_complete = pyqtSignal(bool)

    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, trading_mode_manager: TradingModeStateManager, loop: asyncio.AbstractEventLoop, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.trading_mode_manager = trading_mode_manager
        self.loop = loop
        self._is_initialized = False
        self._pending_tasks = 0

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        self.setLayout(self.main_layout)

        self._setup_ui()
        self._initialize_async_components()

    def _setup_ui(self):
        """Configura la interfaz de usuario básica del dashboard usando Magic Cards."""
        # Importar layout horizontal para tarjetas principales
        from PyQt5.QtWidgets import QHBoxLayout
        
        # === MAGIC CARDS SECTION ===
        # Layout horizontal para las Magic Cards principales
        magic_cards_layout = QHBoxLayout()
        magic_cards_layout.setSpacing(20)
        
        # Portfolio Magic Card
        self.portfolio_magic_card = PortfolioMagicCard(self)
        self.portfolio_magic_card.card_clicked.connect(self._on_portfolio_card_clicked)
        magic_cards_layout.addWidget(self.portfolio_magic_card)
        
        # Trading Status Magic Card
        self.trading_magic_card = TradingMagicCard(self)
        self.trading_magic_card.card_clicked.connect(self._on_trading_card_clicked)
        magic_cards_layout.addWidget(self.trading_magic_card)
        
        # Performance Magic Card
        self.performance_magic_card = MagicCardWidget(
            title="Performance",
            subtitle="Today's trading performance",
            card_type="performance",
            parent=self
        )
        self.performance_magic_card.add_metric("Win Rate", "0%", "neutral")
        self.performance_magic_card.add_metric("Profit", "$0.00", "neutral")
        self.performance_magic_card.add_metric("Trades", "0", "neutral")
        self.performance_magic_card.card_clicked.connect(self._on_performance_card_clicked)
        magic_cards_layout.addWidget(self.performance_magic_card)
        
        # Añadir las Magic Cards al layout principal
        self.main_layout.addLayout(magic_cards_layout)
        
        # === WIDGETS EXISTENTES EN TARJETAS MODERNIZADAS ===
        # Portfolio widget (mantenemos funcionalidad existente)
        self.portfolio_widget = PortfolioWidget(self.user_id, self.main_window, self.api_client, self.trading_mode_manager, self.loop, self)
        
        # Chart widget en tarjeta moderna
        self.chart_widget = ChartWidget(self.main_window, self.api_client, self.loop, self)
        chart_card = QFrame()
        chart_card.setProperty("class", "magic-card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.addWidget(self.chart_widget)
        self.main_layout.addWidget(chart_card, 2)  # Mayor factor de stretch para el gráfico
        
        # Notification widget en tarjeta moderna
        self.notification_widget = NotificationWidget(self.user_id, self.main_window, self.api_client, self.loop, self)
        notification_card = QFrame()
        notification_card.setProperty("class", "magic-card")
        notification_layout = QVBoxLayout(notification_card)
        notification_layout.setContentsMargins(0, 0, 0, 0)
        notification_layout.addWidget(self.notification_widget)
        self.main_layout.addWidget(notification_card, 1)

    def _initialize_async_components(self):
        """Inicia la carga de datos asíncrona para los componentes del dashboard."""
        logger.info("DashboardView: _initialize_async_components INVOCADO")
        self._pending_tasks = 1

        coroutine_factory = lambda client: client.get_trades(trading_mode="both")
        
        self.main_window.submit_task(
            coroutine_factory,
            self._on_performance_loaded,
            self._on_load_error("desempeño de estrategias")
        )

    def _check_initialization_complete(self):
        """Verifica si todas las tareas de inicialización han finalizado."""
        self._pending_tasks -= 1
        if self._pending_tasks <= 0 and not self._is_initialized:
            self._is_initialized = True
            self.initialization_complete.emit(True)
            logger.info("DashboardView: Inicialización de componentes asíncronos completada.")
            
            self.portfolio_widget.refresh_data()
            # self.chart_widget.enter_view() # No existe, se carga al iniciar
            # self.notification_widget.enter_view() # No existe

    def _on_performance_loaded(self, trades: List[Trade]):
        """Maneja la carga exitosa de datos de desempeño."""
        logger.info(f"DashboardView: {len(trades)} trades cargados para el análisis de desempeño.")
        self._check_initialization_complete()

    def _on_load_error(self, component_name: str) -> Callable[[str], None]:
        """Crea un manejador de errores para un componente específico."""
        def handler(error_msg: str):
            logger.error(f"DashboardView: Error al cargar {component_name}: {error_msg}", exc_info=True)
            self._check_initialization_complete()
        return handler

    def _on_portfolio_card_clicked(self, card_type: str):
        """Maneja el click en la Magic Card del portafolio."""
        logger.info(f"Portfolio Magic Card clicked: {card_type}")
        # Navegar a la vista detallada del portafolio
        self.main_window.navigate_to("portfolio")
        
    def _on_trading_card_clicked(self, card_type: str):
        """Maneja el click en la Magic Card de trading."""
        logger.info(f"Trading Magic Card clicked: {card_type}")
        # Navegar a la vista de estrategias o configuración de trading
        self.main_window.navigate_to("strategies")
        
    def _on_performance_card_clicked(self, card_type: str):
        """Maneja el click en la Magic Card de performance."""
        logger.info(f"Performance Magic Card clicked: {card_type}")
        # Navegar a la vista de historial
        self.main_window.navigate_to("history")
        
    def update_magic_cards_data(self):
        """Actualiza los datos en las Magic Cards con información real."""
        try:
            # Actualizar Portfolio Magic Card
            if hasattr(self.portfolio_widget, 'get_portfolio_summary'):
                portfolio_data = self.portfolio_widget.get_portfolio_summary()
                if portfolio_data:
                    self.portfolio_magic_card.update_portfolio_data(
                        total_value=portfolio_data.get('total_value', 0.0),
                        change_24h=portfolio_data.get('change_24h', 0.0),
                        pnl=portfolio_data.get('pnl', 0.0)
                    )
            
            # Actualizar Trading Magic Card
            trading_mode = self.trading_mode_manager.get_current_mode() if self.trading_mode_manager else "Simulado"
            active_trades = 0  # TODO: Obtener número real de trades activos
            daily_trades = 0   # TODO: Obtener número real de trades del día
            
            self.trading_magic_card.update_trading_data(
                mode=trading_mode,
                active_trades=active_trades,
                daily_trades=daily_trades
            )
            
            # Actualizar Performance Magic Card
            # TODO: Integrar con datos reales de performance
            self.performance_magic_card.update_content(
                title="Performance",
                subtitle="Today's trading performance"
            )
            
        except Exception as e:
            logger.error(f"Error updating Magic Cards data: {e}")

    def cleanup(self):
        """Detiene todos los hilos y tareas activas."""
        logger.info("DashboardView: Iniciando limpieza de tareas.")
        
        # Cleanup de widgets existentes
        if hasattr(self.portfolio_widget, 'cleanup'): 
            self.portfolio_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup'): 
            self.chart_widget.cleanup()
        if hasattr(self.notification_widget, 'cleanup'): 
            self.notification_widget.cleanup()
            
        # Cleanup de Magic Cards
        if hasattr(self, 'portfolio_magic_card'):
            self.portfolio_magic_card.spotlight_timer.stop()
        if hasattr(self, 'trading_magic_card'):
            self.trading_magic_card.spotlight_timer.stop()
        if hasattr(self, 'performance_magic_card'):
            self.performance_magic_card.spotlight_timer.stop()

        logger.info("DashboardView: Limpieza completada.")
