import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4
import httpx
import qasync
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

from src.ultibot_ui.windows.main_window import MainWindow
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui import app_config

# Crear directorio de logs si no existe
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Configuración avanzada de logging con salida a archivo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / "frontend.log")
    ]
)
logger = logging.getLogger(__name__)

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
        self.initialization_finished = asyncio.Event()

    async def initialize(self):
        """
        Realiza la inicialización asíncrona, intentando conectar con el backend.
        """
        logger.info("Iniciando inicialización asíncrona...")
        try:
            await asyncio.sleep(2) # Simula carga inicial
            config_data = await self.api_client.get_user_configuration()
            self.user_id = UUID(config_data.get("userId", str(uuid4())))
            logger.info(f"Configuración recibida para el ID de usuario: {self.user_id}")
            
            self.main_window = MainWindow(
                user_id=self.user_id, 
                api_client=self.api_client,
                loop=self.loop
            )
            self.initialization_complete.emit(self.main_window)

        except APIError as e:
            error_message = f"Fallo al cargar la configuración de la aplicación: {e}"
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
        logger.info("Iniciando el proceso de cierre del cliente HTTP...")
        if self.http_client and not self.http_client.is_closed:
            await self.http_client.aclose()
        logger.info("Cliente HTTP cerrado.")


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
        """
        Slot asíncrono que se ejecuta cuando la aplicación está a punto de cerrarse.
        Gestiona la limpieza de recursos asíncronos antes de que el bucle se detenga.
        """
        logger.info("Señal 'aboutToQuit' recibida. Ejecutando limpieza asíncrona.")
        await controller.cleanup()
        logger.info("Limpieza asíncrona completada.")
        app_is_closing.set()

    app.aboutToQuit.connect(on_about_to_quit)

    # Iniciar la inicialización
    init_task = asyncio.create_task(controller.initialize())
    await controller.initialization_finished.wait()

    if not controller.main_window:
        logger.error("No se pudo crear la ventana principal. Saliendo.")
        init_task.cancel()
        return

    # Esperar a que la señal de cierre se complete
    await app_is_closing.wait()
    logger.info("El bucle principal de la aplicación ha finalizado.")


if __name__ == "__main__":
    try:
        qasync.run(main())
    except Exception as e:
        logger.critical(f"Excepción no controlada en el arranque de la aplicación: {e}", exc_info=True)
        sys.exit(1)
