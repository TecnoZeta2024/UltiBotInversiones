"""
Módulo para los workers de la UI de UltiBot.

Contiene clases que manejan tareas en segundo plano para no bloquear la UI.
"""
import asyncio
import logging
from typing import Optional, Callable, Coroutine

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class ApiWorker(QObject):
    """
    Worker que ejecuta una corutina de API en un hilo separado.
    """
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self,
                 base_url: str,
                 coroutine_factory: Optional[Callable[[UltiBotAPIClient], Coroutine]] = None,
                 token: Optional[str] = None):
        super().__init__()
        self.coroutine_factory = coroutine_factory
        self.base_url = base_url
        self.token = token
        logger.debug(f"ApiWorker initialized with base_url: {self.base_url}, token: {'present' if token else 'absent'}, coroutine_factory: {'set' if coroutine_factory else 'not set'}")

    @pyqtSlot()
    def run(self):
        """
        Ejecuta la corutina de la API.
        """
        if not self.coroutine_factory:
            logger.error("ApiWorker: coroutine_factory not set. Cannot run task.")
            self.error_occurred.emit("Error interno del Worker: Tarea no configurada.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        api_client_instance = None
        try:
            api_client_instance = UltiBotAPIClient(base_url=self.base_url, token=self.token)
            coroutine = self.coroutine_factory(api_client_instance)
            result = loop.run_until_complete(coroutine)
            self.result_ready.emit(result)
        except APIError as e_api:
            logger.error(f"ApiWorker: APIError: {e_api}", exc_info=True)
            self.error_occurred.emit(f"Error de API ({e_api.status_code}): {e_api.message}")
        except Exception as exc:
            logger.error(f"ApiWorker: Generic Exception: {exc}", exc_info=True)
            self.error_occurred.emit(str(exc))
        finally:
            if api_client_instance:
                loop.run_until_complete(api_client_instance.aclose())
            loop.close()
            asyncio.set_event_loop(None)
