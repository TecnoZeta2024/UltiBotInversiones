import logging
import asyncio
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from typing import List, Any # Added for type hinting

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.shared.data_types import AiStrategyConfiguration # Keep if used for type hinting strategy objects
from src.ultibot_ui.workers import ApiWorker
from src.ultibot_ui.models import BaseMainWindow # Keep this for type hinting main_window

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list) # List of AiStrategyConfiguration dicts or compatible structures
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, loop: asyncio.AbstractEventLoop, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client # Store the shared API client
        self.main_window = main_window
        self.loop = loop

    def fetch_strategies(self) -> None: # This method is not async, it starts a worker
        """
        Starts a worker to fetch strategies from the backend and emits a signal with the data.
        The actual API call (get_strategies) is async and run by the worker.
        """
        logger.info("UIStrategyService: Initiating fetch_strategies via ApiWorker.")
        # The coroutine_factory's argument 'client' will be self.api_client passed by the worker
        worker = ApiWorker(
            api_client=self.api_client,
            coroutine_factory=lambda client: client.get_strategies(),
            loop=self.loop
        )
        thread = QThread()
        # Ensure main_window has add_thread method.
        if hasattr(self.main_window, 'add_thread'):
            self.main_window.add_thread(thread)
        else:
            logger.warning("UIStrategyService: main_window does not have add_thread method. Thread not tracked by main_window.")

        worker.moveToThread(thread)

        worker.result_ready.connect(self._handle_strategies_result)
        worker.error_occurred.connect(self._handle_strategies_error)
        
        thread.started.connect(worker.run)
        # Ensure thread quits and worker is deleted after task completion or error
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater) # Ensure thread itself is cleaned up
        
        thread.start()
        logger.debug("UIStrategyService: ApiWorker for fetch_strategies started.")

    def _handle_strategies_result(self, strategies: List[Any]): # 'Any' can be refined if strategy type is known
        try:
            # Assuming strategies might be Pydantic models or list of dicts
            # Based on original code: [s.model_dump(mode='json') for s in strategies]
            if strategies and hasattr(strategies[0], 'model_dump'):
                strategy_dicts = [s.model_dump(mode='json') for s in strategies]
            elif isinstance(strategies, list) and all(isinstance(item, dict) for item in strategies):
                strategy_dicts = strategies # Already a list of dicts
            elif isinstance(strategies, list): # List of something else, try to process if possible or log
                # This case might need more specific handling depending on actual returned type
                logger.warning(f"UIStrategyService: Strategies are a list, but not of dicts. Attempting direct emit.")
                strategy_dicts = strategies # Emit as is, or raise error
            else:
                logger.warning(f"UIStrategyService: Unexpected type for strategies: {type(strategies)}. Emitting empty list.")
                strategy_dicts = []

            self.strategies_updated.emit(strategy_dicts)
            logger.info(f"UIStrategyService: Successfully fetched and emitted {len(strategy_dicts)} strategies.")
        except Exception as e:
            logger.error(f"UIStrategyService: Error processing strategies result: {e}", exc_info=True)
            self.error_occurred.emit(f"Error processing strategies data: {str(e)}")

    def _handle_strategies_error(self, error_message: str):
        logger.error(f"UIStrategyService: Failed to fetch strategies: {error_message}")
        self.error_occurred.emit(f"Failed to fetch strategies: {error_message}")
