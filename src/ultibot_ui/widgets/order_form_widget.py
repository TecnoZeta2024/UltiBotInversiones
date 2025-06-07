"""
Order Form Widget - Formulario para crear órdenes de mercado.
Soporta tanto paper trading como real trading con awareness del modo actual.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Coroutine
from uuid import UUID
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QDoubleSpinBox, QFrame, QGroupBox, QMessageBox,
    QTextEdit, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QThread
from PyQt5.QtGui import QFont, QColor, QDoubleValidator

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager
from src.shared.data_types import TradeOrderDetails
from src.ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class OrderFormWidget(QWidget):
    """
    Widget para crear y ejecutar órdenes de mercado.
    
    Soporta tanto paper trading como real trading con integración completa
    al sistema de gestión de modo de trading.
    """
    
    order_executed = pyqtSignal(object)
    order_failed = pyqtSignal(str)
    
    def __init__(self, user_id: UUID, backend_base_url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.backend_base_url = backend_base_url
        self.active_api_workers = []
        
        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)
        
        self.init_ui()
        self._update_mode_display()
        
        logger.info("OrderFormWidget initialized")

    def _run_api_worker_and_await_result(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine]) -> Any:
        import qasync

        qasync_loop = asyncio.get_event_loop()
        future = qasync_loop.create_future()

        worker = ApiWorker(coroutine_factory=coroutine_factory, base_url=self.backend_base_url)
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

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        self._create_header(main_layout)
        self._create_form(main_layout)
        self._create_api_credentials_section(main_layout)
        self._create_action_buttons(main_layout)
        self._create_results_area(main_layout)

    def _create_header(self, layout: QVBoxLayout):
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Box)
        header_frame.setMaximumHeight(60)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("Crear Orden de Mercado")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.mode_indicator = QLabel()
        self.mode_indicator.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.mode_indicator)
        
        layout.addWidget(header_frame)

    def _create_form(self, layout: QVBoxLayout):
        form_group = QGroupBox("Detalles de la Orden")
        form_layout = QFormLayout(form_group)
        
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("Ej: BTCUSDT")
        self.symbol_input.textChanged.connect(self._validate_form)
        form_layout.addRow("Símbolo:", self.symbol_input)
        
        self.side_combo = QComboBox()
        self.side_combo.addItems(["BUY", "SELL"])
        self.side_combo.currentTextChanged.connect(self._validate_form)
        form_layout.addRow("Operación:", self.side_combo)
        
        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.00000001, 999999999.0)
        self.quantity_input.setDecimals(8)
        self.quantity_input.setSingleStep(0.01)
        self.quantity_input.valueChanged.connect(self._validate_form)
        form_layout.addRow("Cantidad:", self.quantity_input)
        
        self.mode_info_label = QLabel()
        self.mode_info_label.setWordWrap(True)
        self.mode_info_label.setStyleSheet("color: #888; font-style: italic;")
        form_layout.addRow("Modo:", self.mode_info_label)
        
        layout.addWidget(form_group)

    def _create_api_credentials_section(self, layout: QVBoxLayout):
        self.credentials_group = QGroupBox("Credenciales API (Solo Real Trading)")
        credentials_layout = QFormLayout(self.credentials_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("API Key de Binance")
        self.api_key_input.textChanged.connect(self._validate_form)
        credentials_layout.addRow("API Key:", self.api_key_input)
        
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input.setPlaceholderText("API Secret de Binance")
        self.api_secret_input.textChanged.connect(self._validate_form)
        credentials_layout.addRow("API Secret:", self.api_secret_input)
        
        self.show_credentials_checkbox = QCheckBox("Mostrar credenciales")
        self.show_credentials_checkbox.toggled.connect(self._toggle_credentials_visibility)
        credentials_layout.addRow("", self.show_credentials_checkbox)
        
        security_warning = QLabel(
            "⚠️ IMPORTANTE: Las credenciales se envían de forma segura pero no se almacenan. "
            "Asegúrese de que su API Key tenga solo permisos de trading y no de retiro."
        )
        security_warning.setWordWrap(True)
        security_warning.setStyleSheet("color: #ffc107; font-size: 11px;")
        credentials_layout.addRow("", security_warning)
        
        layout.addWidget(self.credentials_group)

    def _create_action_buttons(self, layout: QVBoxLayout):
        buttons_layout = QHBoxLayout()
        
        self.validate_button = QPushButton("Validar Orden")
        self.validate_button.clicked.connect(self._validate_order)
        buttons_layout.addWidget(self.validate_button)
        
        buttons_layout.addStretch()
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self._clear_form)
        buttons_layout.addWidget(self.clear_button)
        
        self.execute_button = QPushButton("Ejecutar Orden")
        self.execute_button.clicked.connect(self._execute_order)
        self.execute_button.setEnabled(False)
        buttons_layout.addWidget(self.execute_button)
        
        layout.addLayout(buttons_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _create_results_area(self, layout: QVBoxLayout):
        results_group = QGroupBox("Resultado")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                border: 1px solid #444;
                color: #EEE;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)

    def _update_mode_display(self):
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
        
        if mode_info['mode'] == 'paper':
            self.mode_info_label.setText("Modo Paper Trading: Las operaciones se ejecutarán con fondos virtuales.")
            self.credentials_group.setVisible(False)
        else:
            self.mode_info_label.setText("Modo Real Trading: Las operaciones se ejecutarán con fondos reales en Binance.")
            self.credentials_group.setVisible(True)
        
        if mode_info['mode'] == 'real':
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                }
            """)
            self.execute_button.setText("🚨 EJECUTAR ORDEN REAL")
        else:
            self.execute_button.setStyleSheet("")
            self.execute_button.setText("Ejecutar Orden Paper")
        
        self._validate_form()

    def _on_trading_mode_changed(self, new_mode: str):
        logger.info(f"OrderFormWidget: Modo de trading cambió a {new_mode}")
        self._update_mode_display()

    def _toggle_credentials_visibility(self, show: bool):
        echo_mode = QLineEdit.Normal if show else QLineEdit.Password
        self.api_key_input.setEchoMode(echo_mode)
        self.api_secret_input.setEchoMode(echo_mode)

    def _validate_form(self):
        is_valid = True
        
        if not self.symbol_input.text().strip():
            is_valid = False
        
        if self.quantity_input.value() <= 0:
            is_valid = False
        
        current_mode = self.trading_mode_manager.current_mode
        if current_mode == 'real':
            if not self.api_key_input.text().strip() or not self.api_secret_input.text().strip():
                is_valid = False
        
        self.execute_button.setEnabled(is_valid)
        self.validate_button.setEnabled(is_valid)

    def _validate_order(self):
        order_data = self._get_order_data()
        
        validation_result = f"""
📋 VALIDACIÓN DE ORDEN
========================
Símbolo: {order_data['symbol']}
Operación: {order_data['side']}
Cantidad: {order_data['quantity']:,.8f}
Modo: {order_data['trading_mode'].upper()}
Usuario: {order_data['user_id']}

Estado: ✅ Orden válida y lista para ejecutar
        """
        
        if order_data['trading_mode'] == 'real':
            validation_result += f"""
⚠️  TRADING REAL ACTIVO
- Se utilizarán fondos reales
- Credenciales API configuradas: Sí
"""
        
        self.results_text.setText(validation_result)

    def _execute_order(self):
        current_mode = self.trading_mode_manager.current_mode
        
        if current_mode == 'real':
            reply = QMessageBox.question(
                self, 
                "Confirmar Orden Real",
                f"¿Está seguro de que desea ejecutar esta orden con FONDOS REALES?\n\n"
                f"Símbolo: {self.symbol_input.text()}\n"
                f"Operación: {self.side_combo.currentText()}\n"
                f"Cantidad: {self.quantity_input.value():,.8f}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        order_data = self._get_order_data()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.execute_button.setEnabled(False)
        
        self._run_api_worker_and_await_result(
            lambda api_client: api_client.create_trade(
                symbol=order_data["symbol"],
                side=order_data["side"],
                quantity=order_data["quantity"],
                trading_mode=order_data["trading_mode"],
                api_key=order_data.get("api_key"),
                api_secret=order_data.get("api_secret")
            )
        ).add_done_callback(self._handle_order_result_from_future)
        
        logger.info(f"Ejecutando orden: {order_data}")

    def _handle_order_result_from_future(self, future: asyncio.Future):
        try:
            result = future.result()
            self._handle_order_result(result)
        except Exception as e:
            self._handle_order_error(str(e))
        finally:
            self._handle_order_finished()

    def _get_order_data(self) -> Dict[str, Any]:
        current_mode = self.trading_mode_manager.current_mode
        
        order_data = {
            "user_id": str(self.user_id),
            "symbol": self.symbol_input.text().strip().upper(),
            "side": self.side_combo.currentText(),
            "quantity": self.quantity_input.value(),
            "trading_mode": current_mode
        }
        
        if current_mode == 'real':
            order_data["api_key"] = self.api_key_input.text().strip()
            order_data["api_secret"] = self.api_secret_input.text().strip()
        
        return order_data

    def _handle_order_result(self, result: Dict[str, Any]):
        order_details = result
        
        result_text = f"""
✅ ORDEN EJECUTADA EXITOSAMENTE
================================
Orden ID: {order_details.get('orderId_internal', 'N/A')}
Símbolo: {order_details.get('symbol', 'N/A')}
Lado: {order_details.get('side', 'N/A')}
Cantidad: {order_details.get('executedQuantity', 0):,.8f}
Precio: {order_details.get('executedPrice', 0):,.4f}
Estado: {order_details.get('status', 'N/A')}
Modo: {self.trading_mode_manager.current_mode.upper()}
Fecha: {order_details.get('timestamp', 'N/A')}

💰 Total: {order_details.get('cumulativeQuoteQty', 0):,.2f} USDT
        """
        
        self.results_text.setText(result_text)
        self.order_executed.emit(order_details)
        
        QTimer.singleShot(5000, self._clear_form)

    def _handle_order_error(self, error_msg: str):
        error_text = f"""
❌ ERROR EN LA EJECUCIÓN
========================
{error_msg}

Por favor, verifique:
- Símbolo válido
- Cantidad suficiente
- Credenciales API (modo real)
- Conexión a internet
- Estado del mercado
        """
        
        self.results_text.setText(error_text)
        self.order_failed.emit(error_msg)

    def _handle_order_finished(self):
        self.progress_bar.setVisible(False)
        self.execute_button.setEnabled(True)
        self._validate_form()

    def _clear_form(self):
        self.symbol_input.clear()
        self.side_combo.setCurrentIndex(0)
        self.quantity_input.setValue(0.0)
        self.api_key_input.clear()
        self.api_secret_input.clear()
        self.show_credentials_checkbox.setChecked(False)
        self.results_text.clear()
        self._validate_form()

    def set_symbol(self, symbol: str):
        self.symbol_input.setText(symbol.upper())
        self._validate_form()

    def set_default_quantity(self, quantity: float):
        self.quantity_input.setValue(quantity)
        self._validate_form()

    def cleanup(self):
        logger.info("OrderFormWidget: Iniciando limpieza de ApiWorkers activos.")
        for worker, thread in list(self.active_api_workers):
            if thread.isRunning():
                logger.info(f"OrderFormWidget: Deteniendo ApiWorker en thread {thread.objectName()}...")
                thread.quit()
                if not thread.wait(2000):
                    logger.warning(f"OrderFormWidget: Thread {thread.objectName()} no terminó a tiempo. Forzando terminación.")
                    thread.terminate()
                    thread.wait()
            if (worker, thread) in self.active_api_workers:
                self.active_api_workers.remove((worker, thread))
                worker.deleteLater()
                thread.deleteLater()
        logger.info("OrderFormWidget: Limpieza de ApiWorkers completada.")
