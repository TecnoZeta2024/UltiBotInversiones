"""
Módulo para el diálogo de configuración de escaneo de mercado.

Este módulo implementa el diálogo principal para configurar filtros avanzados de mercado,
permitiendo a los usuarios crear, editar y ejecutar configuraciones personalizadas de escaneo.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any, Callable, Coroutine
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, 
    QComboBox, QPushButton, QFormLayout, QDialogButtonBox, QMessageBox, 
    QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox, QTabWidget, QWidget,
    QListWidget, QListWidgetItem, QSplitter, QScrollArea, QGridLayout,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon

from ..services.api_client import UltiBotAPIClient, APIError
from ..models import BaseMainWindow
from ...ultibot_backend.core.domain_models.user_configuration_models import (
    MarketScanConfiguration, VolumeFilter, MarketCapRange, TrendDirection
)

logger = logging.getLogger(__name__)

class MarketScanConfigDialog(QDialog):
    """
    Diálogo modal para crear, editar y ejecutar configuraciones de escaneo de mercado.
    
    Permite configurar filtros avanzados como:
    - Filtros de precio y volumen
    - Rangos de market cap
    - Análisis técnico (RSI, tendencias)
    - Exclusiones y filtros de liquidez
    - Ejecutar escaneos en tiempo real
    """
    
    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, loop: asyncio.AbstractEventLoop,
                 scan_config: Optional[Dict[str, Any]] = None,
                 is_edit_mode: bool = False,
                 parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.main_window = main_window
        self.loop = loop
        self.scan_config = scan_config
        self.is_edit_mode = is_edit_mode
        
        self.setWindowTitle("Configuración Avanzada de Escaneo de Mercado")
        self.setMinimumSize(800, 700)
        self.resize(1000, 800)
        
        self._init_ui()
        
        if self.is_edit_mode and self.scan_config:
            self._load_data_for_edit()
            
        # Timer para validación en tiempo real
        self.validation_timer = QTimer()
        self.validation_timer.timeout.connect(self._validate_form_async)
        self.validation_timer.setSingleShot(True)
        
    def _init_ui(self):
        """Inicializa la interfaz de usuario con pestañas organizadas."""
        main_layout = QVBoxLayout(self)
        
        # Información general
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📊 Configuración de Escaneo de Mercado"))
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Pestañas principales
        self.tab_widget = QTabWidget()
        
        # Pestaña 1: Configuración Básica
        self._create_basic_config_tab()
        
        # Pestaña 2: Filtros de Precio y Volumen
        self._create_price_volume_tab()
        
        # Pestaña 3: Market Cap y Liquidez
        self._create_market_cap_tab()
        
        # Pestaña 4: Análisis Técnico
        self._create_technical_analysis_tab()
        
        # Pestaña 5: Exclusiones
        self._create_exclusions_tab()
        
        # Pestaña 6: Vista Previa y Ejecución
        self._create_preview_execution_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Panel de validación
        self._create_validation_panel()
        main_layout.addWidget(self.validation_panel)
        
        # Botones
        self._create_button_panel()
        main_layout.addLayout(self.button_layout)
        
        self.setLayout(main_layout)
        
    def _create_basic_config_tab(self):
        """Crea la pestaña de configuración básica."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Scroll area para contenido largo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Nombre de configuración
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Escaneo Momentum Alcista")
        self.name_edit.textChanged.connect(self._on_config_changed)
        form_layout.addRow("Nombre de Configuración *:", self.name_edit)
        
        # Descripción
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Descripción opcional del escaneo...")
        self.description_edit.setFixedHeight(80)
        self.description_edit.textChanged.connect(self._on_config_changed)
        form_layout.addRow("Descripción:", self.description_edit)
        
        # Configuraciones de ejecución
        execution_group = QGroupBox("Configuración de Ejecución")
        execution_layout = QFormLayout(execution_group)
        
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 500)
        self.max_results_spin.setValue(50)
        self.max_results_spin.setSuffix(" resultados")
        self.max_results_spin.valueChanged.connect(self._on_config_changed)
        execution_layout.addRow("Máximo de Resultados:", self.max_results_spin)
        
        self.scan_interval_spin = QSpinBox()
        self.scan_interval_spin.setRange(1, 1440)  # 1 minuto a 24 horas
        self.scan_interval_spin.setValue(15)
        self.scan_interval_spin.setSuffix(" minutos")
        self.scan_interval_spin.valueChanged.connect(self._on_config_changed)
        execution_layout.addRow("Intervalo de Escaneo:", self.scan_interval_spin)
        
        self.is_active_checkbox = QCheckBox("Configuración activa")
        self.is_active_checkbox.setChecked(True)
        self.is_active_checkbox.toggled.connect(self._on_config_changed)
        execution_layout.addRow(self.is_active_checkbox)
        
        form_layout.addRow(execution_group)
        
        # Monedas base permitidas
        quote_group = QGroupBox("Monedas Base Permitidas")
        quote_layout = QGridLayout(quote_group)
        
        self.quote_currencies = {}
        currencies = ["USDT", "BUSD", "BTC", "ETH", "BNB", "USDC"]
        for i, currency in enumerate(currencies):
            checkbox = QCheckBox(currency)
            checkbox.setChecked(currency in ["USDT", "BUSD", "BTC", "ETH"])
            checkbox.toggled.connect(self._on_config_changed)
            self.quote_currencies[currency] = checkbox
            quote_layout.addWidget(checkbox, i // 3, i % 3)
            
        form_layout.addRow(quote_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "🔧 Configuración Básica")
        
    def _create_price_volume_tab(self):
        """Crea la pestaña de filtros de precio y volumen."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Filtros de precio 24h
        price_24h_group = QGroupBox("Cambio de Precio 24h")
        price_24h_layout = QFormLayout(price_24h_group)
        
        self.min_price_change_24h_spin = QDoubleSpinBox()
        self.min_price_change_24h_spin.setRange(-100, 1000)
        self.min_price_change_24h_spin.setSuffix(" %")
        self.min_price_change_24h_spin.setDecimals(2)
        self.min_price_change_24h_spin.setSpecialValueText("Sin límite")
        self.min_price_change_24h_spin.setValue(self.min_price_change_24h_spin.minimum())
        self.min_price_change_24h_spin.valueChanged.connect(self._on_config_changed)
        price_24h_layout.addRow("Cambio Mínimo 24h:", self.min_price_change_24h_spin)
        
        self.max_price_change_24h_spin = QDoubleSpinBox()
        self.max_price_change_24h_spin.setRange(-100, 1000)
        self.max_price_change_24h_spin.setSuffix(" %")
        self.max_price_change_24h_spin.setDecimals(2)
        self.max_price_change_24h_spin.setSpecialValueText("Sin límite")
        self.max_price_change_24h_spin.setValue(self.max_price_change_24h_spin.minimum())
        self.max_price_change_24h_spin.valueChanged.connect(self._on_config_changed)
        price_24h_layout.addRow("Cambio Máximo 24h:", self.max_price_change_24h_spin)
        
        form_layout.addRow(price_24h_group)
        
        # Filtros de precio 7d
        price_7d_group = QGroupBox("Cambio de Precio 7 días")
        price_7d_layout = QFormLayout(price_7d_group)
        
        self.min_price_change_7d_spin = QDoubleSpinBox()
        self.min_price_change_7d_spin.setRange(-100, 1000)
        self.min_price_change_7d_spin.setSuffix(" %")
        self.min_price_change_7d_spin.setDecimals(2)
        self.min_price_change_7d_spin.setSpecialValueText("Sin límite")
        self.min_price_change_7d_spin.setValue(self.min_price_change_7d_spin.minimum())
        self.min_price_change_7d_spin.valueChanged.connect(self._on_config_changed)
        price_7d_layout.addRow("Cambio Mínimo 7d:", self.min_price_change_7d_spin)
        
        self.max_price_change_7d_spin = QDoubleSpinBox()
        self.max_price_change_7d_spin.setRange(-100, 1000)
        self.max_price_change_7d_spin.setSuffix(" %")
        self.max_price_change_7d_spin.setDecimals(2)
        self.max_price_change_7d_spin.setSpecialValueText("Sin límite")
        self.max_price_change_7d_spin.setValue(self.max_price_change_7d_spin.minimum())
        self.max_price_change_7d_spin.valueChanged.connect(self._on_config_changed)
        price_7d_layout.addRow("Cambio Máximo 7d:", self.max_price_change_7d_spin)
        
        form_layout.addRow(price_7d_group)
        
        # Filtros de volumen
        volume_group = QGroupBox("Filtros de Volumen")
        volume_layout = QFormLayout(volume_group)
        
        self.volume_filter_combo = QComboBox()
        for volume_filter in VolumeFilter:
            self.volume_filter_combo.addItem(self._get_volume_filter_display_name(volume_filter), volume_filter.value)
        self.volume_filter_combo.currentTextChanged.connect(self._on_volume_filter_changed)
        self.volume_filter_combo.currentTextChanged.connect(self._on_config_changed)
        volume_layout.addRow("Tipo de Filtro:", self.volume_filter_combo)
        
        self.min_volume_24h_spin = QDoubleSpinBox()
        self.min_volume_24h_spin.setRange(0, 1e12)
        self.min_volume_24h_spin.setSuffix(" USD")
        self.min_volume_24h_spin.setDecimals(0)
        self.min_volume_24h_spin.setSpecialValueText("Sin límite")
        self.min_volume_24h_spin.setValue(0)
        self.min_volume_24h_spin.valueChanged.connect(self._on_config_changed)
        volume_layout.addRow("Volumen Mínimo 24h:", self.min_volume_24h_spin)
        
        self.min_volume_multiplier_spin = QDoubleSpinBox()
        self.min_volume_multiplier_spin.setRange(0, 10)
        self.min_volume_multiplier_spin.setSuffix("x promedio")
        self.min_volume_multiplier_spin.setDecimals(1)
        self.min_volume_multiplier_spin.setSpecialValueText("Sin límite")
        self.min_volume_multiplier_spin.setValue(0)
        self.min_volume_multiplier_spin.valueChanged.connect(self._on_config_changed)
        volume_layout.addRow("Multiplicador de Volumen:", self.min_volume_multiplier_spin)
        
        form_layout.addRow(volume_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "💹 Precio y Volumen")
        
    def _create_market_cap_tab(self):
        """Crea la pestaña de market cap y liquidez."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Rangos de market cap
        market_cap_group = QGroupBox("Rangos de Market Cap")
        market_cap_layout = QGridLayout(market_cap_group)
        
        self.market_cap_ranges = {}
        for i, cap_range in enumerate(MarketCapRange):
            checkbox = QCheckBox(self._get_market_cap_display_name(cap_range))
            checkbox.setChecked(cap_range == MarketCapRange.ALL)
            checkbox.toggled.connect(self._on_config_changed)
            self.market_cap_ranges[cap_range.value] = checkbox
            market_cap_layout.addWidget(checkbox, i // 2, i % 2)
            
        form_layout.addRow(market_cap_group)
        
        # Market cap personalizado
        custom_market_cap_group = QGroupBox("Market Cap Personalizado")
        custom_layout = QFormLayout(custom_market_cap_group)
        
        self.min_market_cap_spin = QDoubleSpinBox()
        self.min_market_cap_spin.setRange(0, 1e15)
        self.min_market_cap_spin.setSuffix(" USD")
        self.min_market_cap_spin.setDecimals(0)
        self.min_market_cap_spin.setSpecialValueText("Sin límite")
        self.min_market_cap_spin.setValue(0)
        self.min_market_cap_spin.valueChanged.connect(self._on_config_changed)
        custom_layout.addRow("Market Cap Mínimo:", self.min_market_cap_spin)
        
        self.max_market_cap_spin = QDoubleSpinBox()
        self.max_market_cap_spin.setRange(0, 1e15)
        self.max_market_cap_spin.setSuffix(" USD")
        self.max_market_cap_spin.setDecimals(0)
        self.max_market_cap_spin.setSpecialValueText("Sin límite")
        self.max_market_cap_spin.setValue(0)
        self.max_market_cap_spin.valueChanged.connect(self._on_config_changed)
        custom_layout.addRow("Market Cap Máximo:", self.max_market_cap_spin)
        
        form_layout.addRow(custom_market_cap_group)
        
        # Filtros de liquidez
        liquidity_group = QGroupBox("Filtros de Liquidez y Listing")
        liquidity_layout = QFormLayout(liquidity_group)
        
        self.min_liquidity_spin = QDoubleSpinBox()
        self.min_liquidity_spin.setRange(0, 1)
        self.min_liquidity_spin.setDecimals(2)
        self.min_liquidity_spin.setSpecialValueText("Sin límite")
        self.min_liquidity_spin.setValue(0)
        self.min_liquidity_spin.valueChanged.connect(self._on_config_changed)
        liquidity_layout.addRow("Score Mínimo de Liquidez:", self.min_liquidity_spin)
        
        self.exclude_new_listings_spin = QSpinBox()
        self.exclude_new_listings_spin.setRange(0, 365)
        self.exclude_new_listings_spin.setSuffix(" días")
        self.exclude_new_listings_spin.setSpecialValueText("Sin límite")
        self.exclude_new_listings_spin.setValue(0)
        self.exclude_new_listings_spin.valueChanged.connect(self._on_config_changed)
        liquidity_layout.addRow("Excluir Nuevos Listings:", self.exclude_new_listings_spin)
        
        form_layout.addRow(liquidity_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "💰 Market Cap y Liquidez")
        
    def _create_technical_analysis_tab(self):
        """Crea la pestaña de análisis técnico."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Dirección de tendencia
        trend_group = QGroupBox("Dirección de Tendencia")
        trend_layout = QFormLayout(trend_group)
        
        self.trend_direction_combo = QComboBox()
        for trend in TrendDirection:
            self.trend_direction_combo.addItem(self._get_trend_display_name(trend), trend.value)
        self.trend_direction_combo.setCurrentText(self._get_trend_display_name(TrendDirection.ANY))
        self.trend_direction_combo.currentTextChanged.connect(self._on_config_changed)
        trend_layout.addRow("Tendencia Requerida:", self.trend_direction_combo)
        
        form_layout.addRow(trend_group)
        
        # Indicadores RSI
        rsi_group = QGroupBox("Filtros RSI")
        rsi_layout = QFormLayout(rsi_group)
        
        self.min_rsi_spin = QDoubleSpinBox()
        self.min_rsi_spin.setRange(0, 100)
        self.min_rsi_spin.setDecimals(1)
        self.min_rsi_spin.setSpecialValueText("Sin límite")
        self.min_rsi_spin.setValue(0)
        self.min_rsi_spin.valueChanged.connect(self._on_config_changed)
        rsi_layout.addRow("RSI Mínimo:", self.min_rsi_spin)
        
        self.max_rsi_spin = QDoubleSpinBox()
        self.max_rsi_spin.setRange(0, 100)
        self.max_rsi_spin.setDecimals(1)
        self.max_rsi_spin.setSpecialValueText("Sin límite")
        self.max_rsi_spin.setValue(0)
        self.max_rsi_spin.valueChanged.connect(self._on_config_changed)
        rsi_layout.addRow("RSI Máximo:", self.max_rsi_spin)
        
        form_layout.addRow(rsi_group)
        
        # Información adicional
        info_label = QLabel(
            "ℹ️ Los filtros de análisis técnico utilizan datos de indicadores calculados por el sistema.\n"
            "Los valores RSI van de 0 a 100, donde valores altos (>70) indican sobrecompra\n"
            "y valores bajos (<30) indican sobreventa."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        form_layout.addRow(info_label)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "📈 Análisis Técnico")
        
    def _create_exclusions_tab(self):
        """Crea la pestaña de exclusiones."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Símbolos excluidos
        symbols_group = QGroupBox("Símbolos Excluidos")
        symbols_layout = QVBoxLayout(symbols_group)
        
        self.excluded_symbols_edit = QTextEdit()
        self.excluded_symbols_edit.setPlaceholderText("Ingrese símbolos separados por comas:\nBTC, ETH, BNB, DOGE")
        self.excluded_symbols_edit.setFixedHeight(100)
        self.excluded_symbols_edit.textChanged.connect(self._on_config_changed)
        symbols_layout.addWidget(self.excluded_symbols_edit)
        
        symbols_help = QLabel("💡 Tip: Ingrese solo el símbolo base (ej: BTC, no BTC/USDT)")
        symbols_help.setStyleSheet("color: #666; font-size: 11px;")
        symbols_layout.addWidget(symbols_help)
        
        form_layout.addRow(symbols_group)
        
        # Categorías excluidas
        categories_group = QGroupBox("Categorías Excluidas")
        categories_layout = QVBoxLayout(categories_group)
        
        self.excluded_categories_edit = QTextEdit()
        self.excluded_categories_edit.setPlaceholderText(
            "Ingrese categorías separadas por comas:\nmeme, stablecoin, wrapped, fan-token"
        )
        self.excluded_categories_edit.setFixedHeight(100)
        self.excluded_categories_edit.textChanged.connect(self._on_config_changed)
        categories_layout.addWidget(self.excluded_categories_edit)
        
        categories_help = QLabel(
            "💡 Categorías comunes: meme, defi, layer1, layer2, stablecoin, wrapped, "
            "nft, gaming, metaverse, fan-token, exchange"
        )
        categories_help.setWordWrap(True)
        categories_help.setStyleSheet("color: #666; font-size: 11px;")
        categories_layout.addWidget(categories_help)
        
        form_layout.addRow(categories_group)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        self.tab_widget.addTab(tab, "🚫 Exclusiones")
        
    def _create_preview_execution_tab(self):
        """Crea la pestaña de vista previa y ejecución."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Panel de control de ejecución
        control_group = QGroupBox("Control de Ejecución")
        control_layout = QHBoxLayout(control_group)
        
        self.test_scan_btn = QPushButton("🔍 Ejecutar Escaneo de Prueba")
        self.test_scan_btn.clicked.connect(self._execute_test_scan)
        control_layout.addWidget(self.test_scan_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # Vista previa de configuración
        preview_group = QGroupBox("Vista Previa de Configuración")
        preview_layout = QVBoxLayout(preview_group)
        
        self.config_preview = QTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setFixedHeight(200)
        preview_layout.addWidget(self.config_preview)
        
        layout.addWidget(preview_group)
        
        # Resultados del escaneo
        results_group = QGroupBox("Resultados del Escaneo")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Símbolo", "Precio", "Cambio 24h (%)", "Volumen 24h", "Market Cap", "RSI"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "⚡ Ejecución")
        
    def _create_validation_panel(self):
        """Crea el panel de validación."""
        self.validation_panel = QGroupBox("Estado de Validación")
        layout = QVBoxLayout(self.validation_panel)
        
        self.validation_status_label = QLabel("✅ Configuración válida")
        self.validation_status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.validation_status_label)
        
        self.validation_details = QLabel("")
        self.validation_details.setWordWrap(True)
        self.validation_details.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.validation_details)
        
    def _create_button_panel(self):
        """Crea el panel de botones."""
        self.button_layout = QHBoxLayout()
        
        # Botón de validar
        self.validate_btn = QPushButton("✓ Validar Configuración")
        self.validate_btn.clicked.connect(self._validate_form_async)
        self.button_layout.addWidget(self.validate_btn)
        
        self.button_layout.addStretch()
        
        # Botones estándar
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._save_config)
        self.button_box.rejected.connect(self.reject)
        self.button_layout.addWidget(self.button_box)
        
    def _get_volume_filter_display_name(self, volume_filter: VolumeFilter) -> str:
        """Retorna el nombre para mostrar del filtro de volumen."""
        display_names = {
            VolumeFilter.NO_FILTER: "Sin filtro",
            VolumeFilter.ABOVE_AVERAGE: "Por encima del promedio",
            VolumeFilter.HIGH_VOLUME: "Alto volumen",
            VolumeFilter.CUSTOM_THRESHOLD: "Umbral personalizado"
        }
        return display_names.get(volume_filter, volume_filter.value)
        
    def _get_market_cap_display_name(self, market_cap: MarketCapRange) -> str:
        """Retorna el nombre para mostrar del rango de market cap."""
        display_names = {
            MarketCapRange.MICRO: "Micro Cap (< $300M)",
            MarketCapRange.SMALL: "Small Cap ($300M - $2B)",
            MarketCapRange.MID: "Mid Cap ($2B - $10B)",
            MarketCapRange.LARGE: "Large Cap ($10B - $200B)",
            MarketCapRange.MEGA: "Mega Cap (> $200B)",
            MarketCapRange.ALL: "Todos los rangos"
        }
        return display_names.get(market_cap, market_cap.value)
        
    def _get_trend_display_name(self, trend: TrendDirection) -> str:
        """Retorna el nombre para mostrar de la dirección de tendencia."""
        display_names = {
            TrendDirection.BULLISH: "🔺 Alcista",
            TrendDirection.BEARISH: "🔻 Bajista", 
            TrendDirection.SIDEWAYS: "↔️ Lateral",
            TrendDirection.ANY: "🔄 Cualquiera"
        }
        return display_names.get(trend, trend.value)
        
    def _on_config_changed(self):
        """Maneja cambios en la configuración para validación automática."""
        # Usar timer para evitar validaciones excesivas
        self.validation_timer.stop()
        self.validation_timer.start(500)  # Validar después de 500ms de inactividad
        
        # Actualizar vista previa
        self._update_config_preview()
        
    def _on_volume_filter_changed(self):
        """Maneja el cambio en el tipo de filtro de volumen."""
        current_filter = self.volume_filter_combo.currentData()
        
        # Habilitar/deshabilitar controles según el filtro seleccionado
        is_custom = current_filter == VolumeFilter.CUSTOM_THRESHOLD.value
        self.min_volume_24h_spin.setEnabled(is_custom or current_filter != VolumeFilter.NO_FILTER.value)
        self.min_volume_multiplier_spin.setEnabled(current_filter == VolumeFilter.ABOVE_AVERAGE.value)
        
    def _update_config_preview(self):
        """Actualiza la vista previa de la configuración."""
        config = self._get_form_data()
        
        preview_text = f"""
📋 CONFIGURACIÓN DE ESCANEO: {config.get('name', 'Sin nombre')}

📊 CONFIGURACIÓN BÁSICA:
• Máximo de resultados: {config.get('max_results', 50)}
• Intervalo de escaneo: {config.get('scan_interval_minutes', 15)} minutos
• Estado: {'Activa' if config.get('is_active', True) else 'Inactiva'}

💹 FILTROS DE PRECIO:
• Cambio 24h: {config.get('min_price_change_24h_percent', 'Sin límite')}% - {config.get('max_price_change_24h_percent', 'Sin límite')}%
• Cambio 7d: {config.get('min_price_change_7d_percent', 'Sin límite')}% - {config.get('max_price_change_7d_percent', 'Sin límite')}%

📈 VOLUMEN Y MARKET CAP:
• Filtro de volumen: {self.volume_filter_combo.currentText()}
• Volumen mínimo 24h: {config.get('min_volume_24h_usd', 'Sin límite')} USD
• Rangos de market cap: {len([r for r in config.get('market_cap_ranges', []) if r])} seleccionados

🔍 ANÁLISIS TÉCNICO:
• Tendencia: {self.trend_direction_combo.currentText()}
• RSI: {config.get('min_rsi', 'Sin límite')} - {config.get('max_rsi', 'Sin límite')}

🚫 EXCLUSIONES:
• Símbolos excluidos: {len(config.get('excluded_symbols', []))} símbolos
• Categorías excluidas: {len(config.get('excluded_categories', []))} categorías

💱 MONEDAS BASE:
• Permitidas: {', '.join(config.get('allowed_quote_currencies', []))}
        """.strip()
        
        self.config_preview.setPlainText(preview_text)
        
    def _submit_api_task(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], on_success: Callable, on_error: Callable):
        """Envía una tarea a la ventana principal para su ejecución."""
        self.main_window.submit_task(coroutine_factory, on_success, on_error)

    def _validate_form_async(self):
        """Valida el formulario de forma asíncrona."""
        try:
            config_data = self._get_form_data()
            
            # Usar el API client para la validación del backend si es necesario
            # Por ahora, solo validación del lado del cliente
            self._perform_validation(config_data)
            
        except Exception as e:
            logger.error(f"Error en validación: {e}", exc_info=True)
            self._show_validation_error(f"Error en validación: {str(e)}")
            
    def _perform_validation(self, config_data: Dict[str, Any]):
        """Realiza la validación de la configuración."""
        errors = []
        warnings = []
        
        # Validaciones básicas
        if not config_data.get('name', '').strip():
            errors.append("El nombre de la configuración es obligatorio")
            
        # Validaciones de rangos
        min_price_24h = config_data.get('min_price_change_24h_percent')
        max_price_24h = config_data.get('max_price_change_24h_percent')
        if (min_price_24h is not None and max_price_24h is not None and 
            min_price_24h != self.min_price_change_24h_spin.minimum() and 
            max_price_24h != self.max_price_change_24h_spin.minimum() and
            min_price_24h >= max_price_24h):
            errors.append("El cambio mínimo de precio 24h debe ser menor al máximo")
            
        min_rsi = config_data.get('min_rsi')
        max_rsi = config_data.get('max_rsi')
        if (min_rsi is not None and max_rsi is not None and 
            min_rsi != self.min_rsi_spin.minimum() and 
            max_rsi != self.max_rsi_spin.minimum() and
            min_rsi >= max_rsi):
            errors.append("El RSI mínimo debe ser menor al máximo")
            
        # Validaciones de advertencias
        if config_data.get('max_results', 50) > 200:
            warnings.append("Un número alto de resultados puede impactar el rendimiento")
            
        if not config_data.get('allowed_quote_currencies'):
            warnings.append("No se han seleccionado monedas base permitidas")
            
        # Mostrar resultados
        if errors:
            self._show_validation_error(errors)
        elif warnings:
            self._show_validation_warning(warnings)
        else:
            self._show_validation_success()
            
    def _show_validation_success(self):
        """Muestra estado de validación exitosa."""
        self.validation_status_label.setText("✅ Configuración válida")
        self.validation_status_label.setStyleSheet("color: green; font-weight: bold;")
        self.validation_details.setText("Todos los parámetros son válidos. Lista para guardar y ejecutar.")
        
    def _show_validation_warning(self, warnings: List[str]):
        """Muestra advertencias de validación."""
        self.validation_status_label.setText("⚠️ Configuración válida con advertencias")
        self.validation_status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.validation_details.setText("Advertencias: " + "; ".join(warnings))
        
    def _show_validation_error(self, errors):
        """Muestra errores de validación."""
        if isinstance(errors, list):
            error_text = "; ".join(errors)
        else:
            error_text = str(errors)
            
        self.validation_status_label.setText("❌ Configuración inválida")
        self.validation_status_label.setStyleSheet("color: red; font-weight: bold;")
        self.validation_details.setText("Errores: " + error_text)
        
    def _execute_test_scan(self):
        """Ejecuta un escaneo de prueba."""
        config_data = self._get_form_data()
        if not config_data.get('name', '').strip():
            QMessageBox.warning(self, "Configuración Incompleta", 
                              "Complete el nombre de la configuración antes de ejecutar.")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.test_scan_btn.setEnabled(False)
        
        coroutine_factory = lambda client: client.execute_market_scan(config_data)
        self._submit_api_task(coroutine_factory, self._on_scan_completed, self._on_scan_error)
            
    def _on_scan_completed(self, results: List[Dict[str, Any]]):
        """Maneja la finalización exitosa del escaneo."""
        try:
            self._reset_scan_ui()
            
            # Mostrar resultados en la tabla
            self.results_table.setRowCount(len(results))
            
            for row, result in enumerate(results):
                # Símbolo
                symbol_item = QTableWidgetItem(result.get('symbol', 'N/A'))
                self.results_table.setItem(row, 0, symbol_item)
                
                # Precio
                price = result.get('price', 0)
                price_item = QTableWidgetItem(f"${price:.6f}" if price < 1 else f"${price:.2f}")
                self.results_table.setItem(row, 1, price_item)
                
                # Cambio 24h
                change_24h = result.get('price_change_24h_percent', 0)
                change_item = QTableWidgetItem(f"{change_24h:.2f}%")
                change_item.setBackground(Qt.green if change_24h > 0 else Qt.red)
                self.results_table.setItem(row, 2, change_item)
                
                # Volumen 24h
                volume = result.get('volume_24h_usd', 0)
                volume_item = QTableWidgetItem(f"${volume:,.0f}")
                self.results_table.setItem(row, 3, volume_item)
                
                # Market Cap
                market_cap = result.get('market_cap_usd', 0)
                if market_cap > 1e9:
                    cap_text = f"${market_cap/1e9:.1f}B"
                elif market_cap > 1e6:
                    cap_text = f"${market_cap/1e6:.1f}M"
                else:
                    cap_text = f"${market_cap:,.0f}"
                cap_item = QTableWidgetItem(cap_text)
                self.results_table.setItem(row, 4, cap_item)
                
                # RSI
                rsi = result.get('rsi', None)
                rsi_item = QTableWidgetItem(f"{rsi:.1f}" if rsi is not None else "N/A")
                self.results_table.setItem(row, 5, rsi_item)
                
            # Cambiar a la pestaña de resultados
            self.tab_widget.setCurrentIndex(5)  # Pestaña de ejecución
            
            # Mostrar mensaje de éxito
            QMessageBox.information(
                self, "Escaneo Completado", 
                f"Escaneo completado exitosamente. Se encontraron {len(results)} resultados."
            )
            
        except Exception as e:
            logger.error(f"Error al procesar resultados del escaneo: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error al procesar resultados: {str(e)}")
            
    def _on_scan_error(self, error_message: str):
        """Maneja errores en el escaneo."""
        self._reset_scan_ui()
        QMessageBox.critical(self, "Error en Escaneo", f"Error al ejecutar escaneo:\n{error_message}")
        
    def _reset_scan_ui(self):
        """Resetea la UI después del escaneo."""
        self.progress_bar.setVisible(False)
        self.test_scan_btn.setEnabled(True)
            
    def _get_form_data(self) -> Dict[str, Any]:
        """Recoge los datos del formulario y los devuelve como diccionario."""
        # Obtener monedas base seleccionadas
        allowed_quotes = [
            currency for currency, checkbox in self.quote_currencies.items() 
            if checkbox.isChecked()
        ]
        
        # Obtener rangos de market cap seleccionados
        selected_market_cap_ranges = [
            range_key for range_key, checkbox in self.market_cap_ranges.items()
            if checkbox.isChecked()
        ]
        
        # Procesar símbolos excluidos
        excluded_symbols_text = self.excluded_symbols_edit.toPlainText().strip()
        excluded_symbols = [
            symbol.strip().upper() for symbol in excluded_symbols_text.split(',')
            if symbol.strip()
        ] if excluded_symbols_text else []
        
        # Procesar categorías excluidas
        excluded_categories_text = self.excluded_categories_edit.toPlainText().strip()
        excluded_categories = [
            category.strip().lower() for category in excluded_categories_text.split(',')
            if category.strip()
        ] if excluded_categories_text else []
        
        # Construir datos de configuración
        config_data = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip() or None,
            "max_results": self.max_results_spin.value(),
            "scan_interval_minutes": self.scan_interval_spin.value(),
            "is_active": self.is_active_checkbox.isChecked(),
            "allowed_quote_currencies": allowed_quotes,
            "market_cap_ranges": selected_market_cap_ranges,
            "volume_filter_type": self.volume_filter_combo.currentData(),
            "trend_direction": self.trend_direction_combo.currentData(),
        }
        
        # Agregar filtros opcionales solo si están configurados
        def add_optional_float(key: str, spin_widget, special_value: float = None):
            value = spin_widget.value()
            if special_value is None:
                special_value = spin_widget.minimum()
            if value != special_value and value > special_value:
                config_data[key] = value
                
        def add_optional_int(key: str, spin_widget, special_value: int = None):
            value = spin_widget.value()
            if special_value is None:
                special_value = spin_widget.minimum()
            if value != special_value and value > special_value:
                config_data[key] = value
        
        # Filtros de precio
        add_optional_float("min_price_change_24h_percent", self.min_price_change_24h_spin)
        add_optional_float("max_price_change_24h_percent", self.max_price_change_24h_spin)
        add_optional_float("min_price_change_7d_percent", self.min_price_change_7d_spin)
        add_optional_float("max_price_change_7d_percent", self.max_price_change_7d_spin)
        
        # Filtros de volumen
        add_optional_float("min_volume_24h_usd", self.min_volume_24h_spin)
        add_optional_float("min_volume_multiplier", self.min_volume_multiplier_spin)
        
        # Filtros de market cap personalizados
        add_optional_float("min_market_cap_usd", self.min_market_cap_spin)
        add_optional_float("max_market_cap_usd", self.max_market_cap_spin)
        
        # Filtros de liquidez
        add_optional_float("min_liquidity_score", self.min_liquidity_spin)
        add_optional_int("exclude_new_listings_days", self.exclude_new_listings_spin)
        
        # Filtros de RSI
        add_optional_float("min_rsi", self.min_rsi_spin)
        add_optional_float("max_rsi", self.max_rsi_spin)
        
        # Exclusiones
        if excluded_symbols:
            config_data["excluded_symbols"] = excluded_symbols
        if excluded_categories:
            config_data["excluded_categories"] = excluded_categories
            
        return config_data
        
    def _load_data_for_edit(self):
        """Carga los datos para modo edición."""
        if not self.scan_config:
            return
            
        try:
            # Cargar datos básicos
            self.name_edit.setText(self.scan_config.get('name', ''))
            self.description_edit.setPlainText(self.scan_config.get('description', ''))
            self.max_results_spin.setValue(self.scan_config.get('max_results', 50))
            self.scan_interval_spin.setValue(self.scan_config.get('scan_interval_minutes', 15))
            self.is_active_checkbox.setChecked(self.scan_config.get('is_active', True))
            
            # Cargar monedas base
            allowed_quotes = self.scan_config.get('allowed_quote_currencies', [])
            for currency, checkbox in self.quote_currencies.items():
                checkbox.setChecked(currency in allowed_quotes)
                
            # Cargar rangos de market cap
            market_cap_ranges = self.scan_config.get('market_cap_ranges', [])
            for range_key, checkbox in self.market_cap_ranges.items():
                checkbox.setChecked(range_key in market_cap_ranges)
                
            # Cargar filtros de precio
            self.min_price_change_24h_spin.setValue(
                self.scan_config.get('min_price_change_24h_percent', self.min_price_change_24h_spin.minimum())
            )
            self.max_price_change_24h_spin.setValue(
                self.scan_config.get('max_price_change_24h_percent', self.max_price_change_24h_spin.minimum())
            )
            
            # Cargar otros filtros...
            # (Implementar según necesidades)
            
            self._update_config_preview()
            
        except Exception as e:
            logger.error(f"Error al cargar datos para edición: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Error al cargar configuración: {str(e)}")
            
    def _save_config(self):
        """Guarda la configuración."""
        config_data = self._get_form_data()
        if not config_data.get('name', '').strip():
            QMessageBox.warning(self, "Campo Requerido", 
                              "El nombre de la configuración es obligatorio.")
            return
            
        if self.is_edit_mode:
            config_id = self.scan_config.get('id')
            if not config_id:
                QMessageBox.critical(self, "Error", "ID de configuración faltante para edición.")
                return
            coroutine_factory = lambda client: client.update_market_scan_configuration(config_id, config_data)
            on_success = lambda _: QMessageBox.information(self, "Éxito", f"Configuración '{config_data['name']}' actualizada correctamente.")
        else:
            coroutine_factory = lambda client: client.create_market_scan_configuration(config_data)
            on_success = lambda _: QMessageBox.information(self, "Éxito", f"Configuración '{config_data['name']}' creada correctamente.")
        
        self._submit_api_task(coroutine_factory, on_success, self._on_save_config_error)

    def _on_save_config_error(self, error_message: str):
        logger.error(f"Error de API al guardar configuración: {error_message}")
        QMessageBox.critical(self, "Error de API", f"No se pudo guardar la configuración: {error_message}")
        
def main():
    """Función principal para testing del diálogo."""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # Mock API Client para pruebas
    class MockAPIClient:
        async def execute_market_scan(self, config):
            return [
                {
                    'symbol': 'BTC/USDT',
                    'price': 43500.00,
                    'price_change_24h_percent': 2.5,
                    'volume_24h_usd': 15000000000,
                    'market_cap_usd': 850000000000,
                    'rsi': 65.4
                },
                {
                    'symbol': 'ETH/USDT', 
                    'price': 2650.00,
                    'price_change_24h_percent': 1.8,
                    'volume_24h_usd': 8000000000,
                    'market_cap_usd': 320000000000,
                    'rsi': 58.2
                }
            ]
        
        async def create_market_scan_configuration(self, config):
            return {"id": "test-123", **config}
            
        async def update_market_scan_configuration(self, config_id, config):
            return {"id": config_id, **config}
    
    app = QApplication(sys.argv)
    
    mock_client = MockAPIClient()
    # Para pruebas, se necesita un mock de main_window que tenga submit_task
    class MockMainWindow:
        def submit_task(self, coroutine_factory, on_success, on_error):
            async def run_mock_task():
                try:
                    result = await coroutine_factory(mock_client)
                    on_success(result)
                except Exception as e:
                    on_error(str(e))
            asyncio.create_task(run_mock_task())

    mock_main_window = MockMainWindow()
    # Pasar el loop real de qasync si se está ejecutando en un entorno qasync
    # Para este mock, simplemente pasamos None o un loop dummy
    dialog = MarketScanConfigDialog(mock_client, mock_main_window, asyncio.get_event_loop())
    
    if dialog.exec_():
        print("Configuración guardada:", dialog._get_form_data())
    else:
        print("Configuración cancelada")
    
    sys.exit(app.exec_())
