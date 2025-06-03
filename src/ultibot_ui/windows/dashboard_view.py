import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QFrame, QTabWidget, QComboBox # Añadir QTabWidget y QComboBox
from PyQt5.QtCore import Qt, QTimer # Importar QTimer
from typing import Any, Optional, List, Callable, Tuple # Añadir importaciones de typing
from uuid import UUID # Importar UUID
import asyncio # Importar asyncio para iniciar tareas asíncronas

logger = logging.getLogger(__name__)

from src.shared.data_types import Notification, OpportunityStatus, Opportunity # Importar Notification, OpportunityStatus y Opportunity

from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget # Importar PortfolioWidget
from src.ultibot_ui.widgets.trading_mode_selector import TradingModeSelector, TradingModeStatusBar
from src.ultibot_ui.widgets.order_form_widget import OrderFormWidget
from src.ultibot_ui.widgets.real_trade_confirmation_dialog import RealTradeConfirmationDialog # Importar el nuevo diálogo
from src.ultibot_ui.services.api_client import UltiBotAPIClient # Importar el cliente API
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager

from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService # Importar SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService # Importar NotificationService
from src.ultibot_ui.widgets.notification_widget import NotificationWidget # Importar NotificationWidget
from src.ultibot_ui.widgets.strategy_performance_table_view import StrategyPerformanceTableView # Importar el nuevo widget

