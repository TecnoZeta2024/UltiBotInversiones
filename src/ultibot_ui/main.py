"""
UltiBot Frontend Main Application

Este módulo inicializa y configura la aplicación PyQt5 del frontend UltiBot,
incluyendo la configuración de servicios backend y la interfaz de usuario.

Para ejecutar correctamente la aplicación, use desde la raíz del proyecto:
    poetry run python src/ultibot_ui/main.py
    
O asegúrese de que el directorio raíz del proyecto esté en PYTHONPATH.
"""

import asyncio
import os
import sys
import logging
import logging.handlers # Añadido para RotatingFileHandler
from typing import Optional, Any, Callable, Coroutine, List
from uuid import UUID

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot # Added for ApiWorker
from PyQt5.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv
import qasync  # Añadido para integración Qt+asyncio

# Importaciones organizadas por grupos
from src.shared.data_types import APICredential, ServiceName, UserConfiguration # ServiceName might be unused now
from src.ultibot_backend.app_config import AppSettings
# Backend service imports will be removed or replaced with API client usage
# from ..ultibot_backend.adapters.binance_adapter import BinanceAdapter
# from ..ultibot_backend.adapters.persistence_service import SupabasePersistenceService
# from ..ultibot_backend.services.config_service import ConfigService
# from ..ultibot_backend.services.credential_service import CredentialService
# from ..ultibot_backend.services.market_data_service import MarketDataService
# from ..ultibot_backend.services.notification_service import NotificationService
# from ..ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError # Added
from src.ultibot_ui.windows.main_window import MainWindow

# Importar qdarkstyle de forma segura
try:
    import qdarkstyle
    DARK_STYLE_AVAILABLE = True
except ImportError:
    qdarkstyle = None
    DARK_STYLE_AVAILABLE = False
    print("Advertencia: qdarkstyle no está instalado. La aplicación usará el tema por defecto de Qt.")

logger = logging.getLogger(__name__)

