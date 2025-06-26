"""
Order Form Widget - Formulario para crear órdenes de mercado.
Soporta tanto paper trading como real trading con awareness del modo actual.
"""
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Coroutine
from uuid import UUID
from PySide6 import QtWidgets, QtCore, QtGui

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.services.trading_mode_state import get_trading_mode_manager, TradingModeStateManager
from shared.data_types import TradeOrderDetails

logger = logging.getLogger(__name__)

class OrderFormWidget(QtWidgets.QWidget):
    """
    Widget para crear y ejecutar órdenes de mercado.
    
    Soporta tanto paper trading como real trading con integración completa
    al sistema de gestión de modo de trading.
    """
    
    order_executed = QtCore.Signal(object)
    order_failed = QtCore.Signal(str)
    
    def __init__(self, user_id: UUID, api_client: UltiBotAPIClient, main_event_loop: asyncio.AbstractEventLoop, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.main_event_loop = main_event_loop
        
        self.trading_mode_manager: TradingModeStateManager = get_trading_mode_manager()
        self.trading_mode_manager.trading_mode_changed.connect(self._on_trading_mode_changed)
        
        self.init_ui()
        self._update_mode_display()
        
        logger.info("OrderFormWidget initialized")

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        self._create_header(main_layout)
        self._create_form(main_layout)
        self._create_api_credentials_section(main_layout)
        self._create_action_buttons(main_layout)
        self._create_results_area(main_layout)

    def _create_header(self, layout: QtWidgets.QVBoxLayout):
        header_frame = QtWidgets.QFrame()
        header_frame.setFrameStyle(QtWidgets.QFrame.Shape.Box)
        header_frame.setMaximumHeight(60)
        
        header_layout = QtWidgets.QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QtWidgets.QLabel("Crear Orden de Mercado")
        title_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.mode_indicator = QtWidgets.QLabel()
        self.mode_indicator.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        header_layout.addWidget(self.mode_indicator)
        
        layout.addWidget(header_frame)

    def _create_form(self, layout: QtWidgets.QVBoxLayout):
        form_group = QtWidgets.QGroupBox("Detalles de la Orden")
        form_layout = QtWidgets.QFormLayout(form_group)
        
        self.symbol_input = QtWidgets.QLineEdit()
        self.symbol_input.setPlaceholderText("Ej: BTCUSDT")
        self.symbol_input.textChanged.connect(self._validate_form)
        form_layout.addRow("Símbolo:", self.symbol_input)
        
        self.side_combo = QtWidgets.QComboBox()
        self.side_combo.addItems(["BUY", "SELL"])
        self.side_combo.currentTextChanged.connect(self._validate_form)
        form_layout.addRow("Operación:", self.side_combo)
        
        self.quantity_input = QtWidgets.QDoubleSpinBox()
        self.quantity_input.setRange(0.00000001, 999999999.0)
        self.quantity_input.setDecimals(8)
        self.quantity_input.setSingleStep(0.01)
        self.quantity_input.valueChanged.connect(self._validate_form)
        form_layout.addRow("Cantidad:", self.quantity_input)
        
        self.mode_info_label = QtWidgets.QLabel()
        self.mode_info_label.setWordWrap(True)
        self.mode_info_label.setStyleSheet("color: #888; font-style: italic;")
        form_layout.addRow("Modo:", self.mode_info_label)
        
        layout.addWidget(form_group)

    def _create_api_credentials_section(self, layout: QtWidgets.QVBoxLayout):
        self.credentials_group = QtWidgets.QGroupBox("Credenciales API (Solo Real Trading)")
        credentials_layout = QtWidgets.QFormLayout(self.credentials_group)
        
        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("API Key de Binance")
        self.api_key_input.textChanged.connect(self._validate_form)
        credentials_layout.addRow("API Key:", self.api_key_input)
        
        self.api_secret_input = QtWidgets.QLineEdit()
        self.api_secret_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.api_secret_input.setPlaceholderText("API Secret de Binance")
        self.api_secret_input.textChanged.connect(self._validate_form)
        credentials_layout.addRow("API Secret:", self.api_secret_input)
        
        self.show_credentials_checkbox = QtWidgets.QCheckBox("Mostrar credenciales")
        self.show_credentials_checkbox.toggled.connect(self._toggle_credentials_visibility)
        credentials_layout.addRow("", self.show_credentials_checkbox)
        
        security_warning = QtWidgets.QLabel(
            "⚠️ IMPORTANTE: Las credenciales se envían de forma segura pero no se almacenan. "
            "Asegúrese de que su API Key tenga solo permisos de trading y no de retiro."
        )
        security_warning.setWordWrap(True)
        security_warning.setStyleSheet("color: #ffc107; font-size: 11px;")
        credentials_layout.addRow("", security_warning)
        
        layout.addWidget(self.credentials_group)

    def _create_action_buttons(self, layout: QtWidgets.QVBoxLayout):
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.validate_button = QtWidgets.QPushButton("Validar Orden")
        self.validate_button.clicked.connect(self._validate_order)
        buttons_layout.addWidget(self.validate_button)
        
        buttons_layout.addStretch()
        
        self.clear_button = QtWidgets.QPushButton("Limpiar")
        self.clear_button.clicked.connect(self._clear_form)
        buttons_layout.addWidget(self.clear_button)
        
        self.execute_button = QtWidgets.QPushButton("Ejecutar Orden")
        self.execute_button.clicked.connect(self._execute_order)
        self.execute_button.setEnabled(False)
        buttons_layout.addWidget(self.execute_button)
        
        layout.addLayout(buttons_layout)
        
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _create_results_area(self, layout: QtWidgets.QVBoxLayout):
        results_group = QtWidgets.QGroupBox("Resultado")
        results_layout = QtWidgets.QVBoxLayout(results_group)
        
        self.results_text = QtWidgets.QTextEdit()
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
        echo_mode = QtWidgets.QLineEdit.EchoMode.Normal if show else QtWidgets.QLineEdit.EchoMode.Password
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
        
        validation_result = (
            "📋 VALIDACIÓN DE ORDEN\n"
            "========================\n"
            f"Símbolo: {order_data['symbol']}\n"
            f"Operación: {order_data['side']}\n"
            f"Cantidad: {order_data['quantity']:,.8f}\n"
            f"Modo: {order_data['trading_mode'].upper()}\n"
            f"Usuario: {order_data['user_id']}\n\n"
            "Estado: ✅ Orden válida y lista para ejecutar"
        )
        
        if order_data['trading_mode'] == 'real':
            validation_result += (
                "\n\n"
                "⚠️  TRADING REAL ACTIVO\n"
                "- Se utilizarán fondos reales\n"
                "- Credenciales API configuradas: Sí"
            )
        
        self.results_text.setText(validation_result)

    def _execute_order(self):
        current_mode = self.trading_mode_manager.current_mode
        
        if current_mode == 'real':
            reply = QtWidgets.QMessageBox.question(
                self, 
                "Confirmar Orden Real",
                f"¿Está seguro de que desea ejecutar esta orden con FONDOS REALES?\n\n"
                f"Símbolo: {self.symbol_input.text()}\n"
                f"Operación: {self.side_combo.currentText()}\n"
                f"Cantidad: {self.quantity_input.value():,.8f}",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No
            )
            
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return
        
        self.main_event_loop.call_soon_threadsafe(
            lambda: asyncio.ensure_future(self._execute_order_async())
        )
        
    async def _execute_order_async(self):
        order_data = self._get_order_data()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.execute_button.setEnabled(False)
        
        logger.info(f"Ejecutando orden: {order_data}")
        
        try:
            result = await self.api_client.execute_market_order(order_data)
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
        
        result_text = (
            "✅ ORDEN EJECUTADA EXITOSAMENTE\n"
            "================================\n"
            f"Orden ID: {order_details.get('orderId_internal', 'N/A')}\n"
            f"Símbolo: {order_details.get('symbol', 'N/A')}\n"
            f"Lado: {order_details.get('side', 'N/A')}\n"
            f"Cantidad: {order_details.get('executedQuantity', 0):,.8f}\n"
            f"Precio: {order_details.get('executedPrice', 0):,.4f}\n"
            f"Estado: {order_details.get('status', 'N/A')}\n"
            f"Modo: {self.trading_mode_manager.current_mode.upper()}\n"
            f"Fecha: {order_details.get('timestamp', 'N/A')}\n\n"
            f"💰 Total: {order_details.get('cumulativeQuoteQty', 0):,.2f} USDT"
        )
        
        self.results_text.setText(result_text)
        self.order_executed.emit(order_details)
        
        QtCore.QTimer.singleShot(5000, self._clear_form)

    def _handle_order_error(self, error_msg: str):
        error_text = (
            "❌ ERROR EN LA EJECUCIÓN\n"
            "========================\n"
            f"{error_msg}\n\n"
            "Por favor, verifique:\n"
            "- Símbolo válido\n"
            "- Cantidad suficiente\n"
            "- Credenciales API (modo real)\n"
            "- Conexión a internet\n"
            "- Estado del mercado"
        )
        
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
        logger.info("OrderFormWidget: Cleanup called. No action needed.")
