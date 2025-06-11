"""Market Filter Widgets.

Este módulo implementa widgets especializados y reutilizables para filtros de mercado,
incluyendo selección de rangos, filtros de volumen, y controles de análisis técnico.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QCheckBox, QGroupBox, QSlider,
    QFrame, QPushButton, QButtonGroup, QRadioButton, QScrollArea
)

from ...ultibot_backend.core.domain_models.user_configuration_models import (
    MarketCapRange, VolumeFilter, TrendDirection
)

logger = logging.getLogger(__name__)

class PriceRangeWidget(QWidget):
    """Widget para seleccionar rangos de precios con validación."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, title: str = "Rango de Precios", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox(self.title)
        group_layout = QFormLayout(group)
        
        # Precio mínimo
        self.min_price_spin = QDoubleSpinBox()
        self.min_price_spin.setRange(0.0, 1000000.0)
        self.min_price_spin.setDecimals(4)
        self.min_price_spin.setSuffix(" USDT")
        self.min_price_spin.setSpecialValueText("Sin límite")
        self.min_price_spin.setValue(0.0)
        group_layout.addRow("Precio Mínimo:", self.min_price_spin)
        
        # Precio máximo
        self.max_price_spin = QDoubleSpinBox()
        self.max_price_spin.setRange(0.0, 1000000.0)
        self.max_price_spin.setDecimals(4)
        self.max_price_spin.setSuffix(" USDT")
        self.max_price_spin.setSpecialValueText("Sin límite")
        self.max_price_spin.setValue(0.0)
        group_layout.addRow("Precio Máximo:", self.max_price_spin)
        
        # Conectar señales
        self.min_price_spin.valueChanged.connect(self._on_value_changed)
        self.max_price_spin.valueChanged.connect(self._on_value_changed)
        
        layout.addWidget(group)
        
    def _on_value_changed(self):
        """Emite señal cuando cambian los valores."""
        self.value_changed.emit()
        
    def get_range(self) -> Tuple[Optional[float], Optional[float]]:
        """Obtiene el rango seleccionado."""
        min_val = self.min_price_spin.value() if self.min_price_spin.value() > 0 else None
        max_val = self.max_price_spin.value() if self.max_price_spin.value() > 0 else None
        return min_val, max_val
        
    def set_range(self, min_val: Optional[float], max_val: Optional[float]):
        """Establece el rango."""
        self.min_price_spin.setValue(min_val if min_val else 0.0)
        self.max_price_spin.setValue(max_val if max_val else 0.0)
        
    def is_valid(self) -> Tuple[bool, str]:
        """Valida el rango."""
        min_val, max_val = self.get_range()
        if min_val and max_val and min_val >= max_val:
            return False, "El precio mínimo debe ser menor al máximo"
        return True, ""

class PercentageChangeWidget(QWidget):
    """Widget para cambios porcentuales con períodos."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, title: str = "Cambio Porcentual", periods: List[str] = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.periods = periods or ["24h", "7d", "30d"]
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox(self.title)
        group_layout = QVBoxLayout(group)
        
        # Selector de período
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Período:"))
        
        self.period_combo = QComboBox()
        for period in self.periods:
            self.period_combo.addItem(period)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        
        group_layout.addLayout(period_layout)
        
        # Rangos de cambio
        range_layout = QFormLayout()
        
        self.min_change_spin = QDoubleSpinBox()
        self.min_change_spin.setRange(-100.0, 1000.0)
        self.min_change_spin.setDecimals(2)
        self.min_change_spin.setSuffix("%")
        self.min_change_spin.setSpecialValueText("Sin límite")
        self.min_change_spin.setValue(-100.0)
        range_layout.addRow("Cambio Mínimo:", self.min_change_spin)
        
        self.max_change_spin = QDoubleSpinBox()
        self.max_change_spin.setRange(-100.0, 1000.0)
        self.max_change_spin.setDecimals(2)
        self.max_change_spin.setSuffix("%")
        self.max_change_spin.setSpecialValueText("Sin límite")
        self.max_change_spin.setValue(1000.0)
        range_layout.addRow("Cambio Máximo:", self.max_change_spin)
        
        group_layout.addLayout(range_layout)
        
        # Conectar señales
        self.period_combo.currentTextChanged.connect(self.value_changed.emit)
        self.min_change_spin.valueChanged.connect(self.value_changed.emit)
        self.max_change_spin.valueChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del widget."""
        period = self.period_combo.currentText()
        min_change = self.min_change_spin.value() if self.min_change_spin.value() > -100.0 else None
        max_change = self.max_change_spin.value() if self.max_change_spin.value() < 1000.0 else None
        
        return {
            'period': period,
            'min_change': min_change,
            'max_change': max_change
        }
        
    def set_config(self, config: Dict[str, Any]):
        """Establece la configuración del widget."""
        period = config.get('period', '24h')
        index = self.period_combo.findText(period)
        if index >= 0:
            self.period_combo.setCurrentIndex(index)
            
        min_change = config.get('min_change')
        max_change = config.get('max_change')
        
        self.min_change_spin.setValue(min_change if min_change is not None else -100.0)
        self.max_change_spin.setValue(max_change if max_change is not None else 1000.0)
        
    def is_valid(self) -> Tuple[bool, str]:
        """Valida la configuración."""
        config = self.get_config()
        min_change = config['min_change']
        max_change = config['max_change']
        
        if min_change and max_change and min_change >= max_change:
            return False, "El cambio mínimo debe ser menor al máximo"
        return True, ""