# --- Global Stylesheet for Dark Mode ---
DARK_GLOBAL_STYLESHEET = """
QWidget {
    background-color: #121212; /* Deep dark grey for main background */
    color: #E0E0E0; /* Light grey for text */
    font-family: "Inter", "Roboto", Arial, sans-serif; /* Desired font family */
    font-size: 14px; /* Default body text size */
    font-weight: 400; /* Default body text weight */
}

QFrame, QGroupBox, QTabWidget::pane {
    background-color: #1E1E1E;
    border-radius: 8px;
    border: 1px solid #383838; /* Slightly more defined border for containers */
}

QGroupBox {
    padding: 20px;
    margin-top: 22px;
    font-size: 14px; /* GroupBox content should follow default body font size */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 12px;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C2FF, stop:1 #00FF8C); /* Gradient Blue to Green */
    color: #121212;
    border-radius: 4px;
    margin-left: 12px;
    font-size: 18px;
    font-weight: 600;
}

QLabel {
    background-color: transparent;
    padding: 2px; /* Minimal padding for labels */
}

/* Specific Label Styles based on ObjectName for Typography */
QLabel#viewTitleLabel { /* For main view titles, e.g., "Dashboard", "Opportunities" */
    font-size: 22px;
    font-weight: 600;
    color: #E0E0E0;
    padding-bottom: 8px;
    border: none; /* Ensure no accidental borders from QFrame inheritance */
}
QLabel#sectionTitleLabel {
    font-size: 18px;
    font-weight: 500;
    color: #00FF8C;
    margin-bottom: 6px;
    border: none;
}
QLabel#statusLabel {
    font-size: 12px;
    color: #999999; /* Slightly darker grey for status */
    font-style: italic;
    border: none;
}
QLabel#dataDisplayLabel {
    font-size: 16px;
    font-weight: 500;
    color: #00C2FF;
    border: none;
}
QLabel#smallDetailLabel { /* For less important labels like "Filtrar por modo:" */
    font-size: 12px;
    color: #BBBBBB; /* Lighter than status, but not primary */
    border: none;
}


QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007BFF, stop:1 #00C2FF); /* Blue gradient */
    color: #FFFFFF; /* White text on button */
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0056b3, stop:1 #00A0DD); /* Darker blue gradient */
}
QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #004085, stop:1 #007BFF); /* Even darker */
}
QPushButton:disabled {
    background-color: #2A2A2A; /* Darker grey for disabled */
    color: #555555;
}

QPushButton#accentButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF8C, stop:1 #00DB7A); /* Green gradient */
    color: #121212;
}
QPushButton#accentButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00DB7A, stop:1 #00C2FF); /* Green to blue gradient on hover */
}
QPushButton#accentButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B36B, stop:1 #00A0DD);
}


QTableWidget {
    gridline-color: #383838;
    background-color: #1A1A1A; /* Slightly darker table background */
    border: 1px solid #383838;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #222222;
    color: #00FF8C; /* Green accent for header text */
    padding: 8px;
    border: 1px solid #383838;
    font-size: 14px;
    font-weight: 600; /* Bolder header */
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2A2A2A;
    color: #DDDDDD; /* Slightly brighter item text */
}
QTableWidget::item:selected {
    background-color: #007BFF; /* Blue selection */
    color: #FFFFFF;
}
QTableWidget::item { /* Monospace for data */
    font-family: "Consolas", "Menlo", "Monaco", "Lucida Console", monospace;
}


QComboBox {
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #222222; /* Darker combo box */
    min-height: 24px;
    font-size: 14px;
    color: #E0E0E0;
}
QComboBox:editable {
    background: #222222;
}
QComboBox:!editable, QComboBox::drop-down:editable {
     background: #282828;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left-width: 1px;
    border-left-color: #383838;
    border-left-style: solid;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
/* QComboBox::down-arrow: Needs resource file or SVG icon */


QScrollBar:vertical {
    border: none;
    background: #1A1A1A; /* Darker scrollbar track */
    width: 14px;
    margin: 14px 0 14px 0;
}
QScrollBar::handle:vertical {
    background: #00C2FF; /* Blue accent for handle */
    min-height: 30px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #00A0DD; /* Darker blue on hover */
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #1A1A1A;
    height: 14px;
    margin: 0 14px 0 14px;
}
QScrollBar::handle:horizontal {
    background: #00C2FF;
    min-width: 30px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover {
    background: #00A0DD;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}

QTabWidget::pane {
    border-top: 2px solid #00FF8C; /* Green accent line for pane top */
    padding: 16px;
    background-color: #1E1E1E;
}
QTabBar::tab {
    background: #1E1E1E;
    border: 1px solid #383838;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 120px;
    padding: 10px 12px;
    font-size: 14px;
    font-weight: 600; /* Bolder tab labels */
    color: #999999; /* Dimmer unselected tab text */
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #2A2A2A;
    color: #00FF8C; /* Green accent for selected/hovered tab text */
}
QTabBar::tab:selected {
    border-color: #00FF8C;
    border-bottom: 2px solid #2A2A2A;
    margin-bottom: -1px;
}
QTabBar::tab:!selected {
    margin-top: 3px;
}


QFrame#headerFrame {
    background-color: #1E1E1E;
    border-bottom: 2px solid #00C2FF; /* Blue accent for header */
    border-radius: 0px;
    padding: 8px;
}

QProgressBar {
    border: 1px solid #383838;
    border-radius: 6px;
    text-align: center;
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-weight: 600; /* Bolder progress text */
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF8C, stop:1 #00C2FF); /* Green to Blue gradient */
    border-radius: 5px;
}
"""

