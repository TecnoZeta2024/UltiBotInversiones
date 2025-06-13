"""Preset Management Dialog.

Este módulo contiene el diálogo para gestión CRUD de presets de escaneo de mercado,
permitiendo crear, editar, eliminar y ejecutar presets tanto del sistema como personalizados.
"""

import asyncio
import logging
from datetime import timezone # ADDED timezone
from typing import Dict, List, Optional, Union, Callable, Coroutine

from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget
)

from ...ultibot_backend.core.domain_models.user_configuration_models import (
    MarketScanConfiguration, ScanPreset, TrendDirection, VolumeFilter, MarketCapRange
)
from ..services.api_client import UltiBotAPIClient, APIError
from ..models import BaseMainWindow

logger = logging.getLogger(__name__)

class PresetDetailsWidget(QWidget):
    """Widget para mostrar y editar detalles de un preset."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario del widget de detalles."""
        layout = QVBoxLayout(self)
        
        # Información básica del preset
        basic_group = QGroupBox("Información Básica")
        basic_layout = QGridLayout(basic_group)
        
        # Nombre
        basic_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Nombre descriptivo del preset")
        basic_layout.addWidget(self.name_edit, 0, 1)
        
        # Descripción
        basic_layout.addWidget(QLabel("Descripción:"), 1, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Descripción detallada del preset y su propósito")
        basic_layout.addWidget(self.description_edit, 1, 1)
        
        # Categoría
        basic_layout.addWidget(QLabel("Categoría:"), 2, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "momentum", "breakout", "value", "scalping", "swing", 
            "reversal", "trend", "custom", "experimental"
        ])
        self.category_combo.setEditable(True)
        basic_layout.addWidget(self.category_combo, 2, 1)
        
        # Estrategias recomendadas
        basic_layout.addWidget(QLabel("Estrategias Recomendadas:"), 3, 0)
        self.strategies_edit = QLineEdit()
        self.strategies_edit.setPlaceholderText("Estrategias separadas por comas (ej: momentum_rsi, breakout_volume)")
        basic_layout.addWidget(self.strategies_edit, 3, 1)
        
        layout.addWidget(basic_group)
        
        # Configuración de escaneo
        config_group = QGroupBox("Configuración de Escaneo")
        config_layout = QVBoxLayout(config_group)
        
        # Scroll area para la configuración
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Filtros de precio
        price_frame = QFrame()
        price_frame.setFrameStyle(QFrame.StyledPanel)
        price_layout = QGridLayout(price_frame)
        price_layout.addWidget(QLabel("<b>Filtros de Precio (24h)</b>"), 0, 0, 1, 2)
        
        price_layout.addWidget(QLabel("Cambio mínimo %:"), 1, 0)
        self.min_price_change_edit = QLineEdit()
        self.min_price_change_edit.setPlaceholderText("Ej: 5.0")
        price_layout.addWidget(self.min_price_change_edit, 1, 1)
        
        price_layout.addWidget(QLabel("Cambio máximo %:"), 2, 0)
        self.max_price_change_edit = QLineEdit()
        self.max_price_change_edit.setPlaceholderText("Ej: 50.0")
        price_layout.addWidget(self.max_price_change_edit, 2, 1)
        
        scroll_layout.addWidget(price_frame, 0, 0)
        
        # Filtros de volumen
        volume_frame = QFrame()
        volume_frame.setFrameStyle(QFrame.StyledPanel)
        volume_layout = QGridLayout(volume_frame)
        volume_layout.addWidget(QLabel("<b>Filtros de Volumen</b>"), 0, 0, 1, 2)
        
        volume_layout.addWidget(QLabel("Tipo de filtro:"), 1, 0)
        self.volume_filter_combo = QComboBox()
        for volume_filter in VolumeFilter:
            self.volume_filter_combo.addItem(
                self._get_volume_filter_display_name(volume_filter), 
                volume_filter.value
            )
        volume_layout.addWidget(self.volume_filter_combo, 1, 1)
        
        volume_layout.addWidget(QLabel("Volumen mínimo USD:"), 2, 0)
        self.min_volume_edit = QLineEdit()
        self.min_volume_edit.setPlaceholderText("Ej: 1000000")
        volume_layout.addWidget(self.min_volume_edit, 2, 1)
        
        scroll_layout.addWidget(volume_frame, 0, 1)
        
        # Filtros de market cap
        market_cap_frame = QFrame()
        market_cap_frame.setFrameStyle(QFrame.StyledPanel)
        market_cap_layout = QGridLayout(market_cap_frame)
        market_cap_layout.addWidget(QLabel("<b>Market Cap</b>"), 0, 0, 1, 2)
        
        self.market_cap_checkboxes = {}
        row = 1
        for cap_range in MarketCapRange:
            if cap_range != MarketCapRange.ALL:
                checkbox = QCheckBox(self._get_market_cap_display_name(cap_range))
                self.market_cap_checkboxes[cap_range.value] = checkbox
                market_cap_layout.addWidget(checkbox, row, 0)
                row += 1
        
        scroll_layout.addWidget(market_cap_frame, 1, 0)
        
        # Análisis técnico
        technical_frame = QFrame()
        technical_frame.setFrameStyle(QFrame.StyledPanel)
        technical_layout = QGridLayout(technical_frame)
        technical_layout.addWidget(QLabel("<b>Análisis Técnico</b>"), 0, 0, 1, 2)
        
        technical_layout.addWidget(QLabel("Dirección de tendencia:"), 1, 0)
        self.trend_combo = QComboBox()
        for trend in TrendDirection:
            self.trend_combo.addItem(
                self._get_trend_display_name(trend), 
                trend.value
            )
        technical_layout.addWidget(self.trend_combo, 1, 1)
        
        technical_layout.addWidget(QLabel("RSI mínimo:"), 2, 0)
        self.min_rsi_edit = QLineEdit()
        self.min_rsi_edit.setPlaceholderText("Ej: 30")
        technical_layout.addWidget(self.min_rsi_edit, 2, 1)
        
        technical_layout.addWidget(QLabel("RSI máximo:"), 3, 0)
        self.max_rsi_edit = QLineEdit()
        self.max_rsi_edit.setPlaceholderText("Ej: 70")
        technical_layout.addWidget(self.max_rsi_edit, 3, 1)
        
        scroll_layout.addWidget(technical_frame, 1, 1)
        
        # Configuración de ejecución
        execution_frame = QFrame()
        execution_frame.setFrameStyle(QFrame.StyledPanel)
        execution_layout = QGridLayout(execution_frame)
        execution_layout.addWidget(QLabel("<b>Configuración de Ejecución</b>"), 0, 0, 1, 2)
        
        execution_layout.addWidget(QLabel("Máximo resultados:"), 1, 0)
        self.max_results_edit = QLineEdit()
        self.max_results_edit.setPlaceholderText("50")
        self.max_results_edit.setText("50")
        execution_layout.addWidget(self.max_results_edit, 1, 1)
        
        execution_layout.addWidget(QLabel("Intervalo de escaneo (min):"), 2, 0)
        self.scan_interval_edit = QLineEdit()
        self.scan_interval_edit.setPlaceholderText("15")
        self.scan_interval_edit.setText("15")
        execution_layout.addWidget(self.scan_interval_edit, 2, 1)
        
        scroll_layout.addWidget(execution_frame, 2, 0, 1, 2)
        
        scroll_area.setWidget(scroll_widget)
        config_layout.addWidget(scroll_area)
        
        layout.addWidget(config_group)
        
        # Estado del preset
        status_group = QGroupBox("Estado y Estadísticas")
        status_layout = QGridLayout(status_group)
        
        self.is_system_checkbox = QCheckBox("Preset del sistema")
        self.is_system_checkbox.setEnabled(False)  # Solo lectura
        status_layout.addWidget(self.is_system_checkbox, 0, 0)
        
        self.is_active_checkbox = QCheckBox("Preset activo")
        self.is_active_checkbox.setChecked(True)
        status_layout.addWidget(self.is_active_checkbox, 0, 1)
        
        status_layout.addWidget(QLabel("Veces usado:"), 1, 0)
        self.usage_count_label = QLabel("0")
        status_layout.addWidget(self.usage_count_label, 1, 1)
        
        status_layout.addWidget(QLabel("Tasa de éxito:"), 2, 0)
        self.success_rate_label = QLabel("N/A")
        status_layout.addWidget(self.success_rate_label, 2, 1)
        
        layout.addWidget(status_group)
        
    def _get_volume_filter_display_name(self, volume_filter: VolumeFilter) -> str:
        """Obtiene el nombre a mostrar para un filtro de volumen."""
        names = {
            VolumeFilter.NO_FILTER: "Sin filtro",
            VolumeFilter.ABOVE_AVERAGE: "Por encima del promedio",
            VolumeFilter.HIGH_VOLUME: "Volumen alto",
            VolumeFilter.CUSTOM_THRESHOLD: "Umbral personalizado"
        }
        return names.get(volume_filter, volume_filter.value)
        
    def _get_market_cap_display_name(self, market_cap_range: MarketCapRange) -> str:
        """Obtiene el nombre a mostrar para un rango de market cap."""
        names = {
            MarketCapRange.MICRO: "Micro Cap (< $300M)",
            MarketCapRange.SMALL: "Small Cap ($300M - $2B)",
            MarketCapRange.MID: "Mid Cap ($2B - $10B)",
            MarketCapRange.LARGE: "Large Cap ($10B - $200B)",
            MarketCapRange.MEGA: "Mega Cap (> $200B)"
        }
        return names.get(market_cap_range, market_cap_range.value)
        
    def _get_trend_display_name(self, trend: TrendDirection) -> str:
        """Obtiene el nombre a mostrar para una dirección de tendencia."""
        names = {
            TrendDirection.BULLISH: "Alcista",
            TrendDirection.BEARISH: "Bajista",
            TrendDirection.SIDEWAYS: "Lateral",
            TrendDirection.ANY: "Cualquiera"
        }
        return names.get(trend, trend.value)
        
    def load_preset(self, preset: ScanPreset):
        """Carga los datos de un preset en el widget."""
        # Información básica
        self.name_edit.setText(preset.name)
        self.description_edit.setPlainText(preset.description)
        
        # Buscar categoría en el combo o agregarla si no existe
        category_index = self.category_combo.findText(preset.category)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        else:
            self.category_combo.addItem(preset.category)
            self.category_combo.setCurrentText(preset.category)
        
        # Estrategias recomendadas
        if preset.recommended_strategies:
            self.strategies_edit.setText(", ".join(preset.recommended_strategies))
        
        # Configuración de escaneo
        config = preset.market_scan_configuration
        
        # Filtros de precio
        if config.min_price_change_24h_percent is not None:
            self.min_price_change_edit.setText(str(config.min_price_change_24h_percent))
        if config.max_price_change_24h_percent is not None:
            self.max_price_change_edit.setText(str(config.max_price_change_24h_percent))
        
        # Filtros de volumen
        if config.volume_filter_type:
            volume_index = self.volume_filter_combo.findData(config.volume_filter_type.value)
            if volume_index >= 0:
                self.volume_filter_combo.setCurrentIndex(volume_index)
        
        if config.min_volume_24h_usd is not None:
            self.min_volume_edit.setText(str(int(config.min_volume_24h_usd)))
        
        # Market cap ranges
        if config.market_cap_ranges:
            for cap_range_value in config.market_cap_ranges:
                if isinstance(cap_range_value, MarketCapRange):
                    range_value = cap_range_value.value
                else:
                    range_value = cap_range_value
                
                if range_value in self.market_cap_checkboxes:
                    self.market_cap_checkboxes[range_value].setChecked(True)
        
        # Análisis técnico
        if config.trend_direction:
            trend_index = self.trend_combo.findData(config.trend_direction.value)
            if trend_index >= 0:
                self.trend_combo.setCurrentIndex(trend_index)
        
        if config.min_rsi is not None:
            self.min_rsi_edit.setText(str(config.min_rsi))
        if config.max_rsi is not None:
            self.max_rsi_edit.setText(str(config.max_rsi))
        
        # Configuración de ejecución
        if config.max_results is not None:
            self.max_results_edit.setText(str(config.max_results))
        if config.scan_interval_minutes is not None:
            self.scan_interval_edit.setText(str(config.scan_interval_minutes))
        
        # Estado
        self.is_system_checkbox.setChecked(preset.is_system_preset)
        self.is_active_checkbox.setChecked(preset.is_active)
        
        # Estadísticas
        if preset.usage_count is not None:
            self.usage_count_label.setText(str(preset.usage_count))
        
        if preset.success_rate is not None:
            self.success_rate_label.setText(f"{preset.success_rate:.1%}")
        else:
            self.success_rate_label.setText("N/A")
    
    def get_preset_data(self) -> Dict:
        """Obtiene los datos del preset desde el widget."""
        # Configuración básica
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        category = self.category_combo.currentText().strip()
        
        # Estrategias recomendadas
        strategies_text = self.strategies_edit.text().strip()
        recommended_strategies = []
        if strategies_text:
            recommended_strategies = [s.strip() for s in strategies_text.split(",") if s.strip()]
        
        # Market cap ranges seleccionados
        market_cap_ranges = []
        for range_value, checkbox in self.market_cap_checkboxes.items():
            if checkbox.isChecked():
                market_cap_ranges.append(range_value)
        
        if not market_cap_ranges:
            market_cap_ranges = [MarketCapRange.ALL.value]
        
        # Configuración de escaneo
        scan_config_data = {
            "id": "",  # Se asigna en el backend
            "name": name,
            "description": description,
            "market_cap_ranges": market_cap_ranges,
            "allowed_quote_currencies": ["USDT", "BUSD", "BTC", "ETH"],
            "is_active": self.is_active_checkbox.isChecked()
        }
        
        # Filtros de precio
        try:
            if self.min_price_change_edit.text():
                scan_config_data["min_price_change_24h_percent"] = float(self.min_price_change_edit.text())
        except ValueError:
            pass
        
        try:
            if self.max_price_change_edit.text():
                scan_config_data["max_price_change_24h_percent"] = float(self.max_price_change_edit.text())
        except ValueError:
            pass
        
        # Filtros de volumen
        volume_filter_value = self.volume_filter_combo.currentData()
        if volume_filter_value and volume_filter_value != VolumeFilter.NO_FILTER.value:
            scan_config_data["volume_filter_type"] = volume_filter_value
        
        try:
            if self.min_volume_edit.text():
                scan_config_data["min_volume_24h_usd"] = float(self.min_volume_edit.text())
        except ValueError:
            pass
        
        # Análisis técnico
        trend_value = self.trend_combo.currentData()
        if trend_value and trend_value != TrendDirection.ANY.value:
            scan_config_data["trend_direction"] = trend_value
        
        try:
            if self.min_rsi_edit.text():
                scan_config_data["min_rsi"] = float(self.min_rsi_edit.text())
        except ValueError:
            pass
        
        try:
            if self.max_rsi_edit.text():
                scan_config_data["max_rsi"] = float(self.max_rsi_edit.text())
        except ValueError:
            pass
        
        # Configuración de ejecución
        try:
            if self.max_results_edit.text():
                scan_config_data["max_results"] = int(self.max_results_edit.text())
        except ValueError:
            scan_config_data["max_results"] = 50
        
        try:
            if self.scan_interval_edit.text():
                scan_config_data["scan_interval_minutes"] = int(self.scan_interval_edit.text())
        except ValueError:
            scan_config_data["scan_interval_minutes"] = 15
        
        return {
            "name": name,
            "description": description,
            "category": category,
            "recommended_strategies": recommended_strategies if recommended_strategies else None,
            "market_scan_configuration": scan_config_data,
            "is_system_preset": self.is_system_checkbox.isChecked(),
            "is_active": self.is_active_checkbox.isChecked()
        }
    
    def clear_form(self):
        """Limpia todos los campos del formulario."""
        self.name_edit.clear()
        self.description_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.strategies_edit.clear()
        
        # Limpiar filtros
        self.min_price_change_edit.clear()
        self.max_price_change_edit.clear()
        self.volume_filter_combo.setCurrentIndex(0)
        self.min_volume_edit.clear()
        
        # Limpiar market cap
        for checkbox in self.market_cap_checkboxes.values():
            checkbox.setChecked(False)
        
        # Limpiar análisis técnico
        self.trend_combo.setCurrentIndex(0)
        self.min_rsi_edit.clear()
        self.max_rsi_edit.clear()
        
        # Limpiar configuración de ejecución
        self.max_results_edit.setText("50")
        self.scan_interval_edit.setText("15")
        
        # Estado
        self.is_system_checkbox.setChecked(False)
        self.is_active_checkbox.setChecked(True)
        
        # Estadísticas
        self.usage_count_label.setText("0")
        self.success_rate_label.setText("N/A")

