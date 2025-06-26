# --- Configuración temprana del bucle de eventos ---
import asyncio
import sys
# Configuración de la política de bucle de eventos para Windows
if sys.platform == "win32" and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# --- Fin de la Configuración temprana del bucle de eventos ---

import logging
import os
from logging.config import dictConfig
from typing import Optional, cast

import qasync
from PySide6 import QtWidgets, QtCore

from ultibot_ui.config import app_config
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.windows.main_window import MainWindow

# --- Configuración de Logging ---
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default", "stream": "ext://sys.stdout"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(LOGS_DIR, "frontend.log"),
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "httpx": {"handlers": ["console", "file"], "level": "INFO"},
        "src.ultibot_ui": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
        "ultibot_backend": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
        "qasync": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
    "root": {"level": "DEBUG", "handlers": ["console", "file"]},
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class UltiBotApplication(QtWidgets.QApplication):
    """
    Clase principal que encapsula la lógica de la aplicación de la UI,
    gestionando la inicialización, el ciclo de vida y la limpieza de recursos.
    """
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window: Optional[MainWindow] = None
        self.api_client: Optional[UltiBotAPIClient] = None
        self.main_event_loop: Optional[qasync.QEventLoop] = None

        self.aboutToQuit.connect(self.cleanup)

    def load_stylesheet(self):
        """Carga la hoja de estilos QSS."""
        stylesheet_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
        try:
            with open(stylesheet_path, "r") as f:
                self.setStyleSheet(f.read())
            logger.info("Stylesheet loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Stylesheet not found at {stylesheet_path}")

    async def initialize_async(self):
        """
        Realiza la inicialización asíncrona de la aplicación de forma controlada y secuencial.
        """
        logger.info("Starting asynchronous initialization...")

        # 1. Configurar el bucle de eventos asíncrono con qasync
        self.main_event_loop = qasync.QEventLoop(self)
        asyncio.set_event_loop(self.main_event_loop)
        logger.info("QEventLoop initialized and set.")

        # 2. Cargar la hoja de estilos
        self.load_stylesheet()

        # 3. Inicializar el cliente API
        logger.info("Initializing API client...")
        self.api_client = UltiBotAPIClient(base_url=app_config.BACKEND_API_URL)
        await self.api_client.initialize_client()
        logger.info("API client initialized.")

        # 4. Crear la ventana principal con las dependencias listas
        logger.info("Creating MainWindow...")
        self.main_window = MainWindow(api_client=self.api_client, main_event_loop=self.main_event_loop)
        logger.info("MainWindow created.")

        # 5. Cargar la configuración inicial del usuario
        try:
            logger.info("Fetching initial user configuration...")
            await self.main_window.fetch_initial_user_configuration_async()
            logger.info("Initial user configuration fetched and applied successfully.")
        except APIError as e:
            logger.critical(f"Failed to fetch initial configuration: {e}. Application may not function correctly.")
            if self.main_window:
                self.main_window.show_error_message(f"Error al cargar configuración inicial: {e}")
        except Exception as e:
            logger.critical(f"An unexpected error occurred during configuration fetch: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_error_message(f"Error inesperado: {e}")
        
        # 6. Mostrar la ventana principal solo después de que todo esté listo
        if self.main_window:
            logger.info("Initialization complete. Showing MainWindow.")
            self.main_window.show()
            # Llamar a la inicialización post-show de forma segura
            await self.main_window.post_show_initialization()
        else:
            logger.critical("MainWindow not created due to an error. Application cannot start.")
            self.exit(1)

    @QtCore.Slot()
    def cleanup(self):
        """
        Limpia los recursos de la aplicación de forma segura al cerrar.
        Este slot es llamado por la señal aboutToQuit.
        """
        logger.info("Cleanup process started...")
        if self.main_window:
            self.main_window.cleanup()

        if self.api_client and self.main_event_loop:
            logger.info("Scheduling API client cleanup task.")
            # Ejecutar la limpieza del cliente en el bucle de eventos
            future = asyncio.run_coroutine_threadsafe(self.api_client.close(), self.main_event_loop)
            try:
                # Esperar a que la limpieza finalice
                future.result(timeout=5)
                logger.info("API client cleanup finished.")
            except Exception as e:
                logger.error(f"Error during API client cleanup: {e}")
        
        logger.info("Application cleanup finished.")

    def run(self):
        """Inicia el bucle de eventos de la aplicación."""
        if not self.main_event_loop:
            logger.critical("Event loop not initialized. Cannot run the application.")
            return 1  # Devuelve un código de error
        
        exit_code = 0
        logger.info("Starting application event loop.")
        try:
            # El bucle de eventos ya está configurado, solo necesitamos ejecutarlo.
            self.exec()
        except KeyboardInterrupt:
            logger.info("Application interrupted by user.")
        except Exception as e:
            logger.critical(f"Unhandled exception during app execution: {e}", exc_info=True)
            exit_code = 1
        finally:
            logger.info("Application event loop has stopped.")
        return exit_code


def main():
    """Punto de entrada principal para la aplicación de UI."""
    # QApplication debe ser instanciado primero
    app = UltiBotApplication(sys.argv)
    
    # El bucle de eventos se configura dentro de initialize_async
    # y se ejecuta con app.run()
    try:
        # Usamos asyncio.run para manejar el ciclo de vida de la corutina de inicialización
        asyncio.run(app.initialize_async())
        
        # Iniciar la ejecución de la aplicación
        exit_code = app.run()
        sys.exit(exit_code)

    except Exception as e:
        logger.critical(f"Fatal error during application startup: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
