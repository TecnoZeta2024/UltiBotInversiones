import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable, Coroutine, Tuple
from uuid import UUID
from datetime import datetime
import PySide6.QtWidgets as QtWidgets
import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui

import qasync

from ultibot_ui.models import BaseMainWindow
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager

logger = logging.getLogger(__name__)

class PortfolioWidget(QtWidgets.QWidget):
    """
    Widget para la visualización del estado del portafolio con un diseño moderno
    basado en tarjetas y estilos centralizados.
    """
    portfolio_updated = QtCore.Signal(object)
    error_occurred = QtCore.Signal(str)

    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client # Usar la instancia de api_client
        self.main_window = main_window
        self.main_event_loop = main_event_loop # Guardar la referencia al bucle de eventos
        self.current_snapshot: Optional[Dict[str, Any]] = None
        self.open_trades: List[Dict[str, Any]] = []

        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)

        self.init_ui()
        self.setup_update_timer()
        # La limpieza de hilos se gestionará a través de MainWindow

    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa las actualizaciones."""
        self.user_id = user_id
        logger.info(f"PortfolioWidget: User ID set to {user_id}. Starting updates.")
        self.start_updates() # Iniciar actualizaciones una vez que el user_id esté disponible

    def init_ui(self):
        """Inicializa la interfaz de usuario con un layout basado en pestañas."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        self._create_mode_header(main_layout)

        self.tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.portfolio_tab = QtWidgets.QWidget()
        self.init_portfolio_tab()
        self.tab_widget.addTab(self.portfolio_tab, "Portafolio")

        self.trades_tab = QtWidgets.QWidget()
        self.init_trades_tab()
        self.tab_widget.addTab(self.trades_tab, "Operaciones Abiertas")

        self.capital_tab = QtWidgets.QWidget()
        self.init_capital_tab()
        self.tab_widget.addTab(self.capital_tab, "Gestión de Capital")
        self.tab_widget.setTabEnabled(2, False) # Deshabilitar la pestaña de capital

        self._create_status_bar(main_layout)

    def _create_mode_header(self, layout: QtWidgets.QVBoxLayout):
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QtWidgets.QLabel("Estado del Portafolio")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.mode_indicator = QtWidgets.QLabel()
        self._update_mode_indicator()
        header_layout.addWidget(self.mode_indicator)
        
        layout.addLayout(header_layout)

    def _update_mode_indicator(self):
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.mode_indicator.setText(f"{mode_info['icon']} {mode_info['display_name']}")
        self.mode_indicator.setProperty("tradingMode", self.trading_mode_manager.current_mode)

    def init_portfolio_tab(self):
        layout = QtWidgets.QVBoxLayout(self.portfolio_tab)
        layout.setSpacing(15)
        
        self.balance_label = QtWidgets.QLabel("Saldo Disponible: N/A")
        self.total_assets_label = QtWidgets.QLabel("Valor Total Activos: N/A")
        self.portfolio_value_label = QtWidgets.QLabel("Valor Total Portafolio: N/A")
        
        summary_layout = QtWidgets.QHBoxLayout()
        summary_layout.addWidget(self.balance_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.total_assets_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.portfolio_value_label)
        layout.addLayout(summary_layout)

        self.assets_table = self._create_assets_table()
        layout.addWidget(self.assets_table)
        
        self.comparison_info = QtWidgets.QLabel("")
        self.comparison_info.setObjectName("subtitleLabel")
        self.comparison_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.comparison_info)

    def init_trades_tab(self):
        layout = QtWidgets.QVBoxLayout(self.trades_tab)
        layout.setSpacing(15)
        
        self.trades_title = QtWidgets.QLabel()
        self.trades_title.setObjectName("subtitleLabel")
        self.trades_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._update_trades_title()
        layout.addWidget(self.trades_title)
        
        self.open_trades_table = self._create_open_trades_table()
        layout.addWidget(self.open_trades_table)
        
        self.trades_info_label = QtWidgets.QLabel("No hay operaciones abiertas")
        self.trades_info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.trades_info_label.setObjectName("subtitleLabel")
        layout.addWidget(self.trades_info_label)

    def _update_trades_title(self):
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.trades_title.setText(f"Operaciones {mode_info['display_name']} con TSL/TP Activos")

    def init_capital_tab(self):
        layout = QtWidgets.QVBoxLayout(self.capital_tab)
        layout.setSpacing(15)
        
        info_label = QtWidgets.QLabel("La funcionalidad de Gestión de Capital está en desarrollo.")
        info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def _create_status_bar(self, layout: QtWidgets.QVBoxLayout):
        status_layout = QtWidgets.QHBoxLayout()
        self.last_updated_label = QtWidgets.QLabel("Última actualización: N/A")
        self.last_updated_label.setObjectName("subtitleLabel")
        
        self.refresh_button = QtWidgets.QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_data)
        
        status_layout.addWidget(self.last_updated_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_button)
        layout.addLayout(status_layout)
        
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setProperty("class", "error")
        self.error_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

    def _create_assets_table(self) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Símbolo", "Cantidad", "Precio Entrada", "Precio Actual", "Valor USD", "PnL (%)"])
        
        h_header = table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def _create_open_trades_table(self) -> QtWidgets.QTableWidget:
        table = QtWidgets.QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Símbolo", "Tipo", "Cantidad", "Precio Entrada", "Precio Actual", 
            "Take Profit", "Stop Loss", "Estado TSL", "PnL Actual"
        ])
        
        h_header = table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def setup_update_timer(self):
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setInterval(15000)
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start()
        logger.info("Timer de actualización del portafolio iniciado.")

    def _on_trading_mode_changed(self, new_mode: str):
        logger.info(f"PortfolioWidget: Modo de trading cambió a {new_mode}")
        self._update_mode_indicator()
        self._update_trades_title()
        self.refresh_data()

    def refresh_data(self):
        if self.user_id is None:
            logger.warning("PortfolioWidget: user_id no está disponible. No se puede actualizar el portafolio.")
            self.last_updated_label.setText("Esperando configuración de usuario...")
            return
        
        self.main_event_loop.call_soon_threadsafe(self._update_data_async)

    async def _update_data_async(self):
        current_mode = self.trading_mode_manager.current_mode
        user_id = self.user_id

        if user_id is None:
            logger.error("Intento de actualizar datos sin user_id.")
            self._handle_worker_error("Error interno: user_id no está configurado.")
            return
        
        logger.info(f"Actualizando datos del portafolio para modo: {current_mode}")
        self.last_updated_label.setText(f"Actualizando portafolio ({current_mode.title()})...")
        if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(False)

        try:
            snapshot_task = self.api_client.get_portfolio_snapshot(user_id, current_mode)
            open_trades_task = self.api_client.get_trades(trading_mode=current_mode, status="open")
            
            results = await asyncio.gather(snapshot_task, open_trades_task, return_exceptions=True)
            
            result_data = {
                "portfolio_snapshot": results[0],
                "open_trades": results[1],
                "trading_mode": current_mode
            }
            self._handle_update_result(result_data)
        except Exception as e:
            self._handle_worker_error(str(e))
        finally:
            if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(True)

    def _handle_update_result(self, result_data: Dict[str, Any]):
        logger.info(f"DATOS COMPLETOS RECIBIDOS EN HANDLER: {result_data}")
        has_error = False
        try:
            current_mode = self.trading_mode_manager.current_mode
            if result_data.get("trading_mode", current_mode) != current_mode:
                logger.warning(f"Datos para modo incorrecto. Esperado: {current_mode}, Recibido: {result_data.get('trading_mode')}")
                return

            self.current_snapshot = result_data.get("portfolio_snapshot")
            if isinstance(self.current_snapshot, Exception):
                logger.error(f"Error al obtener snapshot de portafolio: {self.current_snapshot}", exc_info=self.current_snapshot)
                self.error_label.setText("Error al obtener snapshot.")
                has_error = True
            elif self.current_snapshot:
                self._update_portfolio_ui(self.current_snapshot, current_mode)

            self.open_trades = result_data.get("open_trades", [])
            if isinstance(self.open_trades, Exception):
                logger.error(f"Error al obtener trades abiertos: {self.open_trades}", exc_info=self.open_trades)
                self.error_label.setText("Error al obtener trades.")
                has_error = True
            else:
                self._update_open_trades_ui(self.open_trades)

            self.last_updated_label.setText(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if not has_error:
                self.error_label.setText("")

        except Exception as e:
            logger.error(f"Error fatal procesando datos actualizados: {e}", exc_info=True)
            self.error_label.setText("Error al procesar datos.")
        finally:
            if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(True)

    def _update_portfolio_ui(self, snapshot_dict: Dict[str, Any], mode: str):
        portfolio_mode_dict = snapshot_dict.get(f"{mode}_trading", {}) 
        currency = "USDT (Virtual)" if mode == "paper" else "USDT"
        # Asegurarse de que los valores son flotantes antes de formatear
        available_balance = float(portfolio_mode_dict.get('available_balance_usdt', 0.0))
        total_assets = float(portfolio_mode_dict.get('total_assets_value_usd', 0.0))
        total_portfolio = float(portfolio_mode_dict.get('total_portfolio_value_usd', 0.0))
        
        self.balance_label.setText("{:,.2f} {}".format(available_balance, currency))
        self.total_assets_label.setText("{:,.2f} USD".format(total_assets))
        self.portfolio_value_label.setText("{:,.2f} USD".format(total_portfolio))
        self._populate_assets_table(portfolio_mode_dict.get('assets', []))
        other_mode = "real" if mode == "paper" else "paper"
        other_mode_dict = snapshot_dict.get(f"{other_mode}_trading", {})
        other_mode_value = float(other_mode_dict.get('total_portfolio_value_usd', 0.0))
        self.comparison_info.setText("Portafolio {}: {:,.2f} USD".format(other_mode.title(), other_mode_value))

    def _update_open_trades_ui(self, trades: List[Dict[str, Any]]):
        self.trades_info_label.setVisible(not trades)
        self.open_trades_table.setRowCount(len(trades))
        for row, trade in enumerate(trades):
            self._set_item(self.open_trades_table, row, 0, str(trade.get('symbol')))
            self._set_item(self.open_trades_table, row, 1, str(trade.get('trade_type')))
            self._set_item(self.open_trades_table, row, 2, "{:.6f}".format(float(trade.get('quantity', 0))))
            self._set_item(self.open_trades_table, row, 3, "{:.4f}".format(float(trade.get('entry_price', 0))))
            self._set_item(self.open_trades_table, row, 4, "{:.4f}".format(float(trade.get('current_price', 0))))
            self._set_item(self.open_trades_table, row, 5, "{:.4f}".format(float(trade.get('take_profit_price', 0))))
            self._set_item(self.open_trades_table, row, 6, "{:.4f}".format(float(trade.get('stop_loss_price', 0))))
            self._set_item(self.open_trades_table, row, 7, str(trade.get('tsl_status')))
            
            pnl = float(trade.get('pnl_percentage', 0)) * 100
            pnl_item = QtWidgets.QTableWidgetItem(f"{pnl:.2f}%")
            pnl_item.setForeground(QtGui.QColor('green') if pnl >= 0 else QtGui.QColor('red'))
            self.open_trades_table.setItem(row, 8, pnl_item)

    def _set_item(self, table: QtWidgets.QTableWidget, row: int, col: int, text: Optional[str]):
        item = QtWidgets.QTableWidgetItem(str(text) if text is not None else "")
        table.setItem(row, col, item)

    def _handle_worker_error(self, error_msg: str):
        logger.error(f"PortfolioWidget: Error en DataUpdateWorker: {error_msg}")
        self.error_label.setText("Error al cargar datos.")
        self.last_updated_label.setText("Actualización fallida.")

    def start_updates(self):
        self.refresh_data()
        self.update_timer.start()

    def stop_updates(self):
        self.update_timer.stop()

    def _populate_assets_table(self, assets: List[Dict[str, Any]]):
        self.assets_table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            self._set_item(self.assets_table, row, 0, str(asset.get('symbol')))
            self._set_item(self.assets_table, row, 1, "{:.6f}".format(float(asset.get('free', 0))))
            self._set_item(self.assets_table, row, 2, "{:.4f}".format(float(asset.get('avg_entry_price', 0))))
            self._set_item(self.assets_table, row, 3, "{:.4f}".format(float(asset.get('current_price', 0))))
            self._set_item(self.assets_table, row, 4, "{:,.2f}".format(float(asset.get('usd_value', 0))))
            
            pnl_percentage = float(asset.get('pnl_percentage', 0)) * 100
            pnl_item = QtWidgets.QTableWidgetItem(f"{pnl_percentage:.2f}%")
            pnl_item.setForeground(QtGui.QColor('green') if pnl_percentage >= 0 else QtGui.QColor('red'))
            self.assets_table.setItem(row, 5, pnl_item)

    def cleanup(self):
        """
        Detiene las actualizaciones periódicas y asegura que todos los hilos de workers
        se detengan de forma segura antes de que el widget sea destruido.
        """
        logger.info("PortfolioWidget: Iniciando limpieza.")
        self.stop_updates() # Detener el QTimer
        # Los hilos de los workers son gestionados por MainWindow.
        logger.info("PortfolioWidget: Limpieza completada.")
