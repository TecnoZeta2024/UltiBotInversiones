"""
AI Playground Widget - Widget interactivo para testing de prompts con IA
Permite probar prompts con variables y ver respuestas de la IA en tiempo real
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QSplitter, QGroupBox, QScrollArea, QFrame,
    QTabWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QProgressBar, QListWidget, QListWidgetItem,
    QMessageBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QThread, QObject
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QIcon

logger = logging.getLogger(__name__)

class VariableInputWidget(QWidget):
    """
    Widget para capturar valores de variables de entrada
    Detecta automáticamente el tipo de variable y crea el input apropiado
    """
    
    value_changed = pyqtSignal(str, object)  # variable_name, value
    
    def __init__(self, variable_name: str, variable_type: str = "string", parent=None):
        super().__init__(parent)
        self._variable_name = variable_name
        self._variable_type = variable_type
        self._current_value = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la UI del widget de input"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        
        # Label del nombre de variable
        label = QLabel(f"{self._variable_name}:")
        label.setMinimumWidth(100)
        label.setStyleSheet("font-weight: 500;")
        layout.addWidget(label)
        
        # Input según el tipo
        self._input_widget = self._create_input_for_type()
        layout.addWidget(self._input_widget)
        
        # Botón de tipo (para cambiar tipo dinámicamente)
        self._type_combo = QComboBox()
        self._type_combo.addItems(["string", "number", "boolean", "json"])
        self._type_combo.setCurrentText(self._variable_type)
        self._type_combo.setMaximumWidth(80)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self._type_combo)
    
    def _create_input_for_type(self) -> QWidget:
        """Crea el widget de input apropiado para el tipo"""
        if self._variable_type == "string":
            widget = QLineEdit()
            widget.setPlaceholderText(f"Valor para {self._variable_name}")
            widget.textChanged.connect(self._on_value_changed)
            return widget
        
        elif self._variable_type == "number":
            widget = QDoubleSpinBox()
            widget.setRange(-999999999, 999999999)
            widget.setDecimals(6)
            widget.setValue(0.0)
            widget.valueChanged.connect(self._on_value_changed)
            return widget
        
        elif self._variable_type == "boolean":
            widget = QCheckBox()
            widget.setText("True")
            widget.toggled.connect(self._on_value_changed)
            return widget
        
        elif self._variable_type == "json":
            widget = QTextEdit()
            widget.setMaximumHeight(60)
            widget.setPlaceholderText('{"key": "value"}')
            widget.textChanged.connect(self._on_value_changed)
            return widget
        
        else:
            # Fallback a string
            widget = QLineEdit()
            widget.textChanged.connect(self._on_value_changed)
            return widget
    
    @pyqtSlot()
    def _on_value_changed(self):
        """Maneja cambios en el valor del input"""
        try:
            value = self._get_current_value()
            if value != self._current_value:
                self._current_value = value
                self.value_changed.emit(self._variable_name, value)
        except Exception as e:
            logger.debug(f"Error obteniendo valor de {self._variable_name}: {e}")
    
    @pyqtSlot(str)
    def _on_type_changed(self, new_type: str):
        """Maneja cambio de tipo de variable"""
        if new_type != self._variable_type:
            # Guardar valor actual si es posible
            old_value = self._get_current_value()
            
            # Cambiar tipo
            self._variable_type = new_type
            
            # Recrear widget
            old_widget = self._input_widget
            self._input_widget = self._create_input_for_type()
            
            # Reemplazar en layout
            layout = self.layout()
            layout.replaceWidget(old_widget, self._input_widget)
            old_widget.deleteLater()
            
            # Intentar restaurar valor
            try:
                self._set_value(old_value)
            except:
                pass
    
    def _get_current_value(self) -> Any:
        """Obtiene el valor actual del input"""
        if self._variable_type == "string":
            return self._input_widget.text()
        
        elif self._variable_type == "number":
            return self._input_widget.value()
        
        elif self._variable_type == "boolean":
            return self._input_widget.isChecked()
        
        elif self._variable_type == "json":
            text = self._input_widget.toPlainText().strip()
            if not text:
                return {}
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text  # Fallback a string si no es JSON válido
        
        return ""
    
    def _set_value(self, value: Any):
        """Establece el valor del input"""
        try:
            if self._variable_type == "string":
                self._input_widget.setText(str(value))
            
            elif self._variable_type == "number":
                self._input_widget.setValue(float(value))
            
            elif self._variable_type == "boolean":
                self._input_widget.setChecked(bool(value))
            
            elif self._variable_type == "json":
                if isinstance(value, (dict, list)):
                    self._input_widget.setPlainText(json.dumps(value, indent=2))
                else:
                    self._input_widget.setPlainText(str(value))
        
        except Exception as e:
            logger.debug(f"Error estableciendo valor en {self._variable_name}: {e}")
    
    def get_variable_name(self) -> str:
        """Obtiene el nombre de la variable"""
        return self._variable_name
    
    def get_value(self) -> Any:
        """Obtiene el valor actual"""
        return self._get_current_value()
    
    def set_value(self, value: Any):
        """Establece el valor externamente"""
        self._set_value(value)

class PlaygroundHistoryWidget(QWidget):
    """
    Widget que muestra el historial de tests ejecutados
    """
    
    history_item_selected = pyqtSignal(dict)  # Resultado seleccionado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: List[Dict[str, Any]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la UI del historial"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Título y controles
        header_layout = QHBoxLayout()
        
        title = QLabel("Historial de Tests")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setMaximumWidth(30)
        clear_btn.setToolTip("Limpiar historial")
        clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Lista de historial
        self._history_list = QListWidget()
        self._history_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._history_list)
    
    def add_history_item(self, test_result: Dict[str, Any]):
        """Añade un nuevo item al historial"""
        self._history.insert(0, test_result)  # Más reciente primero
        
        # Limitar historial a 20 items
        if len(self._history) > 20:
            self._history = self._history[:20]
        
        self._refresh_list()
    
    def _refresh_list(self):
        """Actualiza la lista visual"""
        self._history_list.clear()
        
        for i, item in enumerate(self._history):
            timestamp = item.get("timestamp", "")
            prompt_name = item.get("prompt_name", "Unknown")
            
            # Formatear timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = "??:??:??"
            
            # Crear item
            display_text = f"[{time_str}] {prompt_name}"
            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            # Tooltip con más info
            variables = item.get("variables_used", {})
            var_summary = ", ".join([f"{k}={v}" for k, v in list(variables.items())[:3]])
            if len(variables) > 3:
                var_summary += "..."
            
            tooltip = f"Prompt: {prompt_name}\n"
            tooltip += f"Tiempo: {timestamp}\n"
            tooltip += f"Variables: {var_summary}"
            list_item.setToolTip(tooltip)
            
            self._history_list.addItem(list_item)
    
    @pyqtSlot(QListWidgetItem)
    def _on_item_clicked(self, item: QListWidgetItem):
        """Maneja clic en item del historial"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.history_item_selected.emit(data)
    
    @pyqtSlot()
    def _clear_history(self):
        """Limpia todo el historial"""
        self._history.clear()
        self._history_list.clear()

