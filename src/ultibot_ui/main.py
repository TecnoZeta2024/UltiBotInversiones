import sys
import os
import logging

# --- Añadir el directorio raíz del proyecto a sys.path ---
# Esto asegura que las importaciones como 'from src.shared...' funcionen
# cuando el script se ejecuta directamente.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from typing import Optional, cast
from uuid import UUID

from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMessageBox

try:
    import qdarkstyle
except ImportError:
    qdarkstyle = None

from src.shared.data_types import UserConfiguration
from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from src.ultibot_ui.windows.main_window import MainWindow

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/frontend.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

class InitializationWorker(QObject):
    """
    Worker que se ejecuta en un hilo separado para realizar la inicialización asíncrona.
    """
    finished = pyqtSignal()
    error = pyqtSignal(str, str)
    user_config_ready = pyqtSignal(UserConfiguration)

    def __init__(self, api_client: UltiBotAPIClient):
        super().__init__()
        self.api_client = api_client

    @pyqtSlot()
    def run(self):
        """Ejecuta las tareas de inicialización."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            config = loop.run_until_complete(self.fetch_user_configuration())
            if config:
                self.user_config_ready.emit(config)
        finally:
            self.finished.emit()
            loop.close()

    async def fetch_user_configuration(self) -> Optional[UserConfiguration]:
        """Obtiene la configuración del usuario desde el backend."""
        logger.info("Worker: Obteniendo configuración de usuario...")
        try:
            config = await self.api_client.get_user_configuration()
            logger.info("Worker: Configuración de usuario obtenida con éxito.")
            return config
        except APIError as e:
            logger.error(f"Worker: Error de API - {e.status_code} - {e.message}")
            self.error.emit("Error de Configuración", f"No se pudo obtener la configuración del servidor ({e.status_code}).\nDetalles: {e.message}")
            return None
        except Exception as e:
            logger.critical(f"Worker: Error inesperado - {e}", exc_info=True)
            self.error.emit("Error Crítico", f"Ocurrió un error inesperado:\n{e}")
            return None

class UltiBotApplication(QObject):
    """
    Clase principal que gestiona la aplicación UI.
    """
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.main_window: Optional[MainWindow] = None
        self.api_client = UltiBotAPIClient(base_url="http://localhost:8000")
        self.user_config: Optional[UserConfiguration] = None
        self.fixed_user_id = UUID("00000000-0000-0000-0000-000000000001")
        
        self.initialization_thread = QThread()
        self.worker = InitializationWorker(self.api_client)
        self.worker.moveToThread(self.initialization_thread)

        self.worker.user_config_ready.connect(self.on_user_config_ready)
        self.worker.error.connect(self.show_error_message)
        self.worker.finished.connect(self.on_worker_finished)
        
        self.initialization_thread.started.connect(self.worker.run)
        self.initialization_thread.start()

    @pyqtSlot(UserConfiguration)
    def on_user_config_ready(self, config: UserConfiguration):
        """Maneja la configuración de usuario recibida y muestra la ventana principal."""
        logger.info("Configuración de usuario recibida. Mostrando ventana principal.")
        self.user_config = config
        self.main_window = MainWindow(
            user_id=self.user_config.id,
            api_client=self.api_client
        )
        self.main_window.show()
        logger.info("Ventana principal (MainWindow) mostrada.")

    @pyqtSlot(str, str)
    def show_error_message(self, title: str, message: str):
        """Muestra un cuadro de diálogo de error."""
        QMessageBox.critical(None, title, message)
        self.app.quit()

    @pyqtSlot()
    def on_worker_finished(self):
        """Limpia el hilo cuando el worker ha terminado."""
        logger.info("El worker de inicialización ha terminado.")
        self.initialization_thread.quit()
        self.initialization_thread.wait()
        if not self.user_config:
             logger.error("No se pudo obtener la configuración del usuario. La aplicación se cerrará.")
             self.app.quit()


    def cleanup(self):
        """Limpia los recursos de la aplicación antes de cerrar."""
        logger.info("Iniciando limpieza de la aplicación...")
        if self.main_window:
            self.main_window.close()
        # El cliente httpx se cierra en el destructor de UltiBotAPIClient
        logger.info("Limpieza completada.")

def main():
    """Función principal que configura y ejecuta la aplicación."""
    app = cast(QApplication, QApplication.instance())
    if not app:
        app = QApplication(sys.argv)
    
    if qdarkstyle:
        try:
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
            logger.info("Estilo oscuro aplicado.")
        except Exception as e:
            logger.error(f"Fallo al aplicar el estilo oscuro: {e}")
    else:
        logger.warning("qdarkstyle no está instalado.")

    ultibot_app = UltiBotApplication(app)
    app.aboutToQuit.connect(ultibot_app.cleanup)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    logger.info("Iniciando el punto de entrada de la aplicación frontend.")
    
    def excepthook(exc_type, exc_value, exc_tb):
        logger.critical("Excepción no controlada:", exc_info=(exc_type, exc_value, exc_tb))
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
