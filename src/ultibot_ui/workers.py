import asyncio
import logging
from typing import Callable, Coroutine, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado, utilizando
    el bucle de eventos principal de la aplicación (qasync).
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 api_client: UltiBotAPIClient,
                 coroutine_factory: Callable[[UltiBotAPIClient], Coroutine[Any, Any, Any]],
                 loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.api_client = api_client
        self.coroutine_factory = coroutine_factory
        self.loop = loop
        logger.debug(f"ApiWorker initialized with shared API client and event loop.")

    @pyqtSlot()
    def run(self):
        """
        Ejecuta la corutina de la API en el bucle de eventos principal de la aplicación
        de forma segura desde un hilo secundario.
        """
        logger.debug("ApiWorker: run method started.")
        try:
            coroutine = self.coroutine_factory(self.api_client)
            future = asyncio.run_coroutine_threadsafe(coroutine, self.loop)
            result = future.result()
            self.result_ready.emit(result)
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc:
            logger.error(f"ApiWorker: Generic Exception: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        
        logger.debug("ApiWorker: run method finished.")