class AIPlaygroundWidget(QWidget):
    """
    Widget principal del AI Playground para testing interactivo de prompts
    
    Funcionalidades:
    - Input dinámico de variables
    - Renderizado de prompts
    - Testing con IA
    - Historial de resultados
    - Configuración de parámetros de IA
    """
    
    # Señales
    test_requested = pyqtSignal(dict)  # Variables para test completo
    render_requested = pyqtSignal(dict)  # Variables para solo renderizado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado interno
        self._current_prompt_data: Optional[Dict[str, Any]] = None
        self._variable_widgets: Dict[str, VariableInputWidget] = {}
        self._last_render_result: Optional[Dict[str, Any]] = None
        self._is_testing = False
        
        # Configuración por defecto
        self._ai_config = {
            "max_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.9,
            "model": "gemini-1.5-flash"
        }
        
        self._setup_ui()
        
        logger.debug("AIPlaygroundWidget inicializado")
    
    def _setup_ui(self):
        """Configura la estructura principal de la UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        
        # === TÍTULO ===
        title = QLabel("🧪 AI Playground")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3; padding: 4px;")
        layout.addWidget(title)
        
        # === TABS PRINCIPALES ===
        self._tabs = QTabWidget()
        
        # Tab 1: Variables y Ejecución
        self._execution_tab = self._create_execution_tab()
        self._tabs.addTab(self._execution_tab, "🎛️ Variables")
        
        # Tab 2: Configuración de IA
        self._config_tab = self._create_config_tab()
        self._tabs.addTab(self._config_tab, "⚙️ Configuración")
        
        # Tab 3: Historial
        self._history_widget = PlaygroundHistoryWidget()
        self._history_widget.history_item_selected.connect(self._on_history_item_selected)
        self._tabs.addTab(self._history_widget, "📋 Historial")
        
        layout.addWidget(self._tabs)
        
        # === PANEL DE RESULTADOS ===
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout(results_group)
        
        # Splitter para rendered prompt y AI response
        results_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Rendered prompt
        rendered_group = QGroupBox("Prompt Renderizado")
        rendered_layout = QVBoxLayout(rendered_group)
        
        self._rendered_output = QTextEdit()
        self._rendered_output.setMaximumHeight(150)
        self._rendered_output.setPlaceholderText("El prompt renderizado aparecerá aquí...")
        font = QFont("Consolas", 10)
        self._rendered_output.setFont(font)
        rendered_layout.addWidget(self._rendered_output)
        
        results_splitter.addWidget(rendered_group)
        
        # AI response
        response_group = QGroupBox("Respuesta de IA")
        response_layout = QVBoxLayout(response_group)
        
        self._ai_response = QTextEdit()
        self._ai_response.setPlaceholderText("La respuesta de la IA aparecerá aquí...")
        self._ai_response.setFont(font)
        response_layout.addWidget(self._ai_response)
        
        results_splitter.addWidget(response_group)
        
        # Proporción inicial
        results_splitter.setSizes([150, 250])
        
        results_layout.addWidget(results_splitter)
        layout.addWidget(results_group)
        
        # === INDICADOR DE ESTADO ===
        self._status_indicator = self._create_status_indicator()
        layout.addWidget(self._status_indicator)
    
    def _create_execution_tab(self) -> QWidget:
        """Crea el tab de variables y ejecución"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # === INFORMACIÓN DEL PROMPT ===
        info_group = QGroupBox("Prompt Actual")
        info_layout = QFormLayout(info_group)
        
        self._prompt_name_label = QLabel("(Ninguno)")
        self._prompt_name_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addRow("Nombre:", self._prompt_name_label)
        
        self._prompt_version_label = QLabel("v1")
        info_layout.addRow("Versión:", self._prompt_version_label)
        
        layout.addWidget(info_group)
        
        # === VARIABLES DE ENTRADA ===
        variables_group = QGroupBox("Variables de Entrada")
        variables_layout = QVBoxLayout(variables_group)
        
        # Scroll area para variables
        self._variables_scroll = QScrollArea()
        self._variables_scroll.setWidgetResizable(True)
        self._variables_scroll.setMaximumHeight(200)
        
        self._variables_container = QWidget()
        self._variables_layout = QVBoxLayout(self._variables_container)
        self._variables_layout.addStretch()
        
        self._variables_scroll.setWidget(self._variables_container)
        variables_layout.addWidget(self._variables_scroll)
        
        # Mensaje cuando no hay variables
        self._no_variables_label = QLabel("No hay variables detectadas en el prompt actual")
        self._no_variables_label.setStyleSheet("color: #666; font-style: italic; text-align: center;")
        self._no_variables_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        variables_layout.addWidget(self._no_variables_label)
        
        layout.addWidget(variables_group)
        
        # === BOTONES DE ACCIÓN ===
        actions_layout = QHBoxLayout()
        
        self._render_btn = QPushButton("👁️ Solo Renderizar")
        self._render_btn.setToolTip("Renderizar el prompt con las variables (sin enviar a IA)")
        self._render_btn.clicked.connect(self._on_render_clicked)
        
        self._test_btn = QPushButton("🧠 Probar con IA")
        self._test_btn.setToolTip("Renderizar y enviar a la IA para obtener respuesta")
        self._test_btn.clicked.connect(self._on_test_clicked)
        
        actions_layout.addWidget(self._render_btn)
        actions_layout.addWidget(self._test_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        return tab
    
    def _create_config_tab(self) -> QWidget:
        """Crea el tab de configuración de IA"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # === PARÁMETROS DEL MODELO ===
        model_group = QGroupBox("Parámetros del Modelo")
        model_layout = QFormLayout(model_group)
        
        # Modelo
        self._model_combo = QComboBox()
        self._model_combo.addItems([
            "gemini-1.5-flash",
            "gemini-1.5-pro", 
            "gemini-1.0-pro"
        ])
        self._model_combo.setCurrentText(self._ai_config["model"])
        model_layout.addRow("Modelo:", self._model_combo)
        
        # Max tokens
        self._max_tokens_spin = QSpinBox()
        self._max_tokens_spin.setRange(1, 8192)
        self._max_tokens_spin.setValue(self._ai_config["max_tokens"])
        model_layout.addRow("Max Tokens:", self._max_tokens_spin)
        
        # Temperature
        self._temperature_spin = QDoubleSpinBox()
        self._temperature_spin.setRange(0.0, 2.0)
        self._temperature_spin.setSingleStep(0.1)
        self._temperature_spin.setDecimals(1)
        self._temperature_spin.setValue(self._ai_config["temperature"])
        model_layout.addRow("Temperature:", self._temperature_spin)
        
        # Top P
        self._top_p_spin = QDoubleSpinBox()
        self._top_p_spin.setRange(0.0, 1.0)
        self._top_p_spin.setSingleStep(0.1)
        self._top_p_spin.setDecimals(1)
        self._top_p_spin.setValue(self._ai_config["top_p"])
        model_layout.addRow("Top P:", self._top_p_spin)
        
        layout.addWidget(model_group)
        
        # === PRESETS DE CONFIGURACIÓN ===
        presets_group = QGroupBox("Presets de Configuración")
        presets_layout = QVBoxLayout(presets_group)
        
        presets_buttons_layout = QHBoxLayout()
        
        creative_btn = QPushButton("🎨 Creativo")
        creative_btn.setToolTip("Temperature: 0.9, Top P: 0.9")
        creative_btn.clicked.connect(lambda: self._apply_preset("creative"))
        
        balanced_btn = QPushButton("⚖️ Balanceado")
        balanced_btn.setToolTip("Temperature: 0.7, Top P: 0.9")
        balanced_btn.clicked.connect(lambda: self._apply_preset("balanced"))
        
        precise_btn = QPushButton("🎯 Preciso")
        precise_btn.setToolTip("Temperature: 0.3, Top P: 0.7")
        precise_btn.clicked.connect(lambda: self._apply_preset("precise"))
        
        presets_buttons_layout.addWidget(creative_btn)
        presets_buttons_layout.addWidget(balanced_btn)
        presets_buttons_layout.addWidget(precise_btn)
        
        presets_layout.addLayout(presets_buttons_layout)
        layout.addWidget(presets_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_status_indicator(self) -> QWidget:
        """Crea el indicador de estado inferior"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setMaximumHeight(25)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 2, 8, 2)
        
        self._status_label = QLabel("Listo para probar")
        self._status_label.setStyleSheet("color: #666; font-size: 11px;")
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximumWidth(150)
        self._progress_bar.setMaximumHeight(16)
        self._progress_bar.setVisible(False)
        self._progress_bar.setRange(0, 0)  # Modo indeterminado
        
        layout.addWidget(self._status_label)
        layout.addStretch()
        layout.addWidget(self._progress_bar)
        
        return frame
    
    # === MÉTODOS PÚBLICOS ===
    
    def set_current_prompt(self, prompt_data: Dict[str, Any]):
        """Establece el prompt actual para testing"""
        self._current_prompt_data = prompt_data
        
        # Actualizar información
        self._prompt_name_label.setText(prompt_data.get("name", "Unknown"))
        self._prompt_version_label.setText(f"v{prompt_data.get('version', 1)}")
        
        # Actualizar variables
        self._update_variables_inputs(prompt_data.get("variables", {}))
        
        # Limpiar resultados anteriores
        self._rendered_output.clear()
        self._ai_response.clear()
        
        self._status_label.setText(f"Prompt '{prompt_data.get('name')}' cargado")
        
        logger.debug(f"Prompt '{prompt_data.get('name')}' establecido en playground")
    
    def set_render_result(self, render_result: Dict[str, Any]):
        """Establece el resultado de renderizado"""
        self._last_render_result = render_result
        
        rendered_content = render_result.get("content", "")
        self._rendered_output.setPlainText(rendered_content)
        
        self._status_label.setText("Prompt renderizado exitosamente")
    
    def set_test_result(self, test_result: Dict[str, Any]):
        """Establece el resultado de test completo con IA"""
        # Actualizar rendered prompt
        rendered_content = test_result.get("rendered_prompt", "")
        self._rendered_output.setPlainText(rendered_content)
        
        # Actualizar AI response
        ai_response = test_result.get("ai_response", "")
        if ai_response:
            self._ai_response.setPlainText(ai_response)
        else:
            self._ai_response.setPlainText("(No hay respuesta de IA)")
        
        # Añadir al historial
        self._history_widget.add_history_item(test_result)
        
        self._status_label.setText("Test completado exitosamente")
    
    # === MÉTODOS PRIVADOS ===
    
    def _update_variables_inputs(self, variables_config: Dict[str, Any]):
        """Actualiza los inputs de variables basado en la configuración"""
        # Limpiar widgets existentes
        for widget in self._variable_widgets.values():
            widget.deleteLater()
        self._variable_widgets.clear()
        
        # Crear nuevos widgets
        if variables_config:
            self._no_variables_label.hide()
            self._variables_scroll.show()
            
            for var_name, var_info in variables_config.items():
                var_type = "string"
                if isinstance(var_info, dict):
                    var_type = var_info.get("type", "string")
                
                widget = VariableInputWidget(var_name, var_type)
                widget.value_changed.connect(self._on_variable_value_changed)
                
                self._variable_widgets[var_name] = widget
                
                # Insertar antes del stretch
                layout = self._variables_layout
                layout.insertWidget(layout.count() - 1, widget)
        
        else:
            self._variables_scroll.hide()
            self._no_variables_label.show()
    
    def _get_current_variables_values(self) -> Dict[str, Any]:
        """Obtiene los valores actuales de todas las variables"""
        values = {}
        for var_name, widget in self._variable_widgets.items():
            values[var_name] = widget.get_value()
        return values
    
    def _update_ai_config(self):
        """Actualiza la configuración de IA desde los controles"""
        self._ai_config = {
            "model": self._model_combo.currentText(),
            "max_tokens": self._max_tokens_spin.value(),
            "temperature": self._temperature_spin.value(),
            "top_p": self._top_p_spin.value()
        }
    
    def _apply_preset(self, preset_name: str):
        """Aplica un preset de configuración"""
        presets = {
            "creative": {"temperature": 0.9, "top_p": 0.9},
            "balanced": {"temperature": 0.7, "top_p": 0.9},
            "precise": {"temperature": 0.3, "top_p": 0.7}
        }
        
        if preset_name in presets:
            preset = presets[preset_name]
            self._temperature_spin.setValue(preset["temperature"])
            self._top_p_spin.setValue(preset["top_p"])
    
    def _set_testing_state(self, is_testing: bool):
        """Actualiza el estado de testing en la UI"""
        self._is_testing = is_testing
        
        # Deshabilitar/habilitar controles
        self._render_btn.setEnabled(not is_testing)
        self._test_btn.setEnabled(not is_testing)
        
        # Mostrar/ocultar progress bar
        self._progress_bar.setVisible(is_testing)
        
        if is_testing:
            self._status_label.setText("Ejecutando test...")
        else:
            self._status_label.setText("Listo para probar")
    
    # === SLOTS ===
    
    @pyqtSlot(str, object)
    def _on_variable_value_changed(self, variable_name: str, value: Any):
        """Maneja cambios en valores de variables"""
        logger.debug(f"Variable '{variable_name}' cambió a: {value}")
    
    @pyqtSlot()
    def _on_render_clicked(self):
        """Maneja clic en botón de renderizar"""
        if not self._current_prompt_data:
            QMessageBox.warning(self, "Error", "No hay prompt seleccionado")
            return
        
        variables = self._get_current_variables_values()
        self._set_testing_state(True)
        
        # Emitir señal para renderizado
        self.render_requested.emit(variables)
        
        # Simular delay y reset estado
        QTimer.singleShot(1000, lambda: self._set_testing_state(False))
    
    @pyqtSlot()
    def _on_test_clicked(self):
        """Maneja clic en botón de test con IA"""
        if not self._current_prompt_data:
            QMessageBox.warning(self, "Error", "No hay prompt seleccionado")
            return
        
        variables = self._get_current_variables_values()
        self._update_ai_config()
        
        self._set_testing_state(True)
        
        # Emitir señal para test completo
        self.test_requested.emit(variables)
        
        # El estado se resetea cuando llega el resultado
    
    @pyqtSlot(dict)
    def _on_history_item_selected(self, history_item: Dict[str, Any]):
        """Maneja selección de item del historial"""
        # Cargar variables del historial
        variables = history_item.get("variables_used", {})
        
        for var_name, value in variables.items():
            if var_name in self._variable_widgets:
                self._variable_widgets[var_name].set_value(value)
        
        # Mostrar resultados
        rendered_prompt = history_item.get("rendered_prompt", "")
        ai_response = history_item.get("ai_response", "")
        
        self._rendered_output.setPlainText(rendered_prompt)
        self._ai_response.setPlainText(ai_response if ai_response else "(Sin respuesta de IA)")
        
        self._status_label.setText("Resultado del historial cargado")
