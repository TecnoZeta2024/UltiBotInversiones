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


def apply_application_style(theme_name: str):
    """Applies the global stylesheet for the given theme."""
    app_instance = QApplication.instance()
    if not app_instance:
        logger.error("QApplication instance not found in apply_application_style. Cannot apply style.")
        return

    if not isinstance(app_instance, QApplication):
        logger.error(
            f"Instance type in apply_application_style is {type(app_instance)}, not QApplication. "
            "Cannot apply stylesheet."
        )
        return
        
    app = app_instance # Now we know it's a QApplication
    base_style = ""
    if DARK_STYLE_AVAILABLE and qdarkstyle:
        base_style = qdarkstyle.load_stylesheet_pyqt5()
    stylesheet = base_style + (LIGHT_GLOBAL_STYLESHEET if theme_name == "light" else DARK_GLOBAL_STYLESHEET)
    try:
        app.setStyleSheet(stylesheet) # Apply to the application instance directly
        logger.info(f"Applied {theme_name} theme to the application.")
    except Exception as e:
        print(f"Failed to apply stylesheet to application: {e}")

class ApiWorker(QObject):
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, coroutine_factory: Callable[[UltiBotAPIClient], Coroutine], base_url: str): # Modificado: recibe base_url
        super().__init__()
        self.coroutine_factory = coroutine_factory
        self.base_url = base_url # Almacena base_url
        logger.debug(f"ApiWorker initialized with base_url: {self.base_url}")

    @pyqtSlot()
    def run(self):
        loop = None
        api_client_instance = None # Nueva instancia de api_client para este hilo
        try:
            # Crea y configura un event loop DEDICADO para este hilo
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Crea una nueva instancia de UltiBotAPIClient para este hilo y su bucle de eventos
            api_client_instance = UltiBotAPIClient(base_url=self.base_url)
            
            coroutine = self.coroutine_factory(api_client_instance) # Pasa la instancia al factory
            task = loop.create_task(coroutine) # Crear la tarea
            
            result = loop.run_until_complete(task)
            self.result_ready.emit(result)
        except asyncio.CancelledError:
            logger.info(f"ApiWorker: Coroutine was cancelled in worker loop {loop}.")
            self.error_occurred.emit("Operación cancelada.")
        except APIError as e_api:
            logger.error(
                f"ApiWorker: APIError caught during coroutine execution: {e_api.message}, "
                f"status: {e_api.status_code}, response: {e_api.response_json}",
                exc_info=True
            )
            error_msg = f"API Error ({e_api.status_code}): {e_api.message}"
            if e_api.response_json and 'detail' in e_api.response_json:
                if isinstance(e_api.response_json['detail'], list):
                    details = ", ".join([err.get('msg', 'validation error') for err in e_api.response_json['detail']])
                    error_msg += f" - Details: {details}"
                else:
                    error_msg += f" - Detail: {e_api.response_json['detail']}"
            self.error_occurred.emit(error_msg)
        except Exception as exc: # pylint: disable=broad-except
            logger.error(
                f"ApiWorker: Generic Exception caught during coroutine execution: {str(exc)}",
                exc_info=True
            )
            self.error_occurred.emit(str(exc))
        finally:
            # Asegurarse de cerrar el cliente HTTP de este hilo
            if api_client_instance and loop: # Añadida verificación 'and loop'
                logger.debug(f"ApiWorker: Cerrando httpx.AsyncClient para worker loop {loop}.")
                # Ejecutar aclose de forma síncrona en este hilo, ya que el bucle está a punto de cerrarse
                try:
                    loop.run_until_complete(api_client_instance.aclose())
                    logger.debug(f"ApiWorker: httpx.AsyncClient cerrado para worker loop {loop}.")
                except Exception as e_aclose:
                    logger.error(f"ApiWorker: Error al cerrar httpx.AsyncClient en worker loop {loop}: {e_aclose}", exc_info=True)

            if loop and loop.is_running(): # Solo intentar limpiar si el loop está corriendo
                try:
                    # Cancelar todas las tareas pendientes en este bucle de eventos
                    pending_tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
                    if pending_tasks:
                        logger.debug(f"ApiWorker: Cancelling {len(pending_tasks)} pending tasks in worker loop {loop}.")
                        for t in pending_tasks:
                            t.cancel()
                        # Esperar a que las tareas se cancelen. return_exceptions=True para no fallar si una tarea ya está cancelada.
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                        logger.debug(f"ApiWorker: Pending tasks cancelled and awaited in worker loop {loop}.")

                    # Apagar los generadores asíncronos
                    if hasattr(loop, 'shutdown_asyncgens'):
                        logger.debug(f"ApiWorker: Shutting down async generators in worker loop {loop}.")
                        loop.run_until_complete(loop.shutdown_asyncgens())
                        logger.debug(f"ApiWorker: Async generators shut down in worker loop {loop}.")

                    # Apagar el ejecutor por defecto (ThreadPoolExecutor)
                    # Esto es crucial para evitar "cannot schedule new futures after shutdown"
                    if hasattr(loop, 'shutdown_default_executor'):
                        logger.debug(f"ApiWorker: Shutting down default executor in worker loop {loop}.")
                        loop.run_until_complete(loop.shutdown_default_executor())
                        logger.debug(f"ApiWorker: Default executor shut down in worker loop {loop}.")

                except Exception as e_shutdown:
                    logger.error(f"ApiWorker: Error during worker loop shutdown procedures: {e_shutdown}", exc_info=True)
                finally:
                    if not loop.is_closed():
                        loop.close()
                        logger.info(f"ApiWorker: Event loop {loop} closed.")
                    else:
                        logger.info(f"ApiWorker: Event loop {loop} was already closed.")
            else:
                logger.info(f"ApiWorker: Event loop {loop} is not running or already closed. Skipping shutdown procedures.")
            
            # Siempre desvincular el bucle de eventos del hilo actual
            asyncio.set_event_loop(None)
            logger.debug("ApiWorker: asyncio event loop for current OS thread set to None.")


