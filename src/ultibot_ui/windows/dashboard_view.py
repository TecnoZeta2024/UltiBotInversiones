import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QFrame, QTabWidget, QComboBox, QMessageBox # Añadir QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread # Importar QTimer, pyqtSignal y QThread
from typing import Any, Optional, List, Callable, Tuple, Coroutine, Dict # Añadir Dict
from datetime import datetime
from uuid import UUID
import asyncio # Importar asyncio para obtener el bucle de eventos

logger = logging.getLogger(__name__) # Mover logger antes del try-except

try:
    import sip # type: ignore
except ImportError:
    logger.warning("Módulo 'sip' no encontrado. Algunas comprobaciones de estado de widgets podrían no funcionar.")
    sip = None # Fallback si sip no está disponible


from src.shared.data_types import Notification, OpportunityStatus, Opportunity

from src.ultibot_ui.widgets.market_data_widget import MarketDataWidget
from src.ultibot_ui.widgets.chart_widget import ChartWidget
from src.ultibot_ui.widgets.portfolio_widget import PortfolioWidget
from src.ultibot_ui.widgets.trading_mode_selector import TradingModeSelector, TradingModeStatusBar
from src.ultibot_ui.widgets.order_form_widget import OrderFormWidget
from src.ultibot_ui.widgets.real_trade_confirmation_dialog import RealTradeConfirmationDialog
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager

from src.ultibot_ui.widgets.notification_widget import NotificationWidget
from src.ultibot_ui.widgets.strategy_performance_table_view import StrategyPerformanceTableView

