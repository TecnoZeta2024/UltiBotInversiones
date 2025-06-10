import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, TextIO
from uuid import UUID, uuid4
import httpx
import qasync
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.services.trading_mode_state import TradingModeStateManager
from src.ultibot_ui import app_config

# --- Configuración de Logging Mejorada ---

# 1. Crear directorio de logs
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# 2. Obtener el logger raíz para configurarlo
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Limpiar handlers existentes para evitar duplicados
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# 3. Crear formateador
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 4. Crear handler para el archivo
file_handler = logging.FileHandler(logs_dir / "frontend.log", mode='w')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# 5. Crear handler para la consola
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

# 6. Clase para redirigir stdout/stderr al logger
class StreamToLogger(TextIO):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger_instance: logging.Logger, level: int):
        self.logger = logger_instance
        self.level = level
        self.linebuf = ''

    def write(self, buf: str):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

# 7. Redirigir stdout y stderr
sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

logger = logging.getLogger(__name__)
logger.info("Logging configurado. stdout y stderr redirigidos al archivo de log.")
# --- Fin de la Configuración de Logging ---


class AppController(QObject):
    """
    Controlador principal que gestiona la inicialización asíncrona y el ciclo de vida de los recursos.
    """
    initialization_complete = pyqtSignal(object) # MainWindow
    initialization_error = pyqtSignal(str)
    
    def __init__(self, loop: asyncio.AbstractEventLoop, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.loop = loop
        self.user_id: Optional[UUID] = None
        self.main_window: Optional[MainWindow] = None
        
        self.http_client = httpx.AsyncClient(
            base_url=app_config.API_BASE_URL,
            timeout=app_config.REQUEST_TIMEOUT
        )
        self.api_client = UltiBotAPIClient(client=self.http_client)
        self.trading_mode_manager = TradingModeStateManager(api_client=self.api_client)
        self.initialization_finished = asyncio.Event()

    async def initialize(self):
        """
        Realiza la inicialización asíncrona, intentando conectar con el backend.
        """
        logger.info("Iniciando inicialización asíncrona...")
        try:
            await asyncio.sleep(2) 
            config_data = await self.api_client.get_user_configuration()
            self.user_id = UUID(config_data.get("userId", str(uuid4())))
            logger.info(f"Configuración recibida para el ID de usuario: {self.user_id}")
            
            # Sincronizar el modo de trading inicial
            await self.trading_mode_manager.sync_with_backend()

            self.main_window = MainWindow(
                user_id=self.user_id, 
                api_client=self.api_client,
                trading_mode_manager=self.trading_mode_manager,
                loop=self.loop
            )
            self.initialization_complete.emit(self.main_window)

        except (APIError, httpx.ConnectError) as e:
            error_message = f"Fallo al conectar con el backend: {e}"
            logger.critical(error_message, exc_info=True)
            self.initialization_error.emit(error_message)
        except Exception as e:
            error_message = f"Error inesperado durante la inicialización: {e}"
            logger.critical(error_message, exc_info=True)
            self.initialization_error.emit(error_message)
        finally:
            self.initialization_finished.set()

    def show_main_window(self, window: MainWindow):
        window.show()
        logger.info("Ventana principal mostrada.")

    def show_error_message(self, message: str):
        QMessageBox.critical(None, "Error Crítico de Inicialización", f"La aplicación no pudo iniciarse: {message}")
        if not self.initialization_finished.is_set():
            self.initialization_finished.set()

    async def cleanup(self):
        """Cierra los recursos asíncronos de forma segura."""
        logger.info("Iniciando el proceso de cierre de la aplicación...")
        if self.main_window:
            logger.info("Limpiando la ventana principal...")
            self.main_window.cleanup()
        
        logger.info("Cerrando el cliente HTTP...")
        if self.http_client and not self.http_client.is_closed:
            await self.http_client.aclose()
        logger.info("Cliente HTTP cerrado. Limpieza completada.")


async def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        with open("src/ultibot_ui/assets/style.qss", "r") as f:
            app.setStyleSheet(f.read())
        logger.info("Stylesheet cargado exitosamente.")
    except FileNotFoundError:
        logger.warning("Archivo de hoja de estilos no encontrado: src/ultibot_ui/assets/style.qss")

    loop = asyncio.get_event_loop()
    controller = AppController(loop=loop)
    controller.initialization_complete.connect(controller.show_main_window)
    controller.initialization_error.connect(controller.show_error_message)

    app_is_closing = asyncio.Event()

    @qasync.asyncSlot()
    async def on_about_to_quit():
        logger.info("Señal 'aboutToQuit' recibida. Ejecutando limpieza asíncrona.")
        await controller.cleanup()
        logger.info("Limpieza asíncrona completada.")
        app_is_closing.set()

    app.aboutToQuit.connect(on_about_to_quit)

    # Lanzar la inicialización como una tarea de fondo
    init_task = asyncio.create_task(controller.initialize())
    
    # Esperar a que la inicialización termine (para bien o para mal)
    await controller.initialization_finished.wait()

    # Si la inicialización falló, no continuar
    if not controller.main_window:
        logger.error("No se pudo crear la ventana principal. Saliendo.")
        init_task.cancel()
        return

    # Esperar a que la aplicación se cierre
    await app_is_closing.wait()
    logger.info("El bucle principal de la aplicación ha finalizado.")


if __name__ == "__main__":
    try:
        qasync.run(main())
    except Exception as e:
        logger.critical(f"Excepción no controlada en el arranque de la aplicación: {e}", exc_info=True)
        sys.exit(1)
