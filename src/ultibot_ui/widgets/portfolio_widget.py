import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable, Coroutine, Tuple
from uuid import UUID
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QPushButton,
    QTabWidget, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QThread
from PyQt5.QtGui import QFont, QColor

import qasync

from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager
from src.ultibot_ui.workers import ApiWorker


logger = logging.getLogger(__name__)

class PortfolioWidget(QWidget):
    """
    Widget para la visualización del estado del portafolio con un diseño moderno
    basado en tarjetas y estilos centralizados.
    """
    portfolio_updated = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_id: UUID, main_window: BaseMainWindow, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.active_workers: List[Tuple[QThread, ApiWorker]] = []
        self.current_snapshot: Optional[Dict[str, Any]] = None
        self.open_trades: List[Dict[str, Any]] = []

        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)

        self.init_ui()
        self.setup_update_timer()

    def _start_api_worker(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success, on_error):
        thread = QThread()
        worker = ApiWorker(coroutine_factory=coroutine_factory)
        worker.moveToThread(thread)

        worker.result_ready.connect(on_success)
        worker.error_occurred.connect(on_error)
        thread.started.connect(worker.run)
        
        def cleanup_worker():
            for i, (t, w) in enumerate(self.active_workers):
                if t is thread:
                    self.active_workers.pop(i)
                    break
            thread.quit()

        worker.result_ready.connect(cleanup_worker)
        worker.error_occurred.connect(cleanup_worker)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self.active_workers.append((thread, worker))
        thread.start()

    def init_ui(self):
        """Inicializa la interfaz de usuario con un layout basado en pestañas."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        self._create_mode_header(main_layout)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.portfolio_tab = QWidget()
        self.init_portfolio_tab()
        self.tab_widget.addTab(self.portfolio_tab, "Portafolio")

        self.trades_tab = QWidget()
        self.init_trades_tab()
        self.tab_widget.addTab(self.trades_tab, "Operaciones Abiertas")

        self.capital_tab = QWidget()
        self.init_capital_tab()
        self.tab_widget.addTab(self.capital_tab, "Gestión de Capital")
        self.tab_widget.setTabEnabled(2, False)

        self._create_status_bar(main_layout)

    def _create_mode_header(self, layout: QVBoxLayout):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("Estado del Portafolio")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.mode_indicator = QLabel()
        self._update_mode_indicator()
        header_layout.addWidget(self.mode_indicator)
        
        layout.addLayout(header_layout)

    def _update_mode_indicator(self):
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.mode_indicator.setText(f"{mode_info['icon']} {mode_info['display_name']}")
        self.mode_indicator.setProperty("tradingMode", self.trading_mode_manager.current_mode)

    def init_portfolio_tab(self):
        layout = QVBoxLayout(self.portfolio_tab)
        layout.setSpacing(15)
        
        self.balance_label = QLabel("Saldo Disponible: N/A")
        self.total_assets_label = QLabel("Valor Total Activos: N/A")
        self.portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.balance_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.total_assets_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.portfolio_value_label)
        layout.addLayout(summary_layout)

        self.assets_table = self._create_assets_table()
        layout.addWidget(self.assets_table)
        
        self.comparison_info = QLabel("")
        self.comparison_info.setObjectName("subtitleLabel")
        self.comparison_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.comparison_info)

    def init_trades_tab(self):
        layout = QVBoxLayout(self.trades_tab)
        layout.setSpacing(15)
        
        self.trades_title = QLabel()
        self.trades_title.setObjectName("subtitleLabel")
        self.trades_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_trades_title()
        layout.addWidget(self.trades_title)
        
        self.open_trades_table = self._create_open_trades_table()
        layout.addWidget(self.open_trades_table)
        
        self.trades_info_label = QLabel("No hay operaciones abiertas")
        self.trades_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trades_info_label.setObjectName("subtitleLabel")
        layout.addWidget(self.trades_info_label)

    def _update_trades_title(self):
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.trades_title.setText(f"Operaciones {mode_info['display_name']} con TSL/TP Activos")

    def init_capital_tab(self):
        layout = QVBoxLayout(self.capital_tab)
        layout.setSpacing(15)
        
        info_label = QLabel("La funcionalidad de Gestión de Capital está en desarrollo.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def _create_status_bar(self, layout: QVBoxLayout):
        status_layout = QHBoxLayout()
        self.last_updated_label = QLabel("Última actualización: N/A")
        self.last_updated_label.setObjectName("subtitleLabel")
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self._start_update_worker)
        
        status_layout.addWidget(self.last_updated_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_button)
        layout.addLayout(status_layout)
        
        self.error_label = QLabel("")
        self.error_label.setProperty("class", "error")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

    def _create_assets_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Símbolo", "Cantidad", "Precio Entrada", "Precio Actual", "Valor USD", "PnL (%)"])
        
        h_header = table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.Stretch)
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def _create_open_trades_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Símbolo", "Tipo", "Cantidad", "Precio Entrada", "Precio Actual", 
            "Take Profit", "Stop Loss", "Estado TSL", "PnL Actual"
        ])
        
        h_header = table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(QHeaderView.Stretch)
        v_header = table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def setup_update_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(15000)
        self.update_timer.timeout.connect(self._start_update_worker)
        self.update_timer.start()
        logger.info("Timer de actualización del portafolio iniciado.")

    def _on_trading_mode_changed(self, new_mode: str):
        logger.info(f"PortfolioWidget: Modo de trading cambió a {new_mode}")
        self._update_mode_indicator()
        self._update_trades_title()
        self._start_update_worker()

    def _start_update_worker(self):
        current_mode = self.trading_mode_manager.current_mode
        user_id = self.user_id
        logger.info(f"Actualizando datos del portafolio para modo: {current_mode}")
        self.last_updated_label.setText(f"Actualizando portafolio ({current_mode.title()})...")
        if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(False)
        
        async def fetch_data_coroutine(api_client: UltiBotAPIClient) -> Dict[str, Any]:
            logger.debug(f"PortfolioWidget: Iniciando fetch_data_coroutine para modo {current_mode}.")
            
            snapshot_task = api_client.get_portfolio_snapshot(user_id, current_mode)
            open_trades_task = api_client.get_trades(trading_mode=current_mode, status="open")
            
            results = await asyncio.gather(
                snapshot_task, 
                open_trades_task,
                return_exceptions=True
            )
            
            return {
                "portfolio_snapshot": results[0],
                "open_trades": results[1],
                "trading_mode": current_mode
            }

        self._start_api_worker(fetch_data_coroutine, self._handle_update_result, self._handle_worker_error)

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
        self.balance_label.setText(f"{portfolio_mode_dict.get('available_balance_usdt', 0.0):,.2f} {currency}")
        self.total_assets_label.setText(f"{portfolio_mode_dict.get('total_assets_value_usd', 0.0):,.2f} USD")
        self.portfolio_value_label.setText(f"{portfolio_mode_dict.get('total_portfolio_value_usd', 0.0):,.2f} USD")
        self._populate_assets_table(self.assets_table, portfolio_mode_dict.get('assets', []))
        other_mode = "real" if mode == "paper" else "paper"
        other_mode_dict = snapshot_dict.get(f"{other_mode}_trading", {})
        self.comparison_info.setText(f"Portafolio {other_mode.title()}: {other_mode_dict.get('total_portfolio_value_usd', 0.0):,.2f} USD")

    def _populate_assets_table(self, table: QTableWidget, assets: List[Dict[str, Any]]):
        table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            self._set_item(table, row, 0, str(asset.get('symbol')))
            self._set_item(table, row, 1, f"{asset.get('quantity', 0):.6f}")
            self._set_item(table, row, 2, f"{asset.get('average_entry_price', 0):.4f}")
            self._set_item(table, row, 3, f"{asset.get('current_price', 0):.4f}")
            self._set_item(table, row, 4, f"{asset.get('value_in_usd', 0):.2f}")
            
            pnl = asset.get('pnl_percentage', 0) * 100
            pnl_item = QTableWidgetItem(f"{pnl:.2f}%")
            pnl_item.setForeground(QColor('green') if pnl >= 0 else QColor('red'))
            table.setItem(row, 5, pnl_item)

    def _update_open_trades_ui(self, trades: List[Dict[str, Any]]):
        self.trades_info_label.setVisible(not trades)
        self.open_trades_table.setRowCount(len(trades))
        for row, trade in enumerate(trades):
            self._set_item(self.open_trades_table, row, 0, str(trade.get('symbol')))
            self._set_item(self.open_trades_table, row, 1, str(trade.get('trade_type')))
            self._set_item(self.open_trades_table, row, 2, f"{trade.get('quantity', 0):.6f}")
            self._set_item(self.open_trades_table, row, 3, f"{trade.get('entry_price', 0):.4f}")
            self._set_item(self.open_trades_table, row, 4, f"{trade.get('current_price', 0):.4f}")
            self._set_item(self.open_trades_table, row, 5, f"{trade.get('take_profit_price', 0):.4f}")
            self._set_item(self.open_trades_table, row, 6, f"{trade.get('stop_loss_price', 0):.4f}")
            self._set_item(self.open_trades_table, row, 7, str(trade.get('tsl_status')))
            
            pnl = trade.get('pnl_percentage', 0) * 100
            pnl_item = QTableWidgetItem(f"{pnl:.2f}%")
            pnl_item.setForeground(QColor('green') if pnl >= 0 else QColor('red'))
            self.open_trades_table.setItem(row, 8, pnl_item)

    def _set_item(self, table: QTableWidget, row: int, col: int, text: Optional[str]):
        item = QTableWidgetItem(str(text) if text is not None else "")
        table.setItem(row, col, item)

    def _handle_worker_error(self, error_msg: str):
        logger.error(f"PortfolioWidget: Error en DataUpdateWorker: {error_msg}")
        self.error_label.setText("Error al cargar datos.")
        self.last_updated_label.setText("Actualización fallida.")

    def refresh_data(self):
        self._start_update_worker()

    def start_updates(self):
        self._start_update_worker()
        self.update_timer.start()

    def stop_updates(self):
        self.update_timer.stop()

    def cleanup(self):
        logger.info("PortfolioWidget: Limpiando hilos y workers activos.")
        self.stop_updates()
        for thread, worker in list(self.active_workers):
            if thread.isRunning():
                thread.quit()
                thread.wait(5000)
        self.active_workers.clear()
        logger.info("PortfolioWidget: Limpieza completada.")
