"""Asset Trading Parameters Dialog.

Este módulo implementa el diálogo para configurar parámetros de trading específicos por activo,
incluyendo gestión CRUD completa, validación en tiempo real, y ejecución con worker threads.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QLabel, QLineEdit, 
    QTextEdit, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, 
    QPushButton, QListWidget, QListWidgetItem, QWidget, QFormLayout,
    QGroupBox, QScrollArea, QMessageBox, QProgressDialog, QTabWidget,
    QFrame, QSizePolicy, QButtonGroup, QRadioButton
)

from ..services.api_client import UltiBotAPIClient, APIError
from ...ultibot_backend.core.domain_models.user_configuration_models import (
    AssetTradingParameters, MarketCapRange, ConfidenceThresholds
)

logger = logging.getLogger(__name__)


class ParameterExecutionWorker(QThread):
    """Worker thread para operaciones asíncronas de parámetros de trading."""
    
    operation_completed = pyqtSignal(dict)
    operation_error = pyqtSignal(str)
    operation_progress = pyqtSignal(str)
    
    def __init__(self, api_client: UltiBotAPIClient, operation: str, data: Dict[str, Any] = None):
        super().__init__()
        self.api_client = api_client
        self.operation = operation
        self.data = data or {}
        
    def run(self):
        """Ejecuta la operación en el worker thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if self.operation == "load_parameters":
                    self.operation_progress.emit("Cargando parámetros de trading...")
                    result = loop.run_until_complete(self.api_client.get_asset_trading_parameters())
                    
                elif self.operation == "create_parameter":
                    self.operation_progress.emit("Creando nuevo parámetro...")
                    result = loop.run_until_complete(
                        self.api_client.create_asset_trading_parameters(self.data)
                    )
                    
                elif self.operation == "update_parameter":
                    parameter_id = self.data.pop("id")
                    self.operation_progress.emit(f"Actualizando parámetro {parameter_id}...")
                    result = loop.run_until_complete(
                        self.api_client.update_asset_trading_parameters(parameter_id, self.data)
                    )
                    
                elif self.operation == "delete_parameter":
                    parameter_id = self.data["id"]
                    self.operation_progress.emit(f"Eliminando parámetro {parameter_id}...")
                    result = loop.run_until_complete(
                        self.api_client.delete_asset_trading_parameters(parameter_id)
                    )
                    
                else:
                    raise ValueError(f"Operación no reconocida: {self.operation}")
                    
                self.operation_completed.emit({"operation": self.operation, "result": result})
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error en worker thread para operación {self.operation}: {e}")
            self.operation_error.emit(str(e))