class DashboardView(QWidget):
    initialization_complete = pyqtSignal()
    notifications_history_fetched = pyqtSignal(list)
    new_notifications_fetched = pyqtSignal(list)
    strategy_performance_fetched = pyqtSignal(list)
    real_opportunities_fetched = pyqtSignal(list)
    real_trades_count_fetched = pyqtSignal(dict)
    dashboard_api_error = pyqtSignal(str)

    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient):
        super().__init__()
        self.user_id = user_id
        self.api_client = api_client
        self.trading_mode_manager = get_trading_mode_manager()
        self.active_api_workers = [] # Para mantener referencia a los workers y threads

        self._setup_ui()
        
        # Conectar señales a manejadores
        self.notifications_history_fetched.connect(self._handle_notifications_history_result)
        self.new_notifications_fetched.connect(self._handle_new_notifications_result)
        self.strategy_performance_fetched.connect(self._handle_strategy_performance_result)
        self.real_opportunities_fetched.connect(self._handle_real_opportunities_result)
        self.real_trades_count_fetched.connect(self._handle_real_trades_count_result)
        self.dashboard_api_error.connect(self._handle_dashboard_api_error)

        self._opportunity_monitor_timer = QTimer(self)
        self._opportunity_monitor_timer.setInterval(10000)
        self._opportunity_monitor_timer.timeout.connect(self._on_opportunity_monitor_timeout)
        self._opportunity_monitor_timer.start()
        logger.info("Monitor de oportunidades de trading real iniciado.")

        # Iniciar la carga de componentes asíncronos
        # Programar la corutina para que se ejecute en el bucle de eventos de qasync
        # Esto evita bloquear el constructor y permite que el bucle de eventos de Qt se inicie.
        QTimer.singleShot(0, self._start_initialization_task)

    def _start_initialization_task(self):
        """Inicia la tarea asíncrona de inicialización de componentes."""
        asyncio.create_task(self._initialize_async_components())

    def _run_api_worker_and_await_result(self, coroutine_factory: Callable[[], Coroutine]) -> Any:
        """
        Ejecuta una corutina (a través de una factory) en un ApiWorker y espera su resultado.
        Retorna un Future que se puede await.
        """
        from src.ultibot_ui.main import ApiWorker # Importar localmente
        import qasync # Importar qasync para obtener el bucle de eventos

        qasync_loop = asyncio.get_event_loop()
        future = qasync_loop.create_future()

        worker = ApiWorker(coroutine_factory=coroutine_factory, qasync_loop=qasync_loop)
        thread = QThread()
        self.active_api_workers.append((worker, thread))

        worker.moveToThread(thread)

        def _on_result(result):
            if not future.done():
                qasync_loop.call_soon_threadsafe(future.set_result, result)
        def _on_error(error_msg):
            if not future.done():
                qasync_loop.call_soon_threadsafe(future.set_exception, Exception(error_msg))
        
        worker.result_ready.connect(_on_result)
        worker.error_occurred.connect(_on_error)
        
        thread.started.connect(worker.run)

        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_api_workers.remove((worker, thread)) if (worker, thread) in self.active_api_workers else None)

        thread.start()
        return future

    async def _initialize_async_components(self):
        """Carga los componentes asíncronos iniciales, intentando paralelizar llamadas independientes."""
        logger.info("DashboardView: _initialize_async_components INVOCADO (v5 - Paralelizado)")
        logger.info("Iniciando carga de componentes asíncronos...")
        all_components_loaded_successfully = True
        
        try:
            # Tareas a ejecutar en paralelo
            tasks_to_gather = []

            # 1. Tarea para cargar notificaciones
            logger.info("DashboardView: Programando carga de notificaciones...")
            # Se añade un límite razonable para la carga inicial de notificaciones.
            notifications_task = self._run_api_worker_and_await_result(
                lambda: self.api_client.get_notification_history(user_id=self.user_id, limit=20) 
            )
            tasks_to_gather.append(notifications_task)

            # 2. Tarea para cargar datos de desempeño de estrategias
            logger.info("DashboardView: Programando carga de desempeño de estrategias...")
            selected_filter_text = self.performance_mode_filter_combo.currentText()
            mode_param_for_api: Optional[str] = None
            if selected_filter_text == "Paper Trading":
                mode_param_for_api = "paper"
            elif selected_filter_text == "Operativa Real":
                mode_param_for_api = "real"
            
            strategy_performance_task = self._run_api_worker_and_await_result(
                lambda: self.api_client.get_strategy_performance(
                    user_id=self.user_id,
                    mode=mode_param_for_api
                )
            )
            tasks_to_gather.append(strategy_performance_task)

            # Ejecutar tareas en paralelo y obtener resultados
            logger.info(f"DashboardView: Ejecutando {len(tasks_to_gather)} tareas en paralelo...")
            # Usamos return_exceptions=True para manejar errores individuales sin detener todo el gather
            results = await asyncio.gather(*tasks_to_gather, return_exceptions=True)
            logger.info("DashboardView: Tareas en paralelo completadas.")

            # Procesar resultados
            # Resultado de notificaciones
            history_notifications_data = results[0]
            if isinstance(history_notifications_data, Exception):
                logger.error(f"DashboardView: Error al cargar notificaciones: {history_notifications_data}", exc_info=history_notifications_data)
                self.dashboard_api_error.emit(f"Error al cargar notificaciones: {history_notifications_data}")
                all_components_loaded_successfully = False
            elif history_notifications_data is not None: # Asegurarse que no es None si no hubo excepción
                self.notifications_history_fetched.emit(history_notifications_data)
                logger.info("DashboardView: Carga de notificaciones COMPLETADA.")
            else: # Caso donde no es excepción pero es None (inesperado para _run_api_worker_and_await_result)
                logger.warning("DashboardView: Carga de notificaciones devolvió None sin excepción.")
                all_components_loaded_successfully = False


            # Resultado de desempeño de estrategias
            performance_data = results[1]
            if isinstance(performance_data, Exception):
                logger.error(f"DashboardView: Error al cargar desempeño de estrategias: {performance_data}", exc_info=performance_data)
                self.dashboard_api_error.emit(f"Error al cargar desempeño de estrategias: {performance_data}")
                all_components_loaded_successfully = False
            elif performance_data is not None:
                self.strategy_performance_fetched.emit(performance_data)
                logger.info("DashboardView: Carga de desempeño de estrategias COMPLETADA.")
            else: # Caso donde no es excepción pero es None
                logger.warning("DashboardView: Carga de desempeño de estrategias devolvió None sin excepción.")
                all_components_loaded_successfully = False

            # 3. Cargar configuración inicial de MarketDataWidget (se ejecuta después de las paralelas)
            # Esta llamada ya es no bloqueante internamente en MarketDataWidget.
            if hasattr(self.market_data_widget, 'load_initial_configuration') and callable(self.market_data_widget.load_initial_configuration):
                logger.info("DashboardView: Iniciando market_data_widget.load_initial_configuration (no-bloqueante)...")
                try:
                    self.market_data_widget.load_initial_configuration()
                    logger.info("DashboardView: market_data_widget.load_initial_configuration INICIADO.")
                except Exception as e_market:
                    logger.error(f"DashboardView: Error al iniciar market_data_widget.load_initial_configuration: {e_market}", exc_info=True)
                    self.dashboard_api_error.emit(f"Error al iniciar carga de MarketData: {e_market}")
                    # Considerar si este error debe afectar all_components_loaded_successfully
                    # Por ahora, no lo hace ya que es una carga "fire and forget" desde la perspectiva de este método.
            else:
                logger.info("DashboardView: market_data_widget.load_initial_configuration no disponible o no es llamable.")

            if all_components_loaded_successfully:
                logger.info("DashboardView: Carga paralela de componentes asíncronos principales completada exitosamente.")
            else:
                logger.warning("DashboardView: Carga paralela de componentes asíncronos principales completada, PERO con errores en uno o más componentes.")

        except Exception as e: # Captura errores de asyncio.gather u otros errores inesperados aquí.
            logger.error(f"DashboardView: Error INESPERADO durante la inicialización asíncrona: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error inesperado durante la inicialización: {e}")
            all_components_loaded_successfully = False
        finally:
            logger.info(f"DashboardView: Emitiendo initialization_complete. Estado de carga exitosa: {all_components_loaded_successfully}")
            if sip and sip.isdeleted(self): 
                logger.warning("DashboardView: El objeto ya fue eliminado, no se emitirá initialization_complete.")
                return
            
            self.initialization_complete.emit()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setMaximumHeight(60)
        header_frame.setStyleSheet("QFrame { background-color: #2C2C2C; border-bottom: 1px solid #444; margin: 0px; }")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        dashboard_title = QLabel("Dashboard - UltiBotInversiones")
        dashboard_title.setStyleSheet("color: #EEE; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(dashboard_title)
        header_layout.addStretch()
        self.trading_mode_selector = TradingModeSelector(style="toggle")
        self.trading_mode_selector.mode_changed.connect(self._on_trading_mode_changed)
        header_layout.addWidget(self.trading_mode_selector)
        self.mode_status_bar = TradingModeStatusBar()
        header_layout.addWidget(self.mode_status_bar)
        main_layout.addWidget(header_frame)

        self.market_data_widget = MarketDataWidget(self.user_id, self.api_client)
        main_layout.addWidget(self.market_data_widget)
        
        center_splitter = QSplitter(Qt.Orientation.Horizontal)
        center_splitter.setContentsMargins(0, 0, 0, 0)
        center_splitter.setChildrenCollapsible(False)
        self.portfolio_widget = PortfolioWidget(self.user_id, self.api_client)
        center_splitter.addWidget(self.portfolio_widget)
        self.portfolio_widget.start_updates()
        self.chart_widget = ChartWidget(self.user_id, self.api_client)
        center_splitter.addWidget(self.chart_widget)
        self.chart_widget.symbol_selected.connect(self._handle_chart_symbol_selection)
        self.chart_widget.interval_selected.connect(self._handle_chart_interval_selection)
        main_layout.addWidget(center_splitter)

        bottom_splitter = QSplitter(Qt.Orientation.Vertical)
        bottom_splitter.setContentsMargins(0, 0, 0, 0)
        bottom_splitter.setChildrenCollapsible(False)
        bottom_tab_widget = QTabWidget()
        bottom_tab_widget.setMaximumHeight(300)
        qasync_loop_for_notifications = asyncio.get_event_loop()
        self.notification_widget = NotificationWidget(api_client=self.api_client, user_id=self.user_id, qasync_loop=qasync_loop_for_notifications)
        bottom_tab_widget.addTab(self.notification_widget, "📢 Notificaciones")
        self.order_form_widget = OrderFormWidget(self.user_id, self.api_client)
        self.order_form_widget.order_executed.connect(self._handle_order_executed)
        self.order_form_widget.order_failed.connect(self._handle_order_failed)
        bottom_tab_widget.addTab(self.order_form_widget, "📈 Crear Orden")
        strategy_performance_tab_content = QWidget()
        strategy_performance_layout = QVBoxLayout(strategy_performance_tab_content)
        strategy_performance_layout.setContentsMargins(5, 5, 5, 5)
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
        main_layout.addWidget(bottom_splitter)
        center_splitter.setSizes([self.width() // 3, 2 * self.width() // 3])

    def _on_trading_mode_changed(self, new_mode: str):
        logger.info(f"Dashboard: Trading mode changed to {new_mode}")
        if hasattr(self.portfolio_widget, 'refresh_data'):
            self.portfolio_widget.refresh_data()
        selected_filter_mode = self.performance_mode_filter_combo.currentText()
        if new_mode == 'paper' and selected_filter_mode != "Paper Trading":
            self.performance_mode_filter_combo.setCurrentText("Paper Trading")
        elif new_mode == 'real' and selected_filter_mode != "Operativa Real":
            self.performance_mode_filter_combo.setCurrentText("Operativa Real")
        else:
            # Llamada refactorizada
            self._load_strategy_performance_data()

    def _on_performance_filter_changed(self, index: int):
        # Llamada refactorizada
        self._load_strategy_performance_data()

    def _handle_strategy_performance_result(self, performance_data: List[Dict[str, Any]]):
        """Manejador para los datos de desempeño de estrategias."""
        if performance_data is not None:
            self.strategy_performance_widget.set_data(performance_data)
            logger.info(f"DashboardView._handle_strategy_performance_result: Datos de desempeño ({len(performance_data)} registros) establecidos en el widget.")
        else:
            self.strategy_performance_widget.set_data([])
            logger.info("DashboardView._handle_strategy_performance_result: No se recibieron datos de desempeño (None), tabla limpiada.")

    def _load_strategy_performance_data(self):
        logger.info("DashboardView._load_strategy_performance_data: INICIO (refactorizado)")
        try:
            selected_filter_text = self.performance_mode_filter_combo.currentText()
            mode_param_for_api: Optional[str] = None
            if selected_filter_text == "Paper Trading":
                mode_param_for_api = "paper"
            elif selected_filter_text == "Operativa Real":
                mode_param_for_api = "real"
            
            logger.info(f"DashboardView._load_strategy_performance_data: Filtro seleccionado: '{selected_filter_text}', Parámetro API: '{mode_param_for_api}'")
            
            # Ejecutar la corutina a través de ApiWorker
            # No await aquí, el resultado se emitirá a través de la señal
            self._run_api_worker_and_await_result(
                lambda: self.api_client.get_strategy_performance(
                    user_id=self.user_id,
                    mode=mode_param_for_api
                )
            ).add_done_callback(
                lambda f: self.strategy_performance_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("DashboardView._load_strategy_performance_data: Llamada a api_client.get_strategy_performance programada.")

        except Exception as e:
            logger.error(f"DashboardView._load_strategy_performance_data: Error inesperado al programar la carga de datos de desempeño: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error al programar carga de desempeño: {e}")
        finally:
            logger.info("DashboardView._load_strategy_performance_data: FIN (programación)")

    def _handle_chart_symbol_selection(self, symbol: str):
        print(f"Dashboard: Símbolo de gráfico seleccionado: {symbol}")
        # La lógica de carga de datos del gráfico ya está en ChartWidget, que usa ApiWorker.
        # Solo necesitamos llamar a su método de carga.
        self.chart_widget.load_chart_data()

    def _handle_chart_interval_selection(self, interval: str):
        print(f"Dashboard: Temporalidad de gráfico seleccionada: {interval}")
        # La lógica de carga de datos del gráfico ya está en ChartWidget, que usa ApiWorker.
        # Solo necesitamos llamar a su método de carga.
        self.chart_widget.load_chart_data()

    # _fetch_and_update_chart_data ya no es necesario aquí, ChartWidget lo maneja.
    # async def _fetch_and_update_chart_data(self):
    #     pass 

    def _handle_notifications_history_result(self, history_notifications_data: List[Dict[str, Any]]):
        """Manejador para los datos de historial de notificaciones."""
        logger.info("DashboardView._handle_notifications_history_result: INICIO")
        if history_notifications_data:
            logger.info(f"DashboardView._handle_notifications_history_result: Recibidas {len(history_notifications_data)} notificaciones del historial.")
            notifications = []
            for data_item in history_notifications_data:
                if not isinstance(data_item, dict):
                    logger.warning(f"Item de notificación (historial) no es un diccionario: {data_item}")
                    continue
                try:
                    user_id_value = None
                    user_id_from_data = data_item.get("userId")
                    if user_id_from_data:
                        try:
                            user_id_value = UUID(user_id_from_data)
                        except ValueError:
                            logger.warning(f"Item de notificación (historial) tiene 'userId' inválido para UUID: {user_id_from_data}. Se usará None.")
                    
                    notification_args = {
                        "userId": user_id_value,
                        "eventType": data_item.get("eventType", "DEFAULT_EVENT"),
                        "channel": data_item.get("channel", "ui"),
                        "title": data_item.get("title", "Notificación sin título"),
                        "message": data_item.get("message", "Mensaje no disponible."),
                        "priority": data_item.get("priority"),
                        "status": data_item.get("status", "new"),
                        "createdAt": data_item.get("createdAt", datetime.utcnow()),
                        "titleKey": data_item.get("titleKey"),
                        "messageKey": data_item.get("messageKey"),
                        "messageParams": data_item.get("messageParams"),
                        "snoozedUntil": data_item.get("snoozedUntil"),
                        "dataPayload": data_item.get("dataPayload"),
                        "actions": data_item.get("actions"),
                        "correlationId": data_item.get("correlationId"),
                        "isSummary": data_item.get("isSummary"),
                        "summarizedNotificationIds": data_item.get("summarizedNotificationIds"),
                        "readAt": data_item.get("readAt"),
                        "sentAt": data_item.get("sentAt"),
                        "statusHistory": data_item.get("statusHistory"),
                        "generatedBy": data_item.get("generatedBy")
                    }
                    
                    notification_id_str = data_item.get("id")
                    if notification_id_str:
                        try:
                            notification_args["id"] = UUID(notification_id_str)
                        except ValueError:
                            logger.warning(f"Item de notificación (historial) tiene 'id' inválido para UUID: {notification_id_str}. Se usará el default_factory.")
                    
                    summarized_ids_raw = data_item.get("summarizedNotificationIds")
                    if isinstance(summarized_ids_raw, list):
                        valid_summarized_ids = []
                        for s_id_raw in summarized_ids_raw:
                            try:
                                valid_summarized_ids.append(UUID(str(s_id_raw)))
                            except ValueError:
                                logger.warning(f"ID resumido inválido '{s_id_raw}' en summarizedNotificationIds (historial), será omitido.")
                        notification_args["summarizedNotificationIds"] = valid_summarized_ids
                    elif summarized_ids_raw is not None:
                        logger.warning(f"summarizedNotificationIds (historial) no es una lista: {summarized_ids_raw}. Se establecerá a None.")
                        notification_args["summarizedNotificationIds"] = None

                    for date_field_key in ["createdAt", "snoozedUntil", "readAt", "sentAt"]:
                        if date_field_key in notification_args and isinstance(notification_args[date_field_key], str):
                        # if date_field_key in notification_args and notification_args[date_field_key] is not None: # Esto es más robusto
                            try:
                                dt_str = notification_args[date_field_key]
                                if dt_str and isinstance(dt_str, str): # Asegurarse de que no es None y es string
                                    if dt_str.endswith('Z'):
                                        dt_str = dt_str[:-1] + '+00:00'
                                    notification_args[date_field_key] = datetime.fromisoformat(dt_str)
                                else:
                                    notification_args[date_field_key] = None # Si no es string o es None, establecer a None
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir '{notification_args[date_field_key]}' a datetime para el campo '{date_field_key}' (historial). Se usará None o el valor por defecto.")
                                notification_args[date_field_key] = None
                    
                    logger.debug(f"DashboardView (historial): Argumentos finales para Notification: {notification_args}")
                    notification_obj = Notification(**notification_args)
                    notifications.append(notification_obj)
                except TypeError as te:
                    logger.error(f"Error de tipo al crear Notification (historial) con datos {data_item} y args procesados {notification_args}: {te}", exc_info=True)
                    continue
                except Exception as ex_inner:
                    logger.error(f"Error inesperado al procesar item de notificación (historial) {data_item}: {ex_inner}", exc_info=True)
                    continue
            
            for notification in notifications:
                self.notification_widget.add_notification(notification)
        
        if not hasattr(self, '_notification_polling_timer') or not self._notification_polling_timer.isActive():
            self._notification_polling_timer = QTimer(self)
            self._notification_polling_timer.setInterval(30000)
            self._notification_polling_timer.timeout.connect(self._on_notification_polling_timeout)
            self._notification_polling_timer.start()
            logger.info("DashboardView._handle_notifications_history_result: Polling de notificaciones iniciado/verificado.")
        else:
            logger.info("DashboardView._handle_notifications_history_result: Polling de notificaciones ya estaba activo.")
        logger.info("DashboardView._handle_notifications_history_result: FIN")

    def _load_and_subscribe_notifications(self):
        # Pylance puede mostrar "Argument missing for parameter 'user_id'" aquí.
        # Esto es un falso positivo. 'user_id' se pasa correctamente a api_client.get_notification_history
        # desde self.user_id, que es un atributo de la instancia DashboardView.
        logger.info("DashboardView._load_and_subscribe_notifications: INICIO (refactorizado)")
        try:
            self._run_api_worker_and_await_result(
                lambda: self.api_client.get_notification_history(user_id=self.user_id)
            ).add_done_callback(
                lambda f: self.notifications_history_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("DashboardView._load_and_subscribe_notifications: Llamada a api_client.get_notification_history programada.")
        except Exception as e:
            logger.error(f"DashboardView._load_and_subscribe_notifications: Error inesperado al programar la carga de notificaciones: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error al programar carga de notificaciones: {e}")
        finally:
            logger.info("DashboardView._load_and_subscribe_notifications: FIN (programación)")

    def _handle_new_notifications_result(self, new_notifications_data: List[Dict[str, Any]]):
        """Manejador para los datos de nuevas notificaciones."""
        logger.info("DashboardView._handle_new_notifications_result: INICIO")
        if new_notifications_data:
            notifications = []
            for data_item in new_notifications_data:
                if not isinstance(data_item, dict):
                    logger.warning(f"Item de notificación (polling) no es un diccionario: {data_item}")
                    continue
                try:
                    user_id_value_polling = None
                    user_id_from_data_polling = data_item.get("userId")
                    if user_id_from_data_polling:
                        try:
                            user_id_value_polling = UUID(user_id_from_data_polling)
                        except ValueError:
                            logger.warning(f"Item de notificación (polling) tiene 'userId' inválido para UUID: {user_id_from_data_polling}. Se usará None.")

                    notification_args = {
                        "userId": user_id_value_polling,
                        "eventType": data_item.get("eventType", "DEFAULT_EVENT"),
                        "channel": data_item.get("channel", "ui"),
                        "title": data_item.get("title", "Notificación sin título"),
                        "message": data_item.get("message", "Mensaje no disponible."),
                        "priority": data_item.get("priority"),
                        "status": data_item.get("status", "new"),
                        "createdAt": data_item.get("createdAt", datetime.utcnow()),
                        "titleKey": data_item.get("titleKey"),
                        "messageKey": data_item.get("messageKey"),
                        "messageParams": data_item.get("messageParams"),
                        "snoozedUntil": data_item.get("snoozedUntil"),
                        "dataPayload": data_item.get("dataPayload"),
                        "actions": data_item.get("actions"),
                        "correlationId": data_item.get("correlationId"),
                        "isSummary": data_item.get("isSummary"),
                        "summarizedNotificationIds": data_item.get("summarizedNotificationIds"),
                        "readAt": data_item.get("readAt"),
                        "sentAt": data_item.get("sentAt"),
                        "statusHistory": data_item.get("statusHistory"),
                        "generatedBy": data_item.get("generatedBy")
                    }

                    notification_id_str_polling = data_item.get("id")
                    if notification_id_str_polling:
                        try:
                            notification_args["id"] = UUID(notification_id_str_polling)
                        except ValueError:
                            logger.warning(f"Item de notificación (polling) tiene 'id' inválido para UUID: {notification_id_str_polling}. Se usará el default_factory.")

                    summarized_ids_raw_polling = data_item.get("summarizedNotificationIds")
                    if isinstance(summarized_ids_raw_polling, list):
                        valid_summarized_ids_polling = []
                        for s_id_raw_polling in summarized_ids_raw_polling:
                            try:
                                valid_summarized_ids_polling.append(UUID(str(s_id_raw_polling)))
                            except ValueError:
                                logger.warning(f"ID resumido inválido '{s_id_raw_polling}' en summarizedNotificationIds (polling), será omitido.")
                        notification_args["summarizedNotificationIds"] = valid_summarized_ids_polling
                    elif summarized_ids_raw_polling is not None:
                        logger.warning(f"summarizedNotificationIds (polling) no es una lista: {summarized_ids_raw_polling}. Se establecerá a None.")
                        notification_args["summarizedNotificationIds"] = None
                    
                    for date_field_key_polling in ["createdAt", "snoozedUntil", "readAt", "sentAt"]:
                        if date_field_key_polling in notification_args and isinstance(notification_args[date_field_key_polling], str):
                            try:
                                dt_str_polling = notification_args[date_field_key_polling]
                                if dt_str_polling and isinstance(dt_str_polling, str):
                                    if dt_str_polling.endswith('Z'):
                                        dt_str_polling = dt_str_polling[:-1] + '+00:00'
                                    notification_args[date_field_key_polling] = datetime.fromisoformat(dt_str_polling)
                                else:
                                    notification_args[date_field_key_polling] = None
                            except (ValueError, TypeError):
                                logger.warning(f"No se pudo convertir '{notification_args[date_field_key_polling]}' a datetime para el campo '{date_field_key_polling}' (polling). Se usará None o el valor por defecto.")
                                notification_args[date_field_key_polling] = None

                    logger.debug(f"DashboardView (polling): Argumentos finales para Notification: {notification_args}")
                    notification_obj = Notification(**notification_args)
                    notifications.append(notification_obj)
                except TypeError as te:
                    logger.error(f"Error de tipo al crear Notification (polling) con datos {data_item} y args procesados {notification_args}: {te}", exc_info=True)
                    continue
                except Exception as ex_inner:
                    logger.error(f"Error inesperado al procesar item de notificación (polling) {data_item}: {ex_inner}", exc_info=True)
                    continue

            for notification in notifications:
                self.notification_widget.add_notification(notification)
        
            logger.info("Nuevas notificaciones recibidas, actualizando desempeño de estrategias.")
            self._load_strategy_performance_data() # Llamada refactorizada
            
        logger.info("DashboardView._handle_new_notifications_result: FIN")

    def _on_notification_polling_timeout(self):
        self._fetch_new_notifications() # Llamada refactorizada

    def _fetch_new_notifications(self):
        logger.info("DashboardView._fetch_new_notifications: INICIO (refactorizado)")
        try:
            self._run_api_worker_and_await_result(
                lambda: self.api_client.get_notification_history(user_id=self.user_id)
            ).add_done_callback(
                lambda f: self.new_notifications_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("DashboardView._fetch_new_notifications: Llamada a api_client.get_notification_history programada.")
        except Exception as e:
            logger.error(f"DashboardView._fetch_new_notifications: Error inesperado al programar la carga de nuevas notificaciones: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error al programar carga de nuevas notificaciones: {e}")
        finally:
            logger.info("DashboardView._fetch_new_notifications: FIN (programación)")

    def _on_opportunity_monitor_timeout(self):
        self._check_pending_real_opportunities() # Llamada refactorizada

    def _handle_real_opportunities_result(self, opportunities_data: List[Dict[str, Any]]):
        """Manejador para los datos de oportunidades de trading real."""
        logger.info("DashboardView._handle_real_opportunities_result: INICIO")
        if opportunities_data:
            opportunities = [Opportunity(**opp_data) for opp_data in opportunities_data]
            if opportunities:
                opportunity_to_confirm = opportunities[0]
                logger.info(f"Oportunidad pendiente de confirmación encontrada: {opportunity_to_confirm.id}")
                dialog = RealTradeConfirmationDialog(opportunity_to_confirm, self.api_client, self)
                dialog.trade_confirmed.connect(self._handle_trade_confirmed)
                dialog.trade_cancelled.connect(self._handle_trade_cancelled)
                dialog.exec_()
                self._refresh_opportunities_ui() # Llamada refactorizada
                self._update_real_trades_count_ui() # Llamada refactorizada
        else:
            logger.debug("No hay oportunidades de trading real pendientes de confirmación.")
        logger.info("DashboardView._handle_real_opportunities_result: FIN")

    def _check_pending_real_opportunities(self):
        logger.info("DashboardView._check_pending_real_opportunities: INICIO (refactorizado)")
        try:
            self._run_api_worker_and_await_result(
                lambda: self.api_client.get_real_trading_candidates()
            ).add_done_callback(
                lambda f: self.real_opportunities_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("DashboardView._check_pending_real_opportunities: Llamada a api_client.get_real_trading_candidates programada.")
        except Exception as e:
            logger.error(f"DashboardView._check_pending_real_opportunities: Error inesperado al programar la verificación de oportunidades: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error al programar verificación de oportunidades: {e}")
        finally:
            logger.info("DashboardView._check_pending_real_opportunities: FIN (programación)")

    def _refresh_opportunities_ui(self):
        logger.info("Actualizando UI de oportunidades (placeholder).")
        # Si hay una vista de oportunidades separada, se llamaría a su método de actualización aquí.
        # Por ahora, es un placeholder.

    def _handle_real_trades_count_result(self, config_status: Dict[str, Any]):
        """Manejador para los datos del contador de trades reales."""
        logger.info("DashboardView._handle_real_trades_count_result: INICIO")
        if config_status and 'real_trades_executed_count' in config_status:
            count = config_status['real_trades_executed_count']
            max_trades = config_status['max_real_trades']
            logger.info(f"Contador de trades reales actualizado: {count}/{max_trades}")
            # Aquí se actualizaría un QLabel o similar en la UI con el contador
        else:
            logger.warning("No se pudo obtener el contador de trades reales del backend.")
        logger.info("DashboardView._handle_real_trades_count_result: FIN")

    def _update_real_trades_count_ui(self):
        logger.info("DashboardView._update_real_trades_count_ui: INICIO (refactorizado)")
        try:
            self._run_api_worker_and_await_result(
                lambda: self.api_client.get_real_trading_mode_status()
            ).add_done_callback(
                lambda f: self.real_trades_count_fetched.emit(f.result()) if not f.exception() else None
            )
            logger.info("DashboardView._update_real_trades_count_ui: Llamada a api_client.get_real_trading_mode_status programada.")
        except Exception as e:
            logger.error(f"DashboardView._update_real_trades_count_ui: Error inesperado al programar la actualización del contador: {e}", exc_info=True)
            self.dashboard_api_error.emit(f"Error al programar actualización de contador de trades: {e}")
        finally:
            logger.info("DashboardView._update_real_trades_count_ui: FIN (programación)")

    def _handle_trade_confirmed(self, opportunity_id: str):
        logger.info(f"Trade real confirmado para oportunidad {opportunity_id}. Actualizando UI.")
        self._refresh_opportunities_ui()
        self._update_real_trades_count_ui()
        self._load_strategy_performance_data()

    def _handle_trade_cancelled(self, opportunity_id: str):
        logger.info(f"Trade real cancelado para oportunidad {opportunity_id}. No se requiere acción adicional en UI.")
        self._refresh_opportunities_ui()

    def _handle_order_executed(self, order_details: dict[str, Any]):
        logger.info(f"Orden ejecutada exitosamente: {order_details}")
        if hasattr(self.portfolio_widget, 'refresh_data'):
            self.portfolio_widget.refresh_data()
        self._load_strategy_performance_data()
        symbol = order_details.get('symbol', 'N/A')
        side = order_details.get('side', 'N/A')
        quantity = order_details.get('quantity', 0)
        mode = order_details.get('trading_mode', 'unknown')
        success_message = f"✅ Orden {side} ejecutada: {quantity:.8f} {symbol} en modo {mode.title()}"
        logger.info(success_message)

    def _handle_order_failed(self, error_message: str):
        logger.error(f"Error en ejecución de orden: {error_message}")
        self.dashboard_api_error.emit(f"Error en orden: {error_message}")

    def _handle_dashboard_api_error(self, message: str):
        """Manejador general para errores de API en DashboardView."""
        logger.error(f"DashboardView: Error de API general: {message}")
        # Aquí podrías mostrar un QMessageBox o actualizar un QLabel de estado
        # Por ahora, solo loguea el error.
        QMessageBox.warning(self, "Error de API en Dashboard", message)

    def cleanup(self):
        logger.info("DashboardView: cleanup called.")
        if hasattr(self.market_data_widget, 'cleanup') and callable(self.market_data_widget.cleanup):
            logger.info("DashboardView: Calling cleanup on market_data_widget.")
            self.market_data_widget.cleanup()
        if hasattr(self.portfolio_widget, 'stop_updates') and callable(self.portfolio_widget.stop_updates):
            logger.info("DashboardView: Calling stop_updates on portfolio_widget.")
            self.portfolio_widget.stop_updates()
        if hasattr(self, '_notification_polling_timer') and self._notification_polling_timer.isActive():
            logger.info("DashboardView: Stopping notification polling timer.")
            self._notification_polling_timer.stop()
        if hasattr(self, '_opportunity_monitor_timer') and self._opportunity_monitor_timer.isActive():
            logger.info("DashboardView: Stopping opportunity monitor timer.")
            self._opportunity_monitor_timer.stop()
        if hasattr(self.notification_widget, 'cleanup') and callable(self.notification_widget.cleanup):
            logger.info("DashboardView: Calling cleanup on notification_widget.")
            self.notification_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup') and callable(self.chart_widget.cleanup):
            logger.info("DashboardView: Calling cleanup on chart_widget.")
            self.chart_widget.cleanup()
        if hasattr(self.order_form_widget, 'cleanup') and callable(self.order_form_widget.cleanup):
            logger.info("DashboardView: Calling cleanup on order_form_widget.")
            self.order_form_widget.cleanup()
        if hasattr(self.strategy_performance_widget, 'cleanup') and callable(self.strategy_performance_widget.cleanup):
            logger.info("DashboardView: Calling cleanup on strategy_performance_widget.")
            self.strategy_performance_widget.cleanup()
        
        # Limpiar workers y threads activos
        for worker, thread in self.active_api_workers[:]:
            if thread.isRunning():
                logger.info(f"DashboardView: Cleaning up active ApiWorker thread {thread.objectName()}.")
                thread.quit()
                if not thread.wait(2000): # Esperar un máximo de 2 segundos
                    logger.warning(f"DashboardView: Thread {thread.objectName()} did not finish in time. Terminating.")
                    thread.terminate()
                    thread.wait()
            if (worker, thread) in self.active_api_workers:
                self.active_api_workers.remove((worker, thread))
        logger.info(f"DashboardView: All active ApiWorkers ({len(self.active_api_workers)} remaining) processed for cleanup.")
        logger.info("DashboardView: cleanup finished.")
