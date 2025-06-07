# src/ultibot_ui/views/strategy_management_view.py
"""
Módulo para la vista de gestión de estrategias.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QTableView, QHeaderView, QAbstractItemView, QApplication,
                             QStyle, QMessageBox, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal, QModelIndex, QThread
from PyQt5.QtGui import QCloseEvent
from typing import Any, Optional, List

import asyncio

from src.shared.data_types import AiStrategyConfiguration
from ..services.api_client import UltiBotAPIClient, APIError
from ..workers import ApiWorker

# NOTA: Se han eliminado los enums y delegados que no se correspondían con el modelo de datos actual.

class StrategyTableModel(QAbstractTableModel):
    def __init__(self, data: List[AiStrategyConfiguration] | None = None, parent=None):
        super().__init__(parent)
        self._data = data or []
        # Cabeceras actualizadas para reflejar el modelo AiStrategyConfiguration
        self._headers = [
            "Nombre", "Pares Aplicables", "Modelo Gemini"
        ]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> QVariant:
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        strategy = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return QVariant(strategy.name)
            elif col == 1:
                pairs = strategy.appliesToPairs or []
                return QVariant(", ".join(pairs) if pairs else "Todos")
            elif col == 2:
                return QVariant(strategy.geminiModelName or "No especificado")
        
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> QVariant:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return QVariant(self._headers[section])
        return QVariant()

    def update_data(self, new_data: List[AiStrategyConfiguration]):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class StrategyManagementView(QWidget):
    _strategies_loaded_signal = pyqtSignal(object) 
    _strategies_error_signal = pyqtSignal(str)

    def __init__(self, backend_base_url: Optional[str] = None, qasync_loop=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Estrategias de IA")
        self.backend_base_url = backend_base_url
        self.qasync_loop = qasync_loop
        self._all_strategies_data: List[AiStrategyConfiguration] = []
        self.active_threads: List[QThread] = []
        
        if not self.qasync_loop:
            try:
                self.qasync_loop = asyncio.get_event_loop()
            except RuntimeError:
                 print("ADVERTENCIA CRÍTICA: StrategyManagementView no hay bucle de eventos asyncio corriendo.")

        self._init_ui()
        self._connect_signals()
        self.cargar_estrategias()

    def _on_strategias_cargadas(self, strategies_list: List[AiStrategyConfiguration]):
        self._handle_strategies_loaded(strategies_list)

    def _on_strategias_error(self, error_message: str):
        self._show_load_error_message(error_message)

    def cargar_estrategias(self):
        if not self.backend_base_url or not self.qasync_loop:
            error_msg = "No se puede cargar estrategias: URL del backend o bucle de eventos no disponible."
            print(f"StrategyManagementView: {error_msg}")
            self._strategies_error_signal.emit(error_msg)
            return

        async def load_strategies_coro(api_client: UltiBotAPIClient):
            # Fallback: obtener config de usuario y extraer las estrategias
            user_config = await api_client.get_user_configuration()
            return user_config.aiStrategyConfigurations or []

        worker = ApiWorker(coroutine_factory=load_strategies_coro, base_url=self.backend_base_url)
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(self._strategies_loaded_signal)
        worker.error_occurred.connect(self._strategies_error_signal)
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        thread.start()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Panel de Gestión de Estrategias de IA")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre...")
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)

        self.strategies_table = QTableView()
        self.table_model = StrategyTableModel([])
        self.strategies_table.setModel(self.table_model)
        self.strategies_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.strategies_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        header = self.strategies_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.strategies_table)

        buttons_layout = QHBoxLayout()
        self.create_strategy_button = QPushButton("Crear Nueva")
        self.create_strategy_button.clicked.connect(self._create_strategy_action)
        buttons_layout.addWidget(self.create_strategy_button)

        self.duplicate_strategy_button = QPushButton("Duplicar Seleccionada")
        self.duplicate_strategy_button.clicked.connect(self._duplicate_strategy_action)
        buttons_layout.addWidget(self.duplicate_strategy_button)

        self.delete_strategy_button = QPushButton("Eliminar Seleccionada")
        self.delete_strategy_button.clicked.connect(self._delete_strategy_action)
        buttons_layout.addWidget(self.delete_strategy_button)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _get_selected_strategy(self) -> Optional[AiStrategyConfiguration]:
        selection_model = self.strategies_table.selectionModel()
        if not selection_model or not selection_model.hasSelection():
            QMessageBox.information(self, "Información", "Por favor, seleccione una estrategia de la lista.")
            return None
        
        selected_row = selection_model.selectedRows()[0].row()
        if hasattr(self.table_model, '_data') and 0 <= selected_row < len(self.table_model._data):
            return self.table_model._data[selected_row]
        return None

    def _connect_signals(self):
        self._strategies_loaded_signal.connect(self._on_strategias_cargadas)
        self._strategies_error_signal.connect(self._on_strategias_error)
        self.search_input.textChanged.connect(self._filter_strategies)
        self.strategies_table.doubleClicked.connect(self._on_table_double_clicked)

    def _on_table_double_clicked(self, index: QModelIndex):
        if index.isValid():
            row = index.row()
            if hasattr(self.table_model, '_data') and 0 <= row < len(self.table_model._data):
                self._edit_strategy_action(self.table_model._data[row])

    def _handle_strategies_loaded(self, strategies_list: List[AiStrategyConfiguration]):
        self._all_strategies_data = strategies_list
        self._filter_strategies()

    def _show_load_error_message(self, error_message: str):
        QMessageBox.critical(self, "Error al Cargar Estrategias", f"No se pudieron cargar las estrategias: {error_message}")

    def _create_strategy_action(self, strategy_to_duplicate: Optional[AiStrategyConfiguration] = None):
        from ..dialogs.strategy_config_dialog import StrategyConfigDialog
        if not self.backend_base_url:
            QMessageBox.warning(self, "API no disponible", "No se puede crear/duplicar una estrategia.")
            return

        dialog = StrategyConfigDialog(api_client=UltiBotAPIClient(self.backend_base_url),
                                     strategy_config=strategy_to_duplicate,
                                     is_duplicating=bool(strategy_to_duplicate),
                                     parent=self)
        if dialog.exec_():
            self.cargar_estrategias()

    def _duplicate_strategy_action(self):
        selected_strategy = self._get_selected_strategy()
        if selected_strategy:
            self._create_strategy_action(strategy_to_duplicate=selected_strategy)

    def _delete_strategy_action(self):
        selected_strategy = self._get_selected_strategy()
        if not selected_strategy or not selected_strategy.id:
            return

        reply = QMessageBox.question(self, "Confirmar Eliminación",
                                     f"¿Eliminar la estrategia '{selected_strategy.name}'?\nEsta acción no se puede deshacer.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            asyncio.create_task(self._delete_strategy_backend(str(selected_strategy.id)))

    async def _delete_strategy_backend(self, strategy_id: str):
        if not self.backend_base_url: return
        try:
            api_client = UltiBotAPIClient(self.backend_base_url)
            # Se asume que el cliente API necesita un método para eliminar/actualizar estrategias.
            # Esto probablemente requiera una actualización del lado del backend también.
            # Por ahora, se asume que una función `delete_strategy` podría existir.
            if hasattr(api_client, 'delete_strategy'):
                await api_client.delete_strategy(strategy_id)
                QMessageBox.information(self, "Éxito", f"Estrategia '{strategy_id}' eliminada.")
                self.cargar_estrategias()
            else:
                 QMessageBox.critical(self, "Funcionalidad no implementada", "El cliente API no tiene el método 'delete_strategy'.")

        except (APIError, Exception) as e:
            msg = e.message if isinstance(e, APIError) else str(e)
            QMessageBox.critical(self, "Error al Eliminar", f"No se pudo eliminar la estrategia: {msg}")

    def _edit_strategy_action(self, strategy_config: AiStrategyConfiguration):
        self._create_strategy_action(strategy_to_duplicate=strategy_config)

    def _filter_strategies(self):
        search_text = self.search_input.text().strip().lower()
        
        if not search_text:
            filtered = self._all_strategies_data
        else:
            filtered = [
                strat for strat in self._all_strategies_data
                if search_text in strat.name.lower()
            ]
        self.table_model.update_data(filtered)

    def closeEvent(self, event: QCloseEvent):
        for thread in self.active_threads[:]:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
        super().closeEvent(event)
