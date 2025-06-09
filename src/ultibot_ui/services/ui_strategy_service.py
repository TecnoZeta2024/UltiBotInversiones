import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.shared.data_types import AiStrategyConfiguration
from src.ultibot_ui.workers import ApiWorker
from src.ultibot_ui.models import BaseMainWindow # Importar BaseMainWindow

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, main_window: BaseMainWindow, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.main_window = main_window # Guardar referencia a main_window

    async def fetch_strategies(self) -> None:
        """
        Fetches strategies from the backend and emits a signal with the data.
        """
        worker = ApiWorker(
            coroutine_factory=lambda api_client: api_client.get_strategies()
        )
        thread = QThread()
        self.main_window.add_thread(thread) # Añadir el hilo a main_window

        worker.moveToThread(thread)

        worker.result_ready.connect(lambda strategies: self.strategies_updated.emit([s.model_dump(mode='json') for s in strategies]))
        worker.error_occurred.connect(lambda e: self.error_occurred.emit(f"Failed to fetch strategies: {e}"))
        
        thread.started.connect(worker.run)
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        
        thread.start()
