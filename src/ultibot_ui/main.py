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
    "formatters": {"default": {"format": "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(module)s.py:%(lineno)d - %(message)s"}},
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
        "src.ultibot_ui": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "ultibot_backend": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "qasync": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
}

# Aplicar la configuración de logging inmediatamente
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

    def load_stylesheet(self):
        """Carga la hoja de estilos QSS."""
        stylesheet_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
        try:
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
            logger.info("Stylesheet loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Stylesheet not found at {stylesheet_path}")

    async def initialize_async(self):
        """
        Realiza la inicialización asíncrona de la aplicación.
        Este método se ejecuta como una tarea dentro del bucle de eventos de qasync.
        """
        try:
            logger.info("Asynchronous initialization started.")

            # 1. Cargar la hoja de estilos
            self.load_stylesheet()

            # 2. Inicializar el cliente API
            logger.info("Initializing API client...")
            self.api_client = UltiBotAPIClient(base_url=app_config.BACKEND_API_URL)
            await self.api_client.initialize_client()
            logger.info("API client initialized.")

            # 3. Crear la ventana principal con las dependencias listas
            logger.info("Creating MainWindow...")
            if not self.main_event_loop:
                raise RuntimeError("Main event loop not available for MainWindow.")
            self.main_window = MainWindow(api_client=self.api_client, main_event_loop=self.main_event_loop)
            logger.info("MainWindow created.")

            # 4. Cargar la configuración inicial del usuario
            logger.info("Fetching initial user configuration...")
            await self.main_window.fetch_initial_user_configuration_async()
            logger.info("Initial user configuration fetched and applied successfully.")
            
            # 5. Mostrar la ventana principal
            logger.info("Initialization complete. Showing MainWindow.")
            self.main_window.show()
            
            # 6. Llamar a la inicialización post-show de forma segura
            await self.main_window.post_show_initialization()

        except APIError as e:
            logger.critical(f"Failed to fetch initial configuration: {e}. Application may not function correctly.")
            if self.main_window:
                self.main_window.show_error_message(f"Error al cargar configuración inicial: {e}")
            else:
                # Si la ventana principal no se pudo crear, salimos
                self.exit(1)
        except Exception as e:
            logger.critical(f"An unexpected error occurred during initialization: {e}", exc_info=True)
            if self.main_window:
                self.main_window.show_error_message(f"Error inesperado: {e}")
            else:
                self.exit(1)

    async def cleanup_async(self):
        """
        Realiza una limpieza asíncrona de todos los recursos pendientes.
        """
        logger.info("Async cleanup process started...")
        
        # 1. Cancelar todas las tareas pendientes de asyncio
        if self.main_event_loop:
            try:
                # Intentar obtener todas las tareas asociadas a nuestro bucle
                # Filtrar la tarea actual para evitar cancelarse a sí misma
                tasks = [t for t in asyncio.all_tasks(loop=self.main_event_loop) if t is not asyncio.current_task()]
                if tasks:
                    logger.info(f"Cancelling {len(tasks)} outstanding tasks. Details: {[t.get_name() for t in tasks]}")
                    for task in tasks:
                        task.cancel()
                    
                    # Esperar a que todas las tareas se cancelen
                    # return_exceptions=True permite que gather no falle si una tarea ya está cancelada o falla
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Task {tasks[i].get_name()} failed during cancellation: {result}", exc_info=True)
                    logger.info("All outstanding tasks have been cancelled or handled.")
            except RuntimeError as e:
                logger.warning(f"Could not cancel outstanding tasks during cleanup: {e}. Event loop might be closing.")
            except Exception as e:
                logger.error(f"Unexpected error during task cancellation: {e}", exc_info=True)

        # 2. Cerrar el cliente API de forma segura
        if self.api_client:
            logger.info("Closing API client.")
            try:
                await self.api_client.close()
                logger.info("API client closed.")
            except Exception as e:
                logger.error(f"Error closing API client: {e}", exc_info=True)
            
        logger.info("Async cleanup finished.")

async def main(app: UltiBotApplication):
    """Punto de entrada principal y asíncrono para la aplicación de UI."""
    # Asignar el bucle de eventos actual a la aplicación para que los componentes internos puedan usarlo.
    try:
        # Usamos `cast` para asegurar al type checker que el bucle en ejecución es del tipo esperado.
        app.main_event_loop = cast(qasync.QEventLoop, asyncio.get_running_loop())
    except RuntimeError:
        logger.critical("No running event loop found.")
        app.exit(1)
        return

    try:
        # La inicialización asíncrona ahora se espera directamente.
        await app.initialize_async()
        logger.info("Application initialized successfully and is running.")
        
        # El bucle de eventos de la aplicación ya está en marcha por qasync.
        # Esperamos aquí hasta que la aplicación se cierre.
        while app.main_window and app.main_window.isVisible():
            await asyncio.sleep(0.1)

    except Exception as e:
        logger.critical(f"Fatal error during application startup: {e}", exc_info=True)
    finally:
        # Esta sección se ejecuta siempre, ya sea por cierre normal o por excepción.
        logger.info("Application is shutting down. Performing async cleanup...")
        await app.cleanup_async()
        app.exit()

if __name__ == "__main__":
    # Se crea la instancia de la aplicación UNA SOLA VEZ, antes de que qasync tome el control.
    app = UltiBotApplication(sys.argv)
    try:
        # qasync.run envuelve la ejecución de la aplicación y el bucle de eventos.
        qasync.run(main(app))
    except Exception as e:
        # Captura final para errores que podrían ocurrir fuera del bucle principal.
        logger.critical(f"A critical error forced the application to close: {e}", exc_info=True)
        sys.exit(1)
