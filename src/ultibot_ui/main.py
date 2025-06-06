"""
UltiBot Frontend Main Application

Este módulo inicializa y configura la aplicación PyQt5 del frontend UltiBot,
incluyendo la configuración de servicios backend y la interfaz de usuario.
"""

import asyncio
import os
import sys
import logging
import logging.handlers
from typing import Optional, Any, Callable, Coroutine, List
from uuid import UUID

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMessageBox
from dotenv import load_dotenv
import qasync

# Importaciones del proyecto
from src.shared.data_types import UserConfiguration
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.dialogs.login_dialog import LoginDialog
from src.ultibot_ui.workers import ApiWorker

try:
    import qdarkstyle
    DARK_STYLE_AVAILABLE = True
except ImportError:
    qdarkstyle = None
    DARK_STYLE_AVAILABLE = False
    print("Advertencia: qdarkstyle no está instalado. La aplicación usará el tema por defecto de Qt.")

logger = logging.getLogger(__name__)

# --- Global Stylesheets ---
DARK_GLOBAL_STYLESHEET = """
QWidget {
    background-color: #121212; 
    color: #E0E0E0; 
    font-family: "Inter", "Roboto", Arial, sans-serif; 
    font-size: 14px; 
    font-weight: 400; 
}
QFrame, QGroupBox, QTabWidget::pane {
    background-color: #1E1E1E;
    border-radius: 8px;
    border: 1px solid #383838; 
}
QGroupBox {
    padding: 20px;
    margin-top: 22px;
    font-size: 14px; 
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 6px 12px;
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00C2FF, stop:1 #00FF8C); 
    color: #121212;
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
    color: #E0E0E0;
    padding-bottom: 8px;
    border: none; 
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
    color: #999999; 
    font-style: italic;
    border: none;
}
QLabel#dataDisplayLabel {
    font-size: 16px;
    font-weight: 500;
    color: #00C2FF;
    border: none;
}
QLabel#smallDetailLabel { 
    font-size: 12px;
    color: #BBBBBB; 
    border: none;
}
QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #007BFF, stop:1 #00C2FF); 
    color: #FFFFFF; 
    border: none;
    padding: 10px 18px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0056b3, stop:1 #00A0DD); 
}
QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #004085, stop:1 #007BFF); 
}
QPushButton:disabled {
    background-color: #2A2A2A; 
    color: #555555;
}
QPushButton#accentButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF8C, stop:1 #00DB7A); 
    color: #121212;
}
QPushButton#accentButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00DB7A, stop:1 #00C2FF); 
}
QPushButton#accentButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B36B, stop:1 #00A0DD);
}
QTableWidget {
    gridline-color: #383838;
    background-color: #1A1A1A; 
    border: 1px solid #383838;
    font-size: 14px;
}
QHeaderView::section {
    background-color: #222222;
    color: #00FF8C; 
    padding: 8px;
    border: 1px solid #383838;
    font-size: 14px;
    font-weight: 600; 
}
QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2A2A2A;
    color: #DDDDDD; 
}
QTableWidget::item:selected {
    background-color: #007BFF; 
    color: #FFFFFF;
}
QTableWidget::item { 
    font-family: "Consolas", "Menlo", "Monaco", "Lucida Console", monospace;
}
QComboBox {
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 10px;
    background-color: #222222; 
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
QScrollBar:vertical {
    border: none;
    background: #1A1A1A; 
    width: 14px;
    margin: 14px 0 14px 0;
}
QScrollBar::handle:vertical {
    background: #00C2FF; 
    min-height: 30px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #00A0DD; 
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
    border-top: 2px solid #00FF8C; 
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
    font-weight: 600; 
    color: #999999; 
}
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #2A2A2A;
    color: #00FF8C; 
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
    border-bottom: 2px solid #00C2FF; 
    border-radius: 0px;
    padding: 8px;
}
QProgressBar {
    border: 1px solid #383838;
    border-radius: 6px;
    text-align: center;
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-weight: 600; 
}
QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF8C, stop:1 #00C2FF); 
    border-radius: 5px;
}
"""