class ParameterDetailsWidget(QWidget):
    """Widget para mostrar y editar detalles de parámetros de trading."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.clear_form()
        
    def setup_ui(self):
        """Configura la interfaz del widget de detalles."""
        layout = QVBoxLayout(self)
        
        # Crear scroll area para el formulario
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        
        # Widget contenedor para el formulario
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # === TAB WIDGET PRINCIPAL ===
        self.tab_widget = QTabWidget()
        
        # Tab 1: Información Básica
        self._create_basic_info_tab()
        
        # Tab 2: Asset Selection
        self._create_asset_selection_tab()
        
        # Tab 3: Risk Management
        self._create_risk_management_tab()
        
        # Tab 4: Position Management
        self._create_position_management_tab()
        
        # Tab 5: Execution Settings
        self._create_execution_settings_tab()
        
        form_layout.addWidget(self.tab_widget)
        
        # Configurar scroll area
        scroll_area.setWidget(form_widget)
        layout.addWidget(scroll_area)
        
    def _create_basic_info_tab(self):
        """Crea la pestaña de información básica."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Información básica
        basic_group = QGroupBox("Información Básica")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: BTC High Volatility Parameters")
        basic_layout.addRow("Nombre*:", self.name_edit)
        
        # Status
        self.is_active_checkbox = QCheckBox("Activo")
        self.is_active_checkbox.setChecked(True)
        basic_layout.addRow("Estado:", self.is_active_checkbox)
        
        layout.addRow(basic_group)
        
        # Thresholds de confianza
        confidence_group = QGroupBox("Umbrales de Confianza")
        confidence_layout = QFormLayout(confidence_group)
        
        self.paper_confidence_spin = QDoubleSpinBox()
        self.paper_confidence_spin.setRange(0.0, 1.0)
        self.paper_confidence_spin.setSingleStep(0.05)
        self.paper_confidence_spin.setDecimals(2)
        self.paper_confidence_spin.setValue(0.5)
        self.paper_confidence_spin.setSuffix(" (50%)")
        confidence_layout.addRow("Paper Trading:", self.paper_confidence_spin)
        
        self.real_confidence_spin = QDoubleSpinBox()
        self.real_confidence_spin.setRange(0.0, 1.0)
        self.real_confidence_spin.setSingleStep(0.05)
        self.real_confidence_spin.setDecimals(2)
        self.real_confidence_spin.setValue(0.95)
        self.real_confidence_spin.setSuffix(" (95%)")
        confidence_layout.addRow("Real Trading:", self.real_confidence_spin)
        
        # Conectar para actualizar sufijos
        self.paper_confidence_spin.valueChanged.connect(
            lambda v: self.paper_confidence_spin.setSuffix(f" ({v*100:.0f}%)")
        )
        self.real_confidence_spin.valueChanged.connect(
            lambda v: self.real_confidence_spin.setSuffix(f" ({v*100:.0f}%)")
        )
        
        layout.addRow(confidence_group)
        
        self.tab_widget.addTab(tab, "Información Básica")
        
    def _create_asset_selection_tab(self):
        """Crea la pestaña de selección de activos."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tipo de aplicación
        application_group = QGroupBox("Aplicación de Parámetros")
        application_layout = QVBoxLayout(application_group)
        
        # Radio buttons para tipo de aplicación
        self.application_type_group = QButtonGroup()
        
        self.symbols_radio = QRadioButton("Símbolos Específicos")
        self.categories_radio = QRadioButton("Categorías de Activos")  
        self.market_cap_radio = QRadioButton("Rango de Market Cap")
        
        self.application_type_group.addButton(self.symbols_radio, 0)
        self.application_type_group.addButton(self.categories_radio, 1)
        self.application_type_group.addButton(self.market_cap_radio, 2)
        
        self.symbols_radio.setChecked(True)  # Default
        
        application_layout.addWidget(self.symbols_radio)
        application_layout.addWidget(self.categories_radio)
        application_layout.addWidget(self.market_cap_radio)
        
        layout.addWidget(application_group)
        
        # Símbolos específicos
        symbols_group = QGroupBox("Símbolos Específicos")
        symbols_layout = QFormLayout(symbols_group)
        
        self.symbols_edit = QLineEdit()
        self.symbols_edit.setPlaceholderText("BTC,ETH,ADA (separados por comas)")
        symbols_layout.addRow("Símbolos:", self.symbols_edit)
        
        layout.addWidget(symbols_group)
        
        # Categorías
        categories_group = QGroupBox("Categorías de Activos")
        categories_layout = QFormLayout(categories_group)
        
        self.categories_edit = QLineEdit()
        self.categories_edit.setPlaceholderText("defi,layer1,gaming (separados por comas)")
        categories_layout.addRow("Categorías:", self.categories_edit)
        
        layout.addWidget(categories_group)
        
        # Market Cap Range
        market_cap_group = QGroupBox("Rango de Market Cap")
        market_cap_layout = QFormLayout(market_cap_group)
        
        self.market_cap_combo = QComboBox()
        for market_cap in MarketCapRange:
            display_name = self._get_market_cap_display_name(market_cap)
            self.market_cap_combo.addItem(display_name, market_cap.value)
        market_cap_layout.addRow("Rango:", self.market_cap_combo)
        
        layout.addWidget(market_cap_group)
        
        # Conectar radio buttons para habilitar/deshabilitar secciones
        self.symbols_radio.toggled.connect(lambda: self._toggle_asset_sections())
        self.categories_radio.toggled.connect(lambda: self._toggle_asset_sections())
        self.market_cap_radio.toggled.connect(lambda: self._toggle_asset_sections())
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Selección de Activos")
        
    def _create_risk_management_tab(self):
        """Crea la pestaña de gestión de riesgo."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Position Size
        position_group = QGroupBox("Gestión de Posición")
        position_layout = QFormLayout(position_group)
        
        self.max_position_size_spin = QDoubleSpinBox()
        self.max_position_size_spin.setRange(0.1, 100.0)
        self.max_position_size_spin.setSingleStep(0.5)
        self.max_position_size_spin.setDecimals(1)
        self.max_position_size_spin.setValue(5.0)
        self.max_position_size_spin.setSuffix("%")
        position_layout.addRow("Tamaño Máximo de Posición:", self.max_position_size_spin)
        
        layout.addRow(position_group)
        
        # Stop Loss y Take Profit
        sl_tp_group = QGroupBox("Stop Loss y Take Profit")
        sl_tp_layout = QFormLayout(sl_tp_group)
        
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.5, 50.0)
        self.stop_loss_spin.setSingleStep(0.5)
        self.stop_loss_spin.setDecimals(1)
        self.stop_loss_spin.setValue(5.0)
        self.stop_loss_spin.setSuffix("%")
        sl_tp_layout.addRow("Stop Loss:", self.stop_loss_spin)
        
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(1.0, 200.0)
        self.take_profit_spin.setSingleStep(1.0)
        self.take_profit_spin.setDecimals(1)
        self.take_profit_spin.setValue(15.0)
        self.take_profit_spin.setSuffix("%")
        sl_tp_layout.addRow("Take Profit:", self.take_profit_spin)
        
        layout.addRow(sl_tp_group)
        
        # Position Sizing Dinámico
        dynamic_group = QGroupBox("Position Sizing Dinámico")
        dynamic_layout = QFormLayout(dynamic_group)
        
        self.dynamic_sizing_checkbox = QCheckBox("Habilitar sizing dinámico basado en volatilidad")
        dynamic_layout.addRow(self.dynamic_sizing_checkbox)
        
        self.volatility_adjustment_spin = QDoubleSpinBox()
        self.volatility_adjustment_spin.setRange(0.5, 2.0)
        self.volatility_adjustment_spin.setSingleStep(0.1)
        self.volatility_adjustment_spin.setDecimals(1)
        self.volatility_adjustment_spin.setValue(1.0)
        self.volatility_adjustment_spin.setEnabled(False)
        dynamic_layout.addRow("Factor de Ajuste de Volatilidad:", self.volatility_adjustment_spin)
        
        # Conectar checkbox para habilitar/deshabilitar spin
        self.dynamic_sizing_checkbox.toggled.connect(
            lambda checked: self.volatility_adjustment_spin.setEnabled(checked)
        )
        
        layout.addRow(dynamic_group)
        
        # Backtesting
        backtest_group = QGroupBox("Backtesting y Validación")
        backtest_layout = QFormLayout(backtest_group)
        
        self.min_backtest_score_spin = QDoubleSpinBox()
        self.min_backtest_score_spin.setRange(0.0, 1.0)
        self.min_backtest_score_spin.setSingleStep(0.05)
        self.min_backtest_score_spin.setDecimals(2)
        self.min_backtest_score_spin.setValue(0.7)
        backtest_layout.addRow("Score Mínimo de Backtest:", self.min_backtest_score_spin)
        
        self.require_forward_testing_checkbox = QCheckBox("Requiere forward testing antes de trading real")
        self.require_forward_testing_checkbox.setChecked(True)
        backtest_layout.addRow(self.require_forward_testing_checkbox)
        
        layout.addRow(backtest_group)
        
        self.tab_widget.addTab(tab, "Gestión de Riesgo")
        
    def _create_position_management_tab(self):
        """Crea la pestaña de gestión de posiciones."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Trading Rules
        trading_group = QGroupBox("Reglas de Trading")
        trading_layout = QFormLayout(trading_group)
        
        self.allow_pyramiding_checkbox = QCheckBox("Permitir pyramiding (agregar a posiciones ganadoras)")
        trading_layout.addRow(self.allow_pyramiding_checkbox)
        
        self.max_concurrent_positions_spin = QSpinBox()
        self.max_concurrent_positions_spin.setRange(1, 20)
        self.max_concurrent_positions_spin.setValue(3)
        trading_layout.addRow("Máximo Posiciones Concurrentes:", self.max_concurrent_positions_spin)
        
        self.min_time_between_trades_spin = QSpinBox()
        self.min_time_between_trades_spin.setRange(0, 168)  # 0 a 168 horas (1 semana)
        self.min_time_between_trades_spin.setValue(1)
        self.min_time_between_trades_spin.setSuffix(" horas")
        trading_layout.addRow("Tiempo Mínimo Entre Trades:", self.min_time_between_trades_spin)
        
        layout.addRow(trading_group)
        
        self.tab_widget.addTab(tab, "Gestión de Posiciones")
        
    def _create_execution_settings_tab(self):
        """Crea la pestaña de configuración de ejecución."""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Order Types
        order_group = QGroupBox("Tipos de Órdenes")
        order_layout = QFormLayout(order_group)
        
        self.use_market_orders_checkbox = QCheckBox("Usar órdenes de mercado en lugar de límite")
        order_layout.addRow(self.use_market_orders_checkbox)
        
        self.slippage_tolerance_spin = QDoubleSpinBox()
        self.slippage_tolerance_spin.setRange(0.01, 5.0)
        self.slippage_tolerance_spin.setSingleStep(0.01)
        self.slippage_tolerance_spin.setDecimals(2)
        self.slippage_tolerance_spin.setValue(0.1)
        self.slippage_tolerance_spin.setSuffix("%")
        order_layout.addRow("Tolerancia de Slippage:", self.slippage_tolerance_spin)
        
        layout.addRow(order_group)
        
        self.tab_widget.addTab(tab, "Configuración de Ejecución")
        
    def _toggle_asset_sections(self):
        """Habilita/deshabilita secciones según el tipo de aplicación seleccionado."""
        symbols_enabled = self.symbols_radio.isChecked()
        categories_enabled = self.categories_radio.isChecked()
        market_cap_enabled = self.market_cap_radio.isChecked()
        
        # Encontrar los group boxes
        for i in range(self.tab_widget.widget(1).layout().count()):
            item = self.tab_widget.widget(1).layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QGroupBox):
                    if "Símbolos Específicos" in widget.title():
                        widget.setEnabled(symbols_enabled)
                    elif "Categorías" in widget.title():
                        widget.setEnabled(categories_enabled)
                    elif "Market Cap" in widget.title():
                        widget.setEnabled(market_cap_enabled)
                        
    def _get_market_cap_display_name(self, market_cap: MarketCapRange) -> str:
        """Convierte MarketCapRange a nombre display."""
        market_cap_names = {
            MarketCapRange.MICRO: "Micro Cap (< $300M)",
            MarketCapRange.SMALL: "Small Cap ($300M - $2B)",
            MarketCapRange.MID: "Mid Cap ($2B - $10B)",
            MarketCapRange.LARGE: "Large Cap ($10B - $200B)",
            MarketCapRange.MEGA: "Mega Cap (> $200B)",
            MarketCapRange.ALL: "Todos los rangos"
        }
        return market_cap_names.get(market_cap, market_cap.value)
        
    def populate_form(self, parameter_data: Dict[str, Any]):
        """Rellena el formulario con datos de parámetros."""
        try:
            # Información básica
            self.name_edit.setText(parameter_data.get('name', ''))
            self.is_active_checkbox.setChecked(parameter_data.get('is_active', True))
            
            # Confidence thresholds
            confidence_thresholds = parameter_data.get('confidence_thresholds', {})
            if confidence_thresholds:
                self.paper_confidence_spin.setValue(confidence_thresholds.get('paper_trading', 0.5))
                self.real_confidence_spin.setValue(confidence_thresholds.get('real_trading', 0.95))
            
            # Asset selection
            applies_to_symbols = parameter_data.get('applies_to_symbols', [])
            applies_to_categories = parameter_data.get('applies_to_categories', [])
            applies_to_market_cap = parameter_data.get('applies_to_market_cap_range')
            
            if applies_to_symbols:
                self.symbols_radio.setChecked(True)
                self.symbols_edit.setText(','.join(applies_to_symbols))
            elif applies_to_categories:
                self.categories_radio.setChecked(True)
                self.categories_edit.setText(','.join(applies_to_categories))
            elif applies_to_market_cap:
                self.market_cap_radio.setChecked(True)
                # Encontrar el índice correcto
                for i in range(self.market_cap_combo.count()):
                    if self.market_cap_combo.itemData(i) == applies_to_market_cap:
                        self.market_cap_combo.setCurrentIndex(i)
                        break
            else:
                self.symbols_radio.setChecked(True)  # Default
                
            self._toggle_asset_sections()
            
            # Risk management
            self.max_position_size_spin.setValue(parameter_data.get('max_position_size_percent', 5.0))
            self.stop_loss_spin.setValue(parameter_data.get('stop_loss_percentage', 5.0))
            self.take_profit_spin.setValue(parameter_data.get('take_profit_percentage', 15.0))
            
            self.dynamic_sizing_checkbox.setChecked(parameter_data.get('dynamic_position_sizing', False))
            self.volatility_adjustment_spin.setValue(parameter_data.get('volatility_adjustment_factor', 1.0))
            
            self.min_backtest_score_spin.setValue(parameter_data.get('min_backtest_score', 0.7))
            self.require_forward_testing_checkbox.setChecked(parameter_data.get('require_forward_testing', True))
            
            # Position management
            self.allow_pyramiding_checkbox.setChecked(parameter_data.get('allow_pyramiding', False))
            self.max_concurrent_positions_spin.setValue(parameter_data.get('max_concurrent_positions', 3))
            self.min_time_between_trades_spin.setValue(parameter_data.get('min_time_between_trades_hours', 1))
            
            # Execution settings
            self.use_market_orders_checkbox.setChecked(parameter_data.get('use_market_orders', False))
            self.slippage_tolerance_spin.setValue(parameter_data.get('slippage_tolerance_percent', 0.1))
            
            logger.info(f"Formulario poblado con parámetros: {parameter_data.get('name', 'sin nombre')}")
            
        except Exception as e:
            logger.error(f"Error poblando formulario: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando datos del formulario: {e}")
            
    def get_form_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario."""
        try:
            data = {
                'name': self.name_edit.text().strip(),
                'is_active': self.is_active_checkbox.isChecked(),
            }
            
            # Confidence thresholds
            data['confidence_thresholds'] = {
                'paper_trading': self.paper_confidence_spin.value(),
                'real_trading': self.real_confidence_spin.value()
            }
            
            # Asset selection
            if self.symbols_radio.isChecked():
                symbols_text = self.symbols_edit.text().strip()
                if symbols_text:
                    data['applies_to_symbols'] = [s.strip().upper() for s in symbols_text.split(',') if s.strip()]
            elif self.categories_radio.isChecked():
                categories_text = self.categories_edit.text().strip()
                if categories_text:
                    data['applies_to_categories'] = [c.strip().lower() for c in categories_text.split(',') if c.strip()]
            elif self.market_cap_radio.isChecked():
                data['applies_to_market_cap_range'] = self.market_cap_combo.currentData()
            
            # Risk management
            data['max_position_size_percent'] = self.max_position_size_spin.value()
            data['stop_loss_percentage'] = self.stop_loss_spin.value()
            data['take_profit_percentage'] = self.take_profit_spin.value()
            
            data['dynamic_position_sizing'] = self.dynamic_sizing_checkbox.isChecked()
            if data['dynamic_position_sizing']:
                data['volatility_adjustment_factor'] = self.volatility_adjustment_spin.value()
            
            data['min_backtest_score'] = self.min_backtest_score_spin.value()
            data['require_forward_testing'] = self.require_forward_testing_checkbox.isChecked()
            
            # Position management
            data['allow_pyramiding'] = self.allow_pyramiding_checkbox.isChecked()
            data['max_concurrent_positions'] = self.max_concurrent_positions_spin.value()
            data['min_time_between_trades_hours'] = self.min_time_between_trades_spin.value()
            
            # Execution settings
            data['use_market_orders'] = self.use_market_orders_checkbox.isChecked()
            data['slippage_tolerance_percent'] = self.slippage_tolerance_spin.value()
            
            return data
            
        except Exception as e:
            logger.error(f"Error obteniendo datos del formulario: {e}")
            raise
            
    def clear_form(self):
        """Limpia el formulario."""
        self.name_edit.clear()
        self.is_active_checkbox.setChecked(True)
        
        self.paper_confidence_spin.setValue(0.5)
        self.real_confidence_spin.setValue(0.95)
        
        self.symbols_radio.setChecked(True)
        self.symbols_edit.clear()
        self.categories_edit.clear()
        self.market_cap_combo.setCurrentIndex(0)
        self._toggle_asset_sections()
        
        self.max_position_size_spin.setValue(5.0)
        self.stop_loss_spin.setValue(5.0)
        self.take_profit_spin.setValue(15.0)
        
        self.dynamic_sizing_checkbox.setChecked(False)
        self.volatility_adjustment_spin.setValue(1.0)
        
        self.min_backtest_score_spin.setValue(0.7)
        self.require_forward_testing_checkbox.setChecked(True)
        
        self.allow_pyramiding_checkbox.setChecked(False)
        self.max_concurrent_positions_spin.setValue(3)
        self.min_time_between_trades_spin.setValue(1)
        
        self.use_market_orders_checkbox.setChecked(False)
        self.slippage_tolerance_spin.setValue(0.1)
        
    def validate_form(self) -> tuple[bool, List[str]]:
        """Valida el formulario y retorna (es_válido, lista_de_errores)."""
        errors = []
        
        # Validar nombre
        if not self.name_edit.text().strip():
            errors.append("El nombre es obligatorio")
            
        # Validar confidence thresholds
        if self.real_confidence_spin.value() <= self.paper_confidence_spin.value():
            errors.append("El umbral de trading real debe ser mayor al de paper trading")
            
        # Validar asset selection
        symbols_checked = self.symbols_radio.isChecked()
        categories_checked = self.categories_radio.isChecked()
        market_cap_checked = self.market_cap_radio.isChecked()
        
        if symbols_checked and not self.symbols_edit.text().strip():
            errors.append("Debe especificar al menos un símbolo")
        elif categories_checked and not self.categories_edit.text().strip():
            errors.append("Debe especificar al menos una categoría")
        elif not (symbols_checked or categories_checked or market_cap_checked):
            errors.append("Debe seleccionar un tipo de aplicación")
            
        # Validar stop loss vs take profit
        if self.take_profit_spin.value() <= self.stop_loss_spin.value():
            errors.append("El take profit debe ser mayor al stop loss")
            
        return len(errors) == 0, errors
        
    def set_form_editable(self, editable: bool):
        """Habilita o deshabilita la edición del formulario."""
        self.setEnabled(editable)