class PresetManagementDialog(QDialog):
    """Diálogo para gestión CRUD de presets de escaneo de mercado."""
    
    preset_executed = pyqtSignal(list)  # Emitido cuando se ejecuta un preset con resultados
    
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, loop: asyncio.AbstractEventLoop, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.main_window = main_window
        self.loop = loop
        self.presets = []
        self.current_preset = None
        
        self.setup_ui()
        self.connect_signals()
        self.load_presets()
        
    def setup_ui(self):
        """Configura la interfaz de usuario del diálogo."""
        self.setWindowTitle("Gestión de Presets de Escaneo")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter()
        
        # Panel izquierdo - Lista de presets
        left_panel = self._create_presets_list_panel()
        splitter.addWidget(left_panel)
        
        # Panel derecho - Detalles del preset
        right_panel = self._create_preset_details_panel()
        splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Botones del diálogo
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
        
    def _create_presets_list_panel(self) -> QWidget:
        """Crea el panel de lista de presets."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title_label = QLabel("Presets Disponibles")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Sistema", "Usuario", "Activos", "Inactivos"])
        self.filter_combo.currentTextChanged.connect(self._filter_presets)
        filter_layout.addWidget(QLabel("Filtrar:"))
        filter_layout.addWidget(self.filter_combo)
        
        layout.addLayout(filter_layout)
        
        # Tabla de presets
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(5)
        self.presets_table.setHorizontalHeaderLabels([
            "Nombre", "Categoría", "Tipo", "Estado", "Usos"
        ])
        
        # Configurar columnas
        header = self.presets_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        
        self.presets_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.presets_table.setAlternatingRowColors(True)
        self.presets_table.itemSelectionChanged.connect(self._on_preset_selection_changed)
        
        layout.addWidget(self.presets_table)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.new_preset_btn = QPushButton("Nuevo Preset")
        self.new_preset_btn.clicked.connect(self._create_new_preset)
        buttons_layout.addWidget(self.new_preset_btn)
        
        self.duplicate_preset_btn = QPushButton("Duplicar")
        self.duplicate_preset_btn.clicked.connect(self._duplicate_preset)
        self.duplicate_preset_btn.setEnabled(False)
        buttons_layout.addWidget(self.duplicate_preset_btn)
        
        self.delete_preset_btn = QPushButton("Eliminar")
        self.delete_preset_btn.clicked.connect(self._delete_preset)
        self.delete_preset_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_preset_btn)
        
        layout.addLayout(buttons_layout)
        
        # Botón de ejecución
        self.execute_preset_btn = QPushButton("Ejecutar Preset")
        self.execute_preset_btn.clicked.connect(self._execute_preset)
        self.execute_preset_btn.setEnabled(False)
        self.execute_preset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        layout.addWidget(self.execute_preset_btn)
        
        return widget
        
    def _create_preset_details_panel(self) -> QWidget:
        """Crea el panel de detalles del preset."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Título
        title_label = QLabel("Detalles del Preset")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Widget de detalles
        self.details_widget = PresetDetailsWidget()
        layout.addWidget(self.details_widget)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.save_preset_btn = QPushButton("Guardar Cambios")
        self.save_preset_btn.clicked.connect(self._save_preset)
        self.save_preset_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_preset_btn)
        
        self.cancel_changes_btn = QPushButton("Cancelar Cambios")
        self.cancel_changes_btn.clicked.connect(self._cancel_changes)
        self.cancel_changes_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_changes_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Status bar
        self.status_label = QLabel("Selecciona un preset para ver sus detalles")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        return widget
        
    def connect_signals(self):
        """Conecta las señales de los widgets."""
        # Conectar cambios en el formulario para habilitar botones de guardar/cancelar
        self._connect_form_change_signals()
        
    def _connect_form_change_signals(self):
        """Conecta las señales de cambio en el formulario."""
        details = self.details_widget
        
        # Campos de texto
        details.name_edit.textChanged.connect(self._on_form_changed)
        details.description_edit.textChanged.connect(self._on_form_changed)
        details.category_combo.currentTextChanged.connect(self._on_form_changed)
        details.strategies_edit.textChanged.connect(self._on_form_changed)
        
        # Filtros de precio
        details.min_price_change_edit.textChanged.connect(self._on_form_changed)
        details.max_price_change_edit.textChanged.connect(self._on_form_changed)
        
        # Filtros de volumen
        details.volume_filter_combo.currentTextChanged.connect(self._on_form_changed)
        details.min_volume_edit.textChanged.connect(self._on_form_changed)
        
        # Market cap checkboxes
        for checkbox in details.market_cap_checkboxes.values():
            checkbox.toggled.connect(self._on_form_changed)
        
        # Análisis técnico
        details.trend_combo.currentTextChanged.connect(self._on_form_changed)
        details.min_rsi_edit.textChanged.connect(self._on_form_changed)
        details.max_rsi_edit.textChanged.connect(self._on_form_changed)
        
        # Configuración de ejecución
        details.max_results_edit.textChanged.connect(self._on_form_changed)
        details.scan_interval_edit.textChanged.connect(self._on_form_changed)
        
        # Estado
        details.is_active_checkbox.toggled.connect(self._on_form_changed)
        
    def _on_form_changed(self):
        """Maneja cambios en el formulario."""
        if self.current_preset is not None:
            self.save_preset_btn.setEnabled(True)
            self.cancel_changes_btn.setEnabled(True)
            self.status_label.setText("Cambios pendientes - Guarda o cancela los cambios")
            self.status_label.setStyleSheet("color: #FF6B00; font-weight: bold;")
            
    def _submit_api_task(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success: Callable, on_error: Callable):
        """Envía una tarea a la ventana principal para su ejecución."""
        self.main_window.submit_task(coroutine_factory, on_success, on_error)

    def load_presets(self):
        """Carga los presets desde el API usando el task manager."""
        self.status_label.setText("Cargando presets...")
        self.status_label.setStyleSheet("color: #FF6B00; font-style: italic;")
        
        self._submit_api_task(
            lambda client: client.get_scan_presets(),
            self._on_load_presets_success,
            self._on_load_presets_error
        )

    def _on_load_presets_success(self, presets: List[Dict]):
        self.presets = presets
        self._populate_presets_table()
        self.status_label.setText(f"Cargados {len(self.presets)} presets")
        self.status_label.setStyleSheet("color: #2E7D32; font-style: italic;")

    def _on_load_presets_error(self, error_msg: str):
        logger.error(f"Error cargando presets: {error_msg}")
        QMessageBox.warning(self, "Error", f"Error cargando presets: {error_msg}")
        self.status_label.setText("Error cargando presets")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")

    def _populate_presets_table(self):
        """Llena la tabla de presets con los datos cargados."""
        # Aplicar filtro actual
        filtered_presets = self._get_filtered_presets()
        
        self.presets_table.setRowCount(len(filtered_presets))
        
        for row, preset in enumerate(filtered_presets):
            # Nombre
            name_item = QTableWidgetItem(preset.get('name', ''))
            name_item.setData(256, preset.get('id', ''))  # Almacenar ID como data
            self.presets_table.setItem(row, 0, name_item)
            
            # Categoría
            category_item = QTableWidgetItem(preset.get('category', ''))
            self.presets_table.setItem(row, 1, category_item)
            
            # Tipo
            type_text = "Sistema" if preset.get('is_system_preset', False) else "Usuario"
            type_item = QTableWidgetItem(type_text)
            self.presets_table.setItem(row, 2, type_item)
            
            # Estado
            status_text = "Activo" if preset.get('is_active', True) else "Inactivo"
            status_item = QTableWidgetItem(status_text)
            self.presets_table.setItem(row, 3, status_item)
            
            # Usos
            usage_count = preset.get('usage_count', 0)
            usage_item = QTableWidgetItem(str(usage_count))
            self.presets_table.setItem(row, 4, usage_item)
            
    def _get_filtered_presets(self) -> List[Dict]:
        """Obtiene los presets filtrados según el filtro actual."""
        filter_text = self.filter_combo.currentText()
        
        if filter_text == "Todos":
            return self.presets
        elif filter_text == "Sistema":
            return [p for p in self.presets if p.get('is_system_preset', False)]
        elif filter_text == "Usuario":
            return [p for p in self.presets if not p.get('is_system_preset', False)]
        elif filter_text == "Activos":
            return [p for p in self.presets if p.get('is_active', True)]
        elif filter_text == "Inactivos":
            return [p for p in self.presets if not p.get('is_active', True)]
        else:
            return self.presets
            
    def _filter_presets(self):
        """Filtra los presets según el filtro seleccionado."""
        self._populate_presets_table()
        
    def _on_preset_selection_changed(self):
        """Maneja el cambio de selección en la tabla de presets."""
        selected_items = self.presets_table.selectedItems()
        
        if not selected_items:
            self._clear_selection()
            return
            
        # Obtener el preset seleccionado
        row = selected_items[0].row()
        preset_id = self.presets_table.item(row, 0).data(256)
        
        # Buscar el preset en la lista
        selected_preset = None
        for preset in self.presets:
            if preset.get('id') == preset_id:
                selected_preset = preset
                break
        
        if selected_preset:
            self.current_preset = selected_preset
            self._load_preset_to_details(selected_preset)
            
            # Habilitar/deshabilitar botones según el tipo de preset
            is_user_preset = not selected_preset.get('is_system_preset', False)
            self.duplicate_preset_btn.setEnabled(True)
            self.delete_preset_btn.setEnabled(is_user_preset)
            self.execute_preset_btn.setEnabled(selected_preset.get('is_active', True))
            
            # Deshabilitar edición para presets del sistema
            self._set_form_editable(is_user_preset)
            
            self.status_label.setText(f"Preset seleccionado: {selected_preset.get('name', '')}")
            self.status_label.setStyleSheet("color: #1976D2; font-style: italic;")
            
        else:
            self._clear_selection()
            
    def _load_preset_to_details(self, preset_data: Dict):
        """Carga los datos de un preset en el widget de detalles."""
        # Crear un objeto ScanPreset temporal para usar el método load_preset
        from datetime import datetime
        
        # Configuración de escaneo
        scan_config_data = preset_data.get('market_scan_configuration', {})
        scan_config = MarketScanConfiguration(**scan_config_data)
        
        # Crear preset temporal
        temp_preset = ScanPreset(
            id=preset_data.get('id', ''),
            name=preset_data.get('name', ''),
            description=preset_data.get('description', ''),
            category=preset_data.get('category', 'custom'),
            market_scan_configuration=scan_config,
            recommended_strategies=preset_data.get('recommended_strategies'),
            usage_count=preset_data.get('usage_count', 0),
            success_rate=preset_data.get('success_rate'),
            is_system_preset=preset_data.get('is_system_preset', False),
            is_active=preset_data.get('is_active', True),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.details_widget.load_preset(temp_preset)
        
    def _clear_selection(self):
        """Limpia la selección actual."""
        self.current_preset = None
        self.details_widget.clear_form()
        
        # Deshabilitar botones
        self.duplicate_preset_btn.setEnabled(False)
        self.delete_preset_btn.setEnabled(False)
        self.execute_preset_btn.setEnabled(False)
        self.save_preset_btn.setEnabled(False)
        self.cancel_changes_btn.setEnabled(False)
        
        self._set_form_editable(False)
        
        self.status_label.setText("Selecciona un preset para ver sus detalles")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")
        
    def _set_form_editable(self, editable: bool):
        """Habilita o deshabilita la edición del formulario."""
        details = self.details_widget
        
        # Campos básicos
        details.name_edit.setEnabled(editable)
        details.description_edit.setEnabled(editable)
        details.category_combo.setEnabled(editable)
        details.strategies_edit.setEnabled(editable)
        
        # Filtros
        details.min_price_change_edit.setEnabled(editable)
        details.max_price_change_edit.setEnabled(editable)
        details.volume_filter_combo.setEnabled(editable)
        details.min_volume_edit.setEnabled(editable)
        
        # Market cap
        for checkbox in details.market_cap_checkboxes.values():
            checkbox.setEnabled(editable)
        
        # Análisis técnico
        details.trend_combo.setEnabled(editable)
        details.min_rsi_edit.setEnabled(editable)
        details.max_rsi_edit.setEnabled(editable)
        
        # Configuración de ejecución
        details.max_results_edit.setEnabled(editable)
        details.scan_interval_edit.setEnabled(editable)
        
        # Estado (solo is_active es editable)
        details.is_active_checkbox.setEnabled(editable)
        
    def _create_new_preset(self):
        """Crea un nuevo preset."""
        # Limpiar selección actual
        self.presets_table.clearSelection()
        self.current_preset = None
        
        # Limpiar y habilitar formulario
        self.details_widget.clear_form()
        self._set_form_editable(True)
        
        # Habilitar botones de guardar/cancelar
        self.save_preset_btn.setEnabled(True)
        self.cancel_changes_btn.setEnabled(True)
        
        # Deshabilitar otros botones
        self.duplicate_preset_btn.setEnabled(False)
        self.delete_preset_btn.setEnabled(False)
        self.execute_preset_btn.setEnabled(False)
        
        self.status_label.setText("Creando nuevo preset - Completa los campos y guarda")
        self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
        
        # Enfocar el campo de nombre
        self.details_widget.name_edit.setFocus()
        
    def _duplicate_preset(self):
        """Duplica el preset seleccionado."""
        if not self.current_preset:
            return
            
        # Crear copia del preset actual
        preset_data = self.details_widget.get_preset_data()
        preset_data["name"] = f"{preset_data['name']} (Copia)"
        preset_data["is_system_preset"] = False  # Las copias siempre son de usuario
        
        # Limpiar selección y cargar datos de la copia
        self.presets_table.clearSelection()
        self.current_preset = None
        
        self.details_widget.clear_form()
        # Cargar los datos de la copia (simulamos un preset temporal)
        temp_preset = self._create_temp_preset_from_data(preset_data)
        self.details_widget.load_preset(temp_preset)
        
        # Habilitar edición
        self._set_form_editable(True)
        self.save_preset_btn.setEnabled(True)
        self.cancel_changes_btn.setEnabled(True)
        
        # Deshabilitar otros botones
        self.duplicate_preset_btn.setEnabled(False)
        self.delete_preset_btn.setEnabled(False)
        self.execute_preset_btn.setEnabled(False)
        
        self.status_label.setText("Duplicando preset - Modifica y guarda")
        self.status_label.setStyleSheet("color: #FF6B00; font-weight: bold;")
        
        # Enfocar el campo de nombre para que el usuario pueda cambiarlo
        self.details_widget.name_edit.setFocus()
        self.details_widget.name_edit.selectAll()
        
    def _create_temp_preset_from_data(self, data: Dict) -> ScanPreset:
        """Crea un preset temporal desde datos de diccionario."""
        from datetime import datetime # This is fine, as timezone is already imported at the top
        
        # Crear configuración de escaneo
        scan_config = MarketScanConfiguration(**data["market_scan_configuration"])
        
        # Crear preset temporal
        temp_preset = ScanPreset(
            id="temp",
            name=data["name"],
            description=data["description"],
            category=data["category"],
            market_scan_configuration=scan_config,
            recommended_strategies=data.get("recommended_strategies"),
            is_system_preset=data.get("is_system_preset", False),
            is_active=data.get("is_active", True),
            usage_count=0,
            success_rate=None,
            created_at=datetime.now(timezone.utc), # MODIFIED
            updated_at=datetime.now(timezone.utc) # MODIFIED
        )
        
        return temp_preset
        
    def _delete_preset(self):
        """Elimina el preset seleccionado."""
        if not self.current_preset or self.current_preset.get('is_system_preset', False):
            return
            
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar el preset '{self.current_preset.get('name', '')}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes: return

        self.status_label.setText(f"Eliminando preset '{self.current_preset.get('name', '')}'...")
        coroutine_factory = lambda client: client.delete_scan_preset(self.current_preset.get('id'))
        self._submit_api_task(coroutine_factory, self._on_delete_preset_success, self._on_delete_preset_error)

    def _on_delete_preset_success(self, _):
        QMessageBox.information(self, "Preset Eliminado", "El preset ha sido eliminado exitosamente.")
        self.load_presets()
        self._clear_selection()

    def _on_delete_preset_error(self, error_msg: str):
        QMessageBox.warning(self, "Error", f"Error eliminando preset: {error_msg}")
        self.status_label.setText("Error al eliminar preset.")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")

    def _execute_preset(self):
        """Ejecuta el preset seleccionado."""
        if not self.current_preset or not self.current_preset.get('is_active', True):
            return
            
        reply = QMessageBox.question(
            self, "Confirmar Ejecución",
            f"¿Quieres ejecutar el preset '{self.current_preset.get('name', '')}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes: return

        self.execute_preset_btn.setEnabled(False)
        self.execute_preset_btn.setText("Ejecutando...")
        self.status_label.setText("Iniciando ejecución del preset...")
        self.status_label.setStyleSheet("color: #FF6B00; font-weight: bold;")

        coroutine_factory = lambda client: client.execute_preset_scan(self.current_preset.get('id'))
        self._submit_api_task(coroutine_factory, self._on_preset_execution_completed, self._on_preset_execution_error)
        
    def _on_preset_execution_completed(self, results: List):
        """Maneja la finalización exitosa de la ejecución del preset."""
        self.execute_preset_btn.setEnabled(True)
        self.execute_preset_btn.setText("Ejecutar Preset")
        
        if results:
            self.status_label.setText(f"Ejecución completada: {len(results)} resultados encontrados")
            self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
            self.preset_executed.emit(results)
            QMessageBox.information(self, "Ejecución Completada", f"Ejecución completada con {len(results)} resultados.")
        else:
            self.status_label.setText("Ejecución completada: Sin resultados")
            self.status_label.setStyleSheet("color: #FF6B00; font-style: italic;")
            QMessageBox.information(self, "Sin Resultados", "La ejecución no encontró activos que cumplan los criterios.")
            
    def _on_preset_execution_error(self, error_message: str):
        """Maneja errores durante la ejecución del preset."""
        self.execute_preset_btn.setEnabled(True)
        self.execute_preset_btn.setText("Ejecutar Preset")
        self.status_label.setText(f"Error en ejecución: {error_message}")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")
        QMessageBox.warning(self, "Error de Ejecución", f"Error ejecutando el preset:\n\n{error_message}")
        
    def _save_preset(self):
        """Guarda los cambios del preset actual."""
        preset_data = self.details_widget.get_preset_data()
        if not preset_data["name"].strip() or not preset_data["description"].strip():
            QMessageBox.warning(self, "Error", "El nombre y la descripción son obligatorios.")
            return

        if self.current_preset is None:
            # Crear nuevo preset
            coroutine_factory = lambda client: client.create_scan_preset(preset_data)
            on_success = self._on_create_preset_success
        else:
            # Actualizar preset existente
            coroutine_factory = lambda client: client.update_scan_preset(self.current_preset['id'], preset_data)
            on_success = self._on_update_preset_success
        
        self._submit_api_task(coroutine_factory, on_success, self._on_save_preset_error)

    def _on_create_preset_success(self, new_preset: Dict):
        self._on_save_success(f"Preset '{new_preset['name']}' creado exitosamente.")

    def _on_update_preset_success(self, updated_preset: Dict):
        self._on_save_success(f"Preset '{updated_preset['name']}' actualizado exitosamente.")

    def _on_save_success(self, message: str):
        QMessageBox.information(self, "Éxito", message)
        self.load_presets()
        self.save_preset_btn.setEnabled(False)
        self.cancel_changes_btn.setEnabled(False)
        self.status_label.setText("Preset guardado exitosamente")
        self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")

    def _on_save_preset_error(self, error_msg: str):
        logger.error(f"Error guardando preset: {error_msg}")
        QMessageBox.warning(self, "Error", f"Error guardando preset: {error_msg}")
        self.status_label.setText("Error al guardar preset.")
        self.status_label.setStyleSheet("color: #D32F2F; font-weight: bold;")

    def _cancel_changes(self):
        """Cancela los cambios pendientes."""
        if self.current_preset is None:
            # Si estamos creando un nuevo preset, limpiar formulario
            self._clear_selection()
        else:
            # Si estamos editando, recargar datos originales
            self._load_preset_to_details(self.current_preset)
            
        self.save_preset_btn.setEnabled(False)
        self.cancel_changes_btn.setEnabled(False)
        
        self.status_label.setText("Cambios cancelados")
        self.status_label.setStyleSheet("color: #666666; font-style: italic;")

def main():
    """Función principal para testing del diálogo."""
    import sys
    
    # Esta sección es para pruebas y no se usará en la aplicación principal.
    # Se deja por si se necesita para debugging futuro.
    pass

if __name__ == "__main__":
    main()
