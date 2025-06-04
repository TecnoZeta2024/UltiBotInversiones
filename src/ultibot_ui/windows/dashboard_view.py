import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QFrame, QTabWidget, QComboBox # Añadir QTabWidget y QComboBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal # Importar QTimer y pyqtSignal
from typing import Any, Optional, List, Callable, Tuple # Añadir importaciones de typing
from datetime import datetime # Añadir importación de datetime
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
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError # Importar el cliente API y APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager

from src.ultibot_ui.widgets.notification_widget import NotificationWidget # Importar NotificationWidget
from src.ultibot_ui.widgets.strategy_performance_table_view import StrategyPerformanceTableView # Importar el nuevo widget

# Los siguientes servicios ya no se importan directamente, se accederán via api_client
# from src.ultibot_backend.services.market_data_service import MarketDataService
# from src.ultibot_backend.services.config_service import ConfigService
# from src.ultibot_backend.services.portfolio_service import PortfolioService
# from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
# from src.ultibot_backend.services.notification_service import NotificationService

class DashboardView(QWidget):
    initialization_complete = pyqtSignal() # Nueva señal

    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient): # Refactorizado para aceptar solo api_client
        super().__init__()
        self.user_id = user_id
        self.api_client = api_client # Guardar la referencia al cliente API
        self.trading_mode_service = trading_mode_service # Store TradingModeService
        
        self.trading_mode_manager = get_trading_mode_manager()
        
        self._setup_ui()
        
        self._opportunity_monitor_timer = QTimer(self)
        self._opportunity_monitor_timer.setInterval(10000) # Chequear cada 10 segundos
        self._opportunity_monitor_timer.timeout.connect(self._on_opportunity_monitor_timeout)
        self._opportunity_monitor_timer.start()
        print("Monitor de oportunidades de trading real iniciado.")

        QTimer.singleShot(0, lambda: self._schedule_task(self._initialize_async_components()))

    async def _initialize_async_components(self):
        """Carga secuencialmente los componentes asíncronos iniciales."""
        try:
            logger.info("DashboardView: _initialize_async_components INVOCADO (v3)") # Incremento versión para nuevo log
            logger.info("Iniciando carga secuencial de componentes asíncronos...")
            all_components_loaded_successfully = True
        except Exception as e_initial:
            logger.error(f"DashboardView: Error MUY TEMPRANO en _initialize_async_components: {e_initial}", exc_info=True)
            self.initialization_complete.emit() # Emitir para no bloquear indefinidamente
            return # Salir si hay un error muy temprano
        try:
            # 1. Cargar notificaciones
            logger.info("DashboardView: Iniciando _load_and_subscribe_notifications...")
            try:
                await self._load_and_subscribe_notifications()
                logger.info("DashboardView: _load_and_subscribe_notifications COMPLETADO.")
            except Exception as e_notify:
                logger.error(f"DashboardView: Error en _load_and_subscribe_notifications: {e_notify}", exc_info=True)
                all_components_loaded_successfully = False

            # 2. Cargar datos de desempeño de estrategias
            logger.info("DashboardView: Iniciando _load_strategy_performance_data...")
            try:
                await self._load_strategy_performance_data()
                logger.info("DashboardView: _load_strategy_performance_data COMPLETADO.")
            except Exception as e_perf:
                logger.error(f"DashboardView: Error en _load_strategy_performance_data: {e_perf}", exc_info=True)
                all_components_loaded_successfully = False
            
            # 3. Cargar configuración inicial de MarketDataWidget
            if hasattr(self.market_data_widget, 'load_initial_configuration') and callable(self.market_data_widget.load_initial_configuration):
                logger.info("DashboardView: Iniciando market_data_widget.load_initial_configuration...")
                try:
                    await self.market_data_widget.load_initial_configuration()
                    logger.info("DashboardView: market_data_widget.load_initial_configuration COMPLETADO.")
                except Exception as e_market:
                    logger.error(f"DashboardView: Error en market_data_widget.load_initial_configuration: {e_market}", exc_info=True)
                    all_components_loaded_successfully = False
            else:
                logger.info("DashboardView: market_data_widget.load_initial_configuration no disponible o no es llamable.")

            if all_components_loaded_successfully:
                logger.info("DashboardView: Carga secuencial de TODOS los componentes asíncronos completada exitosamente.")
            else:
                logger.warning("DashboardView: Carga secuencial de componentes asíncronos completada, PERO con errores en uno o más componentes.")

        except Exception as e:
            logger.error(f"DashboardView: Error INESPERADO durante la inicialización asíncrona secuencial: {e}", exc_info=True)
            all_components_loaded_successfully = False
        finally:
            logger.info(f"DashboardView: Emitiendo initialization_complete. Estado de carga exitosa: {all_components_loaded_successfully}")
            self.initialization_complete.emit()

    def _schedule_task(self, coro):
        logger.info("DashboardView: _schedule_task INVOCADO")
        try:
            # Obtener el bucle de eventos de qasync que se está ejecutando
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                logger.info(f"DashboardView: _schedule_task - Bucle de eventos obtenido y en ejecución: {loop}")
                loop.create_task(coro)
                logger.info("DashboardView: _schedule_task - Tarea creada en el bucle.")
            else:
                logger.error("DashboardView: _schedule_task - No se pudo obtener un bucle de eventos en ejecución. La tarea no se programará.")
        except Exception as e:
            logger.error(f"DashboardView: _schedule_task - Error al programar la tarea: {e}", exc_info=True)


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
        self.notification_widget = NotificationWidget(api_client=self.api_client, user_id=self.user_id)
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
            asyncio.create_task(self._load_strategy_performance_data())

    def _on_performance_filter_changed(self, index: int):
        asyncio.create_task(self._load_strategy_performance_data())

    async def _load_strategy_performance_data(self):
        logger.info("DashboardView._load_strategy_performance_data: INICIO")
        try:
            selected_filter_text = self.performance_mode_filter_combo.currentText()
            mode_param_for_api: Optional[str] = None
            if selected_filter_text == "Paper Trading":
                mode_param_for_api = "paper"
            elif selected_filter_text == "Operativa Real":
                mode_param_for_api = "real"
            
            logger.info(f"DashboardView._load_strategy_performance_data: Filtro seleccionado: '{selected_filter_text}', Parámetro API: '{mode_param_for_api}'")
            
            logger.info("DashboardView._load_strategy_performance_data: Llamando a api_client.get_strategy_performance...")
            performance_data = await self.api_client.get_strategy_performance(
                user_id=self.user_id,
                mode=mode_param_for_api
            )
            logger.info("DashboardView._load_strategy_performance_data: Llamada a api_client.get_strategy_performance completada.")

            if performance_data is not None:
                self.strategy_performance_widget.set_data(performance_data)
                logger.info(f"DashboardView._load_strategy_performance_data: Datos de desempeño ({len(performance_data)} registros) establecidos en el widget.")
            else:
                self.strategy_performance_widget.set_data([])
                logger.info("DashboardView._load_strategy_performance_data: No se recibieron datos de desempeño (None), tabla limpiada.")
        except APIError as api_e:
            logger.error(f"DashboardView._load_strategy_performance_data: APIError al cargar datos de desempeño: {api_e.status_code} - {api_e.message}", exc_info=True)
            self.strategy_performance_widget.set_data([])
        except Exception as e:
            logger.error(f"DashboardView._load_strategy_performance_data: Error inesperado al cargar datos de desempeño: {e}", exc_info=True)
            self.strategy_performance_widget.set_data([])
        finally:
            logger.info("DashboardView._load_strategy_performance_data: FIN")

    def _handle_chart_symbol_selection(self, symbol: str):
        print(f"Dashboard: Símbolo de gráfico seleccionado: {symbol}")
        asyncio.create_task(self._fetch_and_update_chart_data())

    def _handle_chart_interval_selection(self, interval: str):
        print(f"Dashboard: Temporalidad de gráfico seleccionada: {interval}")
        asyncio.create_task(self._fetch_and_update_chart_data())

    async def _fetch_and_update_chart_data(self):
        if self.chart_widget.current_symbol and self.chart_widget.current_interval:
            try:
                candlestick_data = await self.api_client.get_candlestick_data(
                    symbol=self.chart_widget.current_symbol,
                    interval=self.chart_widget.current_interval,
                    limit=200
                )
                self.chart_widget.set_candlestick_data(candlestick_data)
            except APIError as e:
                print(f"APIError al obtener datos de velas para el gráfico: {e.status_code} - {e.message}")
                self.chart_widget.set_candlestick_data([])
                self.chart_widget.chart_area.setText(f"Error API: {e.message}")
            except Exception as e:
                print(f"Error al obtener datos de velas para el gráfico: {e}")
                self.chart_widget.set_candlestick_data([])
                self.chart_widget.chart_area.setText(f"Error al cargar datos: {e}")

    async def _load_and_subscribe_notifications(self):
        # Comentario de prueba para Pylance - Línea 228
        logger.info("DashboardView._load_and_subscribe_notifications: INICIO (v2)")
        try:
            logger.info("DashboardView._load_and_subscribe_notifications: Llamando a api_client.get_notification_history (v2)...")
            history_notifications_data = await self.api_client.get_notification_history(user_id=self.user_id)
            logger.info("DashboardView._load_and_subscribe_notifications: Llamada a api_client.get_notification_history completada.")

            if history_notifications_data:
                logger.info(f"DashboardView._load_and_subscribe_notifications: Recibidas {len(history_notifications_data)} notificaciones del historial.")
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
                                try:
                                    dt_str = notification_args[date_field_key]
                                    if dt_str.endswith('Z'):
                                        dt_str = dt_str[:-1] + '+00:00'
                                    notification_args[date_field_key] = datetime.fromisoformat(dt_str)
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
                logger.info("DashboardView._load_and_subscribe_notifications: Polling de notificaciones iniciado/verificado.")
            else:
                logger.info("DashboardView._load_and_subscribe_notifications: Polling de notificaciones ya estaba activo.")

        except APIError as api_e:
            logger.error(f"DashboardView._load_and_subscribe_notifications: APIError al cargar historial: {api_e.status_code} - {api_e.message}", exc_info=True)
        except Exception as e:
            logger.error(f"DashboardView._load_and_subscribe_notifications: Error inesperado: {e}", exc_info=True)
        finally:
            logger.info("DashboardView._load_and_subscribe_notifications: FIN")

    def _on_notification_polling_timeout(self):
        asyncio.create_task(self._fetch_new_notifications())

    async def _fetch_new_notifications(self):
        try:
            new_notifications_data = await self.api_client.get_notification_history(user_id=self.user_id)
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
                                    if dt_str_polling.endswith('Z'):
                                        dt_str_polling = dt_str_polling[:-1] + '+00:00'
                                    notification_args[date_field_key_polling] = datetime.fromisoformat(dt_str_polling)
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
                await self._load_strategy_performance_data()
                
        except APIError as e:
            print(f"APIError al hacer polling de nuevas notificaciones: {e.status_code} - {e.message}")
        except Exception as e:
            print(f"Error al hacer polling de nuevas notificaciones: {e}")

    def _on_opportunity_monitor_timeout(self):
        asyncio.create_task(self._check_pending_real_opportunities())

    async def _check_pending_real_opportunities(self):
        try:
            opportunities_data = await self.api_client.get_real_trading_candidates()
            if opportunities_data:
                opportunities = [Opportunity(**opp_data) for opp_data in opportunities_data]
                if opportunities:
                    opportunity_to_confirm = opportunities[0]
                    logger.info(f"Oportunidad pendiente de confirmación encontrada: {opportunity_to_confirm.id}")
                    dialog = RealTradeConfirmationDialog(opportunity_to_confirm, self.api_client, self)
                    dialog.trade_confirmed.connect(self._handle_trade_confirmed)
                    dialog.trade_cancelled.connect(self._handle_trade_cancelled)
                    dialog.exec_()
                    await self._refresh_opportunities_ui()
                    await self._update_real_trades_count_ui()
            else:
                logger.debug("No hay oportunidades de trading real pendientes de confirmación.")
        except Exception as e:
            logger.error(f"Error al verificar oportunidades de trading real pendientes: {e}", exc_info=True)

    async def _refresh_opportunities_ui(self):
        logger.info("Actualizando UI de oportunidades (placeholder).")

    async def _update_real_trades_count_ui(self):
        try:
            config_status = await self.api_client.get_real_trading_mode_status()
            if config_status and 'real_trades_executed_count' in config_status:
                count = config_status['real_trades_executed_count']
                max_trades = config_status['max_real_trades']
                logger.info(f"Contador de trades reales actualizado: {count}/{max_trades}")
            else:
                logger.warning("No se pudo obtener el contador de trades reales del backend.")
        except Exception as e:
            logger.error(f"Error al actualizar el contador de trades reales en UI: {e}", exc_info=True)

    def _handle_trade_confirmed(self, opportunity_id: str):
        logger.info(f"Trade real confirmado para oportunidad {opportunity_id}. Actualizando UI.")
        asyncio.create_task(self._refresh_opportunities_ui())
        asyncio.create_task(self._update_real_trades_count_ui())
        asyncio.create_task(self._load_strategy_performance_data())

    def _handle_trade_cancelled(self, opportunity_id: str):
        logger.info(f"Trade real cancelado para oportunidad {opportunity_id}. No se requiere acción adicional en UI.")
        asyncio.create_task(self._refresh_opportunities_ui())

    def _handle_order_executed(self, order_details: dict[str, Any]):
        logger.info(f"Orden ejecutada exitosamente: {order_details}")
        if hasattr(self.portfolio_widget, 'refresh_data'):
            self.portfolio_widget.refresh_data()
        asyncio.create_task(self._load_strategy_performance_data())
        symbol = order_details.get('symbol', 'N/A')
        side = order_details.get('side', 'N/A')
        quantity = order_details.get('quantity', 0)
        mode = order_details.get('trading_mode', 'unknown')
        success_message = f"✅ Orden {side} ejecutada: {quantity:.8f} {symbol} en modo {mode.title()}"
        logger.info(success_message)

    def _handle_order_failed(self, error_message: str):
        logger.error(f"Error en ejecución de orden: {error_message}")

    def cleanup(self):
        print("DashboardView: cleanup called.")
        if hasattr(self.market_data_widget, 'cleanup') and callable(self.market_data_widget.cleanup):
            print("DashboardView: Calling cleanup on market_data_widget.")
            self.market_data_widget.cleanup()
        if hasattr(self.portfolio_widget, 'stop_updates') and callable(self.portfolio_widget.stop_updates):
            print("DashboardView: Calling stop_updates on portfolio_widget.")
            self.portfolio_widget.stop_updates()
        if hasattr(self, '_notification_polling_timer') and self._notification_polling_timer.isActive():
            print("DashboardView: Stopping notification polling timer.")
            self._notification_polling_timer.stop()
        if hasattr(self, '_opportunity_monitor_timer') and self._opportunity_monitor_timer.isActive():
            print("DashboardView: Stopping opportunity monitor timer.")
            self._opportunity_monitor_timer.stop()
        if hasattr(self.notification_widget, 'cleanup') and callable(self.notification_widget.cleanup):
            print("DashboardView: Calling cleanup on notification_widget.")
            self.notification_widget.cleanup()
        if hasattr(self.chart_widget, 'cleanup') and callable(self.chart_widget.cleanup):
            print("DashboardView: Calling cleanup on chart_widget.")
            self.chart_widget.cleanup()
        if hasattr(self.order_form_widget, 'cleanup') and callable(self.order_form_widget.cleanup):
            print("DashboardView: Calling cleanup on order_form_widget.")
            self.order_form_widget.cleanup()
        if hasattr(self, 'strategy_performance_widget') and hasattr(self.strategy_performance_widget, 'cleanup') and callable(self.strategy_performance_widget.cleanup):
            print("DashboardView: Calling cleanup on strategy_performance_widget.")
            self.strategy_performance_widget.cleanup()
        print("DashboardView: cleanup finished.")