# --- Light Mode Global Stylesheet ---
LIGHT_GLOBAL_STYLESHEET = """
QWidget {
    background-color: #F8F9FA; /* Light grey for main background */
    color: #212529; /* Dark grey for text */
    font-family: "Inter", "Roboto", Arial, sans-serif;
    font-size: 14px;
    font-weight: 400;
}

QFrame, QGroupBox, QTabWidget::pane {
    background-color: #FFFFFF; /* White for containers */
    border-radius: 8px;
    border: 1px solid #DEE2E6; /* Subtle border */
}

QGroupBox {
    padding: 20px;
    margin-top: 22px;
    font-size: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 12px;
    background-color: #0099E5; /* Softer Blue accent for group titles */
    color: #FFFFFF; /* White text on blue accent */
    border-radius: 4px;
    margin-left: 12px;
    font-size: 18px;
    font-weight: 600;
}

QLabel {
    background-color: transparent;
    padding: 2px;
}

QLabel#viewTitleLabel {
    font-size: 22px;
    font-weight: 600;
    color: #212529;
    padding-bottom: 8px;
}
QLabel#sectionTitleLabel {
    font-size: 18px;
    font-weight: 500;
    color: #00CC7A; /* Softer Green accent */
    margin-bottom: 6px;
}
QLabel#statusLabel {
    font-size: 12px;
    color: #6C757D; /* Greyer for status */
    font-style: italic;
}
QLabel#dataDisplayLabel {
    font-size: 16px;
    font-weight: 500;
    color: #0099E5; /* Softer Blue accent */
}
QLabel#smallDetailLabel {
    font-size: 12px;
    color: #6C757D;
}

QPushButton {
    background-color: #007BFF; /* Standard blue */
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #0056b3;
}
QPushButton:disabled {
    background-color: #E0E0E0;
    color: #AAAAAA;
}
QPushButton#accentButton {
    background-color: #00CC7A; /* Softer green */
    color: #FFFFFF;
}
QPushButton#accentButton:hover {
    background-color: #00B36B;
}


QTableWidget {
    gridline-color: #DEE2E6;
    background-color: #FFFFFF;
    border: 1px solid #DEE2E6;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #E9ECEF;
    color: #212529;
    padding: 8px;
    border: 1px solid #DEE2E6;
    font-size: 14px;
    font-weight: 500;
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #DEE2E6;
}
QTableWidget::item:selected {
    background-color: #007BFF;
    color: white;
}
QTableWidget::item { /* Monospace numbers */
    font-family: "Consolas", "Menlo", "Monaco", monospace;
}


QComboBox {
    border: 1px solid #CED4DA;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #FFFFFF;
    min-height: 24px;
    font-size: 14px;
}
QComboBox:editable {
    background: #FFFFFF;
}
QComboBox:!editable, QComboBox::drop-down:editable {
     background: #E9ECEF;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left-width: 1px;
    border-left-color: #CED4DA;
    border-left-style: solid;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}
/* QComboBox::down-arrow: Needs light version of icon */


QScrollBar:vertical {
    border: none;
    background: #F8F9FA;
    width: 14px;
    margin: 14px 0 14px 0;
}
QScrollBar::handle:vertical {
    background: #CED4DA;
    min-height: 30px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #ADB5BD;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #F8F9FA;
    height: 14px;
    margin: 0 14px 0 14px;
}
QScrollBar::handle:horizontal {
    background: #CED4DA;
    min-width: 30px;
    border-radius: 7px;
}
QScrollBar::handle:horizontal:hover {
    background: #ADB5BD;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}

QTabWidget::pane {
    border-top: 2px solid #0099E5; /* Softer Blue accent line */
    padding: 16px;
    background-color: #FFFFFF;
}
QTabBar::tab {
    background: #E9ECEF;
    border: 1px solid #DEE2E6;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 120px;
    padding: 10px 12px;
    font-size: 14px;
    font-weight: 500;
    color: #495057;
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #FFFFFF;
    color: #0099E5;
}
QTabBar::tab:selected {
    border-color: #0099E5;
    border-bottom: 2px solid #FFFFFF;
    margin-bottom: -1px;
}
QTabBar::tab:!selected {
    margin-top: 3px;
}

QFrame#headerFrame {
    background-color: #FFFFFF;
    border-bottom: 2px solid #00CC7A; /* Softer Green separator */
    border-radius: 0px;
    padding: 8px;
}

QProgressBar {
    border: 1px solid #CED4DA;
    border-radius: 6px;
    text-align: center;
    background-color: #E9ECEF;
    color: #212529;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #00CC7A; /* Softer Green accent */
    border-radius: 5px;
}
"""


