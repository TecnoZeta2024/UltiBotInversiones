import asyncio
import logging
from typing import Optional
from uuid import UUID

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QMessageBox, QRadioButton, QButtonGroup
)

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.services.trading_mode_state import TradingMode, TradingModeStateManager
from src.ultibot_ui.dialogs.confirmation_dialog import ConfirmationDialog
from src.ultibot_ui.models import BaseMainWindow

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """
    Vista de configuración para gestionar el modo de operativa del bot.
    """

    def __init__(
        self,
        user_id: str,
        api_client: UltiBotAPIClient,
        loop: asyncio.AbstractEventLoop,
        parent: Optional[BaseMainWindow] = None,
    ):
        super().__init__(parent)
        self.user_id = user_id
        self.api_client = api_client
        self.loop = loop
        self.main_window = parent
        
        # Acceder al trading_mode_manager desde la ventana principal
        if hasattr(self.main_window, 'trading_mode_manager'):
            self.trading_mode_manager: TradingModeStateManager = self.main_window.trading_mode_manager
        else:
            # Fallback por si se instancia sin una main_window completa (ej. en tests)
            self.trading_mode_manager = TradingModeStateManager(api_client)
            logger.warning("SettingsView initialized without a main_window. TradingModeStateManager may not be shared.")

        self._setup_ui()
        self.trading_mode_manager.trading_mode_changed.connect(self._update_ui_from_state)
        self._update_ui_from_state(self.trading_mode_manager.current_mode.value)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel("Configuración de Operativa")
        title_label.setObjectName("settingsTitleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        mode_group = QGroupBox("Modo de Operativa")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_button_group = QButtonGroup(self)
        
        self.paper_mode_radio = QRadioButton(TradingMode.PAPER.display_name)
        self.paper_mode_radio.setStyleSheet("font-size: 16px;")
        self.mode_button_group.addButton(self.paper_mode_radio)
        mode_layout.addWidget(self.paper_mode_radio)

        self.live_mode_radio = QRadioButton(TradingMode.LIVE.display_name)
        self.live_mode_radio.setStyleSheet("font-size: 16px;")
        self.mode_button_group.addButton(self.live_mode_radio)
        mode_layout.addWidget(self.live_mode_radio)
        
        main_layout.addWidget(mode_group)

        save_button = QPushButton("Aplicar Cambio de Modo")
        save_button.setStyleSheet("padding: 10px 20px; font-size: 16px; font-weight: bold;")
        save_button.clicked.connect(self._handle_save_button_clicked)
        main_layout.addWidget(save_button)

        main_layout.addStretch(1)

    def enter_view(self):
        """Llamado cuando la vista se vuelve activa."""
        logger.info("Entrando a la vista de configuración. Sincronizando estado.")
        self._update_ui_from_state(self.trading_mode_manager.current_mode.value)

    def _update_ui_from_state(self, mode_str: str):
        """Actualiza la selección del radio button según el estado actual."""
        try:
            mode = TradingMode(mode_str)
            if mode == TradingMode.PAPER:
                self.paper_mode_radio.setChecked(True)
            elif mode == TradingMode.LIVE:
                self.live_mode_radio.setChecked(True)
        except ValueError:
            logger.error(f"Estado de modo inválido recibido: {mode_str}")

    def _handle_save_button_clicked(self):
        """Maneja el clic en el botón de guardar."""
        selected_mode = TradingMode.LIVE if self.live_mode_radio.isChecked() else TradingMode.PAPER
        current_mode = self.trading_mode_manager.current_mode

        if selected_mode == current_mode:
            QMessageBox.information(self, "Sin Cambios", "El modo seleccionado ya está activo.")
            return

        if selected_mode == TradingMode.LIVE:
            confirmed = ConfirmationDialog.ask(
                "Confirmar Activación de Modo LIVE",
                "¡ADVERTENCIA CRÍTICA!\n\n"
                "Estás a punto de activar el MODO LIVE. "
                "Las operaciones utilizarán DINERO REAL de tu cuenta.\n\n"
                "Asegúrate de entender todos los riesgos. ¿Deseas continuar?",
                self
            )
            if not confirmed:
                self.paper_mode_radio.setChecked(True) # Revertir selección
                logger.info("Activación del modo LIVE cancelada por el usuario.")
                return
        
        self._set_new_mode(selected_mode)

    def _set_new_mode(self, mode: TradingMode):
        """Llama al state manager para cambiar el modo y maneja la respuesta."""
        logger.info(f"Solicitando cambio de modo a {mode.value}")
        
        # Usar el task_manager de la ventana principal para ejecutar la corutina
        if self.main_window:
            self.main_window.submit_task(
                lambda client: self.trading_mode_manager.set_trading_mode(mode),
                self._handle_set_mode_success,
                self._handle_set_mode_error
            )
        else:
            logger.error("No se puede cambiar el modo: main_window no está disponible.")

    def _handle_set_mode_success(self, result: bool):
        if result:
            QMessageBox.information(self, "Éxito", "El modo de operativa ha sido actualizado.")
            logger.info("El modo de operativa se actualizó correctamente.")
        else:
            # El error ya fue logueado en el state manager, aquí solo informamos al usuario
            QMessageBox.critical(self, "Error", "No se pudo actualizar el modo de operativa. Revisa los logs.")
            # Revertir la UI al estado actual del manager
            self._update_ui_from_state(self.trading_mode_manager.current_mode.value)

    def _handle_set_mode_error(self, error_message: str):
        QMessageBox.critical(self, "Error de Comunicación", f"No se pudo cambiar el modo: {error_message}")
        logger.error(f"Error de comunicación al cambiar de modo: {error_message}")
        # Revertir la UI al estado actual del manager
        self._update_ui_from_state(self.trading_mode_manager.current_mode.value)
