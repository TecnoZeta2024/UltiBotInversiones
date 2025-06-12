"""
Prompt Editor Widget - Editor especializado para templates de prompts
Incluye syntax highlighting, validación y funciones de edición avanzadas
"""

import re
import json
from typing import Dict, List, Set, Optional
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QFrame, QSplitter,
    QScrollArea, QGroupBox, QListWidget, QListWidgetItem,
    QToolBar, QComboBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import (
    QTextCharFormat, QSyntaxHighlighter, QTextDocument,
    QColor, QFont, QTextCursor, QPalette
)

logger = logging.getLogger(__name__)

class PromptSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter para templates de prompts
    Resalta variables, comandos especiales y sintaxis de templates
    """
    
    def __init__(self, parent: QTextDocument):
        super().__init__(parent)
        self._setup_highlighting_rules()
    
    def _setup_highlighting_rules(self):
        """Configura las reglas de resaltado de sintaxis"""
        
        # Formato para variables {{variable}}
        self._variable_format = QTextCharFormat()
        self._variable_format.setForeground(QColor("#FF5722"))  # Rojo-naranja
        self._variable_format.setFontWeight(QFont.Weight.Bold)
        
        # Formato para comandos especiales [COMMAND]
        self._command_format = QTextCharFormat()
        self._command_format.setForeground(QColor("#2196F3"))  # Azul
        self._command_format.setFontWeight(QFont.Weight.Bold)
        
        # Formato para comentarios <!-- comment -->
        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QColor("#4CAF50"))  # Verde
        self._comment_format.setFontItalic(True)
        
        # Formato para strings especiales "quoted text"
        self._string_format = QTextCharFormat()
        self._string_format.setForeground(QColor("#9C27B0"))  # Púrpura
        
        # Formato para números y valores especiales
        self._number_format = QTextCharFormat()
        self._number_format.setForeground(QColor("#FF9800"))  # Naranja
        
        # Patrones de expresiones regulares
        self._highlighting_rules = [
            # Variables: {{variable_name}}
            (re.compile(r'\{\{[^}]+\}\}'), self._variable_format),
            
            # Variables con filtros: {{variable|filter}}
            (re.compile(r'\{\{[^}]+\|[^}]+\}\}'), self._variable_format),
            
            # Comandos: [COMMAND], [INSTRUCTION], etc.
            (re.compile(r'\[([A-Z_]+)\]'), self._command_format),
            
            # Comentarios: <!-- comment -->
            (re.compile(r'<!--.*?-->'), self._comment_format),
            
            # Strings entre comillas
            (re.compile(r'"[^"]*"'), self._string_format),
            (re.compile(r"'[^']*'"), self._string_format),
            
            # Números
            (re.compile(r'\b\d+\.?\d*\b'), self._number_format),
        ]
    
    def highlightBlock(self, text: str):
        """Aplica el resaltado de sintaxis a un bloque de texto"""
        # Aplicar todas las reglas de resaltado
        for pattern, format_obj in self._highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format_obj)

class VariablesSidePanel(QWidget):
    """
    Panel lateral que muestra las variables detectadas en el template
    """
    
    variable_clicked = pyqtSignal(str)  # Variable seleccionada para insertar
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._detected_variables: Set[str] = set()
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la UI del panel de variables"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Título
        title = QLabel("Variables Detectadas")
        title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        layout.addWidget(title)
        
        # Lista de variables
        self._variables_list = QListWidget()
        self._variables_list.setMaximumHeight(150)
        self._variables_list.itemDoubleClicked.connect(self._on_variable_double_clicked)
        layout.addWidget(self._variables_list)
        
        # Variables comunes para insertar rápido
        common_group = QGroupBox("Variables Comunes")
        common_layout = QVBoxLayout(common_group)
        
        common_variables = [
            "{{symbol}}", "{{price}}", "{{volume}}", "{{timestamp}}",
            "{{user_name}}", "{{strategy_name}}", "{{confidence}}",
            "{{market_data}}", "{{analysis_result}}"
        ]
        
        for var in common_variables:
            btn = QPushButton(var)
            btn.setMaximumHeight(25)
            btn.clicked.connect(lambda checked, v=var: self.variable_clicked.emit(v))
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 2px 6px;
                    border: 1px solid #ddd;
                    background: #f9f9f9;
                }
                QPushButton:hover {
                    background: #e3f2fd;
                }
            """)
            common_layout.addWidget(btn)
        
        layout.addWidget(common_group)
        layout.addStretch()
    
    def update_detected_variables(self, variables: Set[str]):
        """Actualiza la lista de variables detectadas"""
        self._detected_variables = variables
        
        self._variables_list.clear()
        for var in sorted(variables):
            item = QListWidgetItem(var)
            item.setToolTip(f"Variable: {var}")
            self._variables_list.addItem(item)
    
    @pyqtSlot(QListWidgetItem)
    def _on_variable_double_clicked(self, item: QListWidgetItem):
        """Emite señal cuando se hace doble clic en una variable"""
        self.variable_clicked.emit(item.text())

