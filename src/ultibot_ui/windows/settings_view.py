from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QGroupBox, QDoubleSpinBox, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from typing import Optional, Dict, Any
from uuid import UUID
import asyncio

from src.ultibot_ui.services.api_client import UltiBotAPIClient # Importar UltiBotAPIClient
from src.shared.data_types import UserConfiguration, RealTradingSettings # Importar RealTradingSettings

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """
    Vista de configuración para el usuario, incluyendo opciones de Paper Trading y Operativa Real Limitada.
    """
    config_changed = pyqtSignal(UserConfiguration)
    real_trading_mode_status_changed = pyqtSignal(bool, int, int) # isActive, executedCount, limit

    def __init__(self, user_id: str, api_client: UltiBotAPIClient, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.current_config: Optional[UserConfiguration] = None
        self.real_trading_status: Dict[str, Any] = {"isActive": False, "executedCount": 0, "limit": 5}

        self._setup_ui()
        asyncio.create_task(self._load_initial_data())

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Configuración General")
        title_label.setObjectName("settingsTitleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Grupo para Paper Trading
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

        # Grupo para Operativa Real Limitada
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

    async def _load_initial_data(self):
        """Carga la configuración inicial y el estado del modo real."""
        await self._load_config_into_ui()
        await self._load_real_trading_status()

    async def _load_config_into_ui(self):
        """Carga la configuración general del usuario y la muestra en la UI."""
        try:
            config_data = await self.api_client.get_user_configuration()
            self.current_config = UserConfiguration(**config_data) # Convertir a UserConfiguration
            assert self.current_config is not None # Asegurar a Pylance que no es None
            
            self.paper_trading_checkbox.setChecked(self.current_config.paperTradingActive or False)
            self.initial_capital_spinbox.setValue(self.current_config.defaultPaperTradingCapital or 10000.0)
            logger.info("Configuración de usuario general cargada en la UI de Settings.")
        except Exception as e:
            logger.error(f"Error al cargar la configuración general en la UI de Settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Carga", f"No se pudo cargar la configuración general: {e}")

    async def _load_real_trading_status(self):
        """Carga el estado del modo de operativa real limitada y actualiza la UI."""
        try:
            status_data = await self.api_client.get_real_trading_mode_status()
            self.real_trading_status = status_data
            self._update_real_trading_ui()
            logger.info(f"Estado de operativa real cargado: {status_data}")
        except Exception as e:
            logger.error(f"Error al cargar el estado de operativa real: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Carga", f"No se pudo cargar el estado del modo real: {e}")

    def _update_real_trading_ui(self):
        """Actualiza los widgets de UI relacionados con el modo de operativa real."""
        is_active = self.real_trading_status.get("isActive", False)
        executed_count = self.real_trading_status.get("executedCount", 0)
        limit = self.real_trading_status.get("limit", 5)

        self.real_trading_checkbox.setChecked(is_active)
        self.real_trades_count_label.setText(f"Operaciones Reales Disponibles: {limit - executed_count}/{limit}")

        # AC5: Bloqueo Post-Límite
        if executed_count >= limit:
            self.real_trading_checkbox.setEnabled(False)
            self.real_trades_count_label.setText(f"Límite de operaciones reales alcanzado: {executed_count}/{limit}")
            QMessageBox.information(self, "Límite Alcanzado", "Has alcanzado el límite de operaciones reales permitidas. El modo real ha sido deshabilitado.")
        else:
            self.real_trading_checkbox.setEnabled(True) # Asegurarse de que esté habilitado si hay cupos

        self.real_trading_mode_status_changed.emit(is_active, executed_count, limit)


    def _handle_save_button_clicked(self):
        """Slot síncrono para manejar el clic del botón Guardar. Crea una tarea para guardar la configuración."""
        asyncio.create_task(self._save_config())

    async def _save_config(self):
        """Guarda los cambios de configuración general desde la UI al backend."""
        if not self.current_config:
            logger.warning("No hay configuración actual para guardar. Recargando y reintentando.")
            await self._load_config_into_ui()
            if not self.current_config:
                QMessageBox.critical(self, "Error", "No se pudo cargar la configuración para guardar.")
                return

        try:
            # Crear una nueva instancia de UserConfiguration con los cambios
            updated_config_data = {
                "paperTradingActive": self.paper_trading_checkbox.isChecked(),
                "defaultPaperTradingCapital": self.initial_capital_spinbox.value(),
                # realTradingSettings se gestiona por separado con sus propios endpoints
            }
            # Usar model_copy para crear una nueva instancia con los cambios
            updated_config_model = self.current_config.model_copy(update=updated_config_data)
            
            # Convertir el modelo Pydantic a un diccionario para el API client
            await self.api_client.update_user_configuration(updated_config_model.model_dump(mode='json', by_alias=True, exclude_none=True))
            logger.info("Configuración de usuario general guardada exitosamente desde la UI de Settings.")
            self.config_changed.emit(updated_config_model)
            QMessageBox.information(self, "Éxito", "Configuración guardada exitosamente.")
        except Exception as e:
            logger.error(f"Error al guardar la configuración general desde la UI de Settings: {e}", exc_info=True)
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la configuración general: {e}")

    def _handle_real_trading_checkbox_state_changed(self, state: int):
        """Maneja el cambio de estado del checkbox de Operativa Real Limitada."""
        if state == Qt.CheckState.Checked: # Corregido: Usar Qt.CheckState.Checked
            asyncio.create_task(self._activate_real_trading_mode())
        else:
            asyncio.create_task(self._deactivate_real_trading_mode())

    async def _activate_real_trading_mode(self):
        """Llama al endpoint para activar el modo de operativa real limitada."""
        try:
            # AC6: Advertencia y Confirmación Adicional
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
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                await self.api_client.activate_real_trading_mode()
                QMessageBox.information(self, "Éxito", "Modo de Operativa Real Limitada activado.")
                await self._load_real_trading_status() # Recargar estado para actualizar UI
            else:
                self.real_trading_checkbox.setChecked(False) # Revertir el checkbox si el usuario cancela
        except Exception as e:
            logger.error(f"Error al activar el modo de operativa real: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Activación", f"No se pudo activar el modo real: {e}")
            self.real_trading_checkbox.setChecked(False) # Revertir el checkbox en caso de error

    async def _deactivate_real_trading_mode(self):
        """Llama al endpoint para desactivar el modo de operativa real limitada."""
        try:
            await self.api_client.deactivate_real_trading_mode()
            QMessageBox.information(self, "Éxito", "Modo de Operativa Real Limitada desactivado.")
            await self._load_real_trading_status() # Recargar estado para actualizar UI
        except Exception as e:
            logger.error(f"Error al desactivar el modo de operativa real: {e}", exc_info=True)
            QMessageBox.critical(self, "Error de Desactivación", f"No se pudo desactivar el modo real: {e}")
            self.real_trading_checkbox.setChecked(True) # Revertir el checkbox en caso de error