class MockAPIClient:
    """Cliente API mock para testing independiente."""
    
    def __init__(self):
        self.parameters = [
            {
                "id": "btc-high-vol",
                "name": "BTC High Volatility",
                "applies_to_symbols": ["BTC"],
                "confidence_thresholds": {
                    "paper_trading": 0.6,
                    "real_trading": 0.95
                },
                "max_position_size_percent": 10.0,
                "stop_loss_percentage": 8.0,
                "take_profit_percentage": 25.0,
                "dynamic_position_sizing": True,
                "volatility_adjustment_factor": 1.2,
                "allow_pyramiding": False,
                "max_concurrent_positions": 2,
                "min_time_between_trades_hours": 6,
                "use_market_orders": False,
                "slippage_tolerance_percent": 0.2,
                "min_backtest_score": 0.8,
                "require_forward_testing": True,
                "is_active": True,
                "created_at": "2025-01-06T20:00:00Z",
                "updated_at": "2025-01-06T20:00:00Z"
            },
            {
                "id": "defi-moderate",
                "name": "DeFi Moderate Risk",
                "applies_to_categories": ["defi", "yield-farming"],
                "confidence_thresholds": {
                    "paper_trading": 0.7,
                    "real_trading": 0.90
                },
                "max_position_size_percent": 5.0,
                "stop_loss_percentage": 12.0,
                "take_profit_percentage": 30.0,
                "dynamic_position_sizing": False,
                "allow_pyramiding": True,
                "max_concurrent_positions": 5,
                "min_time_between_trades_hours": 2,
                "use_market_orders": False,
                "slippage_tolerance_percent": 0.5,
                "min_backtest_score": 0.75,
                "require_forward_testing": True,
                "is_active": True,
                "created_at": "2025-01-06T20:00:00Z",
                "updated_at": "2025-01-06T20:00:00Z"
            }
        ]
        
    async def get_asset_trading_parameters(self):
        """Mock: obtiene parámetros de trading."""
        return self.parameters.copy()
        
    async def create_asset_trading_parameters(self, parameters):
        """Mock: crea parámetros de trading."""
        new_param = parameters.copy()
        new_param["id"] = str(uuid.uuid4())[:8]
        new_param["created_at"] = datetime.now().isoformat()
        new_param["updated_at"] = datetime.now().isoformat()
        self.parameters.append(new_param)
        return new_param
        
    async def update_asset_trading_parameters(self, parameter_id, parameters):
        """Mock: actualiza parámetros de trading."""
        for i, param in enumerate(self.parameters):
            if param["id"] == parameter_id:
                updated_param = param.copy()
                updated_param.update(parameters)
                updated_param["updated_at"] = datetime.now().isoformat()
                self.parameters[i] = updated_param
                return updated_param
        raise APIError(f"Parámetro con ID {parameter_id} no encontrado", 404)
        
    async def delete_asset_trading_parameters(self, parameter_id):
        """Mock: elimina parámetros de trading."""
        for i, param in enumerate(self.parameters):
            if param["id"] == parameter_id:
                self.parameters.pop(i)
                return True
        raise APIError(f"Parámetro con ID {parameter_id} no encontrado", 404)