class PromptEditorWidget(QWidget):
    """
    Editor avanzado para templates de prompts con syntax highlighting,
    detección de variables y funciones de edición especializadas
    """
    
    # Señales
    text_changed = pyqtSignal(str)  # Texto del template cambió
    variables_detected = pyqtSignal(set)  # Variables detectadas en el template
    syntax_error_found = pyqtSignal(str)  # Error de sintaxis encontrado
    template_validated = pyqtSignal(bool)  # Resultado de validación
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado interno
        self._current_text = ""
        self._detected_variables: Set[str] = set()
        self._validation_errors: List[str] = []
        
        # Configuración
        self._auto_detect_variables = True
        self._enable_auto_complete = True
        self._enable_syntax_highlighting = True
        
        # Timers para operaciones diferidas
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._validate_template)
        
        self._variable_detection_timer = QTimer()
        self._variable_detection_timer.setSingleShot(True)
        self._variable_detection_timer.timeout.connect(self._detect_variables)
        
        self._setup_ui()
        self._setup_connections()
        
        logger.debug("PromptEditorWidget inicializado")
    
    def _setup_ui(self):
        """Configura la estructura de la UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # === SPLITTER PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === PANEL PRINCIPAL DEL EDITOR ===
        editor_panel = self._create_editor_panel()
        main_splitter.addWidget(editor_panel)
        
        # === PANEL LATERAL DE VARIABLES ===
        variables_panel = VariablesSidePanel()
        variables_panel.setMaximumWidth(200)
        variables_panel.variable_clicked.connect(self._insert_variable)
        self._variables_panel = variables_panel
        
        main_splitter.addWidget(variables_panel)
        
        # Proporción inicial
        main_splitter.setSizes([400, 200])
        
        layout.addWidget(main_splitter)
    
    def _create_editor_panel(self) -> QWidget:
        """Crea el panel principal del editor"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # === TOOLBAR ===
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # === EDITOR DE TEXTO ===
        self._text_editor = QTextEdit()
        self._text_editor.setPlaceholderText(
            "Escribe tu template de prompt aquí...\n\n"
            "Usa variables como: {{symbol}}, {{price}}, {{user_name}}\n"
            "Usa comandos como: [INSTRUCTION], [CONTEXT], [EXAMPLES]\n"
            "Usa comentarios como: <!-- Este es un comentario -->"
        )
        
        # Configurar fuente monospace
        font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        self._text_editor.setFont(font)
        
        # Configurar syntax highlighter
        if self._enable_syntax_highlighting:
            self._highlighter = PromptSyntaxHighlighter(self._text_editor.document())
        
        layout.addWidget(self._text_editor)
        
        # === BARRA DE ESTADO ===
        status_bar = self._create_status_bar()
        layout.addWidget(status_bar)
        
        return panel
    
    def _create_toolbar(self) -> QWidget:
        """Crea la barra de herramientas del editor"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setMaximumHeight(40)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # === BOTONES DE ACCIÓN ===
        self._validate_btn = QPushButton("✅ Validar")
        self._validate_btn.setToolTip("Validar sintaxis del template")
        self._validate_btn.clicked.connect(self._validate_template)
        
        self._format_btn = QPushButton("🎨 Formatear")
        self._format_btn.setToolTip("Formatear y organizar el template")
        self._format_btn.clicked.connect(self._format_template)
        
        self._clear_btn = QPushButton("🗑️ Limpiar")
        self._clear_btn.setToolTip("Limpiar el editor")
        self._clear_btn.clicked.connect(self._clear_editor)
        
        # === CONFIGURACIONES ===
        self._highlighting_checkbox = QCheckBox("Syntax Highlighting")
        self._highlighting_checkbox.setChecked(self._enable_syntax_highlighting)
        self._highlighting_checkbox.toggled.connect(self._toggle_syntax_highlighting)
        
        self._auto_detect_checkbox = QCheckBox("Auto-detectar Variables")
        self._auto_detect_checkbox.setChecked(self._auto_detect_variables)
        self._auto_detect_checkbox.toggled.connect(self._toggle_auto_detect)
        
        # === LAYOUT ===
        layout.addWidget(self._validate_btn)
        layout.addWidget(self._format_btn)
        layout.addWidget(self._clear_btn)
        layout.addWidget(QFrame())  # Separador
        layout.addWidget(self._highlighting_checkbox)
        layout.addWidget(self._auto_detect_checkbox)
        layout.addStretch()
        
        return toolbar
    
    def _create_status_bar(self) -> QWidget:
        """Crea la barra de estado del editor"""
        status_bar = QFrame()
        status_bar.setFrameStyle(QFrame.Shape.StyledPanel)
        status_bar.setMaximumHeight(25)
        
        layout = QHBoxLayout(status_bar)
        layout.setContentsMargins(8, 2, 8, 2)
        
        # Información de estado
        self._char_count_label = QLabel("0 caracteres")
        self._char_count_label.setStyleSheet("color: #666; font-size: 11px;")
        
        self._var_count_label = QLabel("0 variables")
        self._var_count_label.setStyleSheet("color: #666; font-size: 11px;")
        
        self._validation_status_label = QLabel("✅ Válido")
        self._validation_status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        
        layout.addWidget(self._char_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self._var_count_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self._validation_status_label)
        layout.addStretch()
        
        return status_bar
    
    def _setup_connections(self):
        """Configura las conexiones de señales"""
        # Editor de texto
        self._text_editor.textChanged.connect(self._on_text_changed)
        
        # Timers
        self._validation_timer.timeout.connect(self._validate_template)
        self._variable_detection_timer.timeout.connect(self._detect_variables)
    
    # === PROPIEDADES PÚBLICAS ===
    
    def get_text(self) -> str:
        """Obtiene el texto actual del editor"""
        return self._text_editor.toPlainText()
    
    def set_text(self, text: str):
        """Establece el texto del editor"""
        if text != self._current_text:
            self._text_editor.setPlainText(text)
            self._current_text = text
            self._update_status()
    
    def get_detected_variables(self) -> Set[str]:
        """Obtiene las variables detectadas en el template"""
        return self._detected_variables.copy()
    
    def is_template_valid(self) -> bool:
        """Indica si el template actual es válido"""
        return len(self._validation_errors) == 0
    
    def get_validation_errors(self) -> List[str]:
        """Obtiene la lista de errores de validación"""
        return self._validation_errors.copy()
    
    # === MÉTODOS PÚBLICOS ===
    
    def insert_text_at_cursor(self, text: str):
        """Inserta texto en la posición del cursor"""
        cursor = self._text_editor.textCursor()
        cursor.insertText(text)
        self._text_editor.setTextCursor(cursor)
    
    def format_template(self):
        """Formatea el template para mejor legibilidad"""
        self._format_template()
    
    def validate_template(self) -> bool:
        """Valida la sintaxis del template manualmente"""
        self._validate_template()
        return self.is_template_valid()
    
    def clear_editor(self):
        """Limpia el contenido del editor"""
        self._clear_editor()
    
    # === SLOTS PRIVADOS ===
    
    @pyqtSlot()
    def _on_text_changed(self):
        """Maneja cambios en el texto del editor"""
        new_text = self._text_editor.toPlainText()
        
        if new_text != self._current_text:
            self._current_text = new_text
            
            # Emitir señal de cambio
            self.text_changed.emit(new_text)
            
            # Programar validación y detección de variables
            self._validation_timer.stop()
            self._validation_timer.start(500)  # 500ms delay
            
            if self._auto_detect_variables:
                self._variable_detection_timer.stop()
                self._variable_detection_timer.start(300)  # 300ms delay
            
            # Actualizar status inmediatamente
            self._update_status()
    
    @pyqtSlot(str)
    def _insert_variable(self, variable: str):
        """Inserta una variable en el cursor"""
        self.insert_text_at_cursor(variable)
        self._text_editor.setFocus()
    
    @pyqtSlot()
    def _validate_template(self):
        """Valida la sintaxis del template"""
        self._validation_errors.clear()
        text = self._current_text
        
        try:
            # Validaciones básicas
            
            # 1. Balanceo de llaves para variables
            open_braces = text.count('{{')
            close_braces = text.count('}}')
            if open_braces != close_braces:
                self._validation_errors.append(
                    f"Llaves desbalanceadas: {open_braces} abiertas, {close_braces} cerradas"
                )
            
            # 2. Validar variables malformadas
            variable_pattern = re.compile(r'\{\{([^}]*)\}\}')
            for match in variable_pattern.finditer(text):
                var_content = match.group(1).strip()
                if not var_content:
                    self._validation_errors.append(
                        f"Variable vacía en posición {match.start()}"
                    )
                elif not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\|[a-zA-Z_][a-zA-Z0-9_]*)*$', var_content):
                    self._validation_errors.append(
                        f"Variable malformada: '{var_content}'"
                    )
            
            # 3. Validar comandos
            command_pattern = re.compile(r'\[([^\]]*)\]')
            valid_commands = {
                'INSTRUCTION', 'CONTEXT', 'EXAMPLES', 'CONSTRAINTS', 
                'OUTPUT_FORMAT', 'TONE', 'STYLE', 'PERSONA'
            }
            
            for match in command_pattern.finditer(text):
                command = match.group(1).strip()
                if command and command not in valid_commands:
                    self._validation_errors.append(
                        f"Comando no reconocido: '[{command}]'"
                    )
            
            # 4. Validar comentarios HTML
            comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
            remaining_text = comment_pattern.sub('', text)
            if '<!--' in remaining_text and '-->' not in remaining_text:
                self._validation_errors.append("Comentario HTML no cerrado")
            
        except Exception as e:
            self._validation_errors.append(f"Error de validación: {str(e)}")
        
        # Actualizar UI
        is_valid = len(self._validation_errors) == 0
        self.template_validated.emit(is_valid)
        
        if is_valid:
            self._validation_status_label.setText("✅ Válido")
            self._validation_status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        else:
            error_count = len(self._validation_errors)
            self._validation_status_label.setText(f"❌ {error_count} error(es)")
            self._validation_status_label.setStyleSheet("color: #F44336; font-size: 11px;")
            
            # Mostrar el primer error como tooltip
            if self._validation_errors:
                first_error = self._validation_errors[0]
                self._validation_status_label.setToolTip(
                    f"Errores:\n" + "\n".join(self._validation_errors[:3])
                )
        
        logger.debug(f"Template validado: {len(self._validation_errors)} errores")
    
    @pyqtSlot()
    def _detect_variables(self):
        """Detecta variables en el template actual"""
        text = self._current_text
        variables = set()
        
        # Patrón para variables {{variable}} o {{variable|filter}}
        variable_pattern = re.compile(r'\{\{([^}|]+)(?:\|[^}]*)?\}\}')
        
        for match in variable_pattern.finditer(text):
            var_name = match.group(1).strip()
            if var_name and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var_name):
                variables.add(var_name)
        
        if variables != self._detected_variables:
            self._detected_variables = variables
            self.variables_detected.emit(variables)
            self._variables_panel.update_detected_variables(variables)
            self._update_status()
    
    @pyqtSlot()
    def _format_template(self):
        """Formatea el template para mejor legibilidad"""
        text = self._current_text
        
        # Formateo básico
        # 1. Normalizar espacios alrededor de variables
        text = re.sub(r'\s*\{\{\s*([^}]+)\s*\}\}\s*', r' {{\1}} ', text)
        
        # 2. Normalizar comandos
        text = re.sub(r'\s*\[\s*([^\]]+)\s*\]\s*', r'\n[\1]\n', text)
        
        # 3. Limpiar líneas vacías múltiples
        text = re.sub(r'\n\s*\n\s*\n', r'\n\n', text)
        
        # 4. Limpiar espacios al final de líneas
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        
        # Actualizar editor si hay cambios
        if text.strip() != self._current_text.strip():
            self.set_text(text.strip())
    
    @pyqtSlot()
    def _clear_editor(self):
        """Limpia el contenido del editor"""
        self._text_editor.clear()
        self._current_text = ""
        self._detected_variables.clear()
        self._validation_errors.clear()
        self._update_status()
    
    @pyqtSlot(bool)
    def _toggle_syntax_highlighting(self, enabled: bool):
        """Activa/desactiva el syntax highlighting"""
        self._enable_syntax_highlighting = enabled
        
        if enabled and not hasattr(self, '_highlighter'):
            self._highlighter = PromptSyntaxHighlighter(self._text_editor.document())
        elif not enabled and hasattr(self, '_highlighter'):
            # Remover highlighter
            self._highlighter.setDocument(None)
            delattr(self, '_highlighter')
    
    @pyqtSlot(bool)
    def _toggle_auto_detect(self, enabled: bool):
        """Activa/desactiva la auto-detección de variables"""
        self._auto_detect_variables = enabled
        
        if enabled:
            self._detect_variables()
    
    def _update_status(self):
        """Actualiza las etiquetas de estado"""
        char_count = len(self._current_text)
        var_count = len(self._detected_variables)
        
        self._char_count_label.setText(f"{char_count} caracteres")
        self._var_count_label.setText(f"{var_count} variables")
