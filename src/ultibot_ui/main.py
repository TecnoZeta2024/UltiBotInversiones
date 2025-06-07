import asyncio
import logging
import sys
from typing import Optional, Any, cast
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import qdarkstyle
from qasync import QEventLoop

from src.shared.data_types import UserConfiguration
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.windows.main_window import MainWindow

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/frontend.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

class UltiBotApplication(QObject):
    """
    Clase principal que gestiona la aplicación UI, incluyendo la inicialización,
    la configuración del usuario y la ventana principal.
    """
    initialization_failed = pyqtSignal(str)

    def __init__(self, app: QApplication, loop: QEventLoop):
        super().__init__()
        self.app = app
        self.loop = loop
        self.main_window: Optional[MainWindow] = None
        self.api_client: Optional[UltiBotAPIClient] = None
        self.user_config: Optional[UserConfiguration] = None
        self.fixed_user_id = UUID("00000000-0000-0000-0000-000000000001")

    async def initialize_api_client(self):
        """Inicializa el cliente de la API de forma segura."""
        if self.api_client:
            await self.api_client.aclose()
        
        self.api_client = UltiBotAPIClient(base_url="http://localhost:8000")
        logger.info("Cliente API inicializado.")

    async def fetch_user_configuration(self) -> Optional[UserConfiguration]:
        """Obtiene la configuración del usuario desde el backend."""
        if not self.api_client:
            await self.initialize_api_client()

        logger.info(f"Obteniendo configuración para el usuario: {self.fixed_user_id}...")
        try:
            if self.api_client:
                config = await self.api_client.get_user_configuration()
                logger.info("Configuración de usuario obtenida con éxito.")
                return config
            else:
                raise Exception("El cliente API no está inicializado.")
        except APIError as e:
            logger.error(f"Error de API al obtener la configuración: {e.status_code} - {e.message}")
            self.show_error_message("Error de Configuración", f"No se pudo obtener la configuración del servidor ({e.status_code}).\nDetalles: {e.message}")
            return None
        except Exception as e:
            logger.critical(f"Error inesperado al obtener la configuración: {e}", exc_info=True)
            self.show_error_message("Error Crítico", f"Ocurrió un error inesperado:\n{e}")
            return None

    def show_error_message(self, title: str, message: str):
        """Muestra un cuadro de diálogo de error de forma segura."""
        def _show_msg():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText(title)
            msg_box.setInformativeText(message)
            msg_box.setWindowTitle("Error")
            msg_box.exec_()
        
        if isinstance(QApplication.instance(), QApplication):
             QTimer.singleShot(0, _show_msg)

    async def start(self):
        """Inicia el flujo de la aplicación de forma asíncrona."""
        self.user_config = await self.fetch_user_configuration()

        if self.user_config is None:
            self.initialization_failed.emit("No se pudo obtener la configuración del usuario.")
            self.app.quit()
            return

        if not self.api_client:
            await self.initialize_api_client()

        if self.api_client:
            self.main_window = MainWindow(
                user_id=self.user_config.id,
                api_client=self.api_client,
                qasync_loop=self.loop
            )
            self.main_window.show()
            logger.info("Ventana principal (MainWindow) mostrada.")
        else:
            self.show_error_message("Error Crítico", "El cliente API no pudo ser inicializado.")
            self.app.quit()

    async def cleanup(self):
        """Limpia los recursos de la aplicación antes de cerrar."""
        logger.info("Iniciando limpieza de la aplicación...")
        if self.main_window:
            self.main_window.close()
        if self.api_client:
            await self.api_client.aclose()
        logger.info("Limpieza completada.")

def main():
    """Función principal que configura y ejecuta la aplicación."""
    app = cast(QApplication, QApplication.instance())
    if not app:
        app = QApplication(sys.argv)
    
    try:
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
        logger.info("Estilo oscuro aplicado.")
    except Exception as e:
        logger.error(f"Fallo al aplicar el estilo oscuro: {e}")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    ultibot_app = UltiBotApplication(app, loop)

    async def on_quit_async():
        await ultibot_app.cleanup()

    def quit_slot():
        """Slot que no devuelve valor para conectar a la señal de PyQt."""
        loop.create_task(on_quit_async())

    app.aboutToQuit.connect(quit_slot)

    try:
        with loop:
            loop.create_task(ultibot_app.start())
            loop.run_forever()
    except Exception as e:
        logger.critical(f"El bucle de eventos principal ha fallado: {e}", exc_info=True)
    finally:
        if not loop.is_closed():
            loop.close()
        logger.info("Bucle de eventos de la aplicación cerrado.")

if __name__ == "__main__":
    def excepthook(exc_type, exc_value, exc_tb):
        logger.critical("Excepción no controlada en el hilo de la UI:", exc_info=(exc_type, exc_value, exc_tb))
        QMessageBox.critical(None, "Error Inesperado", f"Ha ocurrido un error crítico.\nRevise 'logs/frontend.log'.\n\nError: {exc_value}")
        QApplication.quit()

    sys.excepthook = excepthook
    
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Aplicación cerrada por el usuario.")
    except Exception as e:
        logger.critical(f"La aplicación ha fallado de forma inesperada: {e}", exc_info=True)
        
    sys.exit(0)