LIGHT_GLOBAL_STYLESHEET = """
QWidget {
    background-color: #F8F9FA; 
    color: #212529; 
    font-family: "Inter", "Roboto", Arial, sans-serif;
    font-size: 14px;
    font-weight: 400;
}
QFrame, QGroupBox, QTabWidget::pane {
    background-color: #FFFFFF; 
    border-radius: 8px;
    border: 1px solid #DEE2E6; 
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
    background-color: #0099E5; 
    color: #FFFFFF; 
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
    color: #00CC7A; 
    margin-bottom: 6px;
}
QLabel#statusLabel {
    font-size: 12px;
    color: #6C757D; 
    font-style: italic;
}
QLabel#dataDisplayLabel {
    font-size: 16px;
    font-weight: 500;
    color: #0099E5; 
}
QLabel#smallDetailLabel {
    font-size: 12px;
    color: #6C757D;
}
QPushButton {
    background-color: #007BFF; 
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
    background-color: #00CC7A; 
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
QTableWidget::item { 
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
    border-top: 2px solid #0099E5; 
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
    border-bottom: 2px solid #00CC7A; 
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
    background-color: #00CC7A; 
    border-radius: 5px;
}
"""

def apply_application_style(theme_name: str):
    """Applies the global stylesheet for the given theme."""
    app_instance = QApplication.instance()
    if not app_instance:
        logger.error("QApplication instance not found. Cannot apply style.")
        return

    # Asegurar que la instancia es de QApplication, que tiene setStyleSheet
    if not isinstance(app_instance, QApplication):
        logger.warning(f"Instance is {type(app_instance)}, not QApplication. Stylesheet not applied.")
        return
    
    base_style = ""
    if DARK_STYLE_AVAILABLE and qdarkstyle:
        base_style = qdarkstyle.load_stylesheet_pyqt5()
    stylesheet = base_style + (LIGHT_GLOBAL_STYLESHEET if theme_name == "light" else DARK_GLOBAL_STYLESHEET)
    app_instance.setStyleSheet(stylesheet)
    logger.info(f"Applied {theme_name} theme to the application.")

class UltiBotApplication:
    def __init__(self, backend_base_url: str, user_id: UUID):
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
        self.user_id: UUID = user_id
        self.active_threads: List[QThread] = []
        self.backend_base_url: str = backend_base_url
        self.auth_token: Optional[str] = None
        self.qasync_loop: Optional[asyncio.AbstractEventLoop] = None
    
    def setup_qt_application(self) -> None:
        if not self.app:
            raise RuntimeError("QApplication instance not set.")
        logger.info("QApplication instance confirmed.")
    
    async def initialize_core_services(self) -> None:
        temp_api_client = UltiBotAPIClient(base_url=self.backend_base_url, token=self.auth_token)
        try:
            logger.info("Core services can be initialized.")
        finally:
            await temp_api_client.aclose()

    async def ensure_user_configuration(self, auth_token: str) -> Any:
        if not self.user_id:
            raise RuntimeError("User ID not set.")
        if not auth_token:
            raise RuntimeError("Auth token must be provided to get user configuration.")
        if not self.qasync_loop:
            raise RuntimeError("QAsync loop not initialized.")

        logger.info(f"Fetching user configuration for {self.user_id}...")
        future = self.qasync_loop.create_future()
        worker = ApiWorker(
            coroutine_factory=lambda client: client.get_user_configuration(),
            base_url=self.backend_base_url,
            token=auth_token
        )
        thread = QThread()
        self.active_threads.append(thread)
        worker.moveToThread(thread)

        worker.result_ready.connect(lambda result: future.set_result(result) if not future.done() else None)
        worker.error_occurred.connect(lambda error: future.set_exception(Exception(error)) if not future.done() else None)
        
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        worker.result_ready.connect(worker.deleteLater)
        worker.error_occurred.connect(worker.deleteLater)
        thread.finished.connect(lambda: self.active_threads.remove(thread))
        
        thread.start()
        return await future

    def create_main_window(self) -> MainWindow:
        if not self.user_id or not self.qasync_loop:
            raise RuntimeError("User ID or qasync_loop not initialized.")
        
        main_window = MainWindow(
            user_id=self.user_id,
            backend_base_url=self.backend_base_url,
            qasync_loop=self.qasync_loop,
            auth_token=self.auth_token # Pasar el token
        )
        self.main_window = main_window
        return main_window
    
    async def cleanup_resources(self) -> None:
        logger.info("Cleaning up resources...")
        for thread in self.active_threads[:]:
            thread.quit()
            if not thread.wait(5000):
                logger.warning(f"Thread {thread} did not finish in time. Terminating.")
                thread.terminate()
                thread.wait()
        self.active_threads.clear()
        await asyncio.sleep(0.1)
        logger.info("Cleanup complete.")
    
    def show_error_and_exit(self, title: str, message: str, exit_code: int = 1) -> None:
        if self.app:
            QMessageBox.critical(None, title, f"{message}\\n\\nLa aplicación se cerrará.")
        else:
            print(f"ERROR - {title}: {message}")
        sys.exit(exit_code)