class VolumeFilterWidget(QWidget):
    """Widget para filtros de volumen avanzados."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Filtros de Volumen")
        group_layout = QVBoxLayout(group)
        
        # Tipo de filtro
        filter_layout = QFormLayout()
        
        self.volume_filter_combo = QComboBox()
        self._populate_volume_filters()
        filter_layout.addRow("Tipo de Filtro:", self.volume_filter_combo)
        
        group_layout.addLayout(filter_layout)
        
        # Volumen mínimo en USD
        volume_layout = QFormLayout()
        
        self.min_volume_spin = QDoubleSpinBox()
        self.min_volume_spin.setRange(0.0, 1000000000.0)  # 1B USD
        self.min_volume_spin.setDecimals(0)
        self.min_volume_spin.setSuffix(" USD")
        self.min_volume_spin.setSpecialValueText("Sin límite")
        self.min_volume_spin.setValue(0.0)
        volume_layout.addRow("Volumen Mínimo 24h:", self.min_volume_spin)
        
        # Multiplicador de volumen promedio
        self.volume_multiplier_spin = QDoubleSpinBox()
        self.volume_multiplier_spin.setRange(0.1, 50.0)
        self.volume_multiplier_spin.setDecimals(1)
        self.volume_multiplier_spin.setSuffix("x")
        self.volume_multiplier_spin.setValue(1.0)
        self.volume_multiplier_spin.setEnabled(False)
        volume_layout.addRow("Multiplicador de Promedio:", self.volume_multiplier_spin)
        
        group_layout.addLayout(volume_layout)
        
        # Conectar señales
        self.volume_filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.min_volume_spin.valueChanged.connect(self.value_changed.emit)
        self.volume_multiplier_spin.valueChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        
    def _populate_volume_filters(self):
        """Pobla el combo con filtros de volumen."""
        filters = {
            VolumeFilter.NO_FILTER: "Sin filtro",
            VolumeFilter.ABOVE_AVERAGE: "Por encima del promedio",
            VolumeFilter.HIGH_VOLUME: "Volumen alto (Top 10%)",
            VolumeFilter.CUSTOM_THRESHOLD: "Umbral personalizado"
        }
        
        for filter_type, display_name in filters.items():
            self.volume_filter_combo.addItem(display_name, filter_type.value)
            
    def _on_filter_changed(self):
        """Maneja cambios en el tipo de filtro."""
        current_filter = self.volume_filter_combo.currentData()
        
        # Habilitar multiplicador solo para ciertos filtros
        enable_multiplier = current_filter in [
            VolumeFilter.ABOVE_AVERAGE.value, 
            VolumeFilter.HIGH_VOLUME.value
        ]
        self.volume_multiplier_spin.setEnabled(enable_multiplier)
        
        self.value_changed.emit()
        
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del filtro."""
        filter_type = self.volume_filter_combo.currentData()
        min_volume = self.min_volume_spin.value() if self.min_volume_spin.value() > 0 else None
        multiplier = self.volume_multiplier_spin.value() if self.volume_multiplier_spin.isEnabled() else None
        
        return {
            'volume_filter_type': filter_type,
            'min_volume_24h_usd': min_volume,
            'min_volume_multiplier': multiplier
        }
        
    def set_config(self, config: Dict[str, Any]):
        """Establece la configuración del filtro."""
        filter_type = config.get('volume_filter_type', VolumeFilter.NO_FILTER.value)
        
        # Buscar el índice del filtro
        for i in range(self.volume_filter_combo.count()):
            if self.volume_filter_combo.itemData(i) == filter_type:
                self.volume_filter_combo.setCurrentIndex(i)
                break
                
        min_volume = config.get('min_volume_24h_usd')
        multiplier = config.get('min_volume_multiplier')
        
        self.min_volume_spin.setValue(min_volume if min_volume else 0.0)
        self.volume_multiplier_spin.setValue(multiplier if multiplier else 1.0)
        
        self._on_filter_changed()  # Actualizar estado de controles

