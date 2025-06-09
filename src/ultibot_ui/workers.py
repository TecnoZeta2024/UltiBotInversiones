import asyncio
import logging
from typing import Callable, Coroutine, Any, Optional
# import httpx # No longer needed here
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado, utilizando
    una instancia compartida de UltiBotAPIClient.
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 api_client: UltiBotAPIClient,
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine[Any, Any, Any]]] = None):
        super().__init__()
        self.api_client = api_client
        self.coroutine_factory = coroutine_factory
        logger.debug(f"ApiWorker initialized with shared API client and coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @pyqtSlot()
    def run(self):
        """
        Ejecuta la corutina de la API en un nuevo bucle de eventos
        dentro del hilo del worker, utilizando la instancia de APIClient proporcionada.
        """
        logger.debug("ApiWorker: run method started.")
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            return

        # The main application event loop (qasync) should manage the asyncio event loop.
        # We don't create a new event loop here as it can conflict with qasync.
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        
        # The httpx.AsyncClient (and its connection pool) is managed externally (in main.py).
        # It should not be closed by the worker.
        
        try:
            logger.debug("ApiWorker: Creating coroutine from factory using shared API client.")
            # The factory now receives the shared API client
            coroutine = self.coroutine_factory(self.api_client)
            logger.debug(f"ApiWorker: Coroutine created: {coroutine}. Running in event loop.")
            
            # Get the current event loop, which should be managed by qasync
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                # This case should ideally not happen if qasync is managing the main thread's loop
                # and this worker is in a QThread that qasync also manages.
                # If it's a truly separate thread without its own loop, one might be needed.
                # For now, we assume qasync provides the loop.
                logger.warning("ApiWorker: Event loop not running. Tasks may not execute as expected.")

            result = loop.run_until_complete(coroutine)
            
            logger.debug(f"ApiWorker: Coroutine finished. Result: {result}")
            self.result_ready.emit(result)
            logger.debug("ApiWorker: result_ready signal emitted.")
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc: # Catch generic exceptions after specific ones
            logger.error(f"ApiWorker: Generic Exception: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        # finally:
            # The event loop is managed by qasync, so worker does not close it.
            # The shared httpx.AsyncClient is managed in main.py, so worker does not close it.
            # logger.debug("ApiWorker: Event loop will not be closed by the worker.")
        logger.debug("ApiWorker: run method finished.")
