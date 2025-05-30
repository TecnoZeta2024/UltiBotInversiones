from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QGroupBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSignal
import logging
from typing import Optional # Importar Optional
from uuid import UUID # Importar UUID
import asyncio # Importar asyncio para manejar corrutinas

from src.ultibot_backend.services.config_service import ConfigService
from src.shared.data_types import UserConfiguration

logger = logging.getLogger(__name__)

class SettingsView(QWidget):
    """
    Vista de configuración para el usuario, incluyendo opciones de Paper Trading.
    """
    # Señal para notificar cambios en la configuración (ej. para actualizar la UI principal)
    config_changed = pyqtSignal(UserConfiguration)

    def __init__(self, user_id: str, config_service: ConfigService, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.config_service = config_service
        self.current_config: Optional[UserConfiguration] = None # Para almacenar la configuración actual

        self._setup_ui()
        asyncio.create_task(self._load_config_into_ui()) # Ejecutar como tarea asyncio

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título de la vista
        title_label = QLabel("Configuración General")
        title_label.setObjectName("settingsTitleLabel") # Para aplicar estilos CSS
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Grupo para Paper Trading
        paper_trading_group = QGroupBox("Modo Paper Trading")
        paper_trading_layout = QVBoxLayout(paper_trading_group)
        paper_trading_layout.setContentsMargins(10, 10, 10, 10)
        paper_trading_layout.setSpacing(10)

        # Control para activar/desactivar Paper Trading
        self.paper_trading_checkbox = QCheckBox("Activar Paper Trading")
        self.paper_trading_checkbox.setStyleSheet("font-size: 16px;")
        paper_trading_layout.addWidget(self.paper_trading_checkbox)

        # Campo para capital virtual inicial
        capital_layout = QHBoxLayout()
        capital_label = QLabel("Capital Virtual Inicial (USDT):")
        capital_label.setStyleSheet("font-size: 14px;")
        self.initial_capital_spinbox = QDoubleSpinBox()
        self.initial_capital_spinbox.setRange(0.0, 10000000.0) # Rango amplio
        self.initial_capital_spinbox.setSingleStep(100.0)
        self.initial_capital_spinbox.setDecimals(2)
        self.initial_capital_spinbox.setStyleSheet("font-size: 14px; padding: 5px;")
        capital_layout.addWidget(capital_label)
        capital_layout.addWidget(self.initial_capital_spinbox)
        capital_layout.addStretch(1) # Empujar a la izquierda
        paper_trading_layout.addLayout(capital_layout)

        main_layout.addWidget(paper_trading_group)

        # Botón para guardar cambios
        save_button = QPushButton("Guardar Cambios")
        save_button.setStyleSheet("padding: 10px 20px; font-size: 16px; font-weight: bold;")
        save_button.clicked.connect(lambda: asyncio.create_task(self._save_config())) # Conectar a una lambda que crea una tarea
        main_layout.addWidget(save_button)

        main_layout.addStretch(1) # Empujar todo hacia arriba

    async def _load_config_into_ui(self):
        """Carga la configuración actual del usuario y la muestra en la UI."""
        try:
            # Asumimos un user_id fijo para la v1.0, como en el backend
            # FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
            self.current_config = await self.config_service.load_user_configuration(UUID(self.user_id))
            
            self.paper_trading_checkbox.setChecked(self.current_config.paperTradingActive or False)
            self.initial_capital_spinbox.setValue(self.current_config.defaultPaperTradingCapital or 10000.0) # Valor por defecto si es None
            logger.info("Configuración de usuario cargada en la UI de Settings.")
        except Exception as e:
            logger.error(f"Error al cargar la configuración en la UI de Settings: {e}", exc_info=True)
            # Mostrar un mensaje de error al usuario si es necesario

    async def _save_config(self):
        """Guarda los cambios de configuración desde la UI al backend."""
        if not self.current_config:
            logger.warning("No hay configuración actual para guardar. Cargando por defecto y reintentando.")
            await self._load_config_into_ui() # Intentar cargar de nuevo
            if not self.current_config:
                # Si aún no hay config, no podemos guardar
                return

        try:
            # Actualizar el objeto de configuración actual con los valores de la UI
            self.current_config.paperTradingActive = self.paper_trading_checkbox.isChecked()
            self.current_config.defaultPaperTradingCapital = self.initial_capital_spinbox.value()

            # Asumimos un user_id fijo para la v1.0
            # FIXED_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
            await self.config_service.save_user_configuration(UUID(self.user_id), self.current_config)
            logger.info("Configuración de usuario guardada exitosamente desde la UI de Settings.")
            self.config_changed.emit(self.current_config) # Emitir señal de cambio
            # Mostrar un mensaje de éxito al usuario
        except Exception as e:
            logger.error(f"Error al guardar la configuración desde la UI de Settings: {e}", exc_info=True)
            # Mostrar un mensaje de error al usuario
