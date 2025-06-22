from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QGroupBox, QDoubleSpinBox, QMessageBox
from PySide6.QtCore import Qt, Signal as pyqtSignal, QTimer, QThread
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
import asyncio

from ultibot_ui.services.api_client import UltiBotAPIClient
from shared.data_types import UserConfiguration, RealTradingSettings
from ultibot_ui.workers import ApiWorker

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """
    Vista de configuración para el usuario, incluyendo opciones de Paper Trading y Operativa Real Limitada.
    """
    config_changed = pyqtSignal(UserConfiguration)
    real_trading_mode_status_changed = pyqtSignal(bool, int, int)

    def __init__(self, user_id: str, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client # Usar la instancia de api_client
        self.current_config: Optional[UserConfiguration] = None
        self.real_trading_status: Dict[str, Any] = {"isActive": False, "executedCount": 0, "limit": 5}
        self.active_threads: List[QThread] = []

        self._setup_ui()
        QTimer.singleShot(0, self._load_initial_data)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Configuración General")
        title_label.setObjectName("settingsTitleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        paper_trading_group = QGroupBox("Modo Paper Trading")
        paper_trading_layout = QVBoxLayout(paper_trading_group)
        paper_trading_layout.setContentsMargins(10, 10, 10, 10)
        paper_trading_layout.setSpacing(10)

        self.paper_trading_checkbox = QCheckBox("Activar Paper Trading")
        self.paper_trading_checkbox.setStyleSheet("font-size: 16px;")
        paper_trading_layout.addWidget(self.paper_trading_checkbox)

        capital_layout = QHBoxLayout()
        capital_label = QLabel("Capital Virtual Inicial (USDT):")
        capital_label.setStyleSheet("font-size: 14px;")
        self.initial_capital_spinbox = QDoubleSpinBox()
        self.initial_capital_spinbox.setRange(0.0, 10000000.0)
        self.initial_capital_spinbox.setSingleStep(100.0)
        self.initial_capital_spinbox.setDecimals(2)
        self.initial_capital_spinbox.setStyleSheet("font-size: 14px; padding: 5px;")
        capital_layout.addWidget(capital_label)
        capital_layout.addWidget(self.initial_capital_spinbox)
        capital_layout.addStretch(1)
        paper_trading_layout.addLayout(capital_layout)

        main_layout.addWidget(paper_trading_group)

        real_trading_group = QGroupBox("Modo de Operativa Real Limitada")
        real_trading_layout = QVBoxLayout(real_trading_group)
        real_trading_layout.setContentsMargins(10, 10, 10, 10)
        real_trading_layout.setSpacing(10)

        self.real_trading_checkbox = QCheckBox("Activar Operativa Real Limitada")
        self.real_trading_checkbox.setStyleSheet("font-size: 16px;")
        self.real_trading_checkbox.stateChanged.connect(self._handle_real_trading_checkbox_state_changed)
        real_trading_layout.addWidget(self.real_trading_checkbox)

        self.real_trades_count_label = QLabel("Operaciones Reales Disponibles: 0/5")
        self.real_trades_count_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        real_trading_layout.addWidget(self.real_trades_count_label)

        main_layout.addWidget(real_trading_group)

        save_button = QPushButton("Guardar Cambios")
        save_button.setStyleSheet("padding: 10px 20px; font-size: 16px; font-weight: bold;")
        save_button.clicked.connect(self._handle_save_button_clicked)
        main_layout.addWidget(save_button)

        main_layout.addStretch(1)

    def _load_initial_data(self):
        logger.info("SettingsView: Iniciando carga de datos iniciales (_load_initial_data).")
        self._load_config_into_ui()
        self._load_real_trading_status()

    def _start_api_worker(self, coroutine_factory, on_success, on_error):
        worker = ApiWorker(api_client=self.api_client, coroutine_factory=coroutine_factory) # Pasar api_client
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(on_success)
        worker.error_occurred.connect(on_error)
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        thread.start()

    def _load_config_into_ui(self):
        logger.info("SettingsView: Solicitando configuración de usuario general.")
        coro_factory = lambda api_client: api_client.get_user_configuration()
        self._start_api_worker(coro_factory, self._handle_load_config_result, self._handle_load_config_error)

    def _handle_load_config_result(self, config_data: Dict[str, Any]):
        try:
            self.current_config = UserConfiguration(**config_data)
            assert self.current_config is not None
            self.paper_trading_checkbox.setChecked(self.current_config.paper_trading_active or False)
            # Convertir Decimal a float para setValue
            self.initial_capital_spinbox.setValue(float(self.current_config.default_paper_trading_capital or 10000.0))
            logger.info("Configuración de usuario general cargada y aplicada en la UI de Settings.")
        except Exception as e:
            logger.error(f"Error al procesar la configuración general recibida: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Procesamiento", f"No se pudo procesar la configuración general: {e}")

    def _handle_load_config_error(self, error_message: str):
        logger.error(f"Error al cargar la configuración general en SettingsView: {error_message}")
        QMessageBox.critical(self, "Error de Carga", f"No se pudo cargar la configuración general: {error_message}")

    def _load_real_trading_status(self):
        logger.info("SettingsView: Solicitando estado de operativa real.")
        coro_factory = lambda api_client: api_client.get_real_trading_mode_status()
        self._start_api_worker(coro_factory, self._handle_load_real_trading_status_result, self._handle_load_real_trading_status_error)

    def _handle_load_real_trading_status_result(self, status_data: Dict[str, Any]):
        try:
            self.real_trading_status = status_data
            self._update_real_trading_ui()
            logger.info(f"Estado de operativa real cargado y UI actualizada: {status_data}")
        except Exception as e:
            logger.error(f"Error al procesar el estado de operativa real recibido: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Procesamiento", f"No se pudo procesar el estado de operativa real: {e}")

    def _handle_load_real_trading_status_error(self, error_message: str):
        logger.error(f"Error al cargar el estado de operativa real en SettingsView: {error_message}")
        QMessageBox.critical(self, "Error de Carga", f"No se pudo cargar el estado del modo real: {error_message}")

    def _update_real_trading_ui(self):
        is_active = self.real_trading_status.get("isActive", False)
        executed_count = self.real_trading_status.get("executedCount", 0)
        limit = self.real_trading_status.get("limit", 5)

        self.real_trading_checkbox.setChecked(is_active)
        self.real_trades_count_label.setText(f"Operaciones Reales Disponibles: {limit - executed_count}/{limit}")

        if executed_count >= limit:
            self.real_trading_checkbox.setEnabled(False)
            self.real_trades_count_label.setText(f"Límite de operaciones reales alcanzado: {executed_count}/{limit}")
            QMessageBox.information(self, "Límite Alcanzado", "Has alcanzado el límite de operaciones reales permitidas. El modo real ha sido deshabilitado.")
        else:
            self.real_trading_checkbox.setEnabled(True)

        self.real_trading_mode_status_changed.emit(is_active, executed_count, limit)

    def _handle_save_button_clicked(self):
        self._save_config()

    def _save_config(self):
        if not self.current_config:
            logger.error("SettingsView: No hay configuración actual para guardar. Operación cancelada.")
            QMessageBox.critical(self, "Error", "No se pudo guardar: la configuración actual no está cargada. Espere a que finalice la carga inicial.")
            return

        try:
            updated_config_data = {
                "paper_trading_active": self.paper_trading_checkbox.isChecked(),
                "default_paper_trading_capital": self.initial_capital_spinbox.value(),
            }
            updated_config_model = self.current_config.model_copy(update=updated_config_data)
            
            logger.info("SettingsView: Solicitando guardar configuración de usuario general.")
            coro_factory = lambda api_client: api_client.update_user_configuration(updated_config_model.model_dump(mode='json', by_alias=True, exclude_none=True))
            self._start_api_worker(coro_factory, lambda result: self._handle_save_config_result(result, updated_config_model), self._handle_save_config_error)

        except Exception as e:
            logger.error(f"Error al preparar los datos para guardar la configuración: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Preparación", f"No se pudieron preparar los datos para guardar: {e}")

    def _handle_save_config_result(self, result: Any, updated_config_model: UserConfiguration):
        logger.info("Configuración de usuario general guardada exitosamente desde la UI de Settings.")
        self.current_config = updated_config_model
        self.config_changed.emit(updated_config_model)
        QMessageBox.information(self, "Éxito", "Configuración guardada exitosamente.")

    def _handle_save_config_error(self, error_message: str):
        logger.error(f"Error al guardar la configuración general en SettingsView: {error_message}")
        QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la configuración general: {error_message}")

    def _handle_real_trading_checkbox_state_changed(self, state: int):
        if state == Qt.CheckState.Checked:
            self._activate_real_trading_mode()
        else:
            self._deactivate_real_trading_mode()

    def _activate_real_trading_mode(self):
        warning_message = (
            "¡ADVERTENCIA CRÍTICA!\n\n"
            "Estás a punto de activar el MODO DE OPERATIVA REAL LIMITADA.\n"
            "Esto significa que las PRÓXIMAS OPERACIONES que cumplan los criterios de alta confianza "
            "utilizarán DINERO REAL de tu cuenta de Binance.\n\n"
            "Asegúrate de entender los riesgos. ¿Deseas continuar?"
        )
        reply = QMessageBox.warning(
            self, 
            "Confirmar Activación de Modo Real", 
            warning_message, 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("SettingsView: Solicitando activar modo de operativa real.")
            coro_factory = lambda api_client: api_client.activate_real_trading_mode()
            self._start_api_worker(coro_factory, self._handle_activate_real_trading_result, self._handle_activate_real_trading_error)
        else:
            self.real_trading_checkbox.setChecked(False)
            logger.info("SettingsView: Activación del modo real cancelada por el usuario.")

    def _handle_activate_real_trading_result(self, result: Any):
        QMessageBox.information(self, "Éxito", "Modo de Operativa Real Limitada activado.")
        logger.info("SettingsView: Modo de operativa real activado. Recargando estado.")
        self._load_real_trading_status()

    def _handle_activate_real_trading_error(self, error_message: str):
        logger.error(f"Error al activar el modo de operativa real: {error_message}")
        QMessageBox.critical(self, "Error de Activación", f"No se pudo activar el modo real: {error_message}")
        self.real_trading_checkbox.setChecked(False)

    def _deactivate_real_trading_mode(self):
        logger.info("SettingsView: Solicitando desactivar modo de operativa real.")
        coro_factory = lambda api_client: api_client.deactivate_real_trading_mode()
        self._start_api_worker(coro_factory, self._handle_deactivate_real_trading_result, self._handle_deactivate_real_trading_error)

    def _handle_deactivate_real_trading_result(self, result: Any):
        QMessageBox.information(self, "Éxito", "Modo de Operativa Real Limitada desactivado.")
        logger.info("SettingsView: Modo de operativa real desactivado. Recargando estado.")
        self._load_real_trading_status()

    def _handle_deactivate_real_trading_error(self, error_message: str):
        logger.error(f"Error al desactivar el modo de operativa real: {error_message}")
        QMessageBox.critical(self, "Error de Desactivación", f"No se pudo desactivar el modo real: {error_message}")
        self.real_trading_checkbox.setChecked(True)
