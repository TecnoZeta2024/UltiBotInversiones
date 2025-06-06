"""
Widget para visualizar resultados y rendimiento del Paper Trading.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QComboBox, QDateEdit, QPushButton, QGroupBox, QGridLayout,
    QHeaderView, QMessageBox, QProgressBar, QSplitter
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

import uuid # Importar uuid para FIXED_USER_ID

class DataLoadWorker(QThread):
    """Worker thread para cargar datos de la API sin bloquear la UI."""
    
    data_loaded = pyqtSignal(object)  # Cambiado a object para manejar List o Dict
    error_occurred = pyqtSignal(str)  # Señal emitida cuando hay un error
    
    def __init__(self, api_client: UltiBotAPIClient, load_type: str, user_id: Optional[uuid.UUID] = None, **kwargs): # Añadido user_id
        super().__init__()
        self.api_client = api_client
        self.load_type = load_type
        self.user_id = user_id # Almacenar user_id
        self.kwargs = kwargs
        
    def run(self):
        """Ejecuta la carga de datos en el hilo secundario."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.load_type == "trades":
                if not self.user_id:
                    raise ValueError("user_id es requerido para cargar trades.")
                # Pasar user_id explícitamente, el resto de kwargs se mantienen
                result = loop.run_until_complete(
                    self.api_client.get_paper_trading_history(user_id=self.user_id, **self.kwargs)
                )
            elif self.load_type == "metrics":
                # get_paper_trading_performance no toma user_id en api_client.py actualmente
                result = loop.run_until_complete(
                    self.api_client.get_paper_trading_performance(**self.kwargs)
                )
            else:
                raise ValueError(f"Unknown load_type: {self.load_type}")
                
            self.data_loaded.emit(result)
            
        except Exception as e:
            logger.error(f"Error loading {self.load_type}: {e}", exc_info=True)
            self.error_occurred.emit(str(e))
        finally:
            loop.close()

