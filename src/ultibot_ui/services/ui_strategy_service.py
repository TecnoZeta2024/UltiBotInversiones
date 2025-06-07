import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.shared.data_types import AiStrategyConfiguration

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._api_client = api_client

    async def fetch_strategies(self) -> None:
        """
        Fetches strategies from the backend and emits a signal with the data.
        """
        try:
            strategies: List[AiStrategyConfiguration] = await self._api_client.get_strategies()
            logger.info(f"Successfully fetched {len(strategies)} strategies.")
            # Convert models to dicts for signal emission if necessary, or ensure receiver can handle objects
            strategy_dicts = [s.model_dump(mode='json') for s in strategies]
            self.strategies_updated.emit(strategy_dicts)
        except Exception as e:
            error_message = f"Failed to fetch strategies: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
