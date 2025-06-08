import asyncio
import logging
from typing import Optional, Callable, Coroutine

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado, integrándose
    correctamente con el event loop de qasync.
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 api_client: UltiBotAPIClient,
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine]] = None):
        super().__init__()
        self.api_client = api_client
        self.coroutine_factory = coroutine_factory
        logger.debug(f"ApiWorker initialized with api_client: {api_client}, coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @pyqtSlot()
    def run(self):
        """
        Ejecuta la corutina de la API en un nuevo bucle de eventos
        dentro del hilo del worker.
        """
        logger.debug("ApiWorker: run method started.")
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            return

        # Se crea un nuevo bucle de eventos para este hilo.
        # Esto es crucial porque el worker se ejecuta en un QThread separado.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            logger.debug("ApiWorker: Creating coroutine from factory.")
            coroutine = self.coroutine_factory(self.api_client)
            logger.debug(f"ApiWorker: Coroutine created: {coroutine}. Running in event loop.")
            result = loop.run_until_complete(coroutine)
            logger.debug(f"ApiWorker: Coroutine finished. Result: {result}")
            self.result_ready.emit(result)
            logger.debug("ApiWorker: result_ready signal emitted.")
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc:
            logger.error(f"ApiWorker: Generic Exception: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        finally:
            logger.debug("ApiWorker: Closing event loop.")
            loop.close()
            logger.debug("ApiWorker: run method finished.")
