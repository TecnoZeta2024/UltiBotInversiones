import logging
import asyncio
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal as pyqtSignal

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
from ultibot_ui.services.trading_mode_state import get_trading_mode_manager

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.trading_mode_manager = get_trading_mode_manager()

    async def fetch_strategies(self) -> List[Dict[str, Any]]:
        """
        Fetches strategies from the backend and emits a signal with the data.
        """
        try:
            # The API now returns a StrategyListResponse model, which is a dict like {"strategies": [...]}
            response_data: Dict[str, Any] = await self.api_client.get_strategies()
            strategies_list = response_data.get("strategies", [])
            
            logger.info(f"Successfully fetched {len(strategies_list)} strategies.")
            self.strategies_updated.emit(strategies_list)
            return strategies_list # Return for direct use in the worker
        except APIError as e:
            error_message = f"Error de API al obtener estrategias: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise # Re-lanzar para que el worker pueda capturarlo
        except Exception as e:
            error_message = f"Error inesperado al obtener estrategias: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise

    async def create_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva estrategia en el backend.
        """
        try:
            result = await self.api_client.create_strategy_config(strategy_data)
            logger.info(f"Estrategia '{strategy_data.get('configName')}' creada exitosamente.")
            return result
        except APIError as e:
            error_message = f"Error de API al crear estrategia: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al crear estrategia: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise

    async def update_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una estrategia existente en el backend.
        """
        try:
            result = await self.api_client.update_strategy_config(strategy_id, strategy_data)
            logger.info(f"Estrategia '{strategy_data.get('configName')}' (ID: {strategy_id}) actualizada exitosamente.")
            return result
        except APIError as e:
            error_message = f"Error de API al actualizar estrategia {strategy_id}: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al actualizar estrategia {strategy_id}: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise

    async def delete_strategy(self, strategy_id: str) -> None:
        """
        Elimina una estrategia del backend.
        """
        try:
            await self.api_client.delete_strategy_config(strategy_id)
            logger.info(f"Estrategia ID: {strategy_id} eliminada exitosamente.")
        except APIError as e:
            error_message = f"Error de API al eliminar estrategia {strategy_id}: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al eliminar estrategia {strategy_id}: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise


    async def activate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Activa una estrategia de trading.
        """
        try:
            trading_mode = self.trading_mode_manager.current_mode
            result = await self.api_client.activate_strategy(strategy_id, trading_mode)
            logger.info(f"Estrategia {strategy_id} activada exitosamente.")
            return result
        except APIError as e:
            error_message = f"Error de API al activar estrategia {strategy_id}: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al activar estrategia {strategy_id}: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise

    async def deactivate_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Desactiva una estrategia de trading.
        """
        try:
            trading_mode = self.trading_mode_manager.current_mode
            result = await self.api_client.deactivate_strategy(strategy_id, trading_mode)
            logger.info(f"Estrategia {strategy_id} desactivada exitosamente.")
            return result
        except APIError as e:
            error_message = f"Error de API al desactivar estrategia {strategy_id}: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al desactivar estrategia {strategy_id}: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise