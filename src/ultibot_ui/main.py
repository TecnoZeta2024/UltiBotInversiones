import logging
import sys
from typing import Optional

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from src.shared.data_types import UserConfiguration
from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.workers import ApiWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/frontend.log", mode="w"),
    ],
)

log = logging.getLogger(__name__)

class AppController(QObject):
    """Controls the application's startup and initialization flow."""
    initialization_error = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient):
        super().__init__()
        self.api_client = api_client
        self.main_window: Optional[MainWindow] = None

    def start_initialization(self):
        """Starts the background process to fetch initial data."""
        log.info("Controller: Starting initialization worker.")
        self.initialization_worker = ApiWorker(
            api_client=self.api_client,
            coroutine_factory=lambda client: client.get_user_configuration()
        )
        self.initialization_thread = QThread()
        self.initialization_worker.moveToThread(self.initialization_thread)

        self.initialization_thread.started.connect(self.initialization_worker.run)
        self.initialization_worker.result_ready.connect(self.on_initialization_complete)
        self.initialization_worker.error_occurred.connect(self.on_initialization_error)

        # Cleanup
        self.initialization_worker.result_ready.connect(self.initialization_thread.quit)
        self.initialization_worker.error_occurred.connect(self.initialization_thread.quit)
        self.initialization_worker.moveToThread(self.initialization_thread) # Ensure worker is on thread before connecting finished
        self.initialization_thread.finished.connect(self.initialization_worker.deleteLater)
        self.initialization_thread.finished.connect(self.initialization_thread.deleteLater)

        self.initialization_thread.start()

    def on_initialization_complete(self, user_config: UserConfiguration):
        """Called when the initial user data is successfully fetched."""
        log.info(f"Controller: Initialization complete. User ID: {user_config.id}")
        if not isinstance(user_config, UserConfiguration):
            log.error(f"Initialization failed: received type {type(user_config)} instead of UserConfiguration.")
            self.on_initialization_error("Tipo de dato de configuración de usuario inválido.")
            return

        self.main_window = MainWindow(
            user_id=user_config.id,
            api_client=self.api_client
        )
        self.main_window.show()
        log.info("Main window shown.")

    def on_initialization_error(self, error_message: str):
        """Handles errors during the initialization process."""
        log.error(f"Controller: Initialization failed: {error_message}")
        self.initialization_error.emit(error_message)
        QApplication.quit()


def main():
    """
    Main function to initialize and run the PyQt application.
    """
    log.info("Initializing application...")
    app = QApplication(sys.argv)

    api_base_url = "http://127.0.0.1:8000"
    api_client = UltiBotAPIClient(base_url=api_base_url)

    controller = AppController(api_client)
    controller.initialization_error.connect(
        lambda msg: log.critical(f"A critical error occurred: {msg}")
    )
    controller.start_initialization()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