class MarketCapRangeWidget(QWidget):
    """Widget para selección de rangos de market cap."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, allow_multiple: bool = True, parent=None):
        super().__init__(parent)
        self.allow_multiple = allow_multiple
        self.checkboxes = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Rangos de Market Cap")
        group_layout = QVBoxLayout(group)
        
        if self.allow_multiple:
            # Checkboxes para múltiple selección
            for market_cap in MarketCapRange:
                if market_cap == MarketCapRange.ALL:
                    continue  # Omitir "ALL" en selección múltiple
                    
                display_name = self._get_market_cap_display_name(market_cap)
                checkbox = QCheckBox(display_name)
                checkbox.stateChanged.connect(self.value_changed.emit)
                self.checkboxes[market_cap] = checkbox
                group_layout.addWidget(checkbox)
        else:
            # Combo box para selección única
            self.market_cap_combo = QComboBox()
            for market_cap in MarketCapRange:
                display_name = self._get_market_cap_display_name(market_cap)
                self.market_cap_combo.addItem(display_name, market_cap.value)
            self.market_cap_combo.currentTextChanged.connect(self.value_changed.emit)
            group_layout.addWidget(self.market_cap_combo)
            
        # Rango personalizado
        custom_group = QGroupBox("Rango Personalizado (USD)")
        custom_layout = QFormLayout(custom_group)
        
        self.min_market_cap_spin = QDoubleSpinBox()
        self.min_market_cap_spin.setRange(0.0, 10000000000000.0)  # 10T USD
        self.min_market_cap_spin.setDecimals(0)
        self.min_market_cap_spin.setSuffix(" USD")
        self.min_market_cap_spin.setSpecialValueText("Sin límite")
        self.min_market_cap_spin.setValue(0.0)
        custom_layout.addRow("Market Cap Mínimo:", self.min_market_cap_spin)
        
        self.max_market_cap_spin = QDoubleSpinBox()
        self.max_market_cap_spin.setRange(0.0, 10000000000000.0)  # 10T USD
        self.max_market_cap_spin.setDecimals(0)
        self.max_market_cap_spin.setSuffix(" USD")
        self.max_market_cap_spin.setSpecialValueText("Sin límite")
        self.max_market_cap_spin.setValue(0.0)
        custom_layout.addRow("Market Cap Máximo:", self.max_market_cap_spin)
        
        self.min_market_cap_spin.valueChanged.connect(self.value_changed.emit)
        self.max_market_cap_spin.valueChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        layout.addWidget(custom_group)
        
    def _get_market_cap_display_name(self, market_cap: MarketCapRange) -> str:
        """Convierte MarketCapRange a nombre display."""
        names = {
            MarketCapRange.MICRO: "Micro Cap (< $300M)",
            MarketCapRange.SMALL: "Small Cap ($300M - $2B)",
            MarketCapRange.MID: "Mid Cap ($2B - $10B)",
            MarketCapRange.LARGE: "Large Cap ($10B - $200B)",
            MarketCapRange.MEGA: "Mega Cap (> $200B)",
            MarketCapRange.ALL: "Todos los rangos"
        }
        return names.get(market_cap, market_cap.value)
        
    def get_selected_ranges(self) -> List[str]:
        """Obtiene los rangos seleccionados."""
        if self.allow_multiple:
            selected = []
            for market_cap, checkbox in self.checkboxes.items():
                if checkbox.isChecked():
                    selected.append(market_cap.value)
            return selected
        else:
            return [self.market_cap_combo.currentData()]
            
    def set_selected_ranges(self, ranges: List[str]):
        """Establece los rangos seleccionados."""
        if self.allow_multiple:
            for market_cap, checkbox in self.checkboxes.items():
                checkbox.setChecked(market_cap.value in ranges)
        else:
            if ranges:
                for i in range(self.market_cap_combo.count()):
                    if self.market_cap_combo.itemData(i) == ranges[0]:
                        self.market_cap_combo.setCurrentIndex(i)
                        break
                        
    def get_custom_range(self) -> Tuple[Optional[float], Optional[float]]:
        """Obtiene el rango personalizado."""
        min_val = self.min_market_cap_spin.value() if self.min_market_cap_spin.value() > 0 else None
        max_val = self.max_market_cap_spin.value() if self.max_market_cap_spin.value() > 0 else None
        return min_val, max_val
        
    def set_custom_range(self, min_val: Optional[float], max_val: Optional[float]):
        """Establece el rango personalizado."""
        self.min_market_cap_spin.setValue(min_val if min_val else 0.0)
        self.max_market_cap_spin.setValue(max_val if max_val else 0.0)

class TechnicalAnalysisWidget(QWidget):
    """Widget para filtros de análisis técnico."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Análisis Técnico")
        group_layout = QVBoxLayout(group)
        
        # Dirección de tendencia
        trend_layout = QFormLayout()
        
        self.trend_combo = QComboBox()
        self._populate_trend_directions()
        trend_layout.addRow("Dirección de Tendencia:", self.trend_combo)
        
        group_layout.addLayout(trend_layout)
        
        # RSI
        rsi_group = QGroupBox("RSI (Relative Strength Index)")
        rsi_layout = QFormLayout(rsi_group)
        
        self.enable_rsi_checkbox = QCheckBox("Habilitar filtro RSI")
        rsi_layout.addRow(self.enable_rsi_checkbox)
        
        self.min_rsi_spin = QSpinBox()
        self.min_rsi_spin.setRange(0, 100)
        self.min_rsi_spin.setValue(30)
        self.min_rsi_spin.setEnabled(False)
        rsi_layout.addRow("RSI Mínimo:", self.min_rsi_spin)
        
        self.max_rsi_spin = QSpinBox()
        self.max_rsi_spin.setRange(0, 100)
        self.max_rsi_spin.setValue(70)
        self.max_rsi_spin.setEnabled(False)
        rsi_layout.addRow("RSI Máximo:", self.max_rsi_spin)
        
        group_layout.addWidget(rsi_group)
        
        # Score de liquidez
        liquidity_layout = QFormLayout()
        
        self.enable_liquidity_checkbox = QCheckBox("Habilitar filtro de liquidez")
        liquidity_layout.addRow(self.enable_liquidity_checkbox)
        
        self.min_liquidity_spin = QDoubleSpinBox()
        self.min_liquidity_spin.setRange(0.0, 1.0)
        self.min_liquidity_spin.setDecimals(2)
        self.min_liquidity_spin.setSingleStep(0.05)
        self.min_liquidity_spin.setValue(0.5)
        self.min_liquidity_spin.setEnabled(False)
        liquidity_layout.addRow("Score Mínimo de Liquidez:", self.min_liquidity_spin)
        
        group_layout.addLayout(liquidity_layout)
        
        # Conectar señales
        self.trend_combo.currentTextChanged.connect(self.value_changed.emit)
        self.enable_rsi_checkbox.toggled.connect(self._on_rsi_enabled)
        self.min_rsi_spin.valueChanged.connect(self.value_changed.emit)
        self.max_rsi_spin.valueChanged.connect(self.value_changed.emit)
        self.enable_liquidity_checkbox.toggled.connect(self._on_liquidity_enabled)
        self.min_liquidity_spin.valueChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        
    def _populate_trend_directions(self):
        """Pobla el combo con direcciones de tendencia."""
        directions = {
            TrendDirection.ANY: "Cualquier dirección",
            TrendDirection.BULLISH: "Alcista",
            TrendDirection.BEARISH: "Bajista",
            TrendDirection.SIDEWAYS: "Lateral"
        }
        
        for direction, display_name in directions.items():
            self.trend_combo.addItem(display_name, direction.value)
            
    def _on_rsi_enabled(self, enabled: bool):
        """Maneja la habilitación del filtro RSI."""
        self.min_rsi_spin.setEnabled(enabled)
        self.max_rsi_spin.setEnabled(enabled)
        self.value_changed.emit()
        
    def _on_liquidity_enabled(self, enabled: bool):
        """Maneja la habilitación del filtro de liquidez."""
        self.min_liquidity_spin.setEnabled(enabled)
        self.value_changed.emit()
        
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del análisis técnico."""
        config = {
            'trend_direction': self.trend_combo.currentData()
        }
        
        if self.enable_rsi_checkbox.isChecked():
            config['min_rsi'] = self.min_rsi_spin.value()
            config['max_rsi'] = self.max_rsi_spin.value()
            
        if self.enable_liquidity_checkbox.isChecked():
            config['min_liquidity_score'] = self.min_liquidity_spin.value()
            
        return config
        
    def set_config(self, config: Dict[str, Any]):
        """Establece la configuración del análisis técnico."""
        # Dirección de tendencia
        trend = config.get('trend_direction', TrendDirection.ANY.value)
        for i in range(self.trend_combo.count()):
            if self.trend_combo.itemData(i) == trend:
                self.trend_combo.setCurrentIndex(i)
                break
                
        # RSI
        min_rsi = config.get('min_rsi')
        max_rsi = config.get('max_rsi')
        
        if min_rsi is not None and max_rsi is not None:
            self.enable_rsi_checkbox.setChecked(True)
            self.min_rsi_spin.setValue(min_rsi)
            self.max_rsi_spin.setValue(max_rsi)
        else:
            self.enable_rsi_checkbox.setChecked(False)
            
        # Liquidez
        min_liquidity = config.get('min_liquidity_score')
        if min_liquidity is not None:
            self.enable_liquidity_checkbox.setChecked(True)
            self.min_liquidity_spin.setValue(min_liquidity)
        else:
            self.enable_liquidity_checkbox.setChecked(False)
            
    def is_valid(self) -> Tuple[bool, str]:
        """Valida la configuración."""
        if self.enable_rsi_checkbox.isChecked():
            if self.min_rsi_spin.value() >= self.max_rsi_spin.value():
                return False, "El RSI mínimo debe ser menor al máximo"
        return True, ""

class ExclusionFiltersWidget(QWidget):
    """Widget para filtros de exclusión."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Filtros de Exclusión")
        group_layout = QVBoxLayout(group)
        
        # Símbolos excluidos
        symbols_layout = QFormLayout()
        
        self.excluded_symbols_edit = QLineEdit()
        self.excluded_symbols_edit.setPlaceholderText("BTC,ETH,USDT (separados por comas)")
        symbols_layout.addRow("Símbolos Excluidos:", self.excluded_symbols_edit)
        
        group_layout.addLayout(symbols_layout)
        
        # Categorías excluidas
        categories_layout = QFormLayout()
        
        self.excluded_categories_edit = QLineEdit()
        self.excluded_categories_edit.setPlaceholderText("meme,stablecoin,wrapped (separados por comas)")
        categories_layout.addRow("Categorías Excluidas:", self.excluded_categories_edit)
        
        group_layout.addLayout(categories_layout)
        
        # Nuevos listados
        new_listings_layout = QFormLayout()
        
        self.exclude_new_checkbox = QCheckBox("Excluir nuevos listados")
        new_listings_layout.addRow(self.exclude_new_checkbox)
        
        self.new_listings_days_spin = QSpinBox()
        self.new_listings_days_spin.setRange(1, 365)
        self.new_listings_days_spin.setValue(7)
        self.new_listings_days_spin.setSuffix(" días")
        self.new_listings_days_spin.setEnabled(False)
        new_listings_layout.addRow("Días desde listado:", self.new_listings_days_spin)
        
        group_layout.addLayout(new_listings_layout)
        
        # Monedas quote permitidas
        quote_layout = QFormLayout()
        
        self.allowed_quotes_edit = QLineEdit()
        self.allowed_quotes_edit.setText("USDT,BUSD,BTC,ETH")
        self.allowed_quotes_edit.setPlaceholderText("USDT,BUSD,BTC,ETH (separados por comas)")
        quote_layout.addRow("Monedas Quote Permitidas:", self.allowed_quotes_edit)
        
        group_layout.addLayout(quote_layout)
        
        # Conectar señales
        self.excluded_symbols_edit.textChanged.connect(self.value_changed.emit)
        self.excluded_categories_edit.textChanged.connect(self.value_changed.emit)
        self.exclude_new_checkbox.toggled.connect(self._on_new_listings_enabled)
        self.new_listings_days_spin.valueChanged.connect(self.value_changed.emit)
        self.allowed_quotes_edit.textChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        
    def _on_new_listings_enabled(self, enabled: bool):
        """Maneja la habilitación del filtro de nuevos listados."""
        self.new_listings_days_spin.setEnabled(enabled)
        self.value_changed.emit()
        
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de exclusiones."""
        config = {}
        
        # Símbolos excluidos
        symbols_text = self.excluded_symbols_edit.text().strip()
        if symbols_text:
            config['excluded_symbols'] = [s.strip().upper() for s in symbols_text.split(',') if s.strip()]
            
        # Categorías excluidas
        categories_text = self.excluded_categories_edit.text().strip()
        if categories_text:
            config['excluded_categories'] = [c.strip().lower() for c in categories_text.split(',') if c.strip()]
            
        # Nuevos listados
        if self.exclude_new_checkbox.isChecked():
            config['exclude_new_listings_days'] = self.new_listings_days_spin.value()
            
        # Monedas quote
        quotes_text = self.allowed_quotes_edit.text().strip()
        if quotes_text:
            config['allowed_quote_currencies'] = [q.strip().upper() for q in quotes_text.split(',') if q.strip()]
            
        return config
        
    def set_config(self, config: Dict[str, Any]):
        """Establece la configuración de exclusiones."""
        # Símbolos excluidos
        excluded_symbols = config.get('excluded_symbols', [])
        self.excluded_symbols_edit.setText(','.join(excluded_symbols))
        
        # Categorías excluidas
        excluded_categories = config.get('excluded_categories', [])
        self.excluded_categories_edit.setText(','.join(excluded_categories))
        
        # Nuevos listados
        exclude_days = config.get('exclude_new_listings_days')
        if exclude_days:
            self.exclude_new_checkbox.setChecked(True)
            self.new_listings_days_spin.setValue(exclude_days)
        else:
            self.exclude_new_checkbox.setChecked(False)
            
        # Monedas quote
        allowed_quotes = config.get('allowed_quote_currencies', ['USDT', 'BUSD', 'BTC', 'ETH'])
        self.allowed_quotes_edit.setText(','.join(allowed_quotes))

class ConfidenceThresholdWidget(QWidget):
    """Widget reutilizable para umbrales de confianza."""
    
    value_changed = pyqtSignal()
    
    def __init__(self, title: str = "Umbrales de Confianza", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox(self.title)
        group_layout = QFormLayout(group)
        
        # Paper trading threshold
        self.paper_spin = QDoubleSpinBox()
        self.paper_spin.setRange(0.0, 1.0)
        self.paper_spin.setSingleStep(0.05)
        self.paper_spin.setDecimals(2)
        self.paper_spin.setValue(0.5)
        self.paper_spin.setSuffix(" (50%)")
        group_layout.addRow("Paper Trading:", self.paper_spin)
        
        # Real trading threshold
        self.real_spin = QDoubleSpinBox()
        self.real_spin.setRange(0.0, 1.0)
        self.real_spin.setSingleStep(0.05)
        self.real_spin.setDecimals(2)
        self.real_spin.setValue(0.95)
        self.real_spin.setSuffix(" (95%)")
        group_layout.addRow("Real Trading:", self.real_spin)
        
        # Conectar para actualizar sufijos
        self.paper_spin.valueChanged.connect(self._update_paper_suffix)
        self.real_spin.valueChanged.connect(self._update_real_suffix)
        
        # Conectar señales de cambio
        self.paper_spin.valueChanged.connect(self.value_changed.emit)
        self.real_spin.valueChanged.connect(self.value_changed.emit)
        
        layout.addWidget(group)
        
    def _update_paper_suffix(self, value: float):
        """Actualiza el sufijo del paper trading."""
        self.paper_spin.setSuffix(f" ({value*100:.0f}%)")
        
    def _update_real_suffix(self, value: float):
        """Actualiza el sufijo del real trading."""
        self.real_spin.setSuffix(f" ({value*100:.0f}%)")
        
    def get_thresholds(self) -> Dict[str, float]:
        """Obtiene los umbrales configurados."""
        return {
            'paper_trading': self.paper_spin.value(),
            'real_trading': self.real_spin.value()
        }
        
    def set_thresholds(self, thresholds: Dict[str, float]):
        """Establece los umbrales."""
        self.paper_spin.setValue(thresholds.get('paper_trading', 0.5))
        self.real_spin.setValue(thresholds.get('real_trading', 0.95))
        
    def is_valid(self) -> Tuple[bool, str]:
        """Valida los umbrales."""
        if self.real_spin.value() <= self.paper_spin.value():
            return False, "El umbral de trading real debe ser mayor al de paper trading"
        return True, ""
