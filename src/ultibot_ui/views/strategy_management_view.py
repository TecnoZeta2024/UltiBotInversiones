# src/ultibot_ui/views/strategy_management_view.py
"""
Módulo para la vista de gestión de estrategias.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QTableView, QHeaderView, QAbstractItemView, QApplication,
                             QStyle, QMessageBox, QLineEdit, QComboBox, QHBoxLayout, # Añadir QStyle aquí
                              QStyledItemDelegate, QCheckBox, QStyleOptionButton)
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignal, QModelIndex, QEvent, QThread
from PyQt5.QtGui import QPainter, QCloseEvent # Importar QCloseEvent y QThread
from PyQt5.QtWidgets import QStyleOptionButton, QStyle
from typing import Any, Optional

from datetime import datetime
from enum import Enum
import asyncio # Importar asyncio para _schedule_load_strategies

from ..services.api_client import UltiBotAPIClient, APIError

# Definiciones provisionales hasta que estén disponibles globalmente
class BaseStrategyType(Enum):
    SCALPING = "Scalping"
    DAY_TRADING = "DayTrading"
    ARBITRAGE_SIMPLE = "ArbitrageSimple"

class TradingStrategyConfig: # Provisional Placeholder
    def __init__(self, configName, baseStrategyType, isActivePaperMode, isActiveRealMode, applicabilityRules, lastModified, id="some_id"):
        self.id = id
        self.configName = configName
        self.baseStrategyType = baseStrategyType
        self.isActivePaperMode = isActivePaperMode
        self.isActiveRealMode = isActiveRealMode
        self.applicabilityRules = applicabilityRules
        self.lastModified = lastModified

class StrategyTableModel(QAbstractTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = [
            "Nombre Configuración", "Tipo Base", "Estado Paper", 
            "Estado Real", "Pares Aplicables", "Última Modificación"
        ]

    def rowCount(self, parent=QVariant()):
        return len(self._data)

    def columnCount(self, parent=QVariant()):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        col = index.column()
        strategy = self._data[row]
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return QVariant(getattr(strategy, 'configName', 'N/A'))
            elif col == 1:
                base_type = getattr(strategy, 'baseStrategyType', 'N/A')
                return QVariant(base_type.value if isinstance(base_type, Enum) else str(base_type))
            elif col == 2 or col == 3:
                return QVariant()
            elif col == 4:
                pairs = getattr(strategy, 'applicabilityRules', {}).get('explicitPairs', [])
                return QVariant(", ".join(pairs) if pairs else "Todos/Dinámico")
            elif col == 5:
                last_mod = getattr(strategy, 'lastModified', None)
                if isinstance(last_mod, datetime):
                    return QVariant(last_mod.strftime("%Y-%m-%d %H:%M"))
                elif isinstance(last_mod, str):
                    return QVariant(last_mod)
                return QVariant('N/A')
        if role == Qt.ItemDataRole.CheckStateRole:
            if col == 2:
                return Qt.CheckState.Checked if getattr(strategy, 'isActivePaperMode', False) else Qt.CheckState.Unchecked
            elif col == 3:
                return Qt.CheckState.Checked if getattr(strategy, 'isActiveRealMode', False) else Qt.CheckState.Unchecked
        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        strategy = self._data[row]
        if role == Qt.ItemDataRole.CheckStateRole:
            if col == 2:
                setattr(strategy, 'isActivePaperMode', value == Qt.CheckState.Checked)
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.DisplayRole])
                return True
            elif col == 3:
                setattr(strategy, 'isActiveRealMode', value == Qt.CheckState.Checked)
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.DisplayRole])
                return True
        return super().setData(index, value, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.column() == 2 or index.column() == 3:
            flags |= Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        return flags

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return QVariant(self._headers[section])
        return QVariant()

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class ToggleDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        model = index.model()
        if not model:
            super().paint(painter, option, index)
            return

        check_state = model.data(index, Qt.ItemDataRole.CheckStateRole)
        check_box_option = QStyleOptionButton()
        check_box_option.rect = option.rect
        widget = option.widget
        
        # Usar QApplication.style() como fallback si widget o widget.style() es None
        style = widget.style() if widget and hasattr(widget, 'style') and widget.style() is not None else QApplication.style()
        if not style: # Si incluso QApplication.style() fuera None (muy improbable)
            super().paint(painter, option, index)
            return

        indicator_rect = style.subElementRect(QStyle.SubElement.SE_CheckBoxIndicator, check_box_option, widget)
        cell_center_x = option.rect.left() + option.rect.width() / 2
        cell_center_y = option.rect.top() + option.rect.height() / 2
        check_box_option.rect.moveLeft(int(cell_center_x - indicator_rect.width() / 2))
        check_box_option.rect.moveTop(int(cell_center_y - indicator_rect.height() / 2))
        check_box_option.state = QStyle.StateFlag.State_Enabled
        if check_state == Qt.CheckState.Checked:
            check_box_option.state |= QStyle.StateFlag.State_On
        else:
            check_box_option.state |= QStyle.StateFlag.State_Off
        
        style.drawControl(QStyle.ControlElement.CE_CheckBox, check_box_option, painter)

    def editorEvent(self, event, model, option, index: QModelIndex) -> bool:
        # Solo manejar eventos de mouse release y solo si es un QMouseEvent
        from PyQt5.QtGui import QMouseEvent
        if event is not None and hasattr(event, 'type'):
            if event.type() == QEvent.Type.MouseButtonRelease:
                if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                    # index.model() puede ser None en casos muy raros, proteger
                    model_obj = index.model() if hasattr(index, 'model') else None
                    if model_obj is not None and hasattr(model_obj, 'data'):
                        current_state = model_obj.data(index, Qt.ItemDataRole.CheckStateRole)
                        new_state = Qt.CheckState.Checked if current_state == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
                        if model is not None and hasattr(model, 'setData'):
                            return model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
        return super().editorEvent(event, model, option, index)

    # No necesitamos createEditor ni setEditorData si editorEvent y paint hacen todo.
    # Si quisiéramos un QCheckBox real como editor (que aparece al hacer doble clic),
    # entonces necesitaríamos implementar createEditor, setEditorData, y setModelData.
    # Por ahora, el método paint y editorEvent es más directo para un toggle visual.

class StrategyManagementView(QWidget):
    strategy_data_loaded = pyqtSignal(list) 
    strategy_load_failed = pyqtSignal(str) 
    
    # Nuevas señales para el patrón ApiWorker + Future
    _strategies_loaded_signal = pyqtSignal(object) 
    _strategies_error_signal = pyqtSignal(object)  

    def __init__(self, api_client=None, qasync_loop=None, parent=None): # Añadir qasync_loop
        super().__init__(parent)
        self.setWindowTitle("Gestión de Estrategias")
        self.api_client = api_client
        self.qasync_loop = qasync_loop # Guardar el loop
        self._all_strategies_data = [] # Almacenar todas las estrategias
        self.active_threads = [] # Inicializar active_threads
        
        if self.api_client is None:
            print("ADVERTENCIA: StrategyManagementView inicializado sin api_client.")
        if self.qasync_loop is None:
            # Intentar obtener el loop de asyncio si no se pasó, aunque es mejor pasarlo.
            try:
                self.qasync_loop = asyncio.get_event_loop()
                if self.qasync_loop is None: # Aún podría ser None si no hay un loop corriendo
                     print("ADVERTENCIA CRÍTICA: StrategyManagementView no pudo obtener qasync_loop.")
            except RuntimeError: # No hay loop de eventos corriendo
                 print("ADVERTENCIA CRÍTICA: StrategyManagementView no hay bucle de eventos asyncio corriendo y no se pasó qasync_loop.")
                 self.qasync_loop = None # Asegurar que es None

        self._init_ui()
        self._connect_signals()
        # self._schedule_load_strategies() # Reemplazado por la llamada directa a cargar_estrategias
        self.cargar_estrategias() # Llamar al nuevo método de carga

    def _on_strategias_cargadas(self, strategies_list):
        """Maneja la señal de estrategias cargadas exitosamente."""
        self._handle_strategies_loaded(strategies_list)
        # Aquí también se podría llamar a _plot_strategies si fuera necesario

    def _on_strategias_error(self, error_message):
        """Maneja la señal de error en la carga de estrategias."""
        self._show_load_error_message(error_message)

    def cargar_estrategias(self):
        """
        Carga las estrategias usando ApiWorker y emite señales apropiadas.
        """
        if not self.api_client:
            print("StrategyManagementView: No se puede cargar estrategias, api_client no está disponible.")
            self._strategies_error_signal.emit("API client no disponible.")
            return
        
        if self.qasync_loop is None:
            error_msg = "StrategyManagementView: qasync_loop no está disponible. No se pueden cargar estrategias."
            print(error_msg)
            self._strategies_error_signal.emit(error_msg)
            return

        from ..main import ApiWorker # Importación local para evitar circularidad a nivel de módulo
        # from PyQt5.QtCore import QThread # Ya importado arriba

        async def load_strategies_coro():
            """Corutina interna para cargar estrategias y devolver datos o lanzar error."""
            try:
                if self.api_client is None: # Doble verificación por si acaso
                    raise APIError("API client no disponible en corutina.")
                
                strategies_data_raw = await self.api_client.get_strategies()
                strategies_list = []
                if not isinstance(strategies_data_raw, list):
                    # Registrar el error antes de lanzar la excepción
                    error_msg = f"Respuesta inesperada del servidor al obtener estrategias: {type(strategies_data_raw)}"
                    print(f"StrategyManagementView: {error_msg}") # Usar print o logger si está configurado
                    raise APIError(error_msg)

                for item_data in strategies_data_raw:
                    if not isinstance(item_data, dict):
                        print(f"Advertencia: Se encontró un elemento no diccionario en la respuesta de estrategias: {item_data}")
                        continue

                    last_modified_raw = item_data.get('lastModified')
                    last_modified_dt = None
                    if isinstance(last_modified_raw, str):
                        try:
                            if last_modified_raw.endswith('Z'):
                                last_modified_dt = datetime.fromisoformat(last_modified_raw.replace('Z', '+00:00'))
                            else:
                                last_modified_dt = datetime.fromisoformat(last_modified_raw)
                        except ValueError:
                            try:
                                last_modified_dt = datetime.strptime(last_modified_raw, "%Y-%m-%d %H:%M:%S.%f")
                            except ValueError:
                                try:
                                    last_modified_dt = datetime.strptime(last_modified_raw, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    print(f"Advertencia: No se pudo parsear la fecha '{last_modified_raw}'.")
                    elif isinstance(last_modified_raw, datetime):
                        last_modified_dt = last_modified_raw

                    base_strategy_type_raw = item_data.get('baseStrategyType')
                    base_strategy_type_enum = None
                    if isinstance(base_strategy_type_raw, str):
                        try:
                            base_strategy_type_enum = BaseStrategyType(base_strategy_type_raw)
                        except ValueError:
                            print(f"Advertencia: Tipo de estrategia base desconocido '{base_strategy_type_raw}'.")
                            base_strategy_type_enum = base_strategy_type_raw # Mantener como string si no es un Enum conocido
                    elif isinstance(base_strategy_type_raw, BaseStrategyType):
                        base_strategy_type_enum = base_strategy_type_raw
                    
                    strategy_id = item_data.get('id')
                    if strategy_id is None: # Asegurar que el ID no sea None
                        strategy_id = f"placeholder_id_{item_data.get('configName', 'unknown')}"
                    else:
                        strategy_id = str(strategy_id)

                    strategies_list.append(
                        TradingStrategyConfig(
                            id=strategy_id,
                            configName=item_data.get('configName', 'N/A'),
                            baseStrategyType=base_strategy_type_enum,
                            isActivePaperMode=item_data.get('isActivePaperMode', False),
                            isActiveRealMode=item_data.get('isActiveRealMode', False),
                            applicabilityRules=item_data.get('applicabilityRules', {}),
                            lastModified=last_modified_dt
                        )
                    )
                return strategies_list
            except Exception as e:
                # Registrar el error antes de relanzarlo para que ApiWorker lo maneje
                error_msg = f"Error en load_strategies_coro: {type(e).__name__} - {e}"
                print(f"StrategyManagementView: {error_msg}") # Usar print o logger
                # QMessageBox.critical(self, "Error Interno Corutina", error_msg) # No mostrar QMessageBox desde aquí
                raise # Relanzar la excepción para que ApiWorker la capture

        # Crear y iniciar el ApiWorker
        worker = ApiWorker(coroutine_factory=load_strategies_coro, qasync_loop=self.qasync_loop) # Usar coroutine_factory
        
        thread = QThread() # Crear un QThread explícitamente
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        # Conectar señales del worker a las señales de la vista
        worker.result_ready.connect(self._strategies_loaded_signal) # Usar result_ready
        worker.error_occurred.connect(self._strategies_error_signal)   # Usar error_occurred
        
        # Conectar el inicio del thread al método run del worker
        thread.started.connect(worker.run)

        # Limpieza: cuando el worker termina (éxito o error), el thread debe detenerse.
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)

        # Limpieza: cuando el thread termina, debe ser marcado para eliminación.
        # Y el worker también, después de que haya emitido su señal.
        thread.finished.connect(thread.deleteLater)
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        
        # Remover el thread de la lista de activos cuando realmente finalice
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        
        thread.start() # Iniciar el QThread, no el worker directamente

    def _init_ui(self):
        layout = QVBoxLayout(self)
        title_label = QLabel("Panel de Gestión de Estrategias")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Filtros y búsqueda
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre...")
        filter_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Todos los Tipos", None) 
        for strategy_type in BaseStrategyType:
            self.filter_combo.addItem(strategy_type.value, strategy_type)
        
        filter_layout.addWidget(self.filter_combo)
        layout.addLayout(filter_layout)

        self.strategies_table = QTableView()
        self.table_model = StrategyTableModel([])
        self.strategies_table.setModel(self.table_model)
        self.strategies_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Permitir que el delegado maneje la edición (clic para toggle)
        self.strategies_table.setEditTriggers(QAbstractItemView.SelectedClicked | QAbstractItemView.DoubleClicked) # Revertir
        
        header = self.strategies_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(QHeaderView.Stretch) # Revertir
        else:
            # Considerar loggear una advertencia si es apropiado para la aplicación
            print("Advertencia: Horizontal header no encontrado para strategies_table.")


        # Asignar el delegado a las columnas de estado
        # Usamos la misma instancia de delegado si no tiene estado propio, o diferentes si es necesario.
        toggle_delegate = ToggleDelegate(self) # parent es la vista
        self.strategies_table.setItemDelegateForColumn(2, toggle_delegate) # Columna Estado Paper
        self.strategies_table.setItemDelegateForColumn(3, toggle_delegate) # Columna Estado Real

        layout.addWidget(self.strategies_table)

        buttons_layout = QHBoxLayout() # Cambiado a QHBoxLayout para botones en línea
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

    def _get_selected_strategy(self) -> Any | None: # TradingStrategyConfig
        selection_model = self.strategies_table.selectionModel()
        if not selection_model:
            QMessageBox.warning(self, "Error", "El modelo de selección de la tabla no está disponible.")
            return None

        selected_indexes = selection_model.selectedRows()
        if not selected_indexes:
            QMessageBox.information(self, "Información", "Por favor, seleccione una estrategia de la lista.")
            return None
        
        selected_row = selected_indexes[0].row()
        if 0 <= selected_row < len(self.table_model._data):
            return self.table_model._data[selected_row]
        return None

    def _connect_signals(self):
        # Conexiones para el nuevo patrón ApiWorker + Future
        self._strategies_loaded_signal.connect(self._on_strategias_cargadas)
        self._strategies_error_signal.connect(self._on_strategias_error)
        
        # Las señales originales strategy_data_loaded y strategy_load_failed ya no se usan directamente
        # para iniciar la carga, sino que son reemplazadas por el flujo de _strategies_loaded_signal y _strategies_error_signal.
        # Si _handle_strategies_loaded y _show_load_error_message tienen lógica UI útil,
        # _on_strategias_cargadas y _on_strategias_error deberían invocarla o replicarla.
        # Por ahora, las comentamos para evitar doble manejo si _on_strategias_cargadas/_error ya hacen todo.
        # self.strategy_data_loaded.connect(self._handle_strategies_loaded)
        # self.strategy_load_failed.connect(self._show_load_error_message)

        self.search_input.textChanged.connect(self._filter_strategies)
        self.filter_combo.currentIndexChanged.connect(self._filter_strategies)
        self.strategies_table.doubleClicked.connect(self._on_table_double_clicked)
        
        if not hasattr(self, '_dataChanged_connected_for_activation'):
            self.table_model.dataChanged.connect(self._handle_strategy_activation_change)
            self._dataChanged_connected_for_activation = True


    def _on_table_double_clicked(self, index):
        """
        Slot para manejar el doble clic en la tabla de estrategias.
        Abre el diálogo de edición para la estrategia seleccionada.
        """
        if not index.isValid():
            return
        row = index.row()
        if 0 <= row < len(self.table_model._data):
            strategy_config = self.table_model._data[row]
            self._edit_strategy_action(strategy_config)

    def _handle_strategy_activation_change(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list):
        if not topLeft.isValid() or not self.api_client:
            return

        # Solo nos interesan los cambios en las columnas de activación y del rol CheckStateRole
        if Qt.ItemDataRole.CheckStateRole not in roles:
            return

        col = topLeft.column()
        if col not in [2, 3]: # Columna 2: Estado Paper, Columna 3: Estado Real
            return

        row = topLeft.row()
        strategy = self.table_model._data[row] # Acceso directo a los datos del modelo
        strategy_id = getattr(strategy, 'id', None)
        if not strategy_id:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID de la estrategia.")
            # Considerar revertir el cambio visual si el ID no está
            self._schedule_load_strategies() # Recargar para asegurar consistencia visual
            return

        mode = "paper" if col == 2 else "real"
        is_active = getattr(strategy, 'isActivePaperMode' if mode == "paper" else 'isActiveRealMode', False)

        # Subtask 3.3: Diálogo de confirmación para Modo Real
        if mode == "real" and is_active: # Solo al intentar activar en modo real
            confirm_dialog = QMessageBox(self)
            confirm_dialog.setIcon(QMessageBox.Warning)
            confirm_dialog.setWindowTitle("Confirmar Activación en Modo Real")
            confirm_dialog.setText(
                f"¿Está seguro de que desea activar la estrategia '{getattr(strategy, 'configName', 'N/A')}' en Modo Real?\n"
                "Esto podría ejecutar operaciones con fondos reales."
            )
            confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm_dialog.setDefaultButton(QMessageBox.No)
            
            if confirm_dialog.exec_() == QMessageBox.No:
                # Revertir el cambio visual en el modelo si el usuario cancela
                original_state = not is_active
                if mode == "paper":
                    strategy.isActivePaperMode = original_state
                else:
                    strategy.isActiveRealMode = original_state
                # Emitir dataChanged para que la UI se actualice al estado original
                self.table_model.dataChanged.emit(topLeft, topLeft, [Qt.ItemDataRole.CheckStateRole])
                return

        print(f"Intentando cambiar activación para strategy_id: {strategy_id}, mode: {mode}, active: {is_active}")
        asyncio.create_task(self._update_strategy_activation_backend(strategy_id, mode, is_active, topLeft))

    async def _update_strategy_activation_backend(self, strategy_id: str, mode: str, active: bool, index_to_revert: QModelIndex):
        if not self.api_client:
            return
        try:
            await self.api_client.update_strategy_activation_status(strategy_id, mode, active)
            QMessageBox.information(self, "Éxito", f"Estrategia '{strategy_id}' actualizada en modo '{mode}'.")
            # La UI ya se actualizó optimistamente. Si hay error, se revierte.
            # Podríamos recargar todo, pero es más eficiente así.
            # self._schedule_load_strategies() # Opcional: recargar todo para asegurar consistencia total
        except APIError as e:
            QMessageBox.critical(self, "Error de API", f"No se pudo actualizar el estado de la estrategia: {e.message}")
            # Revertir el cambio visual en el modelo
            strategy = self.table_model._data[index_to_revert.row()]
            original_state = not active # El estado antes del intento de cambio
            if mode == "paper":
                strategy.isActivePaperMode = original_state
            else:
                strategy.isActiveRealMode = original_state
            # Emitir dataChanged para que la UI se actualice al estado original
            self.table_model.dataChanged.emit(index_to_revert, index_to_revert, [Qt.ItemDataRole.CheckStateRole])
            # Subtask 3.4: Reflejar fallo de pre-condiciones (esto es un manejo genérico de error de API)
            # Si el backend devuelve un error específico por pre-condiciones, se mostrará en e.message.
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado al actualizar estado: {e}")
            # Revertir como en APIError
            strategy = self.table_model._data[index_to_revert.row()]
            original_state = not active
            if mode == "paper":
                strategy.isActivePaperMode = original_state
            else:
                strategy.isActiveRealMode = original_state
            self.table_model.dataChanged.emit(index_to_revert, index_to_revert, [Qt.ItemDataRole.CheckStateRole])

    def _handle_strategies_loaded(self, strategies_list: list):
        self._all_strategies_data = strategies_list
        self._filter_strategies() # Aplicar filtros actuales a los nuevos datos

    def _show_load_error_message(self, error_message: str):
        QMessageBox.critical(self, "Error al Cargar Estrategias", error_message)

    def _create_strategy_action(self, strategy_to_duplicate: Optional[TradingStrategyConfig] = None):
        action_text = "Duplicando" if strategy_to_duplicate else "Creando"
        print(f"Botón '{action_text} Nueva Configuración de Estrategia' clickeado.")
        
        from ..dialogs.strategy_config_dialog import StrategyConfigDialog
        ai_profiles = [] # TODO: Cargar perfiles AI si es necesario
        
        if self.api_client is None:
            QMessageBox.warning(self, "API no disponible", f"No se puede {action_text.lower()} una estrategia sin conexión al backend.")
            return

        dialog = None
        if strategy_to_duplicate:
            # Para duplicar, pasamos la configuración original, pero el diálogo la tratará como plantilla para una nueva.
            # El diálogo necesitará una lógica para no usar el ID original y limpiar/resetear ciertos campos si es necesario.
            # O, alternativamente, el diálogo toma 'strategy_config' y un flag 'is_duplicating'.
            # Por simplicidad, asumimos que pasar strategy_config y luego el diálogo no guarda con el mismo ID es suficiente.
            # El StrategyConfigDialog debería manejar el caso donde strategy_config.id existe pero se está creando una nueva.
            # Una forma es que el diálogo, al guardar, si se pasó una config original pero no es modo edición,
            # omita el ID en la llamada POST.
            
            # Hacemos una copia superficial para no modificar la original en la tabla si el usuario cancela.
            # Para una copia profunda, se necesitaría `import copy; config_copy = copy.deepcopy(strategy_to_duplicate)`
            # y que TradingStrategyConfig y sus miembros soporten deepcopy.
            config_for_dialog = TradingStrategyConfig(
                configName=f"Copia de {strategy_to_duplicate.configName}",
                baseStrategyType=strategy_to_duplicate.baseStrategyType,
                isActivePaperMode=False, # Las duplicadas empiezan desactivadas
                isActiveRealMode=False,  # Las duplicadas empiezan desactivadas
                applicabilityRules=dict(strategy_to_duplicate.applicabilityRules), # Copia del dict
                lastModified=datetime.now(), # Nueva fecha
                id="" # Forzar creación con string vacío
            )
            # Aquí podríamos querer pasar los 'parameters' también, copiándolos.
            # setattr(config_for_dialog, 'parameters', copy.deepcopy(getattr(strategy_to_duplicate, 'parameters', {})))

            dialog = StrategyConfigDialog(api_client=self.api_client,
                                          strategy_config=config_for_dialog, # Pasamos la copia como si fuera una existente
                                          ai_profiles=ai_profiles,
                                          is_duplicating=True, # Flag para indicar al diálogo que es una duplicación
                                          parent=self)
        else:
            dialog = StrategyConfigDialog(api_client=self.api_client,
                                          ai_profiles=ai_profiles,
                                          parent=self)
        
        if dialog.exec_():
            self._schedule_load_strategies()

    def _duplicate_strategy_action(self):
        selected_strategy = self._get_selected_strategy()
        if not selected_strategy:
            return
        
        strategy_id_to_fetch = getattr(selected_strategy, 'id', None)
        if not strategy_id_to_fetch:
            QMessageBox.warning(self, "Error", "La estrategia seleccionada no tiene un ID válido para duplicar.")
            return

        print(f"Duplicando estrategia ID: {strategy_id_to_fetch}")
        # Aquí podríamos llamar a self.api_client.get_strategy_details(strategy_id_to_fetch)
        # para obtener la configuración más fresca y completa del backend antes de duplicar.
        # Por ahora, usaremos los datos que ya tenemos en la tabla (selected_strategy).
        # Esto es más simple pero podría no tener todos los detalles si la tabla no los muestra todos.
        # La historia dice "Abre el formulario de creación pre-llenado", lo que implica usar los datos.
        
        # Para una duplicación real, es mejor obtener los detalles completos del backend.
        # asyncio.create_task(self._fetch_and_duplicate_strategy(strategy_id_to_fetch))
        # Por simplicidad y para seguir el flujo síncrono del diálogo:
        self._create_strategy_action(strategy_to_duplicate=selected_strategy)


    async def _fetch_and_duplicate_strategy(self, strategy_id: str):
        # Esta es una implementación más robusta para duplicar, obteniendo datos frescos.
        if not self.api_client:
            QMessageBox.warning(self, "API no disponible", "No se puede duplicar sin conexión al backend.")
            return
        try:
            strategy_details_dict = await self.api_client.get_strategy_details(strategy_id)
            
            # Convertir el dict a un objeto TradingStrategyConfig (o similar)
            # Esto asume que TradingStrategyConfig puede ser instanciado desde un dict,
            # o que tenemos una función de utilidad para ello.
            # Por ahora, vamos a simularlo:
            strategy_obj_to_duplicate = TradingStrategyConfig(
                id=strategy_details_dict.get('id'), # Se pasará pero el diálogo debe ignorarlo para POST
                configName=strategy_details_dict.get('configName', 'N/A'),
                baseStrategyType=BaseStrategyType(strategy_details_dict.get('baseStrategyType')) if strategy_details_dict.get('baseStrategyType') else None,
                isActivePaperMode=False, # Duplicates start deactivated
                isActiveRealMode=False,  # Duplicates start deactivated
                applicabilityRules=strategy_details_dict.get('applicabilityRules', {}),
                lastModified=datetime.now() # O parsear de 'lastModified' y luego poner now
                # Aquí faltarían 'parameters', 'description', 'aiAnalysisProfileId', 'riskParametersOverride'
                # que deberían venir de strategy_details_dict
            )
            # Copiar parámetros específicos si existen
            # if 'parameters' in strategy_details_dict:
            #     setattr(strategy_obj_to_duplicate, 'parameters', strategy_details_dict['parameters'])
            
            self._create_strategy_action(strategy_to_duplicate=strategy_obj_to_duplicate)

        except APIError as e:
            QMessageBox.critical(self, "Error al Duplicar", f"No se pudieron obtener los detalles de la estrategia: {e.message}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Duplicar", f"Error inesperado: {str(e)}")


    def _delete_strategy_action(self):
        selected_strategy = self._get_selected_strategy()
        if not selected_strategy:
            return

        strategy_id = getattr(selected_strategy, 'id', None)
        strategy_name = getattr(selected_strategy, 'configName', 'N/A')

        if not strategy_id:
            QMessageBox.warning(self, "Error", "La estrategia seleccionada no tiene un ID válido para eliminar.")
            return

        confirm_dialog = QMessageBox(self)
        confirm_dialog.setIcon(QMessageBox.Warning)
        confirm_dialog.setWindowTitle("Confirmar Eliminación")
        confirm_dialog.setText(f"¿Está seguro de que desea eliminar la configuración de estrategia '{strategy_name}' (ID: {strategy_id})?\nEsta acción no se puede deshacer.")
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.setDefaultButton(QMessageBox.No)

        if confirm_dialog.exec_() == QMessageBox.Yes:
            print(f"Eliminando estrategia ID: {strategy_id}")
            asyncio.create_task(self._delete_strategy_backend(strategy_id))

    async def _delete_strategy_backend(self, strategy_id: str):
        if not self.api_client:
            QMessageBox.warning(self, "API no disponible", "No se puede eliminar sin conexión al backend.")
            return
        try:
            await self.api_client.delete_strategy(strategy_id)
            QMessageBox.information(self, "Éxito", f"Estrategia '{strategy_id}' eliminada correctamente.")
            self._schedule_load_strategies() # Recargar la lista
        except APIError as e:
            QMessageBox.critical(self, "Error al Eliminar", f"No se pudo eliminar la estrategia: {e.message}")
        except Exception as e:
            QMessageBox.critical(self, "Error al Eliminar", f"Error inesperado: {str(e)}")

    def _edit_strategy_action(self, strategy_config: TradingStrategyConfig):
        if not strategy_config:
            return
        print(f"Editando estrategia: {getattr(strategy_config, 'configName', 'ID Desconocida')}")
        from ..dialogs.strategy_config_dialog import StrategyConfigDialog
        ai_profiles = []
        if self.api_client is None:
            QMessageBox.warning(self, "API no disponible", "No se puede editar una estrategia sin conexión al backend.")
            return
        dialog = StrategyConfigDialog(api_client=self.api_client, 
                                      strategy_config=strategy_config, 
                                      ai_profiles=ai_profiles, 
                                      parent=self)
        if dialog.exec_():
            self._schedule_load_strategies()

    def _schedule_load_strategies(self):
        if not self.api_client:
            print("StrategyManagementView: No se puede cargar estrategias, api_client no está disponible.")
            return
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(self._load_strategies_async())
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.create_task(self._load_strategies_async())
        except Exception as e:
            self.strategy_load_failed.emit(f"Error al programar la carga de estrategias: {e}")
            print(f"Error al programar la carga de estrategias: {e}")

    async def _load_strategies_async(self):
        if self.api_client is None:
            self.strategy_load_failed.emit("No se puede cargar estrategias: API client no disponible.")
            return
        try:
            strategies_data_raw = await self.api_client.get_strategies()
            strategies_list = []
            if not isinstance(strategies_data_raw, list): # Verificar si la respuesta general es una lista
                print(f"Advertencia: La respuesta de get_strategies no es una lista: {strategies_data_raw}")
                self.strategy_load_failed.emit(f"Respuesta inesperada del servidor: {type(strategies_data_raw)}")
                return

            for item_data in strategies_data_raw:
                if not isinstance(item_data, dict):
                    print(f"Advertencia: Se encontró un elemento no diccionario en la respuesta de estrategias: {item_data}")
                    continue # Saltar este elemento y continuar con el siguiente

                last_modified_raw = item_data.get('lastModified')
                last_modified_dt = None
                if isinstance(last_modified_raw, str):
                    try:
                        if last_modified_raw.endswith('Z'):
                            last_modified_dt = datetime.fromisoformat(last_modified_raw.replace('Z', '+00:00'))
                        else:
                            last_modified_dt = datetime.fromisoformat(last_modified_raw)
                    except ValueError:
                        try:
                            last_modified_dt = datetime.strptime(last_modified_raw, "%Y-%m-%d %H:%M:%S.%f")
                        except ValueError:
                            try:
                                last_modified_dt = datetime.strptime(last_modified_raw, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                print(f"Advertencia: No se pudo parsear la fecha '{last_modified_raw}'.")
                elif isinstance(last_modified_raw, datetime):
                    last_modified_dt = last_modified_raw

                base_strategy_type_raw = item_data.get('baseStrategyType')
                base_strategy_type_enum = None
                if isinstance(base_strategy_type_raw, str):
                    try:
                        base_strategy_type_enum = BaseStrategyType(base_strategy_type_raw)
                    except ValueError:
                        print(f"Advertencia: Tipo de estrategia base desconocido '{base_strategy_type_raw}'.")
                        base_strategy_type_enum = base_strategy_type_raw
                elif isinstance(base_strategy_type_raw, BaseStrategyType):
                    base_strategy_type_enum = base_strategy_type_raw

                strategy_id = item_data.get('id')
                if strategy_id is None:
                    strategy_id = "placeholder_id_" + item_data.get('configName', 'unknown')
                else:
                    strategy_id = str(strategy_id)

                strategies_list.append(
                    TradingStrategyConfig(
                        id=strategy_id,
                        configName=item_data.get('configName', 'N/A'),
                        baseStrategyType=base_strategy_type_enum,
                        isActivePaperMode=item_data.get('isActivePaperMode', False),
                        isActiveRealMode=item_data.get('isActiveRealMode', False),
                        applicabilityRules=item_data.get('applicabilityRules', {}),
                        lastModified=last_modified_dt
                    )
                )
            self.strategy_data_loaded.emit(strategies_list)
        except APIError as e:
            print(f"Error de API al cargar estrategias: {e}")
            self.strategy_load_failed.emit(f"Error de API: {e}")
        except Exception as e:
            print(f"Error inesperado al cargar estrategias: {e}")
            self.strategy_load_failed.emit(f"Error inesperado: {e}")

    def load_strategies(self):
        """
        Inicia la carga de estrategias. Este método puede ser llamado externamente
        para controlar cuándo se realiza la carga inicial.
        """
        self._schedule_load_strategies()

    def _filter_strategies(self):
        """
        Filtra las estrategias mostradas en la tabla según el texto de búsqueda y el tipo seleccionado.
        """
        search_text = self.search_input.text().strip().lower() if hasattr(self, 'search_input') else ""
        selected_type = self.filter_combo.currentData() if hasattr(self, 'filter_combo') else None
        
        filtered = []
        for strat in self._all_strategies_data:
            name_match = search_text in getattr(strat, 'configName', '').lower()
            type_match = (selected_type is None) or (getattr(strat, 'baseStrategyType', None) == selected_type)
            if name_match and type_match:
                filtered.append(strat)
        self.table_model.update_data(filtered)

    def closeEvent(self, event: QCloseEvent): # Cambiado QEvent a QCloseEvent
        """
        Maneja el evento de cierre de la vista para limpiar hilos activos.
        """
        print(f"StrategyManagementView: closeEvent llamado. Hilos activos: {len(self.active_threads)}")
        for thread in list(self.active_threads): # Iterar sobre una copia
            if hasattr(thread, 'isRunning') and thread.isRunning():
                print(f"StrategyManagementView: Intentando detener QThread: {thread}")
                thread.quit()
                if not thread.wait(1000): # Esperar máximo 1 segundo
                    print(f"StrategyManagementView: QThread {thread} no terminó a tiempo, terminando forzosamente.")
                    thread.terminate()
                    thread.wait() # Esperar a que la terminación se complete
            elif thread in self.active_threads: # Si no está corriendo pero aún en la lista
                 try:
                    self.active_threads.remove(thread)
                 except ValueError:
                    pass # Ya no estaba en la lista, no hay problema
        
        print(f"StrategyManagementView: Hilos restantes después de limpieza: {len(self.active_threads)}")
        super().closeEvent(event)