class UltiBotApplication:
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.settings: Optional[AppSettings] = None
        self.user_id: Optional[UUID] = None
        self.active_threads: List[QThread] = []
        self.api_client: Optional[UltiBotAPIClient] = None # Este ya no se usará para llamadas en hilos
        self.backend_base_url: str = "http://localhost:8000" # Nueva propiedad para pasar a ApiWorker
        self.qasync_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def setup_qt_application(self) -> None:
        """
        Further configures the PyQt5 application if needed.
        Assumes self.app is already an initialized QApplication instance.
        """
        if not self.app:
            raise RuntimeError("QApplication instance not set on UltiBotApplication before calling setup_qt_application.")
        # Further specific setups for self.app can go here if necessary.
        # qdarkstyle and custom theme are handled by apply_application_style,
        # which is called in run_application after this method.
        logger.info("UltiBotApplication.setup_qt_application() called. QApplication instance confirmed.")
    
    def load_configuration(self) -> AppSettings:
        load_dotenv(override=True)
        credential_encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        if not credential_encryption_key:
            raise ValueError(
                "CREDENTIAL_ENCRYPTION_KEY no está configurada en .env file o variables de entorno."
            )
        self.backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000") # Asignar a la nueva propiedad
        settings = AppSettings(CREDENTIAL_ENCRYPTION_KEY=credential_encryption_key)
        self.settings = settings
        self.user_id = settings.FIXED_USER_ID
        # self.api_client = UltiBotAPIClient(base_url=self.backend_base_url) # Ya no se inicializa aquí para llamadas en hilos
        return settings

    async def initialize_core_services(self) -> None:
        if not self.settings:
            raise RuntimeError("Configuration not loaded")
        # if not self.api_client: # Ya no se usa directamente aquí
        #     raise RuntimeError("API Client not initialized")
        
        # Para verificar la conexión inicial, podemos crear un cliente temporal
        temp_api_client = UltiBotAPIClient(base_url=self.backend_base_url)
        try:
            print("API Client is configurado. Core services are now accesible via the API client.")
            # Opcional: probar la conexión aquí
            # if not await temp_api_client.test_connection():
            #     raise APIError(message="Backend connection test failed.")
        except APIError as e:
            raise RuntimeError(f"Failed to connect or initialize with API backend: {e}")
        finally:
            await temp_api_client.aclose() # Asegurarse de cerrar el cliente temporal

    async def ensure_user_configuration(self) -> Any:
        # if not self.api_client: # Ya no se usa directamente aquí
        #     raise RuntimeError("API Client not initialized for ensure_user_configuration")
        if not self.user_id:
            raise RuntimeError("User ID not initialized for ensure_user_configuration")

        logger.info(f"Starting to fetch user configuration for {self.user_id} via API worker...")
        
        loop = self.qasync_loop # Use the stored qasync_loop
        if not loop:
            logger.error("QAsync loop not available in ensure_user_configuration")
            raise RuntimeError("QAsync loop not set in UltiBotApplication")
        logger.debug(f"ensure_user_configuration: Using qasync event loop: {loop}")
        future = loop.create_future()

        # La coroutine_factory ahora acepta un api_client_instance
        worker = ApiWorker(lambda api_client: api_client.get_user_configuration(), self.backend_base_url) # Pasa base_url
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

        # El hilo debe terminar después de que el worker haya emitido su resultado/error
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)

        # El worker se autoelimina DESPUÉS de emitir la señal.
        # Esto asegura que el worker sigue vivo mientras emite y sus slots conectados son llamados.
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)

        # El thread se elimina a sí mismo cuando termina.
        # Ya NO conectamos thread.finished directamente a worker.deleteLater
        thread.finished.connect(thread.deleteLater) 
        thread.finished.connect(lambda t=thread: self.active_threads.remove(t) if t in self.active_threads else None)
        
        thread.start()
        return await future

    async def setup_binance_credentials(self) -> None:
        binance_api_key = os.getenv("BINANCE_API_KEY")
        binance_api_secret = os.getenv("BINANCE_API_SECRET")

        if not binance_api_key or not binance_api_secret:
            print("Advertencia: BINANCE_API_KEY o BINANCE_API_SECRET no encontradas. Omitiendo guardado automático de credenciales de Binance.")
            return

        # if not self.api_client: # Ya no se usa directamente aquí
        #     raise RuntimeError("API Client not initialized")
        if not self.user_id:
            raise RuntimeError("user_id no inicializado")

        print("NOTA: La lógica de 'setup_binance_credentials' para guardar credenciales directamente"
              " desde el UI está siendo refactorizada.")
        
        # Si esta función necesita hacer una llamada a la API,
        # debería usar un ApiWorker o crear un cliente temporal aquí.
        # Por ahora, solo es un print.

    def create_main_window(self) -> MainWindow:
        if self.user_id is None:
            raise RuntimeError("user_id not initialized")
        # if self.api_client is None: # Ya no se usa directamente aquí
        #     raise RuntimeError("api_client not initialized")
        if self.qasync_loop is None:
            raise RuntimeError("qasync_loop not initialized in UltiBotApplication for create_main_window")

        # MainWindow ahora recibirá la base_url para que sus widgets puedan crear ApiWorkers
        main_window = MainWindow(
            user_id=self.user_id,
            backend_base_url=self.backend_base_url, # Pasa la base_url
            qasync_loop=self.qasync_loop
        )
        self.main_window = main_window
        return main_window
    
    async def cleanup_resources(self) -> None: # Cambiado a asíncrono
        logger.info("Iniciando limpieza de recursos de UltiBotApplication.")
        
        # Crear una copia de la lista para evitar problemas de modificación durante la iteración
        threads_to_clean = self.active_threads[:] 
        self.active_threads.clear() # Limpiar la lista original inmediatamente

        for thread in threads_to_clean: 
            if thread.isRunning():
                logger.info(f"Sending quit signal to thread {thread} and waiting for it to finish...")
                thread.quit() 
                # Esperar indefinidamente a que el hilo termine. Esto es crucial.
                # Si el hilo no responde a quit(), wait() bloqueará hasta que termine o se termine forzosamente.
                if not thread.wait(30000): # Aumentar el timeout a 30 segundos
                    logger.warning(f"Thread {thread} did not finish in time (30s). Forcing termination.")
                    thread.terminate() 
                    thread.wait() # Esperar a que la terminación forzada se complete
            else:
                logger.info(f"Thread {thread} is not running, skipping cleanup.")
        
        logger.info(f"All active QThreads processed for cleanup. Remaining: {len(self.active_threads)}.")
        
        # Añadir una pequeña espera para permitir que las tareas pendientes en el bucle principal se resuelvan
        # antes de que el bucle principal se cierre completamente.
        await asyncio.sleep(0.1) # Espera de 100ms
        
        print("Limpieza de recursos completada.")
    
    def show_error_and_exit(self, title: str, message: str, exit_code: int = 1) -> None:
        if self.app:
            QMessageBox.critical(None, title, f"{message}\\n\\nLa aplicación se cerrará.")
        else:
            print(f"ERROR - {title}: {message}")
        sys.exit(exit_code)