class PaperTradingReportWidget(QWidget):
    """
    Widget principal para mostrar resultados y rendimiento del Paper Trading.
    """
    
    def __init__(self, user_id: uuid.UUID, backend_base_url: str, parent=None): # Modificado
        super().__init__(parent)
        self.user_id = user_id # Nuevo
        self.backend_base_url = backend_base_url # Nuevo
        self.api_client = UltiBotAPIClient(base_url=self.backend_base_url) # Modificado
        self.current_trades_data = []
        self.current_metrics_data = {}
        
        self.setup_ui()
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_data()
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Título principal
        title_label = QLabel("Resultados y Rendimiento - Paper Trading")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Splitter principal para dividir métricas y tabla
        main_splitter = QSplitter(Qt.Orientation.Vertical) # Modificado
        layout.addWidget(main_splitter)
        
        # === SECCIÓN 1: MÉTRICAS DE RENDIMIENTO ===
        metrics_group = self.setup_metrics_section()
        main_splitter.addWidget(metrics_group)
        
        # === SECCIÓN 2: FILTROS Y TABLA DE TRADES ===
        trades_section = self.setup_trades_section()
        main_splitter.addWidget(trades_section)
        
        # Configurar tamaños del splitter
        main_splitter.setSizes([200, 400])  # Métricas más pequeñas, tabla más grande
        
        # Barra de progreso para indicar carga
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def setup_metrics_section(self) -> QGroupBox:
        """Configura la sección de métricas de rendimiento."""
        group = QGroupBox("Métricas de Rendimiento Consolidadas")
        layout = QGridLayout(group)
        
        # Crear labels para las métricas
        self.total_trades_label = QLabel("0")
        self.win_rate_label = QLabel("0.00%")
        self.total_pnl_label = QLabel("$0.00")
        self.avg_pnl_label = QLabel("$0.00")
        self.best_trade_label = QLabel("$0.00")
        self.worst_trade_label = QLabel("$0.00")
        self.total_volume_label = QLabel("$0.00")
        
        # Configurar estilos para las métricas
        metric_font = QFont()
        metric_font.setPointSize(12)
        metric_font.setBold(True)
        
        for label in [self.total_trades_label, self.win_rate_label, self.total_pnl_label, 
                     self.avg_pnl_label, self.best_trade_label, self.worst_trade_label, 
                     self.total_volume_label]:
            label.setFont(metric_font)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Modificado
        
        # Organizar métricas en grid
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
        
        # === CONTROLES DE FILTROS ===
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout(filters_group)
        
        # Filtro por par
        filters_layout.addWidget(QLabel("Par:"))
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItem("Todos", "")
        self.symbol_combo.addItem("BTCUSDT", "BTCUSDT")
        self.symbol_combo.addItem("ETHUSDT", "ETHUSDT")
        self.symbol_combo.addItem("ADAUSDT", "ADAUSDT")
        self.symbol_combo.addItem("DOTUSDT", "DOTUSDT")
        self.symbol_combo.addItem("LINKUSDT", "LINKUSDT")
        filters_layout.addWidget(self.symbol_combo)
        
        filters_layout.addWidget(QLabel("  |  "))
        
        # Filtro por fecha desde
        filters_layout.addWidget(QLabel("Desde:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))  # Últimos 30 días por defecto
        self.start_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(self.start_date_edit)
        
        # Filtro por fecha hasta
        filters_layout.addWidget(QLabel("Hasta:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        filters_layout.addWidget(self.end_date_edit)
        
        filters_layout.addWidget(QLabel("  |  "))
        
        # Botón para aplicar filtros
        self.apply_filters_btn = QPushButton("Aplicar Filtros")
        filters_layout.addWidget(self.apply_filters_btn)
        
        # Botón para refrescar
        self.refresh_btn = QPushButton("Refrescar")
        filters_layout.addWidget(self.refresh_btn)
        
        filters_layout.addStretch()  # Empujar controles hacia la izquierda
        
        layout.addWidget(filters_group)
        
        # === TABLA DE TRADES ===
        self.trades_table = QTableWidget()
        self.setup_trades_table()
        layout.addWidget(self.trades_table)
        
        return widget
        
    def setup_trades_table(self):
        """Configura la tabla de trades."""
        # Definir columnas
        columns = [
            "Fecha Cierre", "Par", "Dirección", "Cantidad", 
            "Precio Entrada", "Precio Salida", "P&L ($)", "P&L (%)", 
            "Razón Cierre", "Confianza IA"
        ]
        
        self.trades_table.setColumnCount(len(columns))
        self.trades_table.setHorizontalHeaderLabels(columns)
        
        # Configurar propiedades de la tabla
        self.trades_table.setAlternatingRowColors(True)
        self.trades_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trades_table.setSortingEnabled(True)
        
        # Configurar tamaños de columnas
        header = self.trades_table.horizontalHeader()
        if header: # Añadida comprobación
            header.setStretchLastSection(True)
        
        # Ajustar ancho de columnas específicas
        self.trades_table.setColumnWidth(0, 120)  # Fecha
        self.trades_table.setColumnWidth(1, 80)   # Par
        self.trades_table.setColumnWidth(2, 80)   # Dirección
        self.trades_table.setColumnWidth(3, 100)  # Cantidad
        self.trades_table.setColumnWidth(4, 100)  # Precio Entrada
        self.trades_table.setColumnWidth(5, 100)  # Precio Salida
        self.trades_table.setColumnWidth(6, 80)   # P&L ($)
        self.trades_table.setColumnWidth(7, 80)   # P&L (%)
        
    def connect_signals(self):
        """Conecta las señales de la UI."""
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        self.refresh_btn.clicked.connect(self.load_data)
        
    def apply_filters(self):
        """Aplica los filtros seleccionados y recarga los datos."""
        self.load_data()
        
    def load_data(self):
        """Carga tanto las métricas como los trades."""
        self.load_metrics()
        self.load_trades()
        
    def load_metrics(self):
        """Carga las métricas de rendimiento."""
        self.show_loading(True)
        
        # Obtener filtros
        symbol = self.symbol_combo.currentData() if hasattr(self, 'symbol_combo') else ""
        start_date = None
        end_date = None
        
        if hasattr(self, 'start_date_edit'):
            start_date = self.start_date_edit.date().toPyDate()
            start_date = datetime.combine(start_date, datetime.min.time())
            
        if hasattr(self, 'end_date_edit'):
            end_date = self.end_date_edit.date().toPyDate()
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Crear worker para cargar métricas
        self.metrics_worker = DataLoadWorker(
            self.api_client, 
            "metrics",
            symbol=symbol if symbol else None,
            start_date=start_date,
            end_date=end_date
        )
        self.metrics_worker.data_loaded.connect(self.on_metrics_loaded)
        self.metrics_worker.error_occurred.connect(self.on_error)
        self.metrics_worker.start()
        
    def load_trades(self):
        """Carga la lista de trades."""
        # Obtener filtros
        symbol = self.symbol_combo.currentData() if hasattr(self, 'symbol_combo') else ""
        start_date = None
        end_date = None
        
        if hasattr(self, 'start_date_edit'):
            start_date = self.start_date_edit.date().toPyDate()
            start_date = datetime.combine(start_date, datetime.min.time())
            
        if hasattr(self, 'end_date_edit'):
            end_date = self.end_date_edit.date().toPyDate()
            end_date = datetime.combine(end_date, datetime.max.time())
        
        # Crear worker para cargar trades
        self.trades_worker = DataLoadWorker(
            self.api_client,
            "trades",
            symbol=symbol if symbol else None,
            start_date=start_date,
            end_date=end_date,
            limit=500,  # Cargar hasta 500 trades por ahora
            offset=0,
            # TODO: Obtener el user_id de una fuente apropiada (configuración, sesión, etc.)
            # Por ahora, usamos el FIXED_USER_ID conocido del backend.
            user_id=self.user_id # Modificado
        )
        self.trades_worker.data_loaded.connect(self.on_trades_loaded)
        self.trades_worker.error_occurred.connect(self.on_error)
        self.trades_worker.start()
        
    @pyqtSlot(dict)
    def on_metrics_loaded(self, data: Dict[str, Any]):
        """Maneja la carga exitosa de métricas."""
        try:
            self.current_metrics_data = data
            self.update_metrics_display(data)
            logger.info("Métricas de rendimiento cargadas exitosamente")
        except Exception as e:
            logger.error(f"Error procesando métricas: {e}", exc_info=True)
            self.show_error_message(f"Error procesando métricas: {str(e)}")
        finally:
            self.show_loading(False)
            
    @pyqtSlot(object) # Cambiado a object
    def on_trades_loaded(self, data: List[Dict[str, Any]]): # Cambiado a List[Dict[str, Any]]
        """Maneja la carga exitosa de trades."""
        try:
            # get_paper_trading_history ahora devuelve una lista directamente
            self.current_trades_data = data 
            self.update_trades_table(self.current_trades_data)
            logger.info(f"Trades cargados exitosamente: {len(self.current_trades_data)} trades")
        except Exception as e:
            logger.error(f"Error procesando trades: {e}", exc_info=True)
            self.show_error_message(f"Error procesando trades: {str(e)}")
        finally:
            self.show_loading(False)
            
    @pyqtSlot(str)
    def on_error(self, error_message: str):
        """Maneja errores en la carga de datos."""
        self.show_loading(False)
        self.show_error_message(f"Error cargando datos: {error_message}")
        
    def update_metrics_display(self, metrics: Dict[str, Any]):
        """Actualiza la visualización de métricas."""
        self.total_trades_label.setText(str(metrics.get('total_trades', 0)))
        
        win_rate = metrics.get('win_rate', 0.0)
        self.win_rate_label.setText(f"{win_rate:.2f}%")
        
        total_pnl = metrics.get('total_pnl', 0.0)
        self.total_pnl_label.setText(f"${total_pnl:.2f}")
        
        # Colorear P&L total según ganancia/pérdida
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet("color: green;")
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet("color: red;")
        else:
            self.total_pnl_label.setStyleSheet("color: black;")
        
        avg_pnl = metrics.get('avg_pnl_per_trade', 0.0)
        self.avg_pnl_label.setText(f"${avg_pnl:.2f}")
        
        best_trade = metrics.get('best_trade_pnl', 0.0)
        self.best_trade_label.setText(f"${best_trade:.2f}")
        self.best_trade_label.setStyleSheet("color: green;")
        
        worst_trade = metrics.get('worst_trade_pnl', 0.0)
        self.worst_trade_label.setText(f"${worst_trade:.2f}")
        self.worst_trade_label.setStyleSheet("color: red;")
        
        total_volume = metrics.get('total_volume_traded', 0.0)
        self.total_volume_label.setText(f"${total_volume:.2f}")
        
    def update_trades_table(self, trades: List[Dict[str, Any]]):
        """Actualiza la tabla de trades."""
        self.trades_table.setRowCount(len(trades))
        
        for row, trade in enumerate(trades):
            # Fecha de cierre
            closed_at = trade.get('closed_at')
            if closed_at:
                if isinstance(closed_at, str):
                    try:
                        closed_date = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
                        closed_str = closed_date.strftime('%Y-%m-%d %H:%M')
                    except:
                        closed_str = closed_at
                else:
                    closed_str = str(closed_at)
            else:
                closed_str = "N/A"
            self.trades_table.setItem(row, 0, QTableWidgetItem(closed_str))
            
            # Par
            symbol = trade.get('symbol', 'N/A')
            self.trades_table.setItem(row, 1, QTableWidgetItem(symbol))
            
            # Dirección
            side = trade.get('side', 'N/A').upper()
            side_item = QTableWidgetItem(side)
            if side == 'BUY':
                side_item.setBackground(QColor(200, 255, 200))  # Verde claro
            elif side == 'SELL':
                side_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            self.trades_table.setItem(row, 2, side_item)
            
            # Cantidad
            entry_order = trade.get('entryOrder', {})
            quantity = entry_order.get('executedQuantity', 0.0)
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"{quantity:.6f}"))
            
            # Precio entrada
            entry_price = entry_order.get('executedPrice', 0.0)
            self.trades_table.setItem(row, 4, QTableWidgetItem(f"${entry_price:.4f}"))
            
            # Precio salida (aproximado del primer exit order)
            exit_orders = trade.get('exitOrders', [])
            exit_price = 0.0
            if exit_orders:
                exit_price = exit_orders[0].get('executedPrice', 0.0)
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"${exit_price:.4f}"))
            
            # P&L absoluto
            pnl_usd = trade.get('pnl_usd', 0.0)
            pnl_item = QTableWidgetItem(f"${pnl_usd:.2f}")
            if pnl_usd > 0:
                pnl_item.setBackground(QColor(200, 255, 200))  # Verde claro
            elif pnl_usd < 0:
                pnl_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            self.trades_table.setItem(row, 6, pnl_item)
            
            # P&L porcentual
            pnl_pct = trade.get('pnl_percentage', 0.0)
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:.2f}%")
            if pnl_pct > 0:
                pnl_pct_item.setBackground(QColor(200, 255, 200))  # Verde claro
            elif pnl_pct < 0:
                pnl_pct_item.setBackground(QColor(255, 200, 200))  # Rojo claro
            self.trades_table.setItem(row, 7, pnl_pct_item)
            
            # Razón de cierre
            closing_reason = trade.get('closingReason', 'N/A')
            self.trades_table.setItem(row, 8, QTableWidgetItem(closing_reason))
            
            # Confianza IA
            ai_confidence = trade.get('aiAnalysisConfidence', 0.0)
            if ai_confidence:
                confidence_str = f"{ai_confidence:.2f}"
            else:
                confidence_str = "N/A"
            self.trades_table.setItem(row, 9, QTableWidgetItem(confidence_str))
            
    def show_loading(self, loading: bool):
        """Muestra/oculta el indicador de carga."""
        self.progress_bar.setVisible(loading)
        if loading:
            self.progress_bar.setRange(0, 0)  # Barra de progreso indeterminada
        
    def show_error_message(self, message: str):
        """Muestra un mensaje de error al usuario."""
        QMessageBox.critical(self, "Error", message)
        logger.error(f"Error mostrado al usuario: {message}")
