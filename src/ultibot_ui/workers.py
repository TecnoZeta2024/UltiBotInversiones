import asyncio
import logging
from typing import Optional, Callable, Coroutine
import httpx
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado, creando su
    propia instancia de APIClient para garantizar el aislamiento del hilo.
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine]] = None):
        super().__init__()
        self.coroutine_factory = coroutine_factory
        logger.debug(f"ApiWorker initialized with coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @pyqtSlot()
    def run(self):
        """
        Ejecuta la corutina de la API en un nuevo bucle de eventos
        dentro del hilo del worker, utilizando una instancia de APIClient local.
        """
        logger.debug("ApiWorker: run method started.")
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Cada worker crea su propio cliente para evitar conflictos de hilos y bucles de eventos.
        # TODO: Considerar la centralización de la URL base si es necesario.
        base_url = "http://127.0.0.1:8000"
        async_client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        api_client = UltiBotAPIClient(base_url=base_url, client=async_client)
        
        try:
            logger.debug("ApiWorker: Creating coroutine from factory.")
            coroutine = self.coroutine_factory(api_client)
            logger.debug(f"ApiWorker: Coroutine created: {coroutine}. Running in event loop.")
            
            # Se envuelve la corutina principal en una tarea que también cierra el cliente.
            async def main_task():
                try:
                    return await coroutine
                finally:
                    await async_client.aclose()
            
            result = loop.run_until_complete(main_task())
            
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
            logger.debug("ApiWorker: Event loop will not be closed by the worker.")
            logger.debug("ApiWorker: run method finished.")
