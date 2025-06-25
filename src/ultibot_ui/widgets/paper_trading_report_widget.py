"""
Widget para visualizar resultados y rendimiento del Paper Trading.
"""

import logging
import datetime
from typing import Optional, List, Dict, Any, Callable, Coroutine, cast
from uuid import UUID

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QDateEdit, QPushButton, QGroupBox, QGridLayout,
    QHeaderView, QMessageBox, QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QDate, QThread
from PySide6.QtGui import QFont, QColor
from decimal import Decimal # Importar Decimal

from ultibot_ui.services.api_client import UltiBotAPIClient
from shared.data_types import Trade, PerformanceMetrics
from ultibot_ui.workers import ApiWorker
from ultibot_ui.models import BaseMainWindow

logger = logging.getLogger(__name__)

class PaperTradingReportWidget(QWidget):
    """
    Widget principal para mostrar resultados y rendimiento del Paper Trading.
    """
    
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, parent=None):
        super().__init__(parent)
        self.user_id: Optional[UUID] = None # Se inicializará asíncronamente
        self.api_client = api_client
        self.main_window = main_window
        self.current_trades_data: List[Trade] = []
        self.current_metrics_data: Optional[PerformanceMetrics] = None
        
        self.setup_ui()
        self.connect_signals()
        
        # No llamar a load_data aquí, se llamará después de set_user_id
        
    def set_user_id(self, user_id: UUID):
        """Establece el user_id y activa la carga de datos."""
        self.user_id = user_id
        logger.info(f"PaperTradingReportWidget: User ID set to {user_id}. Loading data.")
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
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        self.refresh_btn.clicked.connect(self.load_data)
        
    def apply_filters(self):
        """Aplica los filtros seleccionados y recarga los datos."""
        self.load_data()
        
    def load_data(self):
        """Carga tanto las métricas como los trades."""
        if self.user_id is None:
            logger.warning("PaperTradingReportWidget: user_id no está disponible. No se pueden cargar los datos.")
            self.show_error_message("Error: Configuración de usuario no cargada. Intente reiniciar la aplicación.")
            return
        self.load_metrics()
        self.load_trades()

    def _start_api_worker(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success, on_error):
        worker = ApiWorker(api_client=self.api_client, coroutine_factory=coroutine_factory)
        thread = QThread()
        worker.moveToThread(thread)

        worker.result_ready.connect(on_success)
        worker.error_occurred.connect(on_error)
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        self.main_window.add_thread(thread)
        thread.start()
        
    def load_metrics(self):
        """Carga las métricas de rendimiento."""
        self.show_loading(True)
        params = self.get_filters()
        # Obtener todos los trades para el cálculo de métricas en el frontend
        coro_factory = lambda client: client.get_trades(user_id=self.user_id, trading_mode="paper", status="closed", **params)
        self._start_api_worker(coro_factory, self._calculate_and_display_metrics, self.on_error)
        
    def load_trades(self):
        """Carga la lista de trades."""
        self.show_loading(True)
        params = self.get_filters()
        params['limit'] = 500
        params['offset'] = 0
        # Obtener trades cerrados para la tabla
        coro_factory = lambda client: client.get_trades(user_id=self.user_id, trading_mode="paper", status="closed", **params)
        self._start_api_worker(coro_factory, self.on_trades_loaded, self.on_error)

    def get_filters(self) -> Dict[str, Any]:
        """Recopila los filtros de la UI."""
        filters = {}
        symbol = self.symbol_combo.currentData()
        if symbol:
            filters['symbol_filter'] = symbol
        
        start_date = cast(datetime.date, self.start_date_edit.date().toPython())
        filters['date_from'] = start_date.isoformat()
        
        end_date = cast(datetime.date, self.end_date_edit.date().toPython())
        filters['date_to'] = end_date.isoformat()
        
        return filters
        
    def _calculate_and_display_metrics(self, trades_data: List[Dict[str, Any]]):
        """
        Calcula las métricas de rendimiento a partir de los trades y actualiza la UI.
        """
        try:
            trades = [Trade.model_validate(t) for t in trades_data]
            
            total_trades = len(trades)
            winning_trades = 0
            losing_trades = 0
            total_pnl = Decimal('0.0')
            best_trade_pnl = Decimal('-999999999.0')
            worst_trade_pnl = Decimal('999999999.0')
            total_volume_traded = Decimal('0.0')
            
            for trade in trades:
                if trade.pnl_usd is not None:
                    total_pnl += trade.pnl_usd
                    if trade.pnl_usd > 0:
                        winning_trades += 1
                    elif trade.pnl_usd < 0:
                        losing_trades += 1
                    
                    if trade.pnl_usd > best_trade_pnl:
                        best_trade_pnl = trade.pnl_usd
                    if trade.pnl_usd < worst_trade_pnl:
                        worst_trade_pnl = trade.pnl_usd
                
                if trade.entryOrder and trade.entryOrder.cumulativeQuoteQty:
                    total_volume_traded += trade.entryOrder.cumulativeQuoteQty
            
            win_rate = Decimal('0.0')
            if total_trades > 0:
                win_rate = (Decimal(winning_trades) / Decimal(total_trades)) * 100
            
            avg_pnl_per_trade = Decimal('0.0')
            if total_trades > 0:
                avg_pnl_per_trade = total_pnl / Decimal(total_trades)

            metrics = PerformanceMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                avg_pnl_per_trade=avg_pnl_per_trade,
                best_trade_pnl=best_trade_pnl if best_trade_pnl != Decimal('-999999999.0') else Decimal('0.0'),
                worst_trade_pnl=worst_trade_pnl if worst_trade_pnl != Decimal('999999999.0') else Decimal('0.0'),
                best_trade_symbol=None, # Añadir valores por defecto
                worst_trade_symbol=None, # Añadir valores por defecto
                period_start=None, # Añadir valores por defecto
                period_end=None, # Añadir valores por defecto
                total_volume_traded=total_volume_traded
            )
            
            self.current_metrics_data = metrics
            self.update_metrics_display(metrics)
            logger.info("Métricas de rendimiento calculadas y cargadas exitosamente.")
        except Exception as e:
            logger.error(f"Error calculando métricas: {e}", exc_info=True)
            self.show_error_message(f"Error calculando métricas: {str(e)}")
        finally:
            self.show_loading(False)
            
    def on_trades_loaded(self, data: object):
        """Maneja la carga exitosa de trades."""
        try:
            if not isinstance(data, list):
                error_msg = f"Tipo de dato inesperado para trades: se esperaba una lista pero se recibió {type(data).__name__}"
                logger.error(error_msg)
                self.on_error(error_msg)
                return
            self.current_trades_data = data 
            self.update_trades_table(self.current_trades_data)
            logger.info(f"Trades cargados exitosamente: {len(self.current_trades_data)} trades")
        except Exception as e:
            logger.error(f"Error procesando trades: {e}", exc_info=True)
            self.show_error_message(f"Error procesando trades: {str(e)}")
        finally:
            self.show_loading(False)
            
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
