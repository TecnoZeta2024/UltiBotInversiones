"""
Widget para visualizar resultados y rendimiento del Paper Trading.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable, Coroutine
from uuid import UUID
import qasync

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QDateEdit, QPushButton, QGroupBox, QGridLayout,
    QHeaderView, QMessageBox, QProgressBar, QSplitter
)
from PyQt5.QtCore import Qt, QDate, pyqtSlot
from PyQt5.QtGui import QFont, QColor

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.shared.data_types import Trade, PerformanceMetrics
from src.ultibot_ui.models import BaseMainWindow

logger = logging.getLogger(__name__)

class PaperTradingReportWidget(QWidget):
    """
    Widget principal para mostrar resultados y rendimiento del Paper Trading.
    """
    
    def __init__(self, user_id: UUID, main_window: BaseMainWindow, api_client: UltiBotAPIClient, loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_window = main_window
        self.api_client = api_client
        self.loop = loop
        self.current_trades_data: List[Trade] = []
        self.current_metrics_data: Optional[PerformanceMetrics] = None
        
        self.setup_ui()
        self.connect_signals()
        
        self.load_data()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        title_label = QLabel("Resultados y Rendimiento - Paper Trading")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(main_splitter)
        
        metrics_group = self.setup_metrics_section()
        main_splitter.addWidget(metrics_group)
        
        trades_section = self.setup_trades_section()
        main_splitter.addWidget(trades_section)
        
        main_splitter.setSizes([200, 400])
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def setup_metrics_section(self) -> QGroupBox:
        """Configura la sección de métricas de rendimiento."""
        group = QGroupBox("Métricas de Rendimiento Consolidadas")
        layout = QGridLayout(group)
        
        self.total_trades_label = QLabel("0")
        self.win_rate_label = QLabel("0.00%")
        self.total_pnl_label = QLabel("$0.00")
        self.avg_pnl_label = QLabel("$0.00")
        self.best_trade_label = QLabel("$0.00")
        self.worst_trade_label = QLabel("$0.00")
        self.total_volume_label = QLabel("$0.00")
        
        metric_font = QFont()
        metric_font.setPointSize(12)
        metric_font.setBold(True)
        
        for label in [self.total_trades_label, self.win_rate_label, self.total_pnl_label, 
                     self.avg_pnl_label, self.best_trade_label, self.worst_trade_label, 
                     self.total_volume_label]:
            label.setFont(metric_font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(QLabel("Total de Operaciones:"), 0, 0)
        layout.addWidget(self.total_trades_label, 0, 1)
        layout.addWidget(QLabel("Win Rate:"), 0, 2)
        layout.addWidget(self.win_rate_label, 0, 3)
        layout.addWidget(QLabel("P&L Total:"), 1, 0)
        layout.addWidget(self.total_pnl_label, 1, 1)
        layout.addWidget(QLabel("P&L Promedio:"), 1, 2)
        layout.addWidget(self.avg_pnl_label, 1, 3)
        layout.addWidget(QLabel("Mejor Trade:"), 2, 0)
        layout.addWidget(self.best_trade_label, 2, 1)
        layout.addWidget(QLabel("Peor Trade:"), 2, 2)
        layout.addWidget(self.worst_trade_label, 2, 3)
        layout.addWidget(QLabel("Volumen Total:"), 3, 0)
        layout.addWidget(self.total_volume_label, 3, 1)
        
        return group
        
    def setup_trades_section(self) -> QWidget:
        """Configura la sección de tabla de trades."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        filters_layout.addWidget(QLabel("Par:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItem("Todos", "")
        self.symbol_combo.addItem("BTCUSDT", "BTCUSDT")
        self.symbol_combo.addItem("ETHUSDT", "ETHUSDT")
        filters_layout.addWidget(self.symbol_combo)
        
        filters_layout.addSpacing(20)
        
        filters_layout.addWidget(QLabel("Desde:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(self.start_date_edit)
        
        filters_layout.addWidget(QLabel("Hasta:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(self.end_date_edit)
        
        filters_layout.addSpacing(20)
        
        self.apply_filters_btn = QPushButton("Aplicar Filtros")
        filters_layout.addWidget(self.apply_filters_btn)
        
        self.refresh_btn = QPushButton("Refrescar")
        filters_layout.addWidget(self.refresh_btn)
        
        filters_layout.addStretch()
        
        layout.addWidget(filters_group)
        
        self.trades_table = QTableWidget()
        self.setup_trades_table()
        layout.addWidget(self.trades_table)
        
        return widget
        
    def setup_trades_table(self):
        """Configura la tabla de trades."""
        columns = [
            "Fecha Cierre", "Par", "Dirección", "Cantidad", 
            "Precio Entrada", "Precio Salida", "P&L ($)", "P&L (%)", 
            "Razón Cierre", "Confianza IA"
        ]
        
        self.trades_table.setColumnCount(len(columns))
        self.trades_table.setHorizontalHeaderLabels(columns)
        self.trades_table.setAlternatingRowColors(True)
        self.trades_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.trades_table.setSortingEnabled(True)
        
        header = self.trades_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
    def connect_signals(self):
        """Conecta las señales de la UI."""
        self.apply_filters_btn.clicked.connect(self.load_data)
        self.refresh_btn.clicked.connect(self.load_data)
        
    @qasync.asyncSlot()
    async def load_data(self):
        """Carga tanto las métricas como los trades."""
        self.load_metrics()
        self.load_trades()

    def load_metrics(self):
        """Carga las métricas de rendimiento."""
        self.show_loading(True)
        params = self.get_filters()
        coro_factory = lambda client: client.get_trading_performance(trading_mode="paper", **params)
        self.main_window.submit_task(coro_factory, self._on_metrics_received, self.on_error)
        
    def load_trades(self):
        """Carga la lista de trades."""
        params = self.get_filters()
        params['limit'] = 500
        params['offset'] = 0
        coro_factory = lambda client: client.get_trades(trading_mode="paper", **params)
        self.main_window.submit_task(coro_factory, self._on_trades_received, self.on_error)

    def get_filters(self) -> Dict[str, Any]:
        """Recopila los filtros de la UI."""
        filters = {}
        symbol = self.symbol_combo.currentData()
        if symbol:
            filters['symbol_filter'] = symbol
        
        start_date = self.start_date_edit.date().toPyDate()
        filters['date_from'] = start_date.isoformat()
        
        end_date = self.end_date_edit.date().toPyDate()
        filters['date_to'] = end_date.isoformat()
        
        return filters
        
    @qasync.asyncSlot(object)
    async def _on_metrics_received(self, data: object):
        """Maneja la carga exitosa de métricas."""
        try:
            if not isinstance(data, dict):
                error_msg = f"Tipo de dato inesperado para métricas: se esperaba un dict pero se recibió {type(data).__name__}"
                logger.error(error_msg)
                self.on_error(error_msg)
                return
            metrics = PerformanceMetrics(**data)
            self.current_metrics_data = metrics
            self.update_metrics_display(metrics)
            logger.info("Métricas de rendimiento cargadas exitosamente")
        except (TypeError, ValueError) as e:
            logger.error(f"Error procesando métricas: {e}", exc_info=True)
            self.show_error_message(f"Error procesando métricas: {str(e)}")
        finally:
            self.show_loading(False)
            
    @qasync.asyncSlot(object)
    async def _on_trades_received(self, data: object):
        """Maneja la carga exitosa de trades."""
        try:
            if not isinstance(data, list):
                error_msg = f"Tipo de dato inesperado para trades: se esperaba una lista pero se recibió {type(data).__name__}"
                logger.error(error_msg)
                self.on_error(error_msg)
                return
            self.current_trades_data = [Trade(**t) for t in data]
            self.update_trades_table(self.current_trades_data)
            logger.info(f"Trades cargados exitosamente: {len(self.current_trades_data)} trades")
        except (TypeError, ValueError) as e:
            logger.error(f"Error procesando trades: {e}", exc_info=True)
            self.show_error_message(f"Error procesando trades: {str(e)}")
        finally:
            self.show_loading(False)
            
    @pyqtSlot(str)
    def on_error(self, error_message: str):
        """Maneja errores en la carga de datos."""
        self.show_loading(False)
        self.show_error_message(f"Error cargando datos: {error_message}")
        
    def update_metrics_display(self, metrics: PerformanceMetrics):
        """Actualiza la visualización de métricas."""
        self.total_trades_label.setText(str(metrics.total_trades))
        self.win_rate_label.setText(f"{metrics.win_rate:.2f}%")
        
        total_pnl = metrics.total_pnl
        self.total_pnl_label.setText(f"${total_pnl:.2f}")
        self.total_pnl_label.setStyleSheet("color: green;" if total_pnl > 0 else "color: red;" if total_pnl < 0 else "color: black;")
        
        self.avg_pnl_label.setText(f"${metrics.avg_pnl_per_trade:.2f}")
        self.best_trade_label.setText(f"${metrics.best_trade_pnl:.2f}")
        self.best_trade_label.setStyleSheet("color: green;")
        self.worst_trade_label.setText(f"${metrics.worst_trade_pnl:.2f}")
        self.worst_trade_label.setStyleSheet("color: red;")
        self.total_volume_label.setText(f"${metrics.total_volume_traded:.2f}")
        
    def update_trades_table(self, trades: List[Trade]):
        """Actualiza la tabla de trades."""
        self.trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            closed_at_str = trade.closed_at.strftime('%Y-%m-%d %H:%M') if trade.closed_at else "N/A"
            self.trades_table.setItem(row, 0, QTableWidgetItem(closed_at_str))
            
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade.symbol or 'N/A'))
            
            side_item = QTableWidgetItem(trade.side.upper() if trade.side else 'N/A')
            if trade.side == 'buy':
                side_item.setBackground(QColor(200, 255, 200))
            elif trade.side == 'sell':
                side_item.setBackground(QColor(255, 200, 200))
            self.trades_table.setItem(row, 2, side_item)
            
            quantity = trade.entryOrder.executedQuantity if trade.entryOrder else 0.0
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"{quantity:.6f}"))
            
            entry_price = trade.entryOrder.executedPrice if trade.entryOrder else 0.0
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"${entry_price:.4f}"))
            
            exit_price = trade.exitOrders[0].executedPrice if trade.exitOrders else 0.0
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"${exit_price:.4f}"))
            
            pnl_usd = trade.pnl_usd or 0.0
            pnl_item = QTableWidgetItem(f"${pnl_usd:.2f}")
            if pnl_usd > 0: pnl_item.setBackground(QColor(200, 255, 200))
            elif pnl_usd < 0: pnl_item.setBackground(QColor(255, 200, 200))
            self.trades_table.setItem(row, 6, pnl_item)
            
            pnl_pct = trade.pnl_percentage or 0.0
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.2f}%")
            if pnl_pct > 0: pnl_pct_item.setBackground(QColor(200, 255, 200))
            elif pnl_pct < 0: pnl_pct_item.setBackground(QColor(255, 200, 200))
            self.trades_table.setItem(row, 7, pnl_pct_item)
            
            self.trades_table.setItem(row, 8, QTableWidgetItem(trade.closingReason or 'N/A'))
            
            confidence_str = f"{trade.aiAnalysisConfidence:.2f}" if trade.aiAnalysisConfidence else "N/A"
            self.trades_table.setItem(row, 9, QTableWidgetItem(confidence_str))
            
    def show_loading(self, loading: bool):
        """Muestra/oculta el indicador de carga."""
        self.progress_bar.setVisible(loading)
        if loading:
            self.progress_bar.setRange(0, 0)
        
    def show_error_message(self, message: str):
        """Muestra un mensaje de error al usuario."""
        QMessageBox.critical(self, "Error", message)
        logger.error(f"Error mostrado al usuario: {message}")

    def cleanup(self):
        """Limpia los recursos del widget."""
        logger.info("PaperTradingReportWidget cleanup: No hay acciones que tomar.")
        pass
