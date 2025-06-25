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
from uuid import UUID

import httpx
import qasync
from typing import cast, Optional
from PySide6 import QtCore, QtGui, QtWidgets

from ultibot_ui.config import app_config
from ultibot_ui.models import UserConfiguration
from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.windows.main_window import MainWindow
# from ultibot_ui.dialogs.login_dialog import LoginDialog # Eliminar importación de LoginDialog
from ultibot_ui.workers import ApiWorker

# --- Configuración de Logging ---
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": os.path.join(LOGS_DIR, "frontend.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "httpx": {"handlers": ["console", "file"], "level": "INFO"},
        "src.ultibot_ui": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
        "ultibot_backend": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
        "qasync": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False}, # Añadido para capturar logs de qasync
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def load_stylesheet(app: QtWidgets.QApplication):
    """Carga la hoja de estilos QSS."""
    stylesheet_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet loaded successfully.")
    except FileNotFoundError:
        logger.error(f"Stylesheet not found at {stylesheet_path}")

async def _main_async(app: QtWidgets.QApplication):
    """Lógica asíncrona principal de la aplicación de UI."""
    logger.info("Initializing or finding application window...")

    # Buscar una instancia existente de MainWindow
    main_window = next((w for w in app.topLevelWidgets() if isinstance(w, MainWindow)), None)

    if not main_window:
        logger.info("No existing MainWindow found. Creating a new one.")
        load_stylesheet(app)

        # Instanciar el cliente API singleton
        api_client = UltiBotAPIClient(base_url=app_config.BACKEND_API_URL)
        await api_client.initialize_client() # Inicializar el cliente httpx aquí

        # Crear y mostrar la ventana principal inmediatamente
        main_window = MainWindow(api_client=api_client)
        main_window.show()
        logger.info("Main window created and shown (loading configuration asynchronously).")

        # Cargar la configuración del usuario directamente sin el diálogo de login
        try:
            logger.info("Fetching initial user configuration asynchronously...")
            user_config_dict = await api_client.get_user_configuration()
            user_config = UserConfiguration.model_validate(user_config_dict)
            user_id = UUID(user_config.user_id)
            logger.info(f"Configuration received and validated for user ID: {user_id}. Updating UI.")
            main_window.set_user_configuration(user_id, user_config)
            
        except APIError as e:
            logger.critical(f"Failed to fetch initial configuration: {e}. Application may not function correctly.")
            main_window.show_error_message(f"Error al cargar configuración inicial: {e}")
        except Exception as e:
            logger.critical(f"An unexpected error occurred during configuration fetch: {e}", exc_info=True)
            main_window.show_error_message(f"Error inesperado: {e}")
    else:
        logger.info("Existing MainWindow found. Activating it.")
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()

    # Devolver la ventana principal para mantener una referencia fuerte
    return main_window

async def cleanup_resources(api_client: UltiBotAPIClient):
    """Cierra los recursos de la aplicación de forma segura."""
    if api_client:
        logger.info("Cleaning up resources...")
        await api_client.close()
        logger.info("Cleanup complete.")
    else:
        logger.warning("API client not available for cleanup.")

def main():
    """Punto de entrada principal para la aplicación de UI."""
    try:
        # Crear o obtener la instancia de QApplication
        app = QtWidgets.QApplication.instance()
        if not app:
            app = QtWidgets.QApplication(sys.argv)
        app = cast(QtWidgets.QApplication, app)
        # El atributo AA_EnableHighDpiScaling está obsoleto en Qt6 y el escalado se maneja automáticamente.
        # app.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling)

        # Configurar y ejecutar el bucle de eventos con qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        app.setProperty("main_event_loop", loop) # Establecer el bucle de eventos como propiedad de la aplicación con el nombre correcto

        # Referencias para mantener la ventana principal y el cliente API vivos
        main_window_ref: Optional[MainWindow] = None
        api_client_ref: Optional[UltiBotAPIClient] = None

        async def _main_async_wrapper(app: QtWidgets.QApplication):
            """Envuelve _main_async para inicializar la aplicación y capturar la referencia a MainWindow."""
            nonlocal main_window_ref
            main_window_ref = await _main_async(app) # _main_async ahora devuelve MainWindow o None
            
            # Programar la inicialización post-mostrar en el bucle de eventos principal
            if main_window_ref:
                # Crear una instancia real de QShowEvent
                show_event = QtGui.QShowEvent() # El tipo de evento Show es el predeterminado
                # Usar cast para ayudar a Pylance a reconocer el tipo de main_window_ref
                main_window_casted = cast(MainWindow, main_window_ref)
                # Usar QTimer.singleShot para diferir la llamada a la siguiente iteración del bucle de eventos
                QtCore.QTimer.singleShot(0, lambda: main_window_casted.post_show_initialization(show_event))

        def cleanup_slot():
            """Slot para ejecutar la limpieza de recursos en el event loop existente."""
            logger.info("aboutToQuit signal received, scheduling resource cleanup.")
            nonlocal main_window_ref # Necesitamos esta referencia para llamar a cleanup
            if main_window_ref:
                main_window_ref.cleanup() # Llamar al cleanup de la ventana principal
            
            # Acceder al cliente API directamente desde la instancia singleton para cerrarlo
            api_client_instance = getattr(UltiBotAPIClient, 'instance', None)
            if api_client_instance:
                loop.create_task(cleanup_resources(api_client_instance))
            else:
                logger.warning("UltiBotAPIClient instance not found for cleanup.")

        app.aboutToQuit.connect(cleanup_slot)

        # Crear y ejecutar la tarea principal de inicialización
        loop.create_task(_main_async_wrapper(app))

        with loop:
            loop.run_forever()

    except KeyboardInterrupt:
        logger.info("Aplicación interrumpida por el usuario.")
    except Exception as e:
        logger.critical(f"Excepción no controlada en main: {e}", exc_info=True)
    finally:
        logger.info("Iniciando cierre de la aplicación y limpieza de tareas pendientes.")
        if 'loop' in locals() and loop.is_running():
            # Cancelar todas las tareas pendientes y esperar a que terminen
            pending_tasks = asyncio.all_tasks(loop=loop)
            for task in pending_tasks:
                task.cancel()
            
            # Esperar un corto tiempo para que las tareas canceladas se limpien
            try:
                loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
            except asyncio.CancelledError:
                pass # Esto es esperado si las tareas se cancelan
            except Exception as e:
                logger.error(f"Error durante la espera de tareas pendientes: {e}", exc_info=True)

            loop.close()
            logger.info("Bucle de eventos cerrado.")
        else:
            logger.warning("El bucle de eventos no estaba corriendo o no se encontró durante el cierre.")
        
        logger.info("Aplicación cerrada.")
        sys.exit(0)

if __name__ == "__main__":
    main()
