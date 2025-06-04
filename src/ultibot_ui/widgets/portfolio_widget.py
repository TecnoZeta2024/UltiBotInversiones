import logging
import asyncio
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QFormLayout, QHBoxLayout, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QPushButton,
    QTabWidget, QProgressBar, QMessageBox # Añadir QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool
from PyQt5.QtGui import QFont, QColor

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary, PortfolioAsset # PortfolioSnapshot podría ser Dict si no se parsea
# from src.ultibot_backend.services.portfolio_service import PortfolioService # Reemplazado por api_client
# from src.ultibot_backend.services.config_service import ConfigService # No se usa directamente
# from src.ultibot_backend.services.market_data_service import MarketDataService # No se usa directamente
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError # Asegurar APIError si se usa
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager


logger = logging.getLogger(__name__)

class DataUpdateWorker(QRunnable):
    """
    Worker para actualizar datos del portafolio y operaciones abiertas según el modo de trading.
    Utiliza UltiBotAPIClient.
    """
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, trading_mode: str): # Eliminado portfolio_service
        super().__init__()
        self.user_id = user_id
        self.api_client = api_client # api_client es ahora el único proveedor de datos
        self.trading_mode = trading_mode
        self.signals = WorkerSignals()

    def run(self):
        """
        Ejecuta la actualización de datos en un hilo separado con filtrado por trading mode.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            logger.debug(f"DataUpdateWorker: Iniciando actualización para user {self.user_id}, modo {self.trading_mode}")
            
            # Obtener snapshot del portafolio para el modo específico usando api_client
            portfolio_snapshot = loop.run_until_complete(
                self.api_client.get_portfolio_snapshot(user_id=self.user_id, trading_mode=self.trading_mode)
            )
            logger.debug(f"DataUpdateWorker: portfolio_snapshot obtenido: {portfolio_snapshot is not None}")
            
            # Obtener trades abiertos para el modo específico
            open_trades = loop.run_until_complete(
                self.api_client.get_open_trades_by_mode(user_id=self.user_id, trading_mode=self.trading_mode)
            )
            logger.debug(f"DataUpdateWorker: open_trades obtenido: {open_trades is not None}")
            
            # Obtener estado de gestión de capital
            capital_status = loop.run_until_complete(
                self.api_client.get_capital_management_status() # Este método no parece depender del user_id o trading_mode en su signatura actual
            )
            logger.debug(f"DataUpdateWorker: capital_status obtenido: {capital_status is not None}")
            
            result_data = {
                "portfolio_snapshot": portfolio_snapshot,
                "open_trades": open_trades,
                "capital_status": capital_status,
                "trading_mode": self.trading_mode
            }
            
            self.signals.result.emit(result_data)
            
        except APIError as e: # Capturar APIError específicamente
            error_msg = f"Error de API actualizando datos del portafolio (modo {self.trading_mode}): {e.message} (status: {e.status_code})"
            logger.error(error_msg, exc_info=True)
            self.signals.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Error inesperado actualizando datos del portafolio (modo {self.trading_mode}): {e}"
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
    Widget para la visualización del estado del portafolio con soporte completo
    para diferenciación entre modos de trading (paper vs real).
    """
    portfolio_updated = pyqtSignal(PortfolioSnapshot)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, parent: Optional[QWidget] = None): # Eliminado portfolio_service, api_client es requerido
        super().__init__(parent)
        self.user_id = user_id
        # self.portfolio_service = portfolio_service # Eliminado
        self.api_client = api_client # api_client ahora es requerido y no opcional
        self.current_snapshot: Optional[PortfolioSnapshot] = None # O Optional[Dict[str, Any]]
        self.current_snapshot_dict: Optional[Dict[str, Any]] = None # Para el dict crudo
        self.current_capital_status: Optional[Dict[str, Any]] = None
        self.open_trades: List[Dict[str, Any]] = []
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(2) # Limitar hilos para no saturar

        # Connect to trading mode state manager
        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)

        self.init_ui()
        self.setup_update_timer()

        # Connect to TradingModeService signal and set initial visibility (from subtask 3)
        self.trading_mode_service.mode_changed.connect(self._handle_mode_change)
        self._update_visibility_based_on_mode()

    def init_ui(self):
        """
        Inicializa la interfaz de usuario con visualización diferenciada por modo.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setSpacing(10)

        # Header con indicador de modo actual
        self._create_mode_header(main_layout)

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
        self._create_status_bar(main_layout)

    def _create_mode_header(self, layout: QVBoxLayout):
        """Crea el header con indicador del modo actual."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_frame.setMaximumHeight(50)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Título principal
        title_label = QLabel("Estado del Portafolio")
        title_font = QFont("Arial", 14, QFont.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Indicador de modo actual
        self.mode_indicator = QLabel()
        self.mode_indicator.setFont(QFont("Arial", 12, QFont.Bold))
        self._update_mode_indicator()
        header_layout.addWidget(self.mode_indicator)
        
        layout.addWidget(header_frame)

    def _update_mode_indicator(self):
        """Actualiza el indicador visual del modo de trading."""
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.mode_indicator.setText(f"{mode_info['icon']} {mode_info['display_name']}")
        self.mode_indicator.setStyleSheet(f"""
            QLabel {{
                color: {mode_info['color']};
                background-color: {mode_info['color']}22;
                border: 2px solid {mode_info['color']};
                border-radius: 5px;
                padding: 3px 8px;
            }}
        """)

    def init_portfolio_tab(self):
        """
        Inicializa la pestaña de resumen del portafolio con vista unificada.
        """
        layout = QVBoxLayout(self.portfolio_tab)
        layout.setSpacing(15)

        # Grupo unificado para el modo actual
        self.current_mode_group = self._create_portfolio_group("Portafolio Actual")
        self.balance_label = QLabel("Saldo Disponible: N/A")
        self.total_assets_label = QLabel("Valor Total Activos: N/A")
        self.portfolio_value_label = QLabel("Valor Total Portafolio: N/A")
        self.assets_table = self._create_assets_table()
        
        mode_layout = self.current_mode_group.layout()
        if isinstance(mode_layout, QFormLayout):
            mode_layout.addRow(self.balance_label)
            mode_layout.addRow(self.total_assets_label)
            mode_layout.addRow(self.portfolio_value_label)
            mode_layout.addRow(QLabel("Activos Poseídos:"))
            mode_layout.addRow(self.assets_table)
        layout.addWidget(self.current_mode_group)

        # Información comparativa (opcional)
        self.comparison_info = QLabel("")
        self.comparison_info.setStyleSheet("color: #888; font-style: italic; text-align: center;")
        self.comparison_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.comparison_info)

    def init_trades_tab(self):
        """
        Inicializa la pestaña de operaciones abiertas con filtrado por modo.
        """
        layout = QVBoxLayout(self.trades_tab)
        layout.setSpacing(15)

        # Título dinámico
        self.trades_title = QLabel("")
        self.trades_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.trades_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_trades_title()
        layout.addWidget(self.trades_title)

        # Tabla de operaciones abiertas
        self.open_trades_table = self._create_open_trades_table()
        layout.addWidget(self.open_trades_table)

        # Información adicional
        self.trades_info_label = QLabel("No hay operaciones abiertas")
        self.trades_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trades_info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.trades_info_label)

    def _update_trades_title(self):
        """Actualiza el título de la pestaña de operaciones."""
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.trades_title.setText(f"Operaciones {mode_info['display_name']} con TSL/TP Activos")

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

    def _create_status_bar(self, layout: QVBoxLayout):
        """Crea la barra de estado."""
        status_layout = QHBoxLayout()
        self.last_updated_label = QLabel("Última actualización: N/A")
        self.last_updated_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self._start_update_worker)
        self.refresh_button.setMaximumWidth(100)
        
        status_layout.addWidget(self.last_updated_label)
        status_layout.addStretch()
        status_layout.addWidget(self.refresh_button)
        layout.addLayout(status_layout)

        # Label de error
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

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
        
        h_header = table.horizontalHeader()
        if h_header: # Check if not None
            h_header.setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        v_header = table.verticalHeader()
        if v_header: # Check if not None
            v_header.setVisible(False)
            
        table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore
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
        
        h_header = table.horizontalHeader()
        if h_header: # Check if not None
            h_header.setSectionResizeMode(QHeaderView.Stretch) # type: ignore
        v_header = table.verticalHeader()
        if v_header: # Check if not None
            v_header.setVisible(False)
            
        table.setEditTriggers(QTableWidget.NoEditTriggers) # type: ignore
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

    def _on_trading_mode_changed(self, new_mode: str):
        """
        Maneja cambios en el modo de trading.
        
        Args:
            new_mode: Nuevo modo de trading ('paper' o 'real')
        """
        logger.info(f"PortfolioWidget: Modo de trading cambió a {new_mode}")
        
        # Actualizar indicadores visuales
        self._update_mode_indicator()
        self._update_trades_title()
        
        # Actualizar título del grupo principal
        mode_info = self.trading_mode_manager.get_mode_display_info()
        self.current_mode_group.setTitle(f"Portafolio {mode_info['display_name']}")
        
        # Refrescar datos inmediatamente
        self._start_update_worker()

    def _start_update_worker(self):
        """
        Inicia el worker para actualizar datos según el modo actual.
        """
        current_mode = self.trading_mode_manager.current_mode
        # Pasar solo api_client al worker
        worker = DataUpdateWorker(self.user_id, self.api_client, current_mode)
        worker.signals.result.connect(self._handle_update_result)
        worker.signals.error.connect(self._handle_worker_error)
        worker.signals.finished.connect(self._worker_finished)

        # Feedback before starting worker
        self.last_updated_label.setText(f"Actualizando portafolio ({current_mode.title()})...")
        if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(False)

        self.thread_pool.start(worker)
        logger.info(f"Actualizando datos del portafolio para modo: {current_mode}")

    def _handle_update_result(self, result_data: Dict[str, Any]):
        """
        Maneja los resultados de la actualización de datos.
        """
        try:
            current_mode = self.trading_mode_manager.current_mode
            result_mode = result_data.get("trading_mode", current_mode)
            
            if result_mode != current_mode:
                logger.debug(f"Ignorando datos de modo {result_mode}, modo actual es {current_mode}")
                # Do not re-enable buttons here if another update is expected for the current mode.
                # However, if this is the only worker response, then re-enable.
                # For simplicity, assume this worker is the one for the current mode.
                if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(True)
                return

            # Actualizar snapshot del portafolio
            # The API returns a dict, PortfolioSnapshot is a Pydantic model.
            # _update_portfolio_ui needs to handle a dict or we need to parse here.
            # Assuming _update_portfolio_ui can handle the dict directly for ahora.
            portfolio_snapshot_data = result_data.get("portfolio_snapshot")
            self.current_snapshot_dict = portfolio_snapshot_data if portfolio_snapshot_data is not None else {}
            if self.current_snapshot_dict is not None:
                self._update_portfolio_ui(self.current_snapshot_dict, current_mode)
            else:
                self._update_portfolio_ui({}, current_mode) # Pass empty dict if snapshot is None

            # Actualizar operaciones abiertas
            open_trades_data = result_data.get("open_trades", []) 
            self.open_trades = open_trades_data if open_trades_data is not None else []
            self._update_open_trades_ui(self.open_trades)

            # Actualizar estado de gestión de capital
            capital_status_data = result_data.get("capital_status")
            self.current_capital_status = capital_status_data if capital_status_data is not None else {}
            if self.current_capital_status is not None:
                self._update_capital_management_ui(self.current_capital_status)
            else:
                self._update_capital_management_ui({}) # Pass empty dict if status is None


            self.last_updated_label.setText(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.error_label.setText("") # Clear previous errors

        except Exception as e:
            error_msg = f"Error procesando datos actualizados del portafolio: {e}"
            logger.error(error_msg, exc_info=True)
            self.error_label.setText(error_msg) # Display error on dedicated label
            QMessageBox.warning(self, "Portfolio Update Error",
                                f"Hubo un error al procesar los datos del portafolio.\n"
                                f"Detalles: {error_msg}")
            # No re-enable el botón aquí si el worker_finished lo hace.
            # self.refresh_button.setEnabled(True) # Movido a _worker_finished o gestionado por el estado del pool


    def _update_portfolio_ui(self, snapshot_dict: Dict[str, Any], mode: str): # snapshot_dict puede ser {}
        """
        Actualiza la UI del portafolio con el snapshot_dict para el modo específico.
        """
        # Extract the correct part of the snapshot dict based on the mode
        # Si snapshot_dict es {}, portfolio_mode_dict también será {}
        portfolio_mode_dict = snapshot_dict.get(f"{mode}_trading", {}) 

        currency = "USDT (Virtual)" if mode == "paper" else "USDT"

        # Actualizar labels principales
        self.balance_label.setText(f"Saldo Disponible: {portfolio_mode_dict.get('available_balance_usdt', 0.0):,.2f} {currency}")
        self.total_assets_label.setText(f"Valor Total Activos: {portfolio_mode_dict.get('total_assets_value_usd', 0.0):,.2f} USD")
        self.portfolio_value_label.setText(f"Valor Total Portafolio: {portfolio_mode_dict.get('total_portfolio_value_usd', 0.0):,.2f} USD")
        
        # Actualizar tabla de activos
        # The assets list is expected to be a list of dicts, matching PortfolioAsset structure
        assets_list = portfolio_mode_dict.get('assets', [])
        self._populate_assets_table(self.assets_table, assets_list)

        # Actualizar información comparativa
        other_mode = "real" if mode == "paper" else "paper"
        other_mode_dict = snapshot_dict.get(f"{other_mode}_trading", {}) if snapshot_dict else {}
        self.comparison_info.setText(
            f"Portafolio {other_mode.title()}: {other_mode_dict.get('total_portfolio_value_usd', 0.0):,.2f} USD"
        )

        # Manejar errores (assuming error_message is a field in portfolio_mode_dict)
        error_message = portfolio_mode_dict.get("error_message")
        if error_message:
            self.current_mode_group.setStyleSheet("QGroupBox { border: 1px solid red; }")
            # self.error_label is a general error label, this specific one might be different
            logger.warning(f"Error message in portfolio data ({mode}): {error_message}")
            QMessageBox.warning(self, f"Error en Portafolio ({mode.title()})", error_message)
            # Consider showing this specific error more prominently if needed
        else:
            # Solo resetear si no hay error. Si portfolio_mode_dict está vacío, no habrá error_message.
            if portfolio_mode_dict: # Solo resetear si hay datos, sino podría haber un error global
                 self.current_mode_group.setStyleSheet("") # Reset border

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

    def _populate_assets_table(self, table: QTableWidget, assets: List[Dict[str, Any]]):
        """
        Llena una tabla con la información de activos.
        Maneja tanto objetos PortfolioAsset como diccionarios.
        """
        table.setRowCount(len(assets))
        for row, asset in enumerate(assets):
            # Comprobar si estamos trabajando con un objeto o un diccionario
            is_dict = isinstance(asset, dict)
            
            # Obtener los valores según el tipo de dato
            symbol = asset["symbol"] if is_dict else asset.symbol
            quantity = asset["quantity"] if is_dict else asset.quantity
            entry_price = asset["entry_price"] if is_dict else asset.entry_price
            current_price = asset["current_price"] if is_dict else asset.current_price
            current_value_usd = asset["current_value_usd"] if is_dict else asset.current_value_usd
            unrealized_pnl_percentage = asset["unrealized_pnl_percentage"] if is_dict else asset.unrealized_pnl_percentage
            
            table.setItem(row, 0, QTableWidgetItem(symbol))
            table.setItem(row, 1, QTableWidgetItem(f"{quantity:,.8f}"))
            table.setItem(row, 2, QTableWidgetItem(f"{entry_price:,.2f}" if entry_price is not None else "N/A"))
            table.setItem(row, 3, QTableWidgetItem(f"{current_price:,.2f}" if current_price is not None else "N/A"))
            table.setItem(row, 4, QTableWidgetItem(f"{current_value_usd:,.2f}" if current_value_usd is not None else "N/A"))
            
            pnl_item = QTableWidgetItem(f"{unrealized_pnl_percentage:,.2f}%" if unrealized_pnl_percentage is not None else "N/A")
            if unrealized_pnl_percentage is not None:
                if unrealized_pnl_percentage > 0:
                    pnl_item.setForeground(QColor("lightgreen"))
                elif unrealized_pnl_percentage < 0:
                    pnl_item.setForeground(QColor("red"))
            table.setItem(row, 5, pnl_item)

    def _handle_worker_error(self, error_msg: str):
        """
        Maneja errores reportados por el worker.
        """
        logger.error(f"PortfolioWidget: Error en DataUpdateWorker: {error_msg}")
        # Usar QMessageBox del módulo QtWidgets
        from PyQt5.QtWidgets import QMessageBox # Importar aquí si no está global
        QMessageBox.critical(self, "Error de Datos del Portafolio",
                             f"No se pudieron cargar los datos del portafolio.\n"
                             f"Detalles: {error_msg}\n\n"
                             "Por favor, intente actualizar manualmente o revise la conexión.")
        self.error_label.setText(f"Error al cargar datos. Ver logs.") # Usar el label de error dedicado
        self.last_updated_label.setText("Actualización fallida.")
        
        # Ensure UI is re-enabled (esto se podría manejar en _worker_finished)
        # if hasattr(self, 'refresh_button'): self.refresh_button.setEnabled(True)

        # Clear potentially stale data from tables by populating with empty lists
        # Asegurarse de que las tablas existen antes de llamar a estos métodos
        if hasattr(self, 'assets_table'):
            self._populate_assets_table(self.assets_table, [])
        if hasattr(self, 'open_trades_table'):
            self._update_open_trades_ui([]) # This will show "No hay operaciones abiertas"
        
        # Reset capital management UI elements to default/error state
        self.total_capital_label.setText("Capital Total: Error")
        self.available_capital_label.setText("Disponible para Nuevas Operaciones: Error")
        self.committed_capital_label.setText("Capital Comprometido Hoy: Error")
        self.daily_limit_label.setText("Límite Diario (50%): Error")
        self.daily_usage_progress.setValue(0)
        self.capital_alerts_frame.setVisible(False)

        self.error_occurred.emit(error_msg)


    def _worker_finished(self):
        """
        Callback cuando el worker termina. Re-habilita el botón de refresco.
        """
        logger.info("Worker de actualización finalizado.")
        if hasattr(self, 'refresh_button'):
            self.refresh_button.setEnabled(True)

    def refresh_data(self):
        """
        Método público para refrescar datos manualmente.
        """
        self._start_update_worker()

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