async def run_application(qt_app_instance: QApplication, q_event_loop: qasync.QEventLoop) -> int:
    ultibot_app = UltiBotApplication()
    ultibot_app.app = qt_app_instance
    ultibot_app.qasync_loop = q_event_loop # Store the qasync loop
    
    exit_code = 0
    try:
        ultibot_app.setup_qt_application() 
        apply_application_style("dark") 
        ultibot_app.load_configuration() # Esto carga backend_base_url
        await ultibot_app.initialize_core_services()
        try:
            # Aumentamos el timeout y agregamos reintentos para la obtención de la configuración del usuario
            retries = 3
            timeout_per_try = 15
            retry_count = 0
            last_error = None
            
            while retry_count < retries:
                try:
                    logger.info(f"Intentando obtener configuración de usuario (intento {retry_count+1}/{retries})...")
                    user_config = await asyncio.wait_for(ultibot_app.ensure_user_configuration(), timeout=timeout_per_try)
                    logger.info(f"User configuration loaded successfully: {user_config}")
                    break  # Si tiene éxito, salimos del bucle
                except asyncio.TimeoutError as e:
                    retry_count += 1
                    last_error = e
                    if retry_count < retries:
                        logger.warning(f"Timeout al obtener configuración de usuario (intento {retry_count}/{retries}). Reintentando...")
                        await asyncio.sleep(2)  # Esperar 2 segundos antes de reintentar
                    else:
                        raise  # Relanzar la excepción si agotamos los intentos
                except Exception as e:
                    retry_count += 1
                    last_error = e
                    if retry_count < retries:
                        logger.warning(f"Error al obtener configuración de usuario (intento {retry_count}/{retries}): {str(e)}. Reintentando...")
                        await asyncio.sleep(2)
                    else:
                        raise
            
            if retry_count == retries:
                if last_error is None:
                    # Esto no debería suceder si el bucle de reintentos se ejecutó y falló,
                    # pero es una salvaguarda.
                    logger.critical("Estado inesperado: Se agotaron los reintentos pero no hay último error registrado.")
                    raise RuntimeError("Fallo en la obtención de la configuración del usuario después de reintentos, sin error específico.")
                else:
                    raise last_error
                
        except asyncio.TimeoutError:
            logger.error("Timeout final al obtener la configuración de usuario después de múltiples intentos")
            ultibot_app.show_error_and_exit(
                "Timeout de configuración de usuario",
                "No se recibió respuesta del backend o del hilo de configuración después de varios intentos."
            )
            return 1 
        except Exception as e:
            logger.error(f"Error final al obtener la configuración de usuario: {str(e)}")
            ultibot_app.show_error_and_exit(
                "Error de Configuración de Usuario",
                f"No se pudo cargar la configuración del usuario: {str(e)}"
            )
            return 1
        
        await ultibot_app.setup_binance_credentials()
        main_window = ultibot_app.create_main_window() # Pasa backend_base_url a MainWindow
        main_window.show()
        
        # Mantener la corrutina viva hasta que la aplicación se cierre
        # QApplication.instance().aboutToQuit se puede usar para establecer este evento
        app_close_event = asyncio.Event()
        original_close_event = main_window.closeEvent
        
        def custom_close_event(event):
            if original_close_event:
                original_close_event(event) # Llama al manejador original si existe
            if event.isAccepted(): # Solo si el cierre es aceptado
                logger.info("MainWindow close event accepted, setting app_close_event for run_application.")
                # Es importante llamar a set() desde el hilo del bucle de eventos de asyncio
                if ultibot_app.qasync_loop:
                    ultibot_app.qasync_loop.call_soon_threadsafe(app_close_event.set)
                else:
                    logger.error("custom_close_event: ultibot_app.qasync_loop is None! Cannot set app_close_event.")
        
        main_window.closeEvent = custom_close_event
        logger.info("run_application: Esperando a que app_close_event se establezca (cierre de la ventana principal)...")
        await app_close_event.wait()
        logger.info("run_application: app_close_event establecido, la corrutina run_application finalizará.")

    except ValueError as ve:
        ultibot_app.show_error_and_exit(
            "Error de Configuración Inicial",
            f"Error de configuración: {str(ve)}"
        )
        exit_code = 1
    except Exception as e:
        ultibot_app.show_error_and_exit(
            "Error de Inicialización de la Aplicación",
            f"Falló la inicialización de la aplicación: {str(e)}"
        )
        exit_code = 1
    finally:
        # cleanup_resources ahora es síncrono, se llamará en el finally de main()
        pass 
    
    return exit_code


