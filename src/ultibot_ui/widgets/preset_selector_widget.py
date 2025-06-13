"""Preset Selector Widgets.

Este módulo implementa widgets especializados para selección de presets y 
visualización de resultados de escaneo de mercado.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone # ADDED timezone

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
    QGroupBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMenu, QAction, QProgressBar, QTextEdit, QSplitter,
    QFrame, QCheckBox, QSpinBox, QLineEdit, QMessageBox
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import QSortFilterProxyModel, QAbstractTableModel

from ..services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)


class ScanExecutionWorker(QThread):
    """Worker thread para ejecutar escaneos de mercado de forma asíncrona."""
    
    scan_completed = pyqtSignal(list)  # Lista de resultados
    scan_error = pyqtSignal(str)  # Mensaje de error
    scan_progress = pyqtSignal(str)  # Mensaje de progreso
    
    def __init__(self, api_client: UltiBotAPIClient, preset_id: Optional[str] = None, 
                 scan_config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.api_client = api_client
        self.preset_id = preset_id
        self.scan_config = scan_config
        
    def run(self):
        """Ejecuta el escaneo en el hilo worker."""
        import asyncio
        
        try:
            # Crear nuevo loop para el hilo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if self.preset_id:
                self.scan_progress.emit(f"Ejecutando preset '{self.preset_id}'...")
                logger.info(f"Ejecutando escaneo con preset: {self.preset_id}")
                result = loop.run_until_complete(
                    self.api_client.execute_preset_scan(self.preset_id)
                )
            elif self.scan_config:
                self.scan_progress.emit("Ejecutando configuración personalizada...")
                logger.info("Ejecutando escaneo con configuración personalizada")
                result = loop.run_until_complete(
                    self.api_client.execute_market_scan(self.scan_config)
                )
            else:
                raise ValueError("Se requiere preset_id o scan_config")
                
            logger.info(f"Escaneo completado, {len(result)} resultados encontrados")
            self.scan_completed.emit(result)
            
        except APIError as e:
            error_msg = f"Error de API durante escaneo: {e}"
            logger.error(error_msg)
            self.scan_error.emit(str(e))
        except Exception as e:
            error_msg = f"Error inesperado durante escaneo: {e}"
            logger.error(error_msg, exc_info=True)
            self.scan_error.emit(error_msg)
        finally:
            loop.close()


class PresetSelectorWidget(QWidget):
    """Widget para seleccionar presets de escaneo de mercado."""
    
    preset_selected = pyqtSignal(dict)  # Preset seleccionado
    preset_executed = pyqtSignal(list)  # Resultados del escaneo
    
    def __init__(self, api_client: Optional[UltiBotAPIClient] = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client or self._create_mock_client()
        self.presets = []
        self.current_preset = None
        self.scan_worker = None
        self.setup_ui()
        self.load_presets()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Group box principal
        group = QGroupBox("Selector de Presets de Escaneo")
        group_layout = QVBoxLayout(group)
        
        # Selector de preset
        selector_layout = QFormLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(300)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        selector_layout.addRow("Preset:", self.preset_combo)
        
        # Categoría del preset
        self.category_label = QLabel("N/A")
        self.category_label.setStyleSheet("color: #666; font-style: italic;")
        selector_layout.addRow("Categoría:", self.category_label)
        
        group_layout.addLayout(selector_layout)
        
        # Descripción del preset
        desc_group = QGroupBox("Descripción")
        desc_layout = QVBoxLayout(desc_group)
        
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(80)
        self.description_text.setReadOnly(True)
        self.description_text.setPlaceholderText("Selecciona un preset para ver su descripción...")
        desc_layout.addWidget(self.description_text)
        
        group_layout.addWidget(desc_group)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("Ejecutar Escaneo")
        self.execute_btn.setEnabled(False)
        self.execute_btn.clicked.connect(self._execute_preset)
        buttons_layout.addWidget(self.execute_btn)
        
        self.refresh_btn = QPushButton("Actualizar Presets")
        self.refresh_btn.clicked.connect(self.load_presets)
        buttons_layout.addWidget(self.refresh_btn)
        
        buttons_layout.addStretch()
        
        self.details_btn = QPushButton("Ver Detalles")
        self.details_btn.setEnabled(False)
        self.details_btn.clicked.connect(self._show_preset_details)
        buttons_layout.addWidget(self.details_btn)
        
        group_layout.addLayout(buttons_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        # Label de estado
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(self.status_label)
        
        layout.addWidget(group)
        
    def load_presets(self):
        """Carga los presets disponibles desde la API."""
        if not self.api_client:
            return
            
        self.status_label.setText("Cargando presets...")
        self.refresh_btn.setEnabled(False)
        
        # Usar QTimer para ejecutar la carga async
        QTimer.singleShot(100, self._load_presets_async)
        
    def _load_presets_async(self):
        """Carga presets de forma asíncrona."""
        try:
            import asyncio
            
            # Crear loop para la carga
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.presets = loop.run_until_complete(
                self.api_client.get_scan_presets(include_system=True)
            )
            
            self._populate_preset_combo()
            self.status_label.setText(f"{len(self.presets)} presets cargados")
            
        except Exception as e:
            logger.error(f"Error cargando presets: {e}")
            self.status_label.setText("Error cargando presets")
        finally:
            self.refresh_btn.setEnabled(True)
            
    def _populate_preset_combo(self):
        """Pobla el combo con los presets cargados."""
        self.preset_combo.clear()
        self.preset_combo.addItem("Seleccionar preset...", None)
        
        # Agrupar por categoría
        system_presets = []
        user_presets = []
        
        for preset in self.presets:
            if preset.get("is_system", False):
                system_presets.append(preset)
            else:
                user_presets.append(preset)
                
        # Agregar presets del sistema
        if system_presets:
            for preset in system_presets:
                name = f"[Sistema] {preset['name']}"
                self.preset_combo.addItem(name, preset)
                
        # Separador si hay ambos tipos
        if system_presets and user_presets:
            self.preset_combo.insertSeparator(self.preset_combo.count())
            
        # Agregar presets del usuario
        for preset in user_presets:
            name = f"[Usuario] {preset['name']}"
            self.preset_combo.addItem(name, preset)
            
    def _on_preset_changed(self, index: int):
        """Maneja el cambio de preset seleccionado."""
        preset = self.preset_combo.itemData(index)
        self.current_preset = preset
        
        if preset:
            # Actualizar información del preset
            self.category_label.setText(preset.get("category", "N/A"))
            self.description_text.setPlainText(preset.get("description", "Sin descripción"))
            
            # Habilitar botones
            self.execute_btn.setEnabled(True)
            self.details_btn.setEnabled(True)
            
            # Emitir señal
            self.preset_selected.emit(preset)
            
        else:
            # Limpiar información
            self.category_label.setText("N/A")
            self.description_text.clear()
            
            # Deshabilitar botones
            self.execute_btn.setEnabled(False)
            self.details_btn.setEnabled(False)
            
    def _execute_preset(self):
        """Ejecuta el preset seleccionado."""
        if not self.current_preset:
            return
            
        preset_id = self.current_preset.get("id")
        if not preset_id:
            QMessageBox.warning(self, "Error", "ID de preset no válido")
            return
            
        # Iniciar worker thread
        self.scan_worker = ScanExecutionWorker(self.api_client, preset_id=preset_id)
        self.scan_worker.scan_completed.connect(self._on_scan_completed)
        self.scan_worker.scan_error.connect(self._on_scan_error)
        self.scan_worker.scan_progress.connect(self._on_scan_progress)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.execute_btn.setEnabled(False)
        
        self.scan_worker.start()
        
    def _on_scan_completed(self, results: List[Dict[str, Any]]):
        """Maneja la completación del escaneo."""
        self.progress_bar.setVisible(False)
        self.execute_btn.setEnabled(True)
        
        self.status_label.setText(f"Escaneo completado: {len(results)} resultados")
        self.preset_executed.emit(results)
        
    def _on_scan_error(self, error_msg: str):
        """Maneja errores durante el escaneo."""
        self.progress_bar.setVisible(False)
        self.execute_btn.setEnabled(True)
        
        self.status_label.setText("Error en escaneo")
        QMessageBox.critical(self, "Error de Escaneo", error_msg)
        
    def _on_scan_progress(self, message: str):
        """Actualiza el progreso del escaneo."""
        self.status_label.setText(message)
        
    def _show_preset_details(self):
        """Muestra los detalles del preset seleccionado."""
        if not self.current_preset:
            return
            
        # Crear diálogo simple para mostrar detalles
        details = []
        details.append(f"Nombre: {self.current_preset.get('name', 'N/A')}")
        details.append(f"Categoría: {self.current_preset.get('category', 'N/A')}")
        details.append(f"Tipo: {'Sistema' if self.current_preset.get('is_system') else 'Usuario'}")
        details.append(f"Descripción: {self.current_preset.get('description', 'N/A')}")
        
        # Mostrar configuración si está disponible
        config = self.current_preset.get('configuration', {})
        if config:
            details.append("\nConfiguración:")
            for key, value in config.items():
                details.append(f"  {key}: {value}")
                
        QMessageBox.information(
            self, 
            f"Detalles del Preset: {self.current_preset['name']}", 
            "\n".join(details)
        )
        
    def get_selected_preset(self) -> Optional[Dict[str, Any]]:
        """Obtiene el preset actualmente seleccionado."""
        return self.current_preset
        
    def set_selected_preset(self, preset_id: str):
        """Selecciona un preset por ID."""
        for i in range(self.preset_combo.count()):
            preset = self.preset_combo.itemData(i)
            if preset and preset.get("id") == preset_id:
                self.preset_combo.setCurrentIndex(i)
                break
                
    def _create_mock_client(self) -> UltiBotAPIClient:
        """Crea un cliente mock para testing independiente."""
        
        class MockAPIClient:
            """Cliente mock para testing."""
            
            async def get_scan_presets(self, include_system: bool = True) -> List[Dict[str, Any]]:
                """Mock de get_scan_presets."""
                presets = [
                    {
                        "id": "momentum_breakout",
                        "name": "Momentum Breakout",
                        "category": "Análisis Técnico",
                        "description": "Busca activos con rupturas de momentum y volumen alto. Ideal para capturas rápidas de tendencias alcistas.",
                        "is_system": True,
                        "configuration": {
                            "min_price_change_24h_percent": 5.0,
                            "min_volume_multiplier": 2.0,
                            "trend_direction": "BULLISH",
                            "min_rsi": 50,
                            "max_rsi": 80
                        }
                    },
                    {
                        "id": "value_discovery",
                        "name": "Value Discovery",
                        "category": "Análisis Fundamental",
                        "description": "Identifica activos con potencial de valor subestimado basado en métricas fundamentales y market cap.",
                        "is_system": True,
                        "configuration": {
                            "max_price_change_24h_percent": -2.0,
                            "market_cap_ranges": ["SMALL_CAP", "MID_CAP"],
                            "min_liquidity_score": 0.6,
                            "trend_direction": "ANY"
                        }
                    },
                    {
                        "id": "user_scalping",
                        "name": "Scalping Personalizado",
                        "category": "Trading Rápido",
                        "description": "Configuración personalizada para scalping con alta frecuencia y profit rápido.",
                        "is_system": False,
                        "configuration": {
                            "min_price_change_1h_percent": 1.0,
                            "min_volume_24h_usd": 1000000,
                            "max_rsi": 70,
                            "allowed_quote_currencies": ["USDT"]
                        }
                    }
                ]
                
                if include_system:
                    return presets
                else:
                    return [p for p in presets if not p.get("is_system", False)]
                    
            async def execute_preset_scan(self, preset_id: str) -> List[Dict[str, Any]]:
                """Mock de execute_preset_scan."""
                # Simular resultados según el preset
                if preset_id == "momentum_breakout":
                    return [
                        {
                            "symbol": "SOLUSDT",
                            "price": 98.45,
                            "price_change_24h_percent": 8.2,
                            "volume_24h_usd": 450000000,
                            "market_cap_usd": 45000000000,
                            "rsi": 65.3,
                            "trend_direction": "BULLISH",
                            "liquidity_score": 0.85,
                            "confidence_score": 0.78
                        },
                        {
                            "symbol": "AVAXUSDT",
                            "price": 34.67,
                            "price_change_24h_percent": 12.5,
                            "volume_24h_usd": 320000000,
                            "market_cap_usd": 14000000000,
                            "rsi": 72.1,
                            "trend_direction": "BULLISH",
                            "liquidity_score": 0.91,
                            "confidence_score": 0.82
                        }
                    ]
                elif preset_id == "value_discovery":
                    return [
                        {
                            "symbol": "ADAUSDT",
                            "price": 0.456,
                            "price_change_24h_percent": -1.8,
                            "volume_24h_usd": 180000000,
                            "market_cap_usd": 16000000000,
                            "rsi": 45.2,
                            "trend_direction": "SIDEWAYS",
                            "liquidity_score": 0.72,
                            "confidence_score": 0.65
                        }
                    ]
                else:
                    return [
                        {
                            "symbol": "BTCUSDT",
                            "price": 42150.00,
                            "price_change_24h_percent": 2.3,
                            "volume_24h_usd": 25000000000,
                            "market_cap_usd": 825000000000,
                            "rsi": 58.7,
                            "trend_direction": "BULLISH",
                            "liquidity_score": 0.95,
                            "confidence_score": 0.88
                        }
                    ]
        
        return MockAPIClient()


class ScanResultsWidget(QWidget):
    """Widget para mostrar resultados de escaneo de mercado."""
    
    symbol_selected = pyqtSignal(str)  # Símbolo seleccionado
    result_action_requested = pyqtSignal(str, dict)  # Acción solicitada (symbol, data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Header con información
        header_layout = QHBoxLayout()
        
        self.results_label = QLabel("Sin resultados")
        self.results_label.setFont(QFont("Arial", 10, QFont.Bold))
        header_layout.addWidget(self.results_label)
        
        header_layout.addStretch()
        
        # Filtro rápido
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filtrar símbolos...")
        self.filter_edit.setMaximumWidth(150)
        self.filter_edit.textChanged.connect(self._filter_results)
        header_layout.addWidget(QLabel("Filtro:"))
        header_layout.addWidget(self.filter_edit)
        
        layout.addLayout(header_layout)
        
        # Tabla de resultados
        self.results_table = QTableWidget()
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setSortingEnabled(True)
        
        # Configurar columnas
        self._setup_table_columns()
        
        # Conectar señales
        self.results_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.results_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Menú contextual
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.results_table)
        
        # Panel de acciones rápidas
        actions_group = QGroupBox("Acciones Rápidas")
        actions_layout = QHBoxLayout(actions_group)
        
        self.view_chart_btn = QPushButton("Ver Gráfico")
        self.view_chart_btn.setEnabled(False)
        self.view_chart_btn.clicked.connect(lambda: self._emit_action("view_chart"))
        actions_layout.addWidget(self.view_chart_btn)
        
        self.add_watchlist_btn = QPushButton("+ Watchlist")
        self.add_watchlist_btn.setEnabled(False)
        self.add_watchlist_btn.clicked.connect(lambda: self._emit_action("add_watchlist"))
        actions_layout.addWidget(self.add_watchlist_btn)
        
        self.create_strategy_btn = QPushButton("Crear Estrategia")
        self.create_strategy_btn.setEnabled(False)
        self.create_strategy_btn.clicked.connect(lambda: self._emit_action("create_strategy"))
        actions_layout.addWidget(self.create_strategy_btn)
        
        actions_layout.addStretch()
        
        self.export_btn = QPushButton("Exportar Resultados")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_results)
        actions_layout.addWidget(self.export_btn)
        
        layout.addWidget(actions_group)
        
    def _setup_table_columns(self):
        """Configura las columnas de la tabla."""
        headers = [
            "Símbolo", "Precio", "Cambio 24h (%)", "Volumen 24h", 
            "Market Cap", "RSI", "Tendencia", "Liquidez", "Confianza"
        ]
        
        self.results_table.setColumnCount(len(headers))
        self.results_table.setHorizontalHeaderLabels(headers)
        
        # Configurar ancho de columnas
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 100)  # Símbolo
        header.resizeSection(1, 80)   # Precio
        header.resizeSection(2, 100)  # Cambio 24h
        header.resizeSection(3, 120)  # Volumen
        header.resizeSection(4, 120)  # Market Cap
        header.resizeSection(5, 60)   # RSI
        header.resizeSection(6, 80)   # Tendencia
        header.resizeSection(7, 70)   # Liquidez
        header.resizeSection(8, 80)   # Confianza
        
    def show_results(self, results: List[Dict[str, Any]]):
        """Muestra los resultados del escaneo."""
        self.results = results
        self._populate_table()
        
        # Actualizar label
        count = len(results)
        self.results_label.setText(f"{count} resultado{'s' if count != 1 else ''} encontrado{'s' if count != 1 else ''}")
        
        # Habilitar botón de exportar si hay resultados
        self.export_btn.setEnabled(count > 0)
        
    def _populate_table(self):
        """Pobla la tabla con los resultados."""
        filtered_results = self._get_filtered_results()
        
        self.results_table.setRowCount(len(filtered_results))
        
        for row, result in enumerate(filtered_results):
            # Símbolo
            symbol_item = QTableWidgetItem(result.get("symbol", "N/A"))
            symbol_item.setFont(QFont("Arial", 9, QFont.Bold))
            self.results_table.setItem(row, 0, symbol_item)
            
            # Precio
            price = result.get("price", 0)
            price_item = QTableWidgetItem(f"${price:.4f}" if price < 1 else f"${price:.2f}")
            self.results_table.setItem(row, 1, price_item)
            
            # Cambio 24h
            change = result.get("price_change_24h_percent", 0)
            change_item = QTableWidgetItem(f"{change:+.2f}%")
            if change > 0:
                change_item.setForeground(QColor("#00aa00"))
            elif change < 0:
                change_item.setForeground(QColor("#cc0000"))
            self.results_table.setItem(row, 2, change_item)
            
            # Volumen 24h
            volume = result.get("volume_24h_usd", 0)
            volume_str = self._format_large_number(volume)
            self.results_table.setItem(row, 3, QTableWidgetItem(volume_str))
            
            # Market Cap
            market_cap = result.get("market_cap_usd", 0)
            market_cap_str = self._format_large_number(market_cap)
            self.results_table.setItem(row, 4, QTableWidgetItem(market_cap_str))
            
            # RSI
            rsi = result.get("rsi", 0)
            rsi_item = QTableWidgetItem(f"{rsi:.1f}" if rsi else "N/A")
            self.results_table.setItem(row, 5, rsi_item)
            
            # Tendencia
            trend = result.get("trend_direction", "N/A")
            trend_display = {"BULLISH": "📈", "BEARISH": "📉", "SIDEWAYS": "➡️"}.get(trend, trend)
            self.results_table.setItem(row, 6, QTableWidgetItem(trend_display))
            
            # Liquidez
            liquidity = result.get("liquidity_score", 0)
            liquidity_item = QTableWidgetItem(f"{liquidity:.2f}" if liquidity else "N/A")
            self.results_table.setItem(row, 7, liquidity_item)
            
            # Confianza
            confidence = result.get("confidence_score", 0)
            confidence_item = QTableWidgetItem(f"{confidence:.1%}" if confidence else "N/A")
            
            # Colorear según confianza
            if confidence >= 0.8:
                confidence_item.setForeground(QColor("#00aa00"))
            elif confidence >= 0.6:
                confidence_item.setForeground(QColor("#ff8800"))
            else:
                confidence_item.setForeground(QColor("#cc0000"))
                
            self.results_table.setItem(row, 8, confidence_item)
            
    def _format_large_number(self, number: float) -> str:
        """Formatea números grandes de forma legible."""
        if number >= 1_000_000_000:
            return f"${number / 1_000_000_000:.1f}B"
        elif number >= 1_000_000:
            return f"${number / 1_000_000:.1f}M"
        elif number >= 1_000:
            return f"${number / 1_000:.1f}K"
        else:
            return f"${number:.2f}"
            
    def _get_filtered_results(self) -> List[Dict[str, Any]]:
        """Obtiene resultados filtrados según el texto de filtro."""
        filter_text = self.filter_edit.text().strip().upper()
        
        if not filter_text:
            return self.results
            
        return [
            result for result in self.results
            if filter_text in result.get("symbol", "").upper()
        ]
        
    def _filter_results(self):
        """Filtra los resultados según el texto ingresado."""
        self._populate_table()
        
    def _on_selection_changed(self):
        """Maneja cambios en la selección de la tabla."""
        selected_items = self.results_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        # Habilitar/deshabilitar botones
        self.view_chart_btn.setEnabled(has_selection)
        self.add_watchlist_btn.setEnabled(has_selection)
        self.create_strategy_btn.setEnabled(has_selection)
        
        # Emitir señal de símbolo seleccionado
        if has_selection:
            row = selected_items[0].row()
            symbol_item = self.results_table.item(row, 0)
            if symbol_item:
                symbol = symbol_item.text()
                self.symbol_selected.emit(symbol)
                
    def _on_cell_double_clicked(self, row: int, column: int):
        """Maneja doble click en celda."""
        symbol_item = self.results_table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            result_data = self._get_result_data_for_symbol(symbol)
            self.result_action_requested.emit("view_details", result_data)
            
    def _get_result_data_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """Obtiene los datos completos para un símbolo."""
        for result in self.results:
            if result.get("symbol") == symbol:
                return result
        return {}
        
    def _show_context_menu(self, position):
        """Muestra menú contextual."""
        if not self.results_table.itemAt(position):
            return
            
        menu = QMenu(self)
        
        view_chart_action = QAction("Ver Gráfico", self)
        view_chart_action.triggered.connect(lambda: self._emit_action("view_chart"))
        menu.addAction(view_chart_action)
        
        add_watchlist_action = QAction("Agregar a Watchlist", self)
        add_watchlist_action.triggered.connect(lambda: self._emit_action("add_watchlist"))
        menu.addAction(add_watchlist_action)
        
        menu.addSeparator()
        
        create_strategy_action = QAction("Crear Estrategia", self)
        create_strategy_action.triggered.connect(lambda: self._emit_action("create_strategy"))
        menu.addAction(create_strategy_action)
        
        copy_symbol_action = QAction("Copiar Símbolo", self)
        copy_symbol_action.triggered.connect(self._copy_symbol)
        menu.addAction(copy_symbol_action)
        
        menu.exec_(self.results_table.mapToGlobal(position))
        
    def _emit_action(self, action: str):
        """Emite acción para el resultado seleccionado."""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        symbol_item = self.results_table.item(row, 0)
        if symbol_item:
            symbol = symbol_item.text()
            result_data = self._get_result_data_for_symbol(symbol)
            self.result_action_requested.emit(action, result_data)
            
    def _copy_symbol(self):
        """Copia el símbolo seleccionado al portapapeles."""
        selected_items = self.results_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            symbol_item = self.results_table.item(row, 0)
            if symbol_item:
                from PyQt5.QtWidgets import QApplication
                QApplication.clipboard().setText(symbol_item.text())
                
    def _export_results(self):
        """Exporta los resultados a CSV."""
        if not self.results:
            return
            
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Resultados",
            f"scan_results_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv", # MODIFIED
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    if not self.results:
                        return
                        
                    fieldnames = self.results[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for result in self.results:
                        writer.writerow(result)
                        
                QMessageBox.information(self, "Exportación Exitosa", f"Resultados exportados a:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"Error al exportar: {e}")
                
    def get_selected_symbol(self) -> Optional[str]:
        """Obtiene el símbolo actualmente seleccionado."""
        selected_items = self.results_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            symbol_item = self.results_table.item(row, 0)
            return symbol_item.text() if symbol_item else None
        return None
        
    def clear_results(self):
        """Limpia los resultados mostrados."""
        self.results = []
        self.results_table.setRowCount(0)
        self.results_label.setText("Sin resultados")
        self.export_btn.setEnabled(False)
        
        # Deshabilitar botones de acción
        self.view_chart_btn.setEnabled(False)
        self.add_watchlist_btn.setEnabled(False)
        self.create_strategy_btn.setEnabled(False)


class PresetQuickActionWidget(QWidget):
    """Widget de acciones rápidas para presets."""
    
    action_requested = pyqtSignal(str, dict)  # Acción solicitada (action, preset_data)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_preset = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Grupo de botones de acción
        self.execute_btn = QPushButton("⚡ Ejecutar")
        self.execute_btn.setToolTip("Ejecutar escaneo con este preset")
        self.execute_btn.setEnabled(False)
        self.execute_btn.clicked.connect(lambda: self._emit_action("execute"))
        layout.addWidget(self.execute_btn)
        
        self.edit_btn = QPushButton("✏️ Editar")
        self.edit_btn.setToolTip("Editar configuración del preset")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(lambda: self._emit_action("edit"))
        layout.addWidget(self.edit_btn)
        
        self.duplicate_btn = QPushButton("📋 Duplicar")
        self.duplicate_btn.setToolTip("Crear una copia de este preset")
        self.duplicate_btn.setEnabled(False)
        self.duplicate_btn.clicked.connect(lambda: self._emit_action("duplicate"))
        layout.addWidget(self.duplicate_btn)
        
        layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setToolTip("Eliminar este preset")
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("QPushButton { color: #cc0000; }")
        self.delete_btn.clicked.connect(lambda: self._emit_action("delete"))
        layout.addWidget(self.delete_btn)
        
    def set_preset(self, preset: Optional[Dict[str, Any]]):
        """Establece el preset activo para las acciones."""
        self.current_preset = preset
        
        has_preset = preset is not None
        is_system = preset.get("is_system", False) if preset else False
        
        # Habilitar botones según disponibilidad
        self.execute_btn.setEnabled(has_preset)
        self.edit_btn.setEnabled(has_preset and not is_system)
        self.duplicate_btn.setEnabled(has_preset)
        self.delete_btn.setEnabled(has_preset and not is_system)
        
    def _emit_action(self, action: str):
        """Emite señal de acción solicitada."""
        if self.current_preset:
            self.action_requested.emit(action, self.current_preset)


# Widget compuesto que combina todo
class PresetScannerWidget(QWidget):
    """Widget compuesto para selección de presets y visualización de resultados."""
    
    def __init__(self, api_client: Optional[UltiBotAPIClient] = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Configura la interfaz del widget compuesto."""
        layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter(Qt.Vertical)
        
        # Panel superior: Selector de presets
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        self.preset_selector = PresetSelectorWidget(self.api_client)
        top_layout.addWidget(self.preset_selector)
        
        self.quick_actions = PresetQuickActionWidget()
        top_layout.addWidget(self.quick_actions)
        
        splitter.addWidget(top_widget)
        
        # Panel inferior: Resultados
        self.results_widget = ScanResultsWidget()
        splitter.addWidget(self.results_widget)
        
        # Configurar tamaños
        splitter.setSizes([300, 500])
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
    def connect_signals(self):
        """Conecta las señales entre widgets."""
        # Cuando se selecciona un preset
        self.preset_selector.preset_selected.connect(self.quick_actions.set_preset)
        
        # Cuando se ejecuta un preset
        self.preset_selector.preset_executed.connect(self.results_widget.show_results)
        
        # Acciones rápidas
        self.quick_actions.action_requested.connect(self._handle_preset_action)
        
    def _handle_preset_action(self, action: str, preset_data: Dict[str, Any]):
        """Maneja las acciones solicitadas en presets."""
        if action == "execute":
            # Re-ejecutar el preset actualmente seleccionado
            self.preset_selector._execute_preset()
        elif action == "edit":
            QMessageBox.information(self, "Acción", f"Editar preset: {preset_data['name']}")
        elif action == "duplicate":
            QMessageBox.information(self, "Acción", f"Duplicar preset: {preset_data['name']}")
        elif action == "delete":
            reply = QMessageBox.question(
                self, 
                "Confirmar Eliminación", 
                f"¿Está seguro de eliminar el preset '{preset_data['name']}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                QMessageBox.information(self, "Acción", f"Eliminar preset: {preset_data['name']}")


# Testing independiente
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test del widget compuesto
    widget = PresetScannerWidget()
    widget.setWindowTitle("Test: Preset Scanner Widget")
    widget.resize(1000, 700)
    widget.show()
    
    sys.exit(app.exec_())