# --- ApiWorker using QThread as per docs/front-end-api-interaction.md ---
# (ApiWorker class definition remains unchanged here)
# To make apply_application_style accessible, it's better as a standalone function
# or part of UltiBotApplication if it needs access to app instance variables,
# but for stylesheets, a standalone function that gets QApplication.instance() is fine.

def apply_application_style(theme_name: str):
    """Applies the global stylesheet for the given theme."""
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if not app:
        print("QApplication instance not found. Cannot apply style.")
        return
    # Defensive: try to get the top-level widgets and apply stylesheet to all
    base_style = ""
    if DARK_STYLE_AVAILABLE and qdarkstyle:
        base_style = qdarkstyle.load_stylesheet_pyqt5()
    stylesheet = base_style + (LIGHT_GLOBAL_STYLESHEET if theme_name == "light" else DARK_GLOBAL_STYLESHEET)
    try:
        # Try to apply to all top-level widgets
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, 'setStyleSheet'):
                widget.setStyleSheet(stylesheet)
        logger.info(f"Applied {theme_name} theme to all top-level widgets.")
    except Exception as e:
        print(f"Failed to apply stylesheet to top-level widgets: {e}")

class ApiWorker(QObject): # ApiWorker definition moved slightly to accommodate the function above
    """
    Worker object to perform asynchronous API calls in a separate thread.
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, awaitable_coroutine: Coroutine):
        super().__init__()
        self.awaitable_coroutine = awaitable_coroutine
        self.main_loop = asyncio.get_event_loop() # Obtener el bucle principal

    @pyqtSlot()
    def run(self):
        """
        Programa la coroutine en el bucle de eventos principal.
        """
        def _task_done(task):
            try:
                result = task.result()
                self.result_ready.emit(result)
            except APIError as e:
                error_msg = f"API Error ({e.status_code}): {e.message}"
                if e.response_json and 'detail' in e.response_json:
                    if isinstance(e.response_json['detail'], list):
                        details = ", ".join([err.get('msg', 'validation error') for err in e.response_json['detail']])
                        error_msg += f" - Details: {details}"
                    else:
                        error_msg += f" - Detail: {e.response_json['detail']}" # Corregido a f-string
                self.error_occurred.emit(error_msg)
            except Exception as e:
                self.error_occurred.emit(f"Unexpected error in API worker: {str(e)}")
            finally:
                # Asegurarse de que el hilo se cierre después de emitir la señal
                if self.thread(): # Verificar si el hilo existe
                    self.thread().quit() # Terminar el QThread

        # Programar la coroutine en el bucle principal de forma segura entre hilos
        self.main_loop.call_soon_threadsafe(
            lambda: self.main_loop.create_task(self.awaitable_coroutine).add_done_callback(_task_done)
        )


class UltiBotApplication:
    """
    Clase principal para manejar la aplicación UltiBot UI.
    
    Encapsula la inicialización de servicios, configuración y UI.
    """
    
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.settings: Optional[AppSettings] = None
        self.user_id: Optional[UUID] = None
        self.active_threads: List[QThread] = [] # To keep track of active threads

        # API Client - Single point of contact for backend services
        self.api_client: Optional[UltiBotAPIClient] = None

        # The following backend service instances will be removed:
        # self.persistence_service: Optional[SupabasePersistenceService] = None
        # self.credential_service: Optional[CredentialService] = None
        # self.market_data_service: Optional[MarketDataService] = None
        # self.config_service: Optional[ConfigService] = None
        # self.notification_service: Optional[NotificationService] = None
        # self.portfolio_service: Optional[PortfolioService] = None
        # self.binance_adapter: Optional[BinanceAdapter] = None
    
    def setup_qt_application(self) -> QApplication:
        """
        Configura la aplicación PyQt5.
        
        Returns:
            QApplication: Instancia de la aplicación Qt configurada.
        """
        app = QApplication(sys.argv)
        # Aplicar el tema oscuro si está disponible y qdarkstyle está importado correctamente
        if DARK_STYLE_AVAILABLE and qdarkstyle is not None:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.app = app
        return app
    
    def load_configuration(self) -> AppSettings:
        """
        Carga la configuración desde variables de entorno.
        """
        load_dotenv(override=True)
        credential_encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not credential_encryption_key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY no está configurada en .env file o variables de entorno."
            )
        # Lee la URL base del backend desde la variable de entorno, con fallback
        base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
        settings = AppSettings(CREDENTIAL_ENCRYPTION_KEY=credential_encryption_key)
        self.settings = settings
        self.user_id = settings.FIXED_USER_ID
        # Inicializa el API Client usando la URL del .env
        self.api_client = UltiBotAPIClient(base_url=base_url)
        return settings

    # Removed initialize_persistence_service method as persistence will be handled by the backend via API client.
    # async def initialize_persistence_service(self) -> SupabasePersistenceService: ...

    # Removed _ensure_user_exists_in_db method as this logic should be backend or handled by API calls.
    # async def _ensure_user_exists_in_db(self, persistence_service: SupabasePersistenceService) -> None: ...

    async def initialize_core_services(self) -> None:
        """
        Initializes core aspects of the application.
        Now primarily involves ensuring the API client is ready.
        """
        if not self.settings:
            raise RuntimeError("Configuration not loaded")
        if not self.api_client:
            raise RuntimeError("API Client not initialized")
        
        try:
            # Este bloque puede ser extendido con lógica de healthcheck si es necesario
            print("API Client is configurado. Core services are now accesibles via the API client.")
        except APIError as e:
            raise RuntimeError(f"Failed to connect or initialize with API backend: {e}")

    async def ensure_user_configuration(self) -> Any:
        """
        Ensures that user configuration is loaded via the API using a non-blocking worker.
        Returns the user configuration or raises an exception if it fails.
        """
        if not self.api_client:
            raise RuntimeError("API Client not initialized for ensure_user_configuration")
        if not self.user_id:
            raise RuntimeError("User ID not initialized for ensure_user_configuration")

        logger.info(f"Starting to fetch user configuration for {self.user_id} via API worker...")
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        worker = ApiWorker(self.api_client.get_user_configuration())
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        def _on_result(result):
            if not future.done():
                loop.call_soon_threadsafe(future.set_result, result)
        def _on_error(error_msg):
            if not future.done():
                loop.call_soon_threadsafe(future.set_exception, Exception(error_msg))

        worker.result_ready.connect(_on_result)
        worker.error_occurred.connect(_on_error)
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: self.active_threads.remove(thread) if thread in self.active_threads else None)
        thread.start()
        return await future

    async def setup_binance_credentials(self) -> None:
        """
        Configura las credenciales de Binance desde variables de entorno.
        
        Raises:
            ValueError: If Binance credentials are not found in environment variables.
            Exception: If there's an issue with credential setup.
        """
        # TODO: This method needs significant refactoring.
        # The API client (as per current api_client.py) does not have methods for:
        # - Directly adding credentials (e.g., self.api_client.add_credential(...))
        # - Directly getting a specific credential (e.g., self.api_client.get_credential(...))
        # This functionality might need to be moved to the backend, or the API client expanded.
        # For now, this method will be partially disabled or logged as a warning.

        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")

        if not binance_api_key or not binance_api_secret:
            print("Advertencia: BINANCE_API_KEY o BINANCE_API_SECRET no encontradas. Omitiendo guardado automático de credenciales de Binance.")
            # raise ValueError("BINANCE_API_KEY o BINANCE_API_SECRET no encontradas...")
            return # Cannot proceed with saving if keys are not present

        if not self.api_client:
            raise RuntimeError("API Client not initialized")
        if not self.user_id:
            raise RuntimeError("user_id no inicializado")

        print("NOTA: La lógica de 'setup_binance_credentials' para guardar credenciales directamente"
              " desde el UI está siendo refactorizada.")
        print("Idealmente, la adición de credenciales se haría a través de un endpoint API seguro.")
        print("Por ahora, se omitirá el guardado directo y la verificación de credenciales existentes"
              " que dependían de CredentialService.")

        # Current API client does not support these direct credential operations:
        # - Check if credentials exist:
        #   response = await self.api_client.get_credential_status(service_name=ServiceName.BINANCE_SPOT) ( hypothetical )
        #   if response and response.get("configured"):
        #       print("Credenciales de Binance ya configuradas según API. Se omite adición desde .env.")
        #       return
        #
        # - Add credentials:
        #   await self.api_client.add_binance_credential(api_key=binance_api_key, api_secret=binance_api_secret) ( hypothetical )
        #   print("Solicitud para guardar credenciales de Binance enviada a la API.")

        # Since the direct methods are not available, we log this and potentially skip.
        # For the purpose of this refactor, we cannot call non-existent API client methods.
        # If the application relies on these credentials being present for other startup processes
        # that *are* being refactored to use the API client, this could be a problem.
        # Sin embargo, la tarea es refactorizar para *usar* el cliente API. Si falta funcionalidad
        # en el cliente para este paso específico, lo anotamos.

    def create_main_window(self) -> MainWindow:
        """
        Crea y configura la ventana principal.
        
        Returns:
            MainWindow: Instance of the main configured window.
            
        Raises:
            RuntimeError: If required services (now the API client) are not initialized.
        """
        if self.user_id is None:
            raise RuntimeError("user_id not initialized")
        if self.api_client is None:
            raise RuntimeError("api_client not initialized")

        # MainWindow will now receive the api_client instead of individual services.
        # This requires MainWindow to be refactored as well.
        main_window = MainWindow(
            user_id=self.user_id,
            api_client=self.api_client  # Pass the API client
        )
        self.main_window = main_window
        return main_window
    
    async def cleanup_resources(self) -> None:
        """
        Cleans up asynchronous resources.
        The API client uses httpx.AsyncClient with context managers,
        so explicit cleanup of the client itself might not be needed here
        unless it holds other resources that need explicit closing.
        """
        print("Iniciando limpieza de recursos asíncronos...")
        
        # Old cleanup tasks for direct services are removed.
        # cleanup_tasks = [
        #     ("PersistenceService", self.persistence_service),
        #     ("MarketDataService", self.market_data_service),
        # ]
        
        # If UltiBotAPIClient had an explicit close/disconnect method, it would be called here.
        # e.g., if self.api_client and hasattr(self.api_client, 'close'):
        #     await self.api_client.close()
        
        print("Limpieza de recursos asíncronos (ahora minimal, API client manages its connections).")
    
    def show_error_and_exit(self, title: str, message: str, exit_code: int = 1) -> None:
        """
        Muestra un mensaje de error y termina la aplicación.
        
        Args:
            title: Título del mensaje de error.
            message: Mensaje de error detallado.
            exit_code: Código de salida de la aplicación.
        """
        if self.app:
            QMessageBox.critical(None, title, f"{message}\\n\\nLa aplicación se cerrará.")
        else:
            print(f"ERROR - {title}: {message}")
        sys.exit(exit_code)


async def run_application() -> None:
    """
    Función principal para ejecutar la aplicación UltiBot.
    """
    ultibot_app = UltiBotApplication()
    
    try:
        # 1. Configurar aplicación PyQt5
        qt_app = ultibot_app.setup_qt_application()
        
        # Apply global stylesheet
        # Initial theme application moved to apply_application_style function
        # The setup_qt_application might apply qdarkstyle initially.
        # We then call our function to set the specific dark/light theme on top.
        apply_application_style("dark") # Default to dark theme on startup

        # To test light theme on startup, change "dark" to "light" above:
        # apply_application_style("light")


        # Initialize event loop for QThread integration if needed later,
        # but ApiWorker creates its own loop for the thread.

        # 2. Cargar configuración (includes API client initialization)
        settings = ultibot_app.load_configuration()
        
        # 3. Initialize core services (now mostly about ensuring API client is ready)
        await ultibot_app.initialize_core_services() # This is async

        # 4. Asegurar configuración de usuario (via API)
        # This needs to be handled carefully with ApiWorker in an async context.
        # For initial setup, if `ensure_user_configuration` becomes synchronous
        # and launches a thread, `run_application` can't `await` it directly.
        # We'll need a bridge or redesign how startup sequence works.

        # Let's assume for now ensure_user_configuration is still awaitable here,
        # and we'll integrate the QThread non-blocking call within it,
        # using an asyncio.Future to bridge QThread signal back to awaitable context.

        # `ensure_user_configuration` now returns a future. We await it.
        user_config_future = ultibot_app.ensure_user_configuration()
        try:
            user_config = await asyncio.wait_for(user_config_future, timeout=30)
            print(f"User configuration loaded successfully via ApiWorker: {user_config}")
        except asyncio.TimeoutError:
            ultibot_app.show_error_and_exit(
                "Timeout de configuración de usuario",
                "No se recibió respuesta del backend o del hilo de configuración en 30 segundos.\n\nVerifica la conexión y los logs del backend/frontend."
            )
            return
        except Exception as e:
            ultibot_app.show_error_and_exit(
                "Error de Configuración de Usuario",
                f"No se pudo cargar la configuración del usuario: {str(e)}"
            )
            return
        
        # 5. Configurar credenciales de Binance (functionality limited by current API client capabilities)
        await ultibot_app.setup_binance_credentials() # This is async
        
        # 6. Crear y mostrar ventana principal (will receive API client)
        # This must happen after essential async setups are "complete" from UI perspective.
        main_window = ultibot_app.create_main_window()
        main_window.show()
        
        # 8. Ejecutar loop de eventos de Qt
        exit_code = qt_app.exec_()
        
        # 9. Limpieza de recursos
        await ultibot_app.cleanup_resources() # Includes stopping threads if any are still running (though they should finish)

        sys.exit(exit_code)
        
    except ValueError as ve: # Typically from load_configuration or early settings issues
        ultibot_app.show_error_and_exit(
            "Error de Configuración Inicial", # Changed title for clarity
            f"Error de configuración: {str(ve)}\\n\\nPor favor verifique su archivo .env o variables de entorno."
        )
    
    except Exception as e: # Catch-all for other errors during async setup
        # This will also catch errors from `await future` if not handled by specific try-except
        ultibot_app.show_error_and_exit(
            "Error de Inicialización de la Aplicación", # Changed title
            f"Falló la inicialización de la aplicación: {str(e)}"
        )


def main() -> None:
    """
    Punto de entrada principal de la aplicación.
    Configura el event loop apropiado para Windows y ejecuta la aplicación.
    """
    print("[DEBUG] Entrando a main() de ultibot_ui.main.py")

    # Configuración de logging con RotatingFileHandler para limitar el tamaño del log
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file_path = os.path.join(log_dir, "frontend.log")
    
    handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=100000,  # Aproximadamente 100KB
        backupCount=0,    # No mantener archivos de backup, solo el actual (se rota/sobrescribe)
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for h_existente in root_logger.handlers[:]:
            root_logger.removeHandler(h_existente)
            
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    logger.info("Logging configurado con RotatingFileHandler para escribir en logs/frontend.log (max ~100KB).")

    # Solución para Windows ProactorEventLoop con psycopg
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Ejecutar la aplicación asíncrona
    asyncio.run(run_application())

if __name__ == "__main__":
    main()
