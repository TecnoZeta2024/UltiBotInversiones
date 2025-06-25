from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QDialog # Importar QDialog
)
from PySide6.QtCore import QEventLoop, QTimer, QThread, Signal
import asyncio
import logging
from typing import Optional, List, Dict, Any

from ultibot_ui.services.ui_strategy_service import UIStrategyService
from ultibot_ui.workers import ApiWorker
from ultibot_ui.models import BaseMainWindow
from ultibot_ui.dialogs.strategy_config_dialog import StrategyConfigDialog

logger = logging.getLogger(__name__)

import asyncio
import logging
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QDialog
)
from PySide6.QtCore import QThread, Signal

from ultibot_ui.services.ui_strategy_service import UIStrategyService
from ultibot_ui.workers import ApiWorker
from ultibot_ui.models import BaseMainWindow # Mantener para type hinting de main_window
from ultibot_ui.dialogs.strategy_config_dialog import StrategyConfigDialog

logger = logging.getLogger(__name__)

class StrategyManagementView(QWidget):
    strategy_created = Signal(dict)
    strategy_updated = Signal(dict)
    strategy_deleted = Signal(str)
    strategy_status_changed = Signal(str, bool)

    def __init__(self, api_client, main_event_loop: asyncio.AbstractEventLoop, parent=None): # Recibir main_event_loop
        super().__init__(parent)
        self.api_client = api_client
        self.main_event_loop = main_event_loop # Almacenar main_event_loop
        self.strategy_service = UIStrategyService(api_client)
        self.active_threads: List[QThread] = []
        self.main_window: Optional[BaseMainWindow] = None
        self.strategies_data: List[Dict[str, Any]] = []
        self.init_ui()
        self.strategy_service.strategies_updated.connect(self.display_strategies)
        self.strategy_service.error_occurred.connect(self.display_error)
        self.strategy_list_widget.itemSelectionChanged.connect(self.on_strategy_selection_changed)
        self.update_action_buttons_state()

    def set_main_window(self, main_window: BaseMainWindow):
        self.main_window = main_window

    def init_ui(self):
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)

        title_label = QLabel("Strategy Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._layout.addWidget(title_label)

        self.strategy_list_widget = QListWidget()
        self._layout.addWidget(self.strategy_list_widget)

        self.button_layout = QHBoxLayout()
        self.new_strategy_button = QPushButton("Nueva Estrategia")
        self.edit_strategy_button = QPushButton("Editar")
        self.delete_strategy_button = QPushButton("Eliminar")
        self.toggle_status_button = QPushButton("Activar/Desactivar")

        self.button_layout.addWidget(self.new_strategy_button)
        self.button_layout.addWidget(self.edit_strategy_button)
        self.button_layout.addWidget(self.delete_strategy_button)
        self.button_layout.addWidget(self.toggle_status_button)
        self._layout.addLayout(self.button_layout)

        self.status_label = QLabel("")
        self._layout.addWidget(self.status_label)

        self.new_strategy_button.clicked.connect(self.create_new_strategy)
        self.edit_strategy_button.clicked.connect(self.edit_selected_strategy)
        self.delete_strategy_button.clicked.connect(self.delete_selected_strategy)
        self.toggle_status_button.clicked.connect(self.toggle_selected_strategy_status)

    def update_action_buttons_state(self):
        has_selection = len(self.strategy_list_widget.selectedItems()) > 0
        self.edit_strategy_button.setEnabled(has_selection)
        self.delete_strategy_button.setEnabled(has_selection)
        self.toggle_status_button.setEnabled(has_selection)

        if has_selection:
            selected_item = self.strategy_list_widget.selectedItems()[0]
            strategy_id = selected_item.data(0)
            strategy = next((s for s in self.strategies_data if s.get('id') == strategy_id), None)
            if strategy:
                is_active = strategy.get('is_active', False)
                self.toggle_status_button.setText("Desactivar" if is_active else "Activar")
            else:
                self.toggle_status_button.setText("Activar/Desactivar")
        else:
            self.toggle_status_button.setText("Activar/Desactivar")

    def on_strategy_selection_changed(self):
        self.update_action_buttons_state()

    def load_strategies(self):
        # coroutine_factory debe aceptar api_client, aunque fetch_strategies no lo use directamente
        # porque ApiWorker lo pasa.
        coro_factory = lambda api_client: self.strategy_service.fetch_strategies()
        
        worker = ApiWorker(api_client=self.api_client, main_event_loop=self.main_event_loop, coroutine_factory=coro_factory)
        thread = QThread()
        thread.setObjectName("StrategyManagementWorkerThread")
        worker.moveToThread(thread)

        worker.result_ready.connect(self.display_strategies)
        worker.error_occurred.connect(self.display_error)
        
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        
        self.active_threads.append(thread)
        if self.main_window:
            self.main_window.add_thread(thread)
        
        thread.start()

    def display_strategies(self, strategies: List[Dict[str, Any]]):
        self.strategy_list_widget.clear()
        self.strategies_data = strategies
        if not strategies:
            self.status_label.setText("No hay estrategias disponibles.")
            self.update_action_buttons_state()
            return
        for strat in strategies:
            status = "Activa" if strat.get('is_active', False) else "Inactiva"
            item = QListWidgetItem(f"{strat.get('name', 'Sin Nombre')} (ID: {strat.get('id', '-')}) - Estado: {status}")
            item.setData(0, strat.get('id'))
            self.strategy_list_widget.addItem(item)
        self.status_label.setText(f"{len(strategies)} estrategias cargadas.")
        self.update_action_buttons_state()

    def display_error(self, error_msg: str):
        self.status_label.setText(f"Error al cargar estrategias: {error_msg}")
        QMessageBox.critical(self, "Error de Estrategias", f"Error: {error_msg}")

    def get_selected_strategy(self) -> Optional[Dict[str, Any]]:
        selected_items = self.strategy_list_widget.selectedItems()
        if not selected_items:
            return None
        selected_id = selected_items[0].data(0)
        return next((s for s in self.strategies_data if s.get('id') == selected_id), None)

    def create_new_strategy(self):
        dialog = StrategyConfigDialog(self.api_client, parent=self)
        if dialog.exec() == QDialog.Accepted:
            strategy_data = dialog.get_strategy_data()
            if strategy_data:
                self.execute_strategy_action(
                    lambda: self.strategy_service.create_strategy(strategy_data),
                    "crear",
                    lambda result: self.strategy_created.emit(result)
                )

    def edit_selected_strategy(self):
        selected_strategy = self.get_selected_strategy()
        if selected_strategy:
            dialog = StrategyConfigDialog(self.api_client, strategy_data=selected_strategy, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_data = dialog.get_strategy_data()
                if updated_data:
                    strategy_id = selected_strategy.get('id')
                    if strategy_id is None:
                        QMessageBox.critical(self, "Error", "ID de estrategia no encontrado para la edición.")
                        return
                    self.execute_strategy_action(
                        lambda: self.strategy_service.update_strategy(str(strategy_id), updated_data),
                        "actualizar",
                        lambda result: self.strategy_updated.emit(result)
                    )
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una estrategia para editar.")

    def delete_selected_strategy(self):
        selected_strategy = self.get_selected_strategy()
        if selected_strategy:
            strategy_id = selected_strategy.get('id')
            if strategy_id is None:
                QMessageBox.critical(self, "Error", "ID de estrategia no encontrado para la eliminación.")
                return
            strategy_name = selected_strategy.get('name', 'Sin Nombre')
            reply = QMessageBox.question(self, "Confirmar Eliminación",
                                         f"¿Está seguro de que desea eliminar la estrategia '{strategy_name}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.execute_strategy_action(
                    lambda: self.strategy_service.delete_strategy(str(strategy_id)),
                    "eliminar",
                    lambda _: self.strategy_deleted.emit(str(strategy_id))
                )
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una estrategia para eliminar.")

    def toggle_selected_strategy_status(self):
        selected_strategy = self.get_selected_strategy()
        if selected_strategy:
            strategy_id = selected_strategy.get('id')
            if strategy_id is None:
                QMessageBox.critical(self, "Error", "ID de estrategia no encontrado para cambiar el estado.")
                return
            current_status = selected_strategy.get('is_active', False)
            new_status = not current_status
            action_name = "activar" if new_status else "desactivar"

            self.execute_strategy_action(
                lambda: self.strategy_service.update_strategy_status(str(strategy_id), new_status),
                action_name,
                lambda _: self.strategy_status_changed.emit(str(strategy_id), new_status)
            )
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, seleccione una estrategia para cambiar su estado.")

    def execute_strategy_action(self, coroutine_func, action_type: str, success_callback=None):
        self.status_label.setText(f"Intentando {action_type} estrategia...")
        
        worker = ApiWorker(api_client=self.api_client, main_event_loop=self.main_event_loop, coroutine_factory=lambda _: coroutine_func()) # Usar self.main_event_loop
        thread = QThread()
        thread.setObjectName(f"Strategy{action_type.capitalize()}WorkerThread")
        worker.moveToThread(thread)

        def on_success(result):
            self.status_label.setText(f"Estrategia {action_type} exitosamente.")
            self.load_strategies()
            if success_callback:
                success_callback(result)

        def on_error(error_msg):
            self.status_label.setText(f"Error al {action_type} estrategia: {error_msg}")
            QMessageBox.critical(self, f"Error al {action_type.capitalize()}", f"Error: {error_msg}")

        worker.result_ready.connect(on_success)
        worker.error_occurred.connect(on_error)
        
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        
        self.active_threads.append(thread)
        if self.main_window:
            self.main_window.add_thread(thread)
        
        thread.start()

    def cleanup(self):
        logger.info(f"StrategyManagementView: Cleaning up. Stopping {len(self.active_threads)} active threads...")
        for thread in self.active_threads[:]:
            if thread.isRunning():
                logger.info(f"StrategyManagementView: Quitting and waiting for thread {thread.objectName() or 'unnamed'}...")
                thread.quit()
                if not thread.wait(5000):
                    logger.warning(f"StrategyManagementView: Thread {thread.objectName() or 'unnamed'} did not terminate gracefully.")
            try:
                thread.finished.disconnect()
            except TypeError:
                pass
            thread.deleteLater()
        self.active_threads.clear()
        logger.info("StrategyManagementView: Cleanup complete.")
