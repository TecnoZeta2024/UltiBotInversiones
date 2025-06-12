"""
AI Studio View - Vista principal para gestión visual de prompts
Parte de la arquitectura MVVM - UI "tonta" que solo maneja presentación
"""

from typing import Dict, Any, Optional
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QLabel, QLineEdit, QComboBox, QPushButton, QListWidget, 
    QListWidgetItem, QTabWidget, QTextEdit, QProgressBar,
    QStatusBar, QMessageBox, QGroupBox, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette

from ..viewmodels.ai_studio_viewmodel import AIStudioViewModel
from ..widgets.prompt_editor_widget import PromptEditorWidget
from ..widgets.ai_playground_widget import AIPlaygroundWidget
from ..services.api_client import APIClient

logger = logging.getLogger(__name__)

class AIStudioView(QWidget):
    """
    Vista principal del AI Studio para gestión de prompts
    
    Layout:
    ┌─────────────────────────────────────────────────────────────┐
    │ Toolbar: Search, Filters, Actions                          │
    ├─────────────────────────────────────────────────────────────┤
    │ ┌─────────────┬─────────────────────┬─────────────────────┐ │
    │ │   Prompts   │    Prompt Editor    │    AI Playground    │ │
    │ │    List     │                     │                     │ │
    │ │             │                     │                     │ │
    │ │             │                     │                     │ │
    │ │             │                     │                     │ │
    │ └─────────────┴─────────────────────┴─────────────────────┘ │
    ├─────────────────────────────────────────────────────────────┤
    │ Status Bar: Current status, progress                        │
    └─────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self._api = api_client
        self._viewmodel = AIStudioViewModel(api_client, self)
        
        # Estado interno de la vista
        self._is_initialized = False
        self._current_prompt_name = None
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        self._setup_styling()
        
        # Inicialización diferida
        QTimer.singleShot(100, self._initialize_async)
        
        logger.info("AIStudioView inicializada")
    
    def _setup_ui(self):
        """Configura la estructura principal de la UI"""
        self.setWindowTitle("AI Studio - Gestión de Prompts")
        self.setMinimumSize(1200, 800)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # === TOOLBAR ===
        toolbar_widget = self._create_toolbar()
        main_layout.addWidget(toolbar_widget)
        
        # === SPLITTER PRINCIPAL ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setSizes([300, 500, 400])  # Proporción inicial
        
        # Panel izquierdo: Lista de prompts
        prompts_panel = self._create_prompts_panel()
        main_splitter.addWidget(prompts_panel)
        
        # Panel central: Editor de prompts
        editor_panel = self._create_editor_panel()
        main_splitter.addWidget(editor_panel)
        
        # Panel derecho: AI Playground
        playground_panel = self._create_playground_panel()
        main_splitter.addWidget(playground_panel)
        
        main_layout.addWidget(main_splitter)
        
        # === STATUS BAR ===
        self._status_bar = self._create_status_bar()
        main_layout.addWidget(self._status_bar)
    
    def _create_toolbar(self) -> QWidget:
        """Crea la barra de herramientas superior"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setMaximumHeight(60)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # === BÚSQUEDA ===
        search_group = QGroupBox("Búsqueda")
        search_layout = QHBoxLayout(search_group)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar prompts...")
        self._search_input.setMinimumWidth(250)
        
        self._search_btn = QPushButton("🔍")
        self._search_btn.setMaximumWidth(40)
        self._search_btn.setToolTip("Buscar prompts")
        
        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._search_btn)
        
        # === FILTROS ===
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Categoría:"))
        self._category_combo = QComboBox()
        self._category_combo.setMinimumWidth(120)
        
        filter_layout.addWidget(self._category_combo)
        
        # === ACCIONES ===
        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        
        self._refresh_btn = QPushButton("🔄 Actualizar")
        self._new_prompt_btn = QPushButton("➕ Nuevo Prompt")
        self._save_btn = QPushButton("💾 Guardar")
        self._save_btn.setEnabled(False)
        
        actions_layout.addWidget(self._refresh_btn)
        actions_layout.addWidget(self._new_prompt_btn)
        actions_layout.addWidget(self._save_btn)
        
        # === LAYOUT TOOLBAR ===
        layout.addWidget(search_group)
        layout.addWidget(filter_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        # Indicador de carga
        self._loading_indicator = QProgressBar()
        self._loading_indicator.setMaximumWidth(200)
        self._loading_indicator.setMaximumHeight(20)
        self._loading_indicator.setVisible(False)
        self._loading_indicator.setRange(0, 0)  # Modo indeterminado
        
        layout.addWidget(self._loading_indicator)
        
        return toolbar
    
    def _create_prompts_panel(self) -> QWidget:
        """Crea el panel izquierdo con la lista de prompts"""
        panel = QGroupBox("Prompts Disponibles")
        layout = QVBoxLayout(panel)
        
        # Lista de prompts
        self._prompts_list = QListWidget()
        self._prompts_list.setMinimumWidth(250)
        self._prompts_list.setAlternatingRowColors(True)
        
        layout.addWidget(self._prompts_list)
        
        # Panel de versiones (colapsable)
        versions_group = QGroupBox("Versiones")
        versions_layout = QVBoxLayout(versions_group)
        
        self._versions_list = QListWidget()
        self._versions_list.setMaximumHeight(150)
        
        versions_layout.addWidget(self._versions_list)
        
        layout.addWidget(versions_group)
        
        return panel
    
    def _create_editor_panel(self) -> QWidget:
        """Crea el panel central con el editor de prompts"""
        panel = QGroupBox("Editor de Prompts")
        layout = QVBoxLayout(panel)
        
        # === METADATOS ===
        metadata_frame = QFrame()
        metadata_layout = QVBoxLayout(metadata_frame)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        
        # Nombre y versión
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre:"))
        self._prompt_name_label = QLabel("(Sin seleccionar)")
        self._prompt_name_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        name_layout.addWidget(self._prompt_name_label)
        name_layout.addStretch()
        
        self._version_label = QLabel("v1")
        self._version_label.setStyleSheet("color: #666; font-size: 12px;")
        name_layout.addWidget(self._version_label)
        
        metadata_layout.addLayout(name_layout)
        
        # Descripción y categoría
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Descripción:"))
        self._description_input = QLineEdit()
        self._description_input.setPlaceholderText("Descripción del prompt...")
        desc_layout.addWidget(self._description_input)
        
        desc_layout.addWidget(QLabel("Categoría:"))
        self._category_input = QComboBox()
        self._category_input.setEditable(True)
        self._category_input.setMinimumWidth(120)
        desc_layout.addWidget(self._category_input)
        
        metadata_layout.addLayout(desc_layout)
        
        layout.addWidget(metadata_frame)
        
        # === EDITOR DE TEMPLATE ===
        editor_tabs = QTabWidget()
        
        # Tab del editor principal
        self._prompt_editor = PromptEditorWidget()
        editor_tabs.addTab(self._prompt_editor, "📝 Template")
        
        # Tab de variables (JSON)
        variables_widget = QWidget()
        variables_layout = QVBoxLayout(variables_widget)
        
        variables_layout.addWidget(QLabel("Variables esperadas (JSON):"))
        self._variables_editor = QTextEdit()
        self._variables_editor.setPlaceholderText('{\n  "symbol": "string",\n  "price": "number"\n}')
        self._variables_editor.setMaximumHeight(150)
        variables_layout.addWidget(self._variables_editor)
        
        editor_tabs.addTab(variables_widget, "🔧 Variables")
        
        layout.addWidget(editor_tabs)
        
        # === ACCIONES DEL EDITOR ===
        editor_actions = QHBoxLayout()
        
        self._validate_btn = QPushButton("✅ Validar Sintaxis")
        self._preview_btn = QPushButton("👁️ Vista Previa")
        self._history_btn = QPushButton("📋 Historial")
        
        editor_actions.addWidget(self._validate_btn)
        editor_actions.addWidget(self._preview_btn)
        editor_actions.addWidget(self._history_btn)
        editor_actions.addStretch()
        
        self._unsaved_indicator = QLabel("●")
        self._unsaved_indicator.setStyleSheet("color: orange; font-size: 16px;")
        self._unsaved_indicator.setVisible(False)
        self._unsaved_indicator.setToolTip("Cambios sin guardar")
        
        editor_actions.addWidget(self._unsaved_indicator)
        
        layout.addLayout(editor_actions)
        
        return panel
    
    def _create_playground_panel(self) -> QWidget:
        """Crea el panel derecho con el AI Playground"""
        panel = QGroupBox("AI Playground")
        layout = QVBoxLayout(panel)
        
        # Widget especializado para playground
        self._playground = AIPlaygroundWidget()
        layout.addWidget(self._playground)
        
        return panel
    
    def _create_status_bar(self) -> QWidget:
        """Crea la barra de estado inferior"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_frame.setMaximumHeight(30)
        
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self._status_label = QLabel("Iniciando AI Studio...")
        self._status_label.setStyleSheet("color: #666;")
        
        layout.addWidget(self._status_label)
        layout.addStretch()
        
        # Métricas rápidas
        self._prompts_count_label = QLabel("0 prompts")
        self._prompts_count_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(self._prompts_count_label)
        
        return status_frame
    
    def _setup_connections(self):
        """Configura las conexiones entre señales y slots"""
        # === CONEXIONES CON VIEWMODEL ===
        
        # Estados
        self._viewmodel.loading_state_changed.connect(self._on_loading_state_changed)
        self._viewmodel.error_occurred.connect(self._on_error_occurred)
        self._viewmodel.status_message_changed.connect(self._on_status_message_changed)
        
        # Datos
        self._viewmodel.prompts_list_changed.connect(self._on_prompts_list_changed)
        self._viewmodel.current_prompt_changed.connect(self._on_current_prompt_changed)
        self._viewmodel.prompt_versions_changed.connect(self._on_prompt_versions_changed)
        self._viewmodel.categories_changed.connect(self._on_categories_changed)
        
        # Operaciones
        self._viewmodel.prompt_saved.connect(self._on_prompt_saved)
        self._viewmodel.prompt_rendered.connect(self._on_prompt_rendered)
        self._viewmodel.prompt_tested.connect(self._on_prompt_tested)
        self._viewmodel.search_results_changed.connect(self._on_search_results_changed)
        
        # === CONEXIONES DE UI ===
        
        # Toolbar
        self._search_btn.clicked.connect(self._on_search_clicked)
        self._search_input.returnPressed.connect(self._on_search_clicked)
        self._category_combo.currentTextChanged.connect(self._on_category_filter_changed)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        self._save_btn.clicked.connect(self._on_save_clicked)
        
        # Listas
        self._prompts_list.itemClicked.connect(self._on_prompt_selected)
        self._versions_list.itemClicked.connect(self._on_version_selected)
        
        # Editor
        self._prompt_editor.text_changed.connect(self._on_template_text_changed)
        self._description_input.textChanged.connect(
            lambda text: self._on_metadata_changed("description", text)
        )
        self._category_input.currentTextChanged.connect(
            lambda text: self._on_metadata_changed("category", text)
        )
        
        # Playground
        self._playground.test_requested.connect(self._on_test_requested)
        self._playground.render_requested.connect(self._on_render_requested)
    
    def _setup_styling(self):
        """Configura estilos específicos de la vista"""
        # Aplicar tema actual
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
            QPushButton:pressed {
                background-color: #1976D2;
                color: white;
            }
        """)
    
    # === INICIALIZACIÓN ASÍNCRONA ===
    
    def _initialize_async(self):
        """Inicialización asíncrona del componente"""
        try:
            # Usar QTimer para ejecutar async
            async def init():
                await self._viewmodel.initialize()
                self._is_initialized = True
            
            # Ejecutar inicialización
            import asyncio
            if asyncio.get_event_loop().is_running():
                asyncio.create_task(init())
            else:
                asyncio.run(init())
                
        except Exception as e:
            logger.error(f"Error en inicialización asíncrona: {str(e)}")
            self._on_error_occurred(f"Error inicializando: {str(e)}")
    
    # === SLOTS DE VIEWMODEL ===
    
    @pyqtSlot(bool)
    def _on_loading_state_changed(self, is_loading: bool):
        """Maneja cambios en el estado de carga"""
        self._loading_indicator.setVisible(is_loading)
        
        # Deshabilitar controles durante carga
        self._search_btn.setEnabled(not is_loading)
        self._refresh_btn.setEnabled(not is_loading)
        self._save_btn.setEnabled(not is_loading and self._viewmodel.has_unsaved_changes)
    
    @pyqtSlot(str)
    def _on_error_occurred(self, error_message: str):
        """Muestra errores al usuario"""
        QMessageBox.warning(self, "Error - AI Studio", error_message)
        logger.warning(f"Error mostrado al usuario: {error_message}")
    
    @pyqtSlot(str)
    def _on_status_message_changed(self, message: str):
        """Actualiza mensaje de estado"""
        self._status_label.setText(message)
    
    @pyqtSlot(list)
    def _on_prompts_list_changed(self, prompts_data: list):
        """Actualiza la lista de prompts"""
        self._prompts_list.clear()
        
        for prompt_dict in prompts_data:
            item = QListWidgetItem(prompt_dict["name"])
            item.setData(Qt.ItemDataRole.UserRole, prompt_dict)
            
            # Tooltip con información
            tooltip = f"Categoría: {prompt_dict.get('category', 'N/A')}\n"
            tooltip += f"Versión: v{prompt_dict.get('version', 1)}\n"
            tooltip += f"Descripción: {prompt_dict.get('description', 'Sin descripción')}"
            item.setToolTip(tooltip)
            
            self._prompts_list.addItem(item)
        
        # Actualizar contador
        self._prompts_count_label.setText(f"{len(prompts_data)} prompts")
        
        logger.debug(f"Lista de prompts actualizada: {len(prompts_data)} items")
    
    @pyqtSlot(dict)
    def _on_current_prompt_changed(self, prompt_data: dict):
        """Actualiza la UI cuando cambia el prompt seleccionado"""
        if not prompt_data:
            return
        
        self._current_prompt_name = prompt_data["name"]
        
        # Actualizar metadatos
        self._prompt_name_label.setText(prompt_data["name"])
        self._version_label.setText(f"v{prompt_data.get('version', 1)}")
        self._description_input.setText(prompt_data.get("description", ""))
        
        # Actualizar categoría en combo
        category = prompt_data.get("category", "general")
        index = self._category_input.findText(category)
        if index >= 0:
            self._category_input.setCurrentIndex(index)
        else:
            self._category_input.setCurrentText(category)
        
        # Actualizar editor
        self._prompt_editor.set_text(prompt_data.get("template", ""))
        
        # Actualizar variables
        variables = prompt_data.get("variables", {})
        import json
        self._variables_editor.setPlainText(json.dumps(variables, indent=2))
        
        # Actualizar playground
        self._playground.set_current_prompt(prompt_data)
        
        # Resetear indicador de cambios
        self._unsaved_indicator.setVisible(False)
        
        logger.debug(f"Prompt '{prompt_data['name']}' cargado en editor")
    
    @pyqtSlot(list)
    def _on_prompt_versions_changed(self, versions_data: list):
        """Actualiza la lista de versiones"""
        self._versions_list.clear()
        
        for version_dict in versions_data:
            version_num = version_dict["version"]
            is_active = version_dict.get("is_active", False)
            created_at = version_dict.get("created_at", "")
            
            text = f"v{version_num}"
            if is_active:
                text += " (activa)"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, version_dict)
            
            # Styling para versión activa
            if is_active:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            # Tooltip
            tooltip = f"Versión: {version_num}\n"
            tooltip += f"Creada: {created_at}\n"
            tooltip += f"Activa: {'Sí' if is_active else 'No'}"
            item.setToolTip(tooltip)
            
            self._versions_list.addItem(item)
        
        logger.debug(f"Versiones actualizadas: {len(versions_data)} items")
    
    @pyqtSlot(list)
    def _on_categories_changed(self, categories: list):
        """Actualiza los combos de categorías"""
        # Combo de filtro
        current_filter = self._category_combo.currentText()
        self._category_combo.clear()
        self._category_combo.addItem("Todas las categorías", "all")
        for cat in categories:
            self._category_combo.addItem(cat, cat)
        
        # Restaurar selección
        index = self._category_combo.findData(current_filter)
        if index >= 0:
            self._category_combo.setCurrentIndex(index)
        
        # Combo de editor
        current_cat = self._category_input.currentText()
        self._category_input.clear()
        self._category_input.addItems(categories)
        self._category_input.setCurrentText(current_cat)
    
    @pyqtSlot(str)
    def _on_prompt_saved(self, success_message: str):
        """Maneja confirmación de guardado exitoso"""
        self._unsaved_indicator.setVisible(False)
        self._save_btn.setEnabled(False)
        
        # Mostrar mensaje temporal
        QMessageBox.information(self, "Éxito", success_message)
    
    @pyqtSlot(dict)
    def _on_prompt_rendered(self, render_result: dict):
        """Maneja resultado de renderizado de prompt"""
        self._playground.set_render_result(render_result)
    
    @pyqtSlot(dict)
    def _on_prompt_tested(self, test_result: dict):
        """Maneja resultado de test con IA"""
        self._playground.set_test_result(test_result)
    
    @pyqtSlot(list)
    def _on_search_results_changed(self, results: list):
        """Actualiza resultados de búsqueda"""
        # Actualizar lista con resultados filtrados
        self._on_prompts_list_changed(results)
    
    # === SLOTS DE UI ===
    
    @pyqtSlot()
    def _on_search_clicked(self):
        """Ejecuta búsqueda de prompts"""
        query = self._search_input.text().strip()
        
        async def search():
            await self._viewmodel.search_prompts(query)
        
        self._execute_async(search)
    
    @pyqtSlot(str)
    def _on_category_filter_changed(self, category: str):
        """Filtra por categoría seleccionada"""
        if category == "Todas las categorías":
            category = "all"
        self._viewmodel.filter_by_category(category)
    
    @pyqtSlot()
    def _on_refresh_clicked(self):
        """Actualiza la lista de prompts"""
        async def refresh():
            await self._viewmodel.refresh_prompts_list()
        
        self._execute_async(refresh)
    
    @pyqtSlot()
    def _on_save_clicked(self):
        """Guarda el prompt actual"""
        async def save():
            await self._viewmodel.save_current_prompt()
        
        self._execute_async(save)
    
    @pyqtSlot(QListWidgetItem)
    def _on_prompt_selected(self, item: QListWidgetItem):
        """Maneja selección de prompt"""
        prompt_data = item.data(Qt.ItemDataRole.UserRole)
        if prompt_data:
            async def select():
                await self._viewmodel.select_prompt(prompt_data["name"])
            
            self._execute_async(select)
    
    @pyqtSlot(QListWidgetItem)
    def _on_version_selected(self, item: QListWidgetItem):
        """Maneja selección de versión"""
        version_data = item.data(Qt.ItemDataRole.UserRole)
        if version_data:
            version = version_data["version"]
            
            async def load_version():
                await self._viewmodel.load_prompt_version(version)
            
            self._execute_async(load_version)
    
    @pyqtSlot(str)
    def _on_template_text_changed(self, text: str):
        """Maneja cambios en el texto del template"""
        self._viewmodel.update_template_text(text)
        self._unsaved_indicator.setVisible(self._viewmodel.has_unsaved_changes)
        self._save_btn.setEnabled(self._viewmodel.has_unsaved_changes)
    
    def _on_metadata_changed(self, field: str, value: str):
        """Maneja cambios en metadatos"""
        self._viewmodel.update_prompt_metadata(field, value)
        self._unsaved_indicator.setVisible(self._viewmodel.has_unsaved_changes)
        self._save_btn.setEnabled(self._viewmodel.has_unsaved_changes)
    
    @pyqtSlot(dict)
    def _on_test_requested(self, variables: dict):
        """Maneja solicitud de test desde playground"""
        async def test():
            await self._viewmodel.test_prompt_with_variables(variables)
        
        self._execute_async(test)
    
    @pyqtSlot(dict)
    def _on_render_requested(self, variables: dict):
        """Maneja solicitud de renderizado desde playground"""
        async def render():
            await self._viewmodel.render_prompt_only(variables)
        
        self._execute_async(render)
    
    # === UTILIDADES ===
    
    def _execute_async(self, coro):
        """Ejecuta una corrutina asíncrona"""
        try:
            import asyncio
            if asyncio.get_event_loop().is_running():
                asyncio.create_task(coro())
            else:
                asyncio.run(coro())
        except Exception as e:
            logger.error(f"Error ejecutando operación asíncrona: {str(e)}")
            self._on_error_occurred(f"Error: {str(e)}")
    
    # === CLEANUP ===
    
    def closeEvent(self, event):
        """Limpia recursos al cerrar"""
        if self._viewmodel:
            self._viewmodel.cleanup()
        super().closeEvent(event)