class DashboardView(QWidget):
    def __init__(self, user_id: UUID, market_data_service: MarketDataService, config_service: ConfigService, notification_service: NotificationService, persistence_service: SupabasePersistenceService, api_client: UltiBotAPIClient, trading_mode_service: TradingModeService): # Add trading_mode_service
        super().__init__()
        self.user_id = user_id
        self.market_data_service = market_data_service
        self.config_service = config_service
        self.notification_service = notification_service # Guardar la referencia al servicio de notificaciones
        self.persistence_service = persistence_service # Guardar la referencia al servicio de persistencia
        self.api_client = api_client # Guardar la referencia al cliente API
        self.trading_mode_service = trading_mode_service # Store TradingModeService
        
        # Get trading mode manager for state synchronization
        self.trading_mode_manager = get_trading_mode_manager()
        
        # Inicializar PortfolioService aquí, ya que DashboardView tiene sus dependencias
        self.portfolio_service = PortfolioService(self.market_data_service, self.persistence_service)
        
        self._setup_ui()
        
        # Iniciar la inicialización del portafolio de paper trading
        asyncio.create_task(self.portfolio_service.initialize_portfolio(self.user_id))
        # Iniciar la carga de notificaciones y la suscripción en tiempo real
        asyncio.create_task(self._load_and_subscribe_notifications())
        # Iniciar el monitoreo de oportunidades de trading real pendientes
        self._opportunity_monitor_timer = QTimer(self)
        self._opportunity_monitor_timer.setInterval(10000) # Chequear cada 10 segundos
        self._opportunity_monitor_timer.timeout.connect(self._on_opportunity_monitor_timeout)
        self._opportunity_monitor_timer.start()
        print("Monitor de oportunidades de trading real iniciado.")

        # Cargar datos de desempeño de estrategias
        asyncio.create_task(self._load_strategy_performance_data())

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # --- Header Area: Trading Mode Selector ---
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setMaximumHeight(60)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2C2C2C;
                border-bottom: 1px solid #444;
                margin: 0px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Dashboard title
        dashboard_title = QLabel("Dashboard - UltiBotInversiones")
        dashboard_title.setStyleSheet("color: #EEE; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(dashboard_title)
        
        # Spacer
        header_layout.addStretch()
        
        # Trading mode selector
        self.trading_mode_selector = TradingModeSelector(style="toggle")
        self.trading_mode_selector.mode_changed.connect(self._on_trading_mode_changed)
        header_layout.addWidget(self.trading_mode_selector)
        
        # Trading mode status bar
        self.mode_status_bar = TradingModeStatusBar()
        header_layout.addWidget(self.mode_status_bar)
        
        main_layout.addWidget(header_frame)

        # --- Top Area: Market Data Widget ---
        # This widget shows overall market tickers, favorite pairs, etc.
        self.market_data_widget = MarketDataWidget(self.user_id, self.market_data_service, self.config_service)
        main_layout.addWidget(self.market_data_widget)
        
        # Iniciar la carga y suscripción de pares para market_data_widget
        asyncio.create_task(self.market_data_widget.load_and_subscribe_pairs())

        # Zona Central (con QSplitter horizontal)
        center_splitter = QSplitter(Qt.Orientation.Horizontal)
        center_splitter.setContentsMargins(0, 0, 0, 0)
        center_splitter.setChildrenCollapsible(False)

        # Panel Izquierdo: Estado del Portafolio (PortfolioWidget)
        self.portfolio_widget = PortfolioWidget(user_id=self.user_id, 
                                                portfolio_service=self.portfolio_service, 
                                                trading_mode_service=self.trading_mode_service, 
                                                api_client=self.api_client)
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

        # Zona Inferior (con QSplitter vertical y QTabWidget)
        bottom_splitter = QSplitter(Qt.Orientation.Vertical) # Usar Qt.Orientation
        bottom_splitter.setContentsMargins(0, 0, 0, 0)
        bottom_splitter.setChildrenCollapsible(False)

        # Crear QTabWidget para la zona inferior
        bottom_tab_widget = QTabWidget()
        bottom_tab_widget.setMaximumHeight(300)  # Limitar altura para no dominar la pantalla
        
        # Pestaña de Notificaciones
        self.notification_widget = NotificationWidget(self.notification_service, self.user_id)
        bottom_tab_widget.addTab(self.notification_widget, "📢 Notificaciones")
        
        # Pestaña de Órdenes de Trading
        self.order_form_widget = OrderFormWidget(self.user_id, self.api_client)
        self.order_form_widget.order_executed.connect(self._handle_order_executed)
        self.order_form_widget.order_failed.connect(self._handle_order_failed)
        bottom_tab_widget.addTab(self.order_form_widget, "📈 Crear Orden")

        # Pestaña de Desempeño por Estrategia
        strategy_performance_tab_content = QWidget()
        strategy_performance_layout = QVBoxLayout(strategy_performance_tab_content)
        strategy_performance_layout.setContentsMargins(5, 5, 5, 5)

        # Controles de filtro para el desempeño de estrategias
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por Modo:"))
        self.performance_mode_filter_combo = QComboBox()
        self.performance_mode_filter_combo.addItems(["Todos", "Paper Trading", "Operativa Real"])
        self.performance_mode_filter_combo.currentIndexChanged.connect(self._on_performance_filter_changed)
        filter_layout.addWidget(self.performance_mode_filter_combo)
        filter_layout.addStretch()
        strategy_performance_layout.addLayout(filter_layout)

        self.strategy_performance_widget = StrategyPerformanceTableView()
        strategy_performance_layout.addWidget(self.strategy_performance_widget)
        
        bottom_tab_widget.addTab(strategy_performance_tab_content, "📊 Desempeño Estrategias")

        bottom_splitter.addWidget(bottom_tab_widget)

        # Añadir el splitter inferior al layout principal
        main_layout.addWidget(bottom_splitter)

        # Establecer tamaños iniciales para los splitters (opcional, para una mejor visualización inicial)
        # Estos valores pueden necesitar ajuste o ser dinámicos
        center_splitter.setSizes([self.width() // 3, 2 * self.width() // 3])
        # bottom_splitter.setSizes([self.height() // 4]) # No se puede usar self.height() aquí directamente

    def _on_trading_mode_changed(self, new_mode: str):
        """
        Handle trading mode changes from the selector.
        
        Args:
            new_mode: The new trading mode ('paper' or 'real')
        """
        logger.info(f"Dashboard: Trading mode changed to {new_mode}")
        
        # The portfolio widget should automatically update through its connection
        # to the trading mode state manager, but we can force a refresh if needed
        if hasattr(self.portfolio_widget, 'refresh_data'):
            self.portfolio_widget.refresh_data()
        
        # Recargar datos de desempeño de estrategias cuando cambia el modo global
        # También actualiza el filtro de desempeño si es relevante
        selected_filter_mode = self.performance_mode_filter_combo.currentText()
        if new_mode == 'paper' and selected_filter_mode != "Paper Trading":
            self.performance_mode_filter_combo.setCurrentText("Paper Trading")
        elif new_mode == 'real' and selected_filter_mode != "Operativa Real":
            self.performance_mode_filter_combo.setCurrentText("Operativa Real")
        else: # Si el modo global cambia a algo que no es paper/real o el filtro ya está en "Todos" o coincide
            asyncio.create_task(self._load_strategy_performance_data())


    def _on_performance_filter_changed(self, index: int):
        """
        Maneja el cambio en el ComboBox de filtro de modo de desempeño.
        """
        asyncio.create_task(self._load_strategy_performance_data())

    async def _load_strategy_performance_data(self):
        """
        Carga los datos de desempeño de las estrategias desde el backend y los muestra,
        utilizando el filtro de modo seleccionado en la UI.
        """
        try:
            selected_filter_text = self.performance_mode_filter_combo.currentText()
            mode_param_for_api: Optional[str] = None
            if selected_filter_text == "Paper Trading":
                mode_param_for_api = "paper"
            elif selected_filter_text == "Operativa Real":
                mode_param_for_api = "real"
            # Si es "Todos", mode_param_for_api permanece None, lo que implica "todos los modos" para el backend.

            logger.info(f"Cargando datos de desempeño de estrategias para el modo de filtro: {selected_filter_text} (API param: {mode_param_for_api})")
            
            performance_data = await self.api_client.get_strategy_performance(
                user_id=self.user_id,
                mode=mode_param_for_api
            )
            if performance_data is not None:
                self.strategy_performance_widget.set_data(performance_data)
                logger.info(f"Datos de desempeño de estrategias cargados y mostrados: {len(performance_data)} registros.")
            else:
                self.strategy_performance_widget.set_data([]) # Limpiar tabla si no hay datos
                logger.info("No se recibieron datos de desempeño de estrategias o fueron None.")
        except Exception as e:
            logger.error(f"Error al cargar datos de desempeño de estrategias: {e}", exc_info=True)
            self.strategy_performance_widget.set_data([]) # Limpiar tabla en caso de error
            # Considerar mostrar un mensaje de error en la UI, tal vez en la misma tabla o una notificación.

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
            
            # Si se obtuvieron notificaciones, es una buena oportunidad para actualizar el desempeño
            # Asumimos que alguna de estas notificaciones podría ser de un trade cerrado.
            if new_notifications:
                logger.info("Nuevas notificaciones recibidas, actualizando desempeño de estrategias.")
                await self._load_strategy_performance_data()
                
        except Exception as e:
            print(f"Error al hacer polling de nuevas notificaciones: {e}")
            # Manejar el error, quizás mostrando una notificación de error en la UI

    def _on_opportunity_monitor_timeout(self):
        """Slot síncrono para el QTimer que inicia la tarea asíncrona de monitoreo de oportunidades."""
        asyncio.create_task(self._check_pending_real_opportunities())

    async def _check_pending_real_opportunities(self):
        """
        Verifica si hay oportunidades de trading real pendientes de confirmación
        y abre el diálogo correspondiente.
        """
        try:
            opportunities_data = await self.api_client.get_real_trading_candidates()
            if opportunities_data:
                # Asumimos que el backend devuelve una lista de diccionarios, convertimos a objetos Opportunity
                opportunities = [Opportunity(**opp_data) for opp_data in opportunities_data]
                
                if opportunities:
                    # Tomar la primera oportunidad pendiente y mostrar el diálogo
                    opportunity_to_confirm = opportunities[0]
                    logger.info(f"Oportunidad pendiente de confirmación encontrada: {opportunity_to_confirm.id}")
                    
                    dialog = RealTradeConfirmationDialog(opportunity_to_confirm, self.api_client, self)
                    dialog.trade_confirmed.connect(self._handle_trade_confirmed)
                    dialog.trade_cancelled.connect(self._handle_trade_cancelled)
                    dialog.exec_() # Mostrar el diálogo de forma modal
                    
                    # Después de cerrar el diálogo, re-chequear oportunidades o actualizar UI
                    await self._refresh_opportunities_ui() # Método para actualizar la UI de oportunidades
                    await self._update_real_trades_count_ui() # Método para actualizar el contador
            else:
                logger.debug("No hay oportunidades de trading real pendientes de confirmación.")

        except Exception as e:
            logger.error(f"Error al verificar oportunidades de trading real pendientes: {e}", exc_info=True)
            # Podríamos mostrar una notificación de error en la UI

    async def _refresh_opportunities_ui(self):
        """
        Método placeholder para actualizar la UI de oportunidades.
        En una implementación real, esto recargaría el widget de oportunidades.
        """
        logger.info("Actualizando UI de oportunidades (placeholder).")
        # TODO: Implementar la lógica real para recargar el widget de oportunidades
        # Por ahora, solo loguea.

    async def _update_real_trades_count_ui(self):
        """
        Método para actualizar el contador de operaciones reales en la UI.
        """
        try:
            config_status = await self.api_client.get_real_trading_mode_status()
            if config_status and 'real_trades_executed_count' in config_status:
                count = config_status['real_trades_executed_count']
                max_trades = config_status['max_real_trades']
                logger.info(f"Contador de trades reales actualizado: {count}/{max_trades}")
                # TODO: Actualizar un QLabel o similar en la UI con este valor
            else:
                logger.warning("No se pudo obtener el contador de trades reales del backend.")
        except Exception as e:
            logger.error(f"Error al actualizar el contador de trades reales en UI: {e}", exc_info=True)

    def _handle_trade_confirmed(self, opportunity_id: str):
        logger.info(f"Trade real confirmado para oportunidad {opportunity_id}. Actualizando UI.")
        # Aquí se podría disparar una actualización más específica de la UI
        asyncio.create_task(self._refresh_opportunities_ui())
        asyncio.create_task(self._update_real_trades_count_ui())
        # Un trade confirmado podría llevar a un trade cerrado pronto, actualizar desempeño.
        asyncio.create_task(self._load_strategy_performance_data())

    def _handle_trade_cancelled(self, opportunity_id: str):
        logger.info(f"Trade real cancelado para oportunidad {opportunity_id}. No se requiere acción adicional en UI.")
        # Opcional: Actualizar el estado de la oportunidad en la UI a "rechazada por usuario" si se implementa en backend.
        asyncio.create_task(self._refresh_opportunities_ui()) # Refrescar por si el estado cambió en backend

    def _handle_order_executed(self, order_details: dict[str, Any]):
        """
        Maneja una orden ejecutada exitosamente desde el OrderFormWidget.
        
        Args:
            order_details: Detalles de la orden ejecutada
        """
        logger.info(f"Orden ejecutada exitosamente: {order_details}")
        
        # Forzar actualización del portfolio widget
        if hasattr(self.portfolio_widget, 'refresh_data'):
            self.portfolio_widget.refresh_data()
        
        # Actualizar desempeño de estrategias después de ejecutar una orden
        # (aunque la orden solo abre el trade, es un punto de cambio)
        asyncio.create_task(self._load_strategy_performance_data())
        
        # Mostrar notificación de éxito en el sistema de notificaciones
        symbol = order_details.get('symbol', 'N/A')
        side = order_details.get('side', 'N/A')
        quantity = order_details.get('quantity', 0)
        mode = order_details.get('trading_mode', 'unknown')
        
        success_message = f"✅ Orden {side} ejecutada: {quantity:.8f} {symbol} en modo {mode.title()}"
        
        # Crear una notificación "local" para mostrar el éxito
        # (esto podría integrarse con el sistema de notificaciones real)
        logger.info(success_message)

    def _handle_order_failed(self, error_message: str):
        """
        Maneja errores en la ejecución de órdenes desde el OrderFormWidget.
        
        Args:
            error_message: Mensaje de error
        """
        logger.error(f"Error en ejecución de orden: {error_message}")
        
        # Podrías mostrar una notificación de error en la UI
        # o registrarlo en el sistema de notificaciones

    def cleanup(self):
        """
        Limpia los recursos utilizados por DashboardView y sus widgets hijos.
        Principalmente, detiene temporizadores y tareas en segundo plano.
        """
        print("DashboardView: cleanup called.")

        # Limpiar MarketDataWidget
        if hasattr(self.market_data_widget, 'cleanup') and callable(self.market_data_widget.cleanup):
            print("DashboardView: Calling cleanup on market_data_widget.")
            self.market_data_widget.cleanup()
        
        # Limpiar PortfolioWidget
        if hasattr(self.portfolio_widget, 'stop_updates') and callable(self.portfolio_widget.stop_updates):
            print("DashboardView: Calling stop_updates on portfolio_widget.")
            self.portfolio_widget.stop_updates() # Asumiendo que stop_updates es el método de limpieza

        # Detener el temporizador de polling de notificaciones
        if hasattr(self, '_notification_polling_timer') and self._notification_polling_timer.isActive():
            print("DashboardView: Stopping notification polling timer.")
            self._notification_polling_timer.stop()

        # Detener el temporizador de monitoreo de oportunidades
        if hasattr(self, '_opportunity_monitor_timer') and self._opportunity_monitor_timer.isActive():
            print("DashboardView: Stopping opportunity monitor timer.")
            self._opportunity_monitor_timer.stop()

        # Limpiar NotificationWidget (si es necesario, por ejemplo, para cancelar suscripciones WebSocket)
        if hasattr(self.notification_widget, 'cleanup') and callable(self.notification_widget.cleanup):
            print("DashboardView: Calling cleanup on notification_widget.")
            self.notification_widget.cleanup()
            
        # Limpiar ChartWidget (si es necesario)
        if hasattr(self.chart_widget, 'cleanup') and callable(self.chart_widget.cleanup):
            print("DashboardView: Calling cleanup on chart_widget.")
            self.chart_widget.cleanup()
        
        # Limpiar OrderFormWidget (si es necesario)
        if hasattr(self.order_form_widget, 'cleanup') and callable(self.order_form_widget.cleanup):
            print("DashboardView: Calling cleanup on order_form_widget.")
            self.order_form_widget.cleanup()

        # Limpiar StrategyPerformanceTableView (si es necesario)
        if hasattr(self, 'strategy_performance_widget') and hasattr(self.strategy_performance_widget, 'cleanup') and callable(self.strategy_performance_widget.cleanup):
            print("DashboardView: Calling cleanup on strategy_performance_widget.")
            self.strategy_performance_widget.cleanup()
        
        print("DashboardView: cleanup finished.")
