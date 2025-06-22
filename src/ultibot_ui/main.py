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

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.windows.main_window import MainWindow

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
        api_client = UltiBotAPIClient(base_url="http://127.0.0.1:8000")
        await api_client.initialize_client() # Inicializar el cliente httpx aquí

        try:
            logger.info("Fetching initial user configuration...")
            user_config = await api_client.get_user_configuration()
            user_id = UUID(user_config['id'])
            logger.info(f"Configuration received for user ID: {user_id}")
            
            main_window = MainWindow(user_id=user_id, api_client=api_client)
            main_window.show()
            logger.info("Main window created and shown.")

        except APIError as e:
            logger.critical(f"Failed to fetch initial configuration: {e}. Cannot start application.")
            await api_client.close() # Asegurarse de cerrar el cliente en caso de error
            return
        except Exception as e:
            logger.critical(f"An unexpected error occurred during initialization: {e}", exc_info=True)
            await api_client.close() # Asegurarse de cerrar el cliente en caso de error
            return
    else:
        logger.info("Existing MainWindow found. Activating it.")
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()

    # Devolver el cliente para que pueda ser cerrado correctamente
    if 'api_client' in locals():
        return api_client
    return None

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

        # Usar un objeto mutable para pasar el cliente API y asegurar su limpieza
        api_client_container: dict[str, Optional[UltiBotAPIClient]] = {'instance': None}

        async def _main_async_wrapper(app: QtWidgets.QApplication):
            """Envuelve _main_async para capturar la instancia del cliente API."""
            api_client = await _main_async(app)
            if api_client:
                api_client_container['instance'] = api_client

        def cleanup_slot():
            """Slot para ejecutar la limpieza de recursos en el event loop existente."""
            logger.info("aboutToQuit signal received, scheduling resource cleanup.")
            if api_client_container['instance']:
                # Usamos create_task para no bloquear la señal de cierre
                loop.create_task(cleanup_resources(api_client_container['instance']))

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