def main() -> None:
    print("[DEBUG] Entrando a main() de ultibot_ui.main.py")

    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file_path = os.path.join(log_dir, "frontend.log")
    
    handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=100000, backupCount=1, encoding='utf-8'  # Modificado: maxBytes a 100KB, backupCount a 1
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s:%(thread)d] - %(filename)s:%(lineno)d - %(message)s")
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for h_existente in root_logger.handlers[:]:
            root_logger.removeHandler(h_existente)
            
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    # Reducir verbosidad de matplotlib
    logging.getLogger('matplotlib').setLevel(logging.INFO)

    logger.info("Logging configurado con RotatingFileHandler.")

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    qt_app = QApplication(sys.argv)
    event_loop = qasync.QEventLoop(qt_app)
    asyncio.set_event_loop(event_loop)
    logger.info("QEventLoop de qasync configurado como el bucle de eventos principal de asyncio.") # NUEVO LOG

    async def periodic_async_logger(loop):
        counter = 0
        while True:
            counter += 1
            logger.info(f"QASYNC_LOOP_HEARTBEAT: El bucle qasync está vivo - pulso #{counter}")
            await asyncio.sleep(5) # Imprime cada 5 segundos

    ultibot_app = UltiBotApplication() # Instanciar aquí para que sea accesible en el finally
    ultibot_app.app = qt_app
    ultibot_app.qasync_loop = event_loop # Store the qasync loop

    exit_code = 0
    try:
        logger.info("Iniciando la ejecución de run_application con event_loop.run_until_complete.")
        # Lanzar el logger periódico como una tarea en segundo plano
        periodic_logger_task = event_loop.create_task(periodic_async_logger(event_loop))
        logger.info("Tarea periodic_async_logger creada en el bucle qasync.")
        
        # Ejecutar la aplicación principal
        exit_code = event_loop.run_until_complete(run_application(qt_app, event_loop))
        
    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario (KeyboardInterrupt).")
        exit_code = 1 
    except Exception as e:
        logger.critical(f"Excepción no controlada en el nivel superior de main: {e}", exc_info=True)
        if QApplication.instance():
            QMessageBox.critical(None, "Error Crítico Inesperado", 
                                 f"Ha ocurrido un error crítico inesperado: {e}\n\nLa aplicación se cerrará.")
        exit_code = 1
    finally:
        if ultibot_app: # Asegurarse de que la instancia existe
            logger.info("Iniciando limpieza de recursos de UltiBotApplication antes del cierre del bucle principal.")
            # Llamar a cleanup_resources de forma asíncrona en el bucle principal
            event_loop.run_until_complete(ultibot_app.cleanup_resources())
            logger.info("Limpieza de recursos de UltiBotApplication completada.")

        logger.info("Cerrando el bucle de eventos de asyncio (qasync)...")
        if event_loop.is_running():
            event_loop.stop() 
        
        try:
            # Cancelar la tarea del logger periódico explícitamente
            if 'periodic_logger_task' in locals() and periodic_logger_task and not periodic_logger_task.done():
                periodic_logger_task.cancel()
                try:
                    # Esperar la cancelación de la tarea del logger periódico
                    event_loop.run_until_complete(periodic_logger_task)
                except asyncio.CancelledError:
                    logger.info("Tarea periodic_async_logger cancelada.")
                except Exception as e:
                    logger.warning(f"Error al esperar la cancelación de periodic_async_logger: {e}")

            tasks = [t for t in asyncio.all_tasks(loop=event_loop) if t is not asyncio.current_task(loop=event_loop)]
            if tasks:
                logger.info(f"Cancelando {len(tasks)} tareas pendientes de asyncio (después de cleanup_resources)...")
                for task in tasks:
                    task.cancel()
                event_loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                logger.info("Tareas pendientes canceladas.")

            if hasattr(event_loop, 'shutdown_asyncgens'):
                logger.info("Cerrando generadores asíncronos...")
                event_loop.run_until_complete(event_loop.shutdown_asyncgens())
                logger.info("Generadores asíncronos cerrados.")

        except Exception as e_shutdown:
            logger.error(f"Error durante el apagado de tareas/generadores de asyncio: {e_shutdown}", exc_info=True)
        finally:
            if not event_loop.is_closed():
                logger.info("Cerrando el bucle de eventos de qasync explícitamente.")
                event_loop.close()
                logger.info("Bucle de eventos de qasync cerrado.")
            else:
                logger.info("El bucle de eventos de qasync ya estaba cerrado.")

    logger.info(f"Saliendo de la aplicación con código de salida: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