async def run_application(ultibot_app: 'UltiBotApplication') -> int:
    try:
        assert ultibot_app.qasync_loop is not None, "QAsync loop must be initialized."
        
        ultibot_app.setup_qt_application()
        apply_application_style("dark")
        
        # --- Flujo de Login ---
        if not ultibot_app.auth_token:
            logger.info("No pre-existing auth token found. Showing login dialog.")
            
            # Factoría corregida para aceptar una coroutine_factory
            def api_worker_factory(coroutine_factory: Callable, token: Optional[str] = None) -> ApiWorker:
                return ApiWorker(
                    base_url=ultibot_app.backend_base_url,
                    coroutine_factory=coroutine_factory,
                    token=token
                )

            login_dialog = LoginDialog(api_worker_factory=api_worker_factory)
            
            login_future = ultibot_app.qasync_loop.create_future()

            @pyqtSlot(str)
            def on_login_success(token: str):
                if not login_future.done():
                    login_future.set_result(token)
            
            @pyqtSlot()
            def on_login_rejected():
                if not login_future.done():
                    login_future.set_result(None)

            login_dialog.login_successful.connect(on_login_success)
            login_dialog.rejected.connect(on_login_rejected)
            
            login_dialog.exec_() # Show modal dialog
            
            token = await login_future
            
            if token:
                ultibot_app.auth_token = token
                logger.info("Login successful. JWT token obtained and stored.")
            else:
                logger.warning("Login was cancelled or failed. Exiting application.")
                ultibot_app.show_error_and_exit("Login Required", "Authentication is required to continue.", exit_code=0)
                return 0
        else:
            logger.info("Auth token already present. Skipping login dialog.")

        await ultibot_app.initialize_core_services()
        
        if ultibot_app.auth_token:
            logger.info("Fetching user configuration...")
            await ultibot_app.ensure_user_configuration(auth_token=ultibot_app.auth_token)
        else:
            # Este caso no debería ocurrir si el flujo de login es correcto, pero es una salvaguarda.
            logger.error("Auth token is missing after login flow. Cannot fetch user configuration.")
            ultibot_app.show_error_and_exit("Error Interno", "El token de autenticación no se encontró después del login.")
            return 1

        main_window = ultibot_app.create_main_window()
        main_window.show()
        
        app_close_event = asyncio.Event()
        main_window.closeEvent = lambda event: app_close_event.set() if event.isAccepted() else None
        
        await app_close_event.wait()
        return 0

    except Exception as e:
        logger.critical(f"Application initialization failed: {e}", exc_info=True)
        ultibot_app.show_error_and_exit("Application Startup Error", f"Failed to initialize the application: {e}")
        return 1

def main() -> None:
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "frontend.log")
    
    handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=100000, backupCount=3, encoding='utf-8')
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s")
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    logging.getLogger('matplotlib').setLevel(logging.INFO)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    qt_app = QApplication(sys.argv)
    event_loop = qasync.QEventLoop(qt_app)
    asyncio.set_event_loop(event_loop)

    load_dotenv(override=True)
    backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    try:
        fixed_user_id = UUID(os.getenv("FIXED_USER_ID", "00000000-0000-0000-0000-000000000000"))
    except ValueError:
        logger.critical("FIXED_USER_ID in .env is not a valid UUID.")
        sys.exit(1)

    ultibot_app = UltiBotApplication(backend_base_url=backend_base_url, user_id=fixed_user_id)
    ultibot_app.app = qt_app
    ultibot_app.qasync_loop = event_loop
    ultibot_app.auth_token = os.getenv("ULTIBOT_AUTH_TOKEN")

    exit_code = 0
    try:
        exit_code = event_loop.run_until_complete(run_application(ultibot_app))
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
        exit_code = 1
    finally:
        event_loop.run_until_complete(ultibot_app.cleanup_resources())
        event_loop.close()

    logger.info(f"Exiting with code {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
