import sys
import asyncio
import logging
from typing import Optional
from uuid import UUID, uuid4
import httpx
import qasync
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtCore import QTimer, QThread, QObject, pyqtSignal

from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.workers import ApiWorker

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AppController(QObject):
    """
    Controlador principal de la aplicación que gestiona la inicialización asíncrona
    y la creación de la ventana principal.
    """
    initialization_complete = pyqtSignal(UUID)
    initialization_error = pyqtSignal(str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.user_id: Optional[UUID] = None

    def start_initialization(self):
        """Inicia el proceso de inicialización asíncrona en un hilo."""
        logger.info("Fetching initial user configuration...")
        # ApiWorker ahora es responsable de crear su propio UltiBotAPIClient
        worker = ApiWorker(
            coroutine_factory=lambda api_client: api_client.get_user_configuration()
        )
        thread = QThread()
        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_config_result)
        worker.error_occurred.connect(self._handle_config_error)

        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _handle_config_result(self, config_data: dict):
        """Maneja el resultado de la configuración del usuario."""
        try:
            # Asumimos que la configuración contiene el user_id o lo generamos si no existe
            self.user_id = UUID(config_data.get("userId", str(uuid4())))
            logger.info(f"Configuration received for user ID: {self.user_id}")
            self.initialization_complete.emit(self.user_id)
        except Exception as e:
            error_message = f"Error processing user configuration: {e}"
            logger.critical(error_message, exc_info=True)
            self.initialization_error.emit(error_message)

    def _handle_config_error(self, error_message: str):
        """Maneja errores durante la carga de la configuración."""
        logger.critical(f"Failed to fetch initial user configuration: {error_message}")
        QMessageBox.critical(None, "Error de Configuración", f"No se pudo cargar la configuración inicial: {error_message}")
        self.initialization_error.emit(f"Failed to load application configuration: {error_message}")

async def main(app: QApplication):
    """Función principal asíncrona para la aplicación UI."""
    
    # Cargar y aplicar el stylesheet
    try:
        with open("src/ultibot_ui/assets/style.qss", "r") as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet loaded successfully.")
    except FileNotFoundError:
        logger.warning("Stylesheet file not found: src/ultibot_ui/assets/style.qss")
    except Exception as e:
        logger.error(f"Error loading stylesheet: {e}")

    controller = AppController()
    
    main_window_instance: Optional[MainWindow] = None

    def on_initialization_complete(user_id: UUID):
        nonlocal main_window_instance
        try:
            main_window_instance = MainWindow(user_id=user_id)
            main_window_instance.show()
            logger.info("Main window shown.")
        except Exception as e:
            logger.critical(f"An unexpected error occurred during main window creation: {e}", exc_info=True)
            QMessageBox.critical(None, "Error Crítico de UI", f"La aplicación no pudo iniciarse debido a un error en la UI: {e}")
            app.quit()

    def on_initialization_error(message: str):
        logger.critical(f"An unexpected error occurred during initialization: {message}")
        QMessageBox.critical(None, "Error Crítico de Inicialización", f"La aplicación no pudo iniciarse: {message}")
        app.quit()

    controller.initialization_complete.connect(on_initialization_complete)
    controller.initialization_error.connect(on_initialization_error)

    controller.start_initialization()

    # Ejecutar el bucle de eventos de Qt. Esto también ejecuta el bucle de asyncio.
    app.exec_()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        with loop:
            loop.run_until_complete(main(app))
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
        sys.exit(1)
