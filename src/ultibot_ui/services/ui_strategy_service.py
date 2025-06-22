import logging
import asyncio
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal as pyqtSignal

from ultibot_ui.services.api_client import UltiBotAPIClient
from shared.data_types import AIStrategyConfiguration

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client # Usar la instancia de api_client
        # El cliente ya no se almacena aquí.

    async def fetch_strategies(self, api_client: UltiBotAPIClient) -> None:
        """
        Fetches strategies from the backend and emits a signal with the data.
        This method now accepts an active API client.
        """
        try:
            # Este método no existe en el cliente, se usa data mock por ahora.
            # En el futuro, se reemplazaría por:
            # strategies: List[AIStrategyConfiguration] = await api_client.get_strategies()
            await asyncio.sleep(0.1) # Simular llamada
            strategies_data = [
                {'id': 'strat_1', 'name': 'Momentum Breakout'},
                {'id': 'strat_2', 'name': 'Mean Reversion ETH'},
                {'id': 'strat_3', 'name': 'AI-Based Signal'},
            ]
            strategies = [AIStrategyConfiguration.model_validate(s) for s in strategies_data]
            
            logger.info(f"Successfully fetched {len(strategies)} strategies.")
            strategy_dicts = [s.model_dump(mode='json') for s in strategies]
            self.strategies_updated.emit(strategy_dicts)
        except Exception as e:
            error_message = f"Failed to fetch strategies: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
