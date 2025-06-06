import logging
import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QPushButton,
    QTabWidget, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool
from PyQt5.QtGui import QFont, QColor

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_ui.services.api_client import UltiBotAPIClient
# Import TradingModeService and TradingMode (from subtask 3)
from src.ultibot_ui.services import TradingModeService, TradingMode


logger = logging.getLogger(__name__)

class DataUpdateWorker(QRunnable):
    """
    Worker para actualizar datos del portafolio y operaciones abiertas.
    """
    def __init__(self, user_id: UUID, portfolio_service: PortfolioService, api_client: UltiBotAPIClient):
        super().__init__()
        self.user_id = user_id
        self.portfolio_service = portfolio_service
        self.api_client = api_client
        self.signals = WorkerSignals()

    def run(self):
        """
        Ejecuta la actualización de datos en un hilo separado.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Obtener snapshot del portafolio
            portfolio_snapshot = loop.run_until_complete(
                self.portfolio_service.get_portfolio_snapshot(self.user_id)
            )
            
            # Obtener trades abiertos
            open_trades = loop.run_until_complete(
                self.api_client.get_open_trades("all")
            )
            
            # Obtener estado de gestión de capital
            capital_status = loop.run_until_complete(
                self.api_client.get_capital_management_status()
            )
            
            result_data = {
                "portfolio_snapshot": portfolio_snapshot,
                "open_trades": open_trades,
                "capital_status": capital_status
            }
            
            self.signals.result.emit(result_data)
            
        except Exception as e:
            error_msg = f"Error actualizando datos del portafolio: {e}"
            logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QObject):
    """
    Señales disponibles de un worker.
    """
    result = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal()

class PortfolioWidget(QWidget):
    """
    Widget extendido para la visualización del estado del portafolio incluyendo
    TSL/TP y gestión de capital.
    """
    portfolio_updated = pyqtSignal(PortfolioSnapshot)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_id: UUID, portfolio_service: PortfolioService,
                 trading_mode_service: TradingModeService, # Added trading_mode_service (from subtask 3)
                 api_client: Optional[UltiBotAPIClient] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.portfolio_service = portfolio_service
        self.trading_mode_service = trading_mode_service # Store trading_mode_service (from subtask 3)
        self.api_client = api_client or UltiBotAPIClient()
        self.current_snapshot: Optional[PortfolioSnapshot] = None
        self.current_capital_status: Optional[Dict[str, Any]] = None
        self.open_trades: List[Dict[str, Any]] = []
        self.thread_pool = QThreadPool()

        self.init_ui()
        self.setup_update_timer()

        # Connect to TradingModeService signal and set initial visibility (from subtask 3)
        self.trading_mode_service.mode_changed.connect(self._handle_mode_change)
        self._update_visibility_based_on_mode()

    def init_ui(self):
        """
        Inicializa la interfaz de usuario con pestañas para mejor organización.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(10)

        # Título principal
        title_label = QLabel("Estado del Portafolio y Operaciones")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Crear widget de pestañas
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Pestaña 1: Resumen del Portafolio
        self.portfolio_tab = QWidget()
        self.init_portfolio_tab()
        self.tab_widget.addTab(self.portfolio_tab, "Portafolio")

        # Pestaña 2: Operaciones Abiertas (TSL/TP)
        self.trades_tab = QWidget()
        self.init_trades_tab()
        self.tab_widget.addTab(self.trades_tab, "Operaciones Abiertas")

        # Pestaña 3: Gestión de Capital
        self.capital_tab = QWidget()
        self.init_capital_tab()
        self.tab_widget.addTab(self.capital_tab, "Gestión de Capital")

        # Barra de estado y última actualización
        status_layout = QHBoxLayout()
        self.last_updated_label = QLabel("Última actualización: N/A")
        self.last_updated_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self._start_update_worker)
        self.refresh_button.setMaximumWidth(100)
        
        status_layout.addWidget(self.last_updated_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_button)
        main_layout.addLayout(status_layout)

        # Label de error
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.error_label)

    def init_portfolio_tab(self):
        """
        Inicializa la pestaña de resumen del portafolio.
        """
        layout = QVBoxLayout(self.portfolio_tab)
        layout.setSpacing(15)

        # Grupo para Paper Trading
        self.paper_trading_group = self._create_portfolio_group("Paper Trading")
        self.paper_balance_label = QLabel("Saldo Disponible: N/A")
        self.paper_total_value_label = QLabel("Valor Total Activos: N/A")
        self.paper_portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        self.paper_assets_table = self._create_assets_table()
        
        paper_layout = self.paper_trading_group.layout()
        if isinstance(paper_layout, QFormLayout):
            paper_layout.addRow(self.paper_balance_label)
            paper_layout.addRow(self.paper_total_value_label)
            paper_layout.addRow(self.paper_portfolio_value_label)
            paper_layout.addRow(QLabel("Activos Poseídos:"))
            paper_layout.addRow(self.paper_assets_table)
        layout.addWidget(self.paper_trading_group)

        # Grupo para Real Trading
        self.real_trading_group = self._create_portfolio_group("Real Trading (Binance)")
        self.real_balance_label = QLabel("Saldo Disponible (USDT): N/A")
        self.real_total_value_label = QLabel("Valor Total Activos: N/A")
        self.real_portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        self.real_assets_table = self._create_assets_table()
        
        real_layout = self.real_trading_group.layout()
        if isinstance(real_layout, QFormLayout):
            real_layout.addRow(self.real_balance_label)
            real_layout.addRow(self.real_total_value_label)
            real_layout.addRow(self.real_portfolio_value_label)
            real_layout.addRow(QLabel("Activos Poseídos:"))
            real_layout.addRow(self.real_assets_table)
        layout.addWidget(self.real_trading_group)

    def init_trades_tab(self):
        """
        Inicializa la pestaña de operaciones abiertas con TSL/TP.
        """
        layout = QVBoxLayout(self.trades_tab)
        layout.setSpacing(15)

        # Título
        trades_title = QLabel("Operaciones Abiertas con TSL/TP Activos")
        trades_title.setFont(QFont("Arial", 14, QFont.Bold))
        trades_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(trades_title)

        # Tabla de operaciones abiertas
        self.open_trades_table = self._create_open_trades_table()
        layout.addWidget(self.open_trades_table)

        # Información adicional
        self.trades_info_label = QLabel("No hay operaciones abiertas")
        self.trades_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trades_info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.trades_info_label)

    def init_capital_tab(self):
        """
        Inicializa la pestaña de gestión de capital.
        """
        layout = QVBoxLayout(self.capital_tab)
        layout.setSpacing(15)

        # Grupo de estado de capital
        self.capital_status_group = self._create_portfolio_group("Estado de Gestión de Capital")
        capital_layout = QFormLayout()
        
        # Labels para información de capital
        self.total_capital_label = QLabel("Capital Total: N/A")
        self.available_capital_label = QLabel("Disponible para Nuevas Operaciones: N/A")
        self.committed_capital_label = QLabel("Capital Comprometido Hoy: N/A")
        self.daily_limit_label = QLabel("Límite Diario (50%): N/A")
        
        capital_layout.addRow(self.total_capital_label)
        capital_layout.addRow(self.available_capital_label)
        capital_layout.addRow(self.committed_capital_label)
        capital_layout.addRow(self.daily_limit_label)
        
        # Barra de progreso del límite diario
        capital_layout.addRow(QLabel("Uso del Límite Diario:"))
        self.daily_usage_progress = QProgressBar()
        self.daily_usage_progress.setRange(0, 100)
        self.daily_usage_progress.setValue(0)
        self.daily_usage_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                background-color: #2C2C2C;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
            QProgressBar[value="85"]::chunk,
            QProgressBar[value="90"]::chunk,
            QProgressBar[value="95"]::chunk {
                background-color: #ffc107;
            }
            QProgressBar[value="100"]::chunk {
                background-color: #dc3545;
            }
        """)
        capital_layout.addRow(self.daily_usage_progress)
        
        self.capital_status_group.setLayout(capital_layout)
        layout.addWidget(self.capital_status_group)

        # Alertas de capital
        self.capital_alerts_frame = QFrame()
        self.capital_alerts_frame.setFrameStyle(QFrame.Box)
        self.capital_alerts_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #ffc107;
                border-radius: 5px;
                background-color: #3a3a3a;
                padding: 10px;
            }
        """)
        self.capital_alerts_frame.setVisible(False)
        
        alerts_layout = QVBoxLayout(self.capital_alerts_frame)
        self.capital_alert_label = QLabel("")
        self.capital_alert_label.setStyleSheet("color: #ffc107; font-weight: bold;")
        self.capital_alert_label.setWordWrap(True)
        alerts_layout.addWidget(self.capital_alert_label)
        
        layout.addWidget(self.capital_alerts_frame)
        layout.addStretch()

    def _create_portfolio_group(self, title: str) -> QGroupBox:
        """
        Crea un grupo con estilo consistente.
        """
        group_box = QGroupBox(title)
        group_box.setLayout(QFormLayout())
        group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #333;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                background-color: #222;
                color: #EEE;
            }
            QLabel {
                color: #DDD;
            }
        """)
        return group_box

    def _create_assets_table(self) -> QTableWidget:
        """
        Crea una tabla para mostrar activos del portafolio.
        """
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Símbolo", "Cantidad", "Precio Entrada", "Precio Actual", "Valor USD", "PnL (%)"])
        
        if table.horizontalHeader() is not None:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if table.verticalHeader() is not None:
            table.verticalHeader().setVisible(False)
            
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(self._get_table_style())
        return table

    def _create_open_trades_table(self) -> QTableWidget:
        """
        Crea una tabla para mostrar operaciones abiertas con TSL/TP.
        """
        table = QTableWidget()
        table.setColumnCount(9)
        table.setHorizontalHeaderLabels([
            "Símbolo", "Tipo", "Cantidad", "Precio Entrada", "Precio Actual", 
            "Take Profit", "Stop Loss", "Estado TSL", "PnL Actual"
        ])
        
        if table.horizontalHeader() is not None:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        if table.verticalHeader() is not None:
            table.verticalHeader().setVisible(False)
            
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(self._get_table_style())
        return table

    def _get_table_style(self) -> str:
        """
        Retorna el estilo CSS para las tablas.
        """
        return """
            QTableWidget {
                background-color: #2C2C2C;
                alternate-background-color: #3A3A3A;
                color: #EEE;
                border: 1px solid #444;
                gridline-color: #444;
            }
            QHeaderView::section {
                background-color: #444;
                color: #EEE;
                padding: 5px;
                border: 1px solid #555;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """

    def setup_update_timer(self):
        """
        Configura el timer de actualización automática.
        """
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(15000)  # 15 segundos
        self.update_timer.timeout.connect(self._start_update_worker)
        self.update_timer.start()
        logger.info("Timer de actualización del portafolio iniciado.")

    # Methods for TradingModeService integration (from subtask 3)
    def _handle_mode_change(self, new_mode: TradingMode):
        """
        Handles the trading mode change signal.
        """
        # logger.debug(f"PortfolioWidget: Mode change detected to {new_mode}") # Logging to be added in next step
        self._update_visibility_based_on_mode()

    def _update_visibility_based_on_mode(self):
        """
        Updates the visibility of paper and real trading groups based on the current trading mode.
        """
        current_mode_from_service = self.trading_mode_service.get_current_mode()
        logger.debug(f"PortfolioWidget._update_visibility_based_on_mode: Setting visibility for mode {current_mode_from_service}")
        if current_mode_from_service == TradingMode.PAPER:
            self.paper_trading_group.setVisible(True)
            self.real_trading_group.setVisible(False)
        elif current_mode_from_service == TradingMode.REAL:
            self.paper_trading_group.setVisible(False)
            self.real_trading_group.setVisible(True)
        else:
            logger.warning(f"PortfolioWidget: Unknown trading mode {current_mode_from_service}, defaulting to show paper.")
            self.paper_trading_group.setVisible(True)
            self.real_trading_group.setVisible(False)
        
        logger.debug(f"Paper trading group visible: {self.paper_trading_group.isVisible()}")
        logger.debug(f"Real trading group visible: {self.real_trading_group.isVisible()}")


    def _start_update_worker(self):
        """
        Inicia el worker para actualizar datos.
        """
        worker = DataUpdateWorker(self.user_id, self.portfolio_service, self.api_client)
        worker.signals.result.connect(self._handle_update_result)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.finished.connect(self._worker_finished)
        self.thread_pool.start(worker)
        logger.info("Actualizando datos del portafolio...")

    def _handle_update_result(self, result_data: Dict[str, Any]):
        """
        Maneja los resultados de la actualización de datos.
        """
        try:
            # Actualizar snapshot del portafolio
            if "portfolio_snapshot" in result_data:
                self.current_snapshot = result_data["portfolio_snapshot"]
                self._update_portfolio_ui(self.current_snapshot)

            # Actualizar operaciones abiertas
            if "open_trades" in result_data:
                self.open_trades = result_data["open_trades"]
                self._update_open_trades_ui(self.open_trades)

            # Actualizar estado de gestión de capital
            if "capital_status" in result_data:
                self.current_capital_status = result_data["capital_status"]
                self._update_capital_management_ui(self.current_capital_status)

            # Actualizar timestamp
            self.last_updated_label.setText(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.error_label.setText("")

        except Exception as e:
            error_msg = f"Error procesando resultados: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_label.setText(error_msg)

    def _update_portfolio_ui(self, snapshot: PortfolioSnapshot):
        """
        Actualiza la UI del portafolio con el snapshot.
        """
        # Actualizar Paper Trading
        self.paper_balance_label.setText(f"Saldo Disponible: {snapshot.paper_trading.available_balance_usdt:,.2f} USDT")
        self.paper_total_value_label.setText(f"Valor Total Activos: {snapshot.paper_trading.total_assets_value_usd:,.2f} USDT")
        self.paper_portfolio_value_label.setText(f"Valor Total Portafolio: {snapshot.paper_trading.total_portfolio_value_usd:,.2f} USDT")
        self._populate_assets_table(self.paper_assets_table, snapshot.paper_trading.assets)

        # Actualizar Real Trading
        self.real_balance_label.setText(f"Saldo Disponible (USDT): {snapshot.real_trading.available_balance_usdt:,.2f} USDT")
        self.real_total_value_label.setText(f"Valor Total Activos: {snapshot.real_trading.total_assets_value_usd:,.2f} USDT")
        self.real_portfolio_value_label.setText(f"Valor Total Portafolio: {snapshot.real_trading.total_portfolio_value_usd:,.2f} USDT")
        self._populate_assets_table(self.real_assets_table, snapshot.real_trading.assets)

        # Manejar errores
        if snapshot.paper_trading.error_message:
            self.paper_trading_group.setTitle(f"Paper Trading (Error: {snapshot.paper_trading.error_message})")
            self.paper_trading_group.setStyleSheet("QGroupBox { border: 1px solid red; }")
        else:
            self.paper_trading_group.setTitle("Paper Trading")

        if snapshot.real_trading.error_message:
            self.real_trading_group.setTitle(f"Real Trading (Binance) (Error: {snapshot.real_trading.error_message})")
            self.real_trading_group.setStyleSheet("QGroupBox { border: 1px solid red; }")
        else:
            self.real_trading_group.setTitle("Real Trading (Binance)")

    def _update_open_trades_ui(self, trades: List[Dict[str, Any]]):
        """
        Actualiza la UI de operaciones abiertas.
        """
        if not trades:
            self.open_trades_table.setRowCount(0)
            self.trades_info_label.setText("No hay operaciones abiertas")
            self.trades_info_label.setVisible(True)
            return

        self.trades_info_label.setVisible(False)
        self.open_trades_table.setRowCount(len(trades))

        for row, trade in enumerate(trades):
            # Símbolo
            self.open_trades_table.setItem(row, 0, QTableWidgetItem(trade.get("symbol", "N/A")))
            
            # Tipo (BUY/SELL)
            side = trade.get("side", "N/A")
            side_item = QTableWidgetItem(side)
            if side == "BUY":
                side_item.setForeground(QColor("lightgreen"))
            elif side == "SELL":
                side_item.setForeground(QColor("lightcoral"))
            self.open_trades_table.setItem(row, 1, side_item)
            
            # Cantidad
            entry_order = trade.get("entryOrder", {})
            quantity = entry_order.get("executedQuantity", 0)
            self.open_trades_table.setItem(row, 2, QTableWidgetItem(f"{quantity:,.8f}"))
            
            # Precio de entrada
            entry_price = entry_order.get("executedPrice", 0)
            self.open_trades_table.setItem(row, 3, QTableWidgetItem(f"{entry_price:,.4f}"))
            
            # Precio actual (necesitaríamos obtenerlo del mercado)
            current_price = trade.get("currentPrice", entry_price)  # Placeholder
            self.open_trades_table.setItem(row, 4, QTableWidgetItem(f"{current_price:,.4f}"))
            
            # Take Profit
            tp_price = trade.get("takeProfitPrice")
            tp_text = f"{tp_price:,.4f}" if tp_price else "N/A"
            self.open_trades_table.setItem(row, 5, QTableWidgetItem(tp_text))
            
            # Stop Loss actual
            current_sl = trade.get("currentStopPrice_tsl")
            sl_text = f"{current_sl:,.4f}" if current_sl else "N/A"
            sl_item = QTableWidgetItem(sl_text)
            if current_sl:
                sl_item.setForeground(QColor("orange"))
            self.open_trades_table.setItem(row, 6, sl_item)
            
            # Estado TSL
            position_status = trade.get("positionStatus", "unknown")
            status_item = QTableWidgetItem(position_status.upper())
            if position_status == "open":
                status_item.setForeground(QColor("lightgreen"))
            self.open_trades_table.setItem(row, 7, status_item)
            
            # PnL actual
            pnl = trade.get("pnl_usd")
            if pnl is not None:
                pnl_text = f"{pnl:,.2f} USD"
                pnl_item = QTableWidgetItem(pnl_text)
                if pnl > 0:
                    pnl_item.setForeground(QColor("lightgreen"))
                elif pnl < 0:
                    pnl_item.setForeground(QColor("red"))
            else:
                pnl_item = QTableWidgetItem("Calculando...")
                pnl_item.setForeground(QColor("gray"))
            self.open_trades_table.setItem(row, 8, pnl_item)

    def _update_capital_management_ui(self, capital_status: Dict[str, Any]):
        """
        Actualiza la UI de gestión de capital.
        """
        if not capital_status:
            return

        # Actualizar labels de información
        total_capital = capital_status.get("total_capital_usd", 0)
        available_capital = capital_status.get("available_for_new_trades_usd", 0)
        committed_capital = capital_status.get("daily_capital_committed_usd", 0)
        daily_limit = capital_status.get("daily_capital_limit_usd", 0)

        self.total_capital_label.setText(f"Capital Total: {total_capital:,.2f} USD")
        self.available_capital_label.setText(f"Disponible para Nuevas Operaciones: {available_capital:,.2f} USD")
        self.committed_capital_label.setText(f"Capital Comprometido Hoy: {committed_capital:,.2f} USD")
        self.daily_limit_label.setText(f"Límite Diario (50%): {daily_limit:,.2f} USD")

        # Actualizar barra de progreso
        if daily_limit > 0:
            usage_percentage = (committed_capital / daily_limit) * 100
            self.daily_usage_progress.setValue(int(usage_percentage))
            
            # Cambiar color según el nivel de uso
            if usage_percentage >= 100:
                self.daily_usage_progress.setStyleSheet(self._get_progress_style("#dc3545"))
            elif usage_percentage >= 85:
                self.daily_usage_progress.setStyleSheet(self._get_progress_style("#ffc107"))
            else:
                self.daily_usage_progress.setStyleSheet(self._get_progress_style("#28a745"))

        # Mostrar alertas si es necesario
        self._update_capital_alerts(capital_status)

    def _get_progress_style(self, color: str) -> str:
        """
        Retorna el estilo CSS para la barra de progreso con el color especificado.
        """
        return f"""
            QProgressBar {{
                border: 2px solid #333;
                border-radius: 5px;
                text-align: center;
                background-color: #2C2C2C;
                color: #EEE;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """

    def _update_capital_alerts(self, capital_status: Dict[str, Any]):
        """
        Actualiza las alertas de gestión de capital.
        """
        alerts = []
        
        # Verificar límite diario
        daily_limit = capital_status.get("daily_capital_limit_usd", 0)
        committed_capital = capital_status.get("daily_capital_committed_usd", 0)
        
        if daily_limit > 0:
            usage_percentage = (committed_capital / daily_limit) * 100
            
            if usage_percentage >= 100:
                alerts.append("⚠️ LÍMITE DIARIO ALCANZADO: No se pueden abrir nuevas operaciones reales hoy.")
            elif usage_percentage >= 90:
                alerts.append("⚠️ CERCA DEL LÍMITE: Ha usado el 90% del límite diario de capital.")
            elif usage_percentage >= 75:
                alerts.append("ℹ️ ADVERTENCIA: Ha usado el 75% del límite diario de capital.")

        # Verificar si hay operaciones en riesgo alto
        if capital_status.get("high_risk_positions_count", 0) > 0:
            alerts.append("⚠️ Hay operaciones con alto riesgo. Revise las posiciones abiertas.")

        # Mostrar u ocultar el frame de alertas
        if alerts:
            alert_text = "\n".join(alerts)
            self.capital_alert_label.setText(alert_text)
            self.capital_alerts_frame.setVisible(True)
            
            # Cambiar color del borde según la severidad
            if any("LÍMITE DIARIO ALCANZADO" in alert for alert in alerts):
                self.capital_alerts_frame.setStyleSheet("""
                    QFrame {
                        border: 2px solid #dc3545;
                        border-radius: 5px;
                        background-color: #3a3a3a;
                        padding: 10px;
                    }
                """)
            elif any("CERCA DEL LÍMITE" in alert for alert in alerts):
                self.capital_alerts_frame.setStyleSheet("""
                    QFrame {
                        border: 2px solid #ffc107;
                        border-radius: 5px;
                        background-color: #3a3a3a;
                        padding: 10px;
                    }
                """)
        else:
            self.capital_alerts_frame.setVisible(False)

    def _populate_assets_table(self, table: QTableWidget, assets: List[PortfolioAsset]):
        """
        Llena una tabla con la información de activos.
        """
        table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            table.setItem(row, 0, QTableWidgetItem(asset.symbol))
            table.setItem(row, 1, QTableWidgetItem(f"{asset.quantity:,.8f}"))
            table.setItem(row, 2, QTableWidgetItem(f"{asset.entry_price:,.2f}" if asset.entry_price is not None else "N/A"))
            table.setItem(row, 3, QTableWidgetItem(f"{asset.current_price:,.2f}" if asset.current_price is not None else "N/A"))
            table.setItem(row, 4, QTableWidgetItem(f"{asset.current_value_usd:,.2f}" if asset.current_value_usd is not None else "N/A"))
            
            pnl_item = QTableWidgetItem(f"{asset.unrealized_pnl_percentage:,.2f}%" if asset.unrealized_pnl_percentage is not None else "N/A")
            if asset.unrealized_pnl_percentage is not None:
                if asset.unrealized_pnl_percentage > 0:
                    pnl_item.setForeground(QColor("lightgreen"))
                elif asset.unrealized_pnl_percentage < 0:
                    pnl_item.setForeground(QColor("red"))
            table.setItem(row, 5, pnl_item)

    def _handle_worker_error(self, error_msg: str):
        """
        Maneja errores reportados por el worker.
        """
        self.error_label.setText(f"Error: {error_msg}")
        self.error_occurred.emit(error_msg)
        logger.error(f"Error en el worker de actualización: {error_msg}")

    def _worker_finished(self):
        """
        Callback cuando el worker termina.
        """
        logger.info("Worker de actualización finalizado.")

    def start_updates(self):
        """
        Inicia las actualizaciones automáticas.
        """
        self._start_update_worker()
        self.update_timer.start()

    def stop_updates(self):
        """
        Detiene las actualizaciones automáticas.
        """
        self.update_timer.stop()
        logger.info("Actualizaciones del portafolio detenidas.")
