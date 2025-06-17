import asyncio
import logging
import os
import sys
from logging.config import dictConfig
from uuid import UUID

import httpx
import qasync
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication, QSplashScreen

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.windows.main_window import MainWindow

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
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def load_stylesheet(app: QApplication):
    """Carga la hoja de estilos QSS."""
    stylesheet_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    try:
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet loaded successfully.")
    except FileNotFoundError:
        logger.error(f"Stylesheet not found at {stylesheet_path}")

async def start_application():
    """Punto de entrada principal para la aplicación de UI."""
    logger.info("Initializing application...")
    
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling) # type: ignore
    
    load_stylesheet(app)

    main_window = None
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        api_client = UltiBotAPIClient(base_url="http://127.0.0.1:8000", client=http_client)
        
        event_loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(event_loop)
        
        try:
            logger.info("Fetching initial user configuration...")
            user_config = await api_client.get_user_configuration()
            user_id = UUID(user_config['id'])
            logger.info(f"Configuration received for user ID: {user_id}")
            
            main_window = MainWindow(user_id=user_id, api_client=api_client)
            main_window.show()
            logger.info("Main window shown.")

        except APIError as e:
            logger.critical(f"Failed to fetch initial configuration: {e}. Cannot start application.")
            # Aquí podrías mostrar un QMessageBox de error
            return
        except Exception as e:
            logger.critical(f"An unexpected error occurred during initialization: {e}", exc_info=True)
            return

        try:
            await event_loop.run_forever() # type: ignore
        finally:
            logger.info("Application event loop stopped.")
            if main_window:
                main_window.cleanup()
            event_loop.close()

if __name__ == "__main__":
    try:
        if sys.platform == "win32" and sys.version_info >= (3, 8):
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
             
        asyncio.run(start_application())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user.")
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