class AssetTradingParametersDialog(QDialog):
    """Diálogo para gestión CRUD de parámetros de trading por activo."""
    
    def __init__(self, api_client: UltiBotAPIClient = None, parent=None):
        super().__init__(parent)
        
        # Configurar API client (usar mock si no se proporciona)
        self.api_client = api_client or MockAPIClient()
        self.is_mock_mode = api_client is None
        
        # Variables de estado
        self.parameters_data = []
        self.current_parameter_id = None
        self.is_form_modified = False
        self.worker = None
        
        # Configurar UI
        self.setWindowTitle("Gestión de Parámetros de Trading por Activo")
        self.setModal(True)
        self.resize(1200, 800)
        self.setup_ui()
        self.setup_connections()
        
        # Cargar datos iniciales
        self.load_parameters()
        
        logger.info("AssetTradingParametersDialog inicializado")
        
    def setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        
        # Header con título
        header_label = QLabel("Configuración de Parámetros de Trading por Activo")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header_label)
        
        # Splitter principal (lista izquierda, detalles derecha)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === PANEL IZQUIERDO: Lista de parámetros ===
        left_panel = self._create_parameters_list_panel()
        splitter.addWidget(left_panel)
        
        # === PANEL DERECHO: Detalles y formulario ===
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([400, 800])
        layout.addWidget(splitter)
        
        # === BOTONES DE ACCIÓN ===
        button_layout = self._create_action_buttons()
        layout.addLayout(button_layout)
        
        if self.is_mock_mode:
            mock_label = QLabel("⚠️ Modo de prueba: usando datos simulados")
            mock_label.setStyleSheet("color: orange; font-weight: bold; margin: 5px;")
            layout.addWidget(mock_label)
            
    def _create_parameters_list_panel(self) -> QWidget:
        """Crea el panel izquierdo con la lista de parámetros."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título y controles
        title_layout = QHBoxLayout()
        title_label = QLabel("Parámetros de Trading")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # Botón refresh
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(30, 30)
        self.refresh_btn.setToolTip("Actualizar lista")
        title_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(title_layout)
        
        # Lista de parámetros
        self.parameters_list = QListWidget()
        self.parameters_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.parameters_list)
        
        # Botones de gestión
        buttons_layout = QVBoxLayout()
        
        self.create_parameter_btn = QPushButton("Crear Nuevo")
        self.create_parameter_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; }")
        buttons_layout.addWidget(self.create_parameter_btn)
        
        self.duplicate_parameter_btn = QPushButton("Duplicar")
        self.duplicate_parameter_btn.setEnabled(False)
        buttons_layout.addWidget(self.duplicate_parameter_btn)
        
        self.delete_parameter_btn = QPushButton("Eliminar")
        self.delete_parameter_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        self.delete_parameter_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_parameter_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
        
    def _create_details_panel(self) -> QWidget:
        """Crea el panel derecho con detalles y formulario."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título de detalles
        self.details_title = QLabel("Seleccione un parámetro para ver detalles")
        self.details_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.details_title)
        
        # Widget de detalles
        self.details_widget = ParameterDetailsWidget()
        self.details_widget.setEnabled(False)
        layout.addWidget(self.details_widget)
        
        return panel
        
    def _create_action_buttons(self) -> QHBoxLayout:
        """Crea los botones de acción principales."""
        layout = QHBoxLayout()
        
        # Botones de formulario (solo visibles cuando hay selección)
        self.save_parameter_btn = QPushButton("Guardar Cambios")
        self.save_parameter_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; }")
        self.save_parameter_btn.setVisible(False)
        layout.addWidget(self.save_parameter_btn)
        
        self.cancel_changes_btn = QPushButton("Cancelar Cambios")
        self.cancel_changes_btn.setVisible(False)
        layout.addWidget(self.cancel_changes_btn)
        
        layout.addStretch()
        
        # Botón cerrar
        self.close_btn = QPushButton("Cerrar")
        layout.addWidget(self.close_btn)
        
        return layout
        
    def setup_connections(self):
        """Configura las conexiones de señales."""
        # Lista de parámetros
        self.parameters_list.currentItemChanged.connect(self._on_parameter_selection_changed)
        
        # Botones de gestión
        self.refresh_btn.clicked.connect(self.load_parameters)
        self.create_parameter_btn.clicked.connect(self._create_new_parameter)
        self.duplicate_parameter_btn.clicked.connect(self._duplicate_parameter)
        self.delete_parameter_btn.clicked.connect(self._delete_parameter)
        
        # Botones de acción
        self.save_parameter_btn.clicked.connect(self._save_parameter)
        self.cancel_changes_btn.clicked.connect(self._cancel_changes)
        self.close_btn.clicked.connect(self.close)
        
        # Detectar cambios en el formulario para mostrar botones de guardar/cancelar
        self._setup_form_change_detection()
        
    def _setup_form_change_detection(self):
        """Configura detección de cambios en el formulario."""
        # Timer para detectar cambios
        self.change_timer = QTimer()
        self.change_timer.setSingleShot(True)
        self.change_timer.timeout.connect(self._on_form_changed)
        
        # Conectar widgets relevantes
        widgets_to_watch = [
            self.details_widget.name_edit,
            self.details_widget.is_active_checkbox,
            self.details_widget.paper_confidence_spin,
            self.details_widget.real_confidence_spin,
            self.details_widget.symbols_edit,
            self.details_widget.categories_edit,
            self.details_widget.market_cap_combo,
            self.details_widget.max_position_size_spin,
            self.details_widget.stop_loss_spin,
            self.details_widget.take_profit_spin,
            self.details_widget.dynamic_sizing_checkbox,
            self.details_widget.volatility_adjustment_spin,
            self.details_widget.min_backtest_score_spin,
            self.details_widget.require_forward_testing_checkbox,
            self.details_widget.allow_pyramiding_checkbox,
            self.details_widget.max_concurrent_positions_spin,
            self.details_widget.min_time_between_trades_spin,
            self.details_widget.use_market_orders_checkbox,
            self.details_widget.slippage_tolerance_spin,
        ]
        
        for widget in widgets_to_watch:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(lambda: self.change_timer.start(500))
            elif hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(lambda: self.change_timer.start(500))
            elif hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(lambda: self.change_timer.start(500))
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(lambda: self.change_timer.start(500))
                
        # Radio buttons
        for radio in [self.details_widget.symbols_radio, self.details_widget.categories_radio, self.details_widget.market_cap_radio]:
            radio.toggled.connect(lambda: self.change_timer.start(500))
            
    def _on_form_changed(self):
        """Maneja cambios en el formulario."""
        if self.current_parameter_id:
            self.is_form_modified = True
            self.save_parameter_btn.setVisible(True)
            self.cancel_changes_btn.setVisible(True)
            
    def load_parameters(self):
        """Carga la lista de parámetros de trading."""
        if self.worker and self.worker.isRunning():
            return
            
        self.worker = ParameterExecutionWorker(self.api_client, "load_parameters")
        self.worker.operation_completed.connect(self._on_parameters_loaded)
        self.worker.operation_error.connect(self._on_operation_error)
        self.worker.start()
        
        logger.info("Iniciando carga de parámetros de trading")
        
    def _on_parameters_loaded(self, result: Dict[str, Any]):
        """Maneja la carga exitosa de parámetros."""
        try:
            self.parameters_data = result["result"]
            self._populate_parameters_list()
            logger.info(f"Cargados {len(self.parameters_data)} parámetros de trading")
            
        except Exception as e:
            logger.error(f"Error procesando parámetros cargados: {e}")
            self._show_error("Error procesando datos", str(e))
            
    def _populate_parameters_list(self):
        """Pobla la lista de parámetros."""
        self.parameters_list.clear()
        
        for param in self.parameters_data:
            # Crear item con información básica
            name = param.get('name', 'Sin nombre')
            is_active = param.get('is_active', True)
            
            # Determinar el tipo de aplicación
            applies_to = ""
            if param.get('applies_to_symbols'):
                applies_to = f"Símbolos: {', '.join(param['applies_to_symbols'][:2])}{'...' if len(param['applies_to_symbols']) > 2 else ''}"
            elif param.get('applies_to_categories'):
                applies_to = f"Categorías: {', '.join(param['applies_to_categories'][:2])}{'...' if len(param['applies_to_categories']) > 2 else ''}"
            elif param.get('applies_to_market_cap_range'):
                applies_to = f"Market Cap: {param['applies_to_market_cap_range']}"
            else:
                applies_to = "Sin aplicación definida"
                
            item_text = f"{name}\n{applies_to}"
            if not is_active:
                item_text += " (Inactivo)"
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, param)
            
            # Aplicar estilo según estado
            if not is_active:
                item.setForeground(Qt.GlobalColor.gray)
                
            self.parameters_list.addItem(item)
            
    def _on_parameter_selection_changed(self, current_item, previous_item):
        """Maneja cambios en la selección de parámetros."""
        if self.is_form_modified:
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Desea continuar sin guardar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                # Restaurar selección anterior
                if previous_item:
                    self.parameters_list.setCurrentItem(previous_item)
                return
                
        # Proceder con el cambio de selección
        if current_item:
            parameter_data = current_item.data(Qt.ItemDataRole.UserRole)
            self.current_parameter_id = parameter_data.get('id')
            self._load_parameter_details(parameter_data)
            
            # Habilitar controles
            self.details_widget.setEnabled(True)
            self.duplicate_parameter_btn.setEnabled(True)
            self.delete_parameter_btn.setEnabled(True)
            
            # Actualizar título
            self.details_title.setText(f"Parámetros: {parameter_data.get('name', 'Sin nombre')}")
            
        else:
            self.current_parameter_id = None
            self.details_widget.clear_form()
            self.details_widget.setEnabled(False)
            self.duplicate_parameter_btn.setEnabled(False)
            self.delete_parameter_btn.setEnabled(False)
            self.details_title.setText("Seleccione un parámetro para ver detalles")
            
        # Ocultar botones de guardar/cancelar
        self.is_form_modified = False
        self.save_parameter_btn.setVisible(False)
        self.cancel_changes_btn.setVisible(False)
        
    def _load_parameter_details(self, parameter_data: Dict[str, Any]):
        """Carga los detalles de un parámetro en el formulario."""
        try:
            self.details_widget.populate_form(parameter_data)
            logger.info(f"Detalles cargados para parámetro: {parameter_data.get('name', 'sin nombre')}")
            
        except Exception as e:
            logger.error(f"Error cargando detalles del parámetro: {e}")
            self._show_error("Error cargando detalles", str(e))
            
    def _create_new_parameter(self):
        """Crea un nuevo parámetro de trading."""
        if self.is_form_modified:
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Desea continuar sin guardar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
                
        # Limpiar selección y formulario
        self.parameters_list.clearSelection()
        self.current_parameter_id = None
        self.details_widget.clear_form()
        self.details_widget.setEnabled(True)
        
        # Establecer valores por defecto para nuevo parámetro
        self.details_widget.name_edit.setText("Nuevo Parámetro")
        self.details_widget.name_edit.selectAll()
        self.details_widget.name_edit.setFocus()
        
        # Mostrar botones de guardar/cancelar
        self.is_form_modified = True
        self.save_parameter_btn.setVisible(True)
        self.cancel_changes_btn.setVisible(True)
        
        # Actualizar título
        self.details_title.setText("Nuevo Parámetro de Trading")
        
        logger.info("Iniciando creación de nuevo parámetro")
        
    def _duplicate_parameter(self):
        """Duplica el parámetro seleccionado."""
        current_item = self.parameters_list.currentItem()
        if not current_item:
            return
            
        parameter_data = current_item.data(Qt.ItemDataRole.UserRole)
        
        # Crear copia con nuevo nombre
        duplicated_data = parameter_data.copy()
        duplicated_data['name'] = f"{parameter_data.get('name', 'Sin nombre')} (Copia)"
        
        # Limpiar campos que no deben duplicarse
        duplicated_data.pop('id', None)
        duplicated_data.pop('created_at', None)
        duplicated_data.pop('updated_at', None)
        
        # Limpiar selección y cargar datos duplicados
        self.parameters_list.clearSelection()
        self.current_parameter_id = None
        self.details_widget.populate_form(duplicated_data)
        self.details_widget.setEnabled(True)
        
        # Mostrar botones de guardar/cancelar
        self.is_form_modified = True
        self.save_parameter_btn.setVisible(True)
        self.cancel_changes_btn.setVisible(True)
        
        # Actualizar título
        self.details_title.setText(f"Duplicando: {parameter_data.get('name', 'Sin nombre')}")
        
        logger.info(f"Duplicando parámetro: {parameter_data.get('name', 'sin nombre')}")
        
    def _delete_parameter(self):
        """Elimina el parámetro seleccionado."""
        current_item = self.parameters_list.currentItem()
        if not current_item:
            return
            
        parameter_data = current_item.data(Qt.ItemDataRole.UserRole)
        parameter_name = parameter_data.get('name', 'Sin nombre')
        
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el parámetro '{parameter_name}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.worker and self.worker.isRunning():
                QMessageBox.warning(self, "Operación en curso", "Hay una operación en curso. Espere a que termine.")
                return
                
            self.worker = ParameterExecutionWorker(
                self.api_client, 
                "delete_parameter", 
                {"id": parameter_data.get('id')}
            )
            self.worker.operation_completed.connect(self._on_parameter_deleted)
            self.worker.operation_error.connect(self._on_operation_error)
            self.worker.start()
            
            logger.info(f"Iniciando eliminación de parámetro: {parameter_name}")
            
    def _on_parameter_deleted(self, result: Dict[str, Any]):
        """Maneja la eliminación exitosa de un parámetro."""
        try:
            QMessageBox.information(self, "Éxito", "Parámetro eliminado exitosamente.")
            
            # Recargar lista
            self.load_parameters()
            
            # Limpiar selección
            self.parameters_list.clearSelection()
            
            logger.info("Parámetro eliminado exitosamente")
            
        except Exception as e:
            logger.error(f"Error procesando eliminación: {e}")
            self._show_error("Error procesando eliminación", str(e))
            
    def _save_parameter(self):
        """Guarda el parámetro actual."""
        # Validar formulario
        is_valid, errors = self.details_widget.validate_form()
        if not is_valid:
            QMessageBox.warning(
                self,
                "Errores de validación",
                "Por favor corrija los siguientes errores:\n\n" + "\n".join(f"• {error}" for error in errors)
            )
            return
            
        try:
            form_data = self.details_widget.get_form_data()
            
            if self.worker and self.worker.isRunning():
                QMessageBox.warning(self, "Operación en curso", "Hay una operación en curso. Espere a que termine.")
                return
                
            # Determinar si es creación o actualización
            if self.current_parameter_id:
                # Actualización
                form_data['id'] = self.current_parameter_id
                self.worker = ParameterExecutionWorker(self.api_client, "update_parameter", form_data)
            else:
                # Creación
                self.worker = ParameterExecutionWorker(self.api_client, "create_parameter", form_data)
                
            self.worker.operation_completed.connect(self._on_parameter_saved)
            self.worker.operation_error.connect(self._on_operation_error)
            self.worker.start()
            
            operation = "actualización" if self.current_parameter_id else "creación"
            logger.info(f"Iniciando {operation} de parámetro: {form_data.get('name', 'sin nombre')}")
            
        except Exception as e:
            logger.error(f"Error preparando datos para guardar: {e}")
            self._show_error("Error preparando datos", str(e))
            
    def _on_parameter_saved(self, result: Dict[str, Any]):
        """Maneja el guardado exitoso de un parámetro."""
        try:
            operation = result["operation"]
            saved_data = result["result"]
            
            operation_text = "creado" if operation == "create_parameter" else "actualizado"
            QMessageBox.information(self, "Éxito", f"Parámetro {operation_text} exitosamente.")
            
            # Recargar lista
            self.load_parameters()
            
            # Actualizar estado
            self.current_parameter_id = saved_data.get('id')
            self.is_form_modified = False
            self.save_parameter_btn.setVisible(False)
            self.cancel_changes_btn.setVisible(False)
            
            logger.info(f"Parámetro {operation_text} exitosamente: {saved_data.get('name', 'sin nombre')}")
            
        except Exception as e:
            logger.error(f"Error procesando guardado: {e}")
            self._show_error("Error procesando guardado", str(e))
            
    def _cancel_changes(self):
        """Cancela los cambios en el formulario."""
        reply = QMessageBox.question(
            self,
            "Cancelar cambios",
            "¿Está seguro que desea cancelar los cambios?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.current_parameter_id:
                # Recargar datos originales
                current_item = self.parameters_list.currentItem()
                if current_item:
                    parameter_data = current_item.data(Qt.ItemDataRole.UserRole)
                    self._load_parameter_details(parameter_data)
            else:
                # Limpiar formulario para nuevo parámetro
                self.details_widget.clear_form()
                self.details_widget.setEnabled(False)
                self.details_title.setText("Seleccione un parámetro para ver detalles")
                
            # Ocultar botones
            self.is_form_modified = False
            self.save_parameter_btn.setVisible(False)
            self.cancel_changes_btn.setVisible(False)
            
            logger.info("Cambios cancelados")
            
    def _on_operation_error(self, error_message: str):
        """Maneja errores en las operaciones."""
        logger.error(f"Error en operación: {error_message}")
        self._show_error("Error en operación", error_message)
        
    def _show_error(self, title: str, message: str):
        """Muestra un mensaje de error."""
        QMessageBox.critical(self, title, message)
        
    def closeEvent(self, event):
        """Maneja el cierre del diálogo."""
        if self.is_form_modified:
            reply = QMessageBox.question(
                self,
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Desea cerrar sin guardar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        # Terminar worker si está ejecutándose
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait(3000)  # Esperar hasta 3 segundos
            
        event.accept()
        logger.info("AssetTradingParametersDialog cerrado")


def main():
    """Función principal para testing independiente."""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Configurar logging para debug
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y mostrar diálogo en modo mock
    dialog = AssetTradingParametersDialog()
    dialog.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
