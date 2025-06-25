import logging
import asyncio
from typing import List, Dict, Any, Optional
from PySide6.QtCore import QObject, Signal as pyqtSignal

from ultibot_ui.services.api_client import UltiBotAPIClient, APIError
# from shared.data_types import AIStrategyConfiguration # Comentado para evitar dependencia no clara

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client

    async def fetch_strategies(self) -> List[Dict[str, Any]]:
        """
        Fetches strategies from the backend and emits a signal with the data.
        """
        try:
            strategies_data: List[Dict[str, Any]] = await self.api_client.get_strategies()
            # Si AIStrategyConfiguration es un modelo Pydantic, se podría validar aquí:
            # strategies = [AIStrategyConfiguration.model_validate(s) for s in strategies_data]
            # strategy_dicts = [s.model_dump(mode='json') for s in strategies]
            # self.strategies_updated.emit(strategy_dicts)
            
            # Por ahora, emitimos los datos tal cual vienen del backend
            logger.info(f"Successfully fetched {len(strategies_data)} strategies.")
            self.strategies_updated.emit(strategies_data)
            return strategies_data # Retornar para uso directo en el worker
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

    async def delete_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """
        Elimina una estrategia del backend.
        """
        try:
            result = await self.api_client.delete_strategy_config(strategy_id)
            logger.info(f"Estrategia ID: {strategy_id} eliminada exitosamente.")
            return result
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

    async def update_strategy_status(self, strategy_id: str, is_active: bool) -> Dict[str, Any]:
        """
        Actualiza el estado activo de una estrategia (activar/desactivar).
        """
        try:
            # Asumiendo que el trading_mode se gestiona a nivel de backend o es un valor por defecto
            # Si el backend requiere trading_mode, se necesitaría obtenerlo de alguna parte (ej. UIConfigService)
            # Por ahora, se usará un valor por defecto o se asumirá que el backend lo infiere.
            # Si es necesario, se puede añadir un parámetro `trading_mode: str` a esta función.
            trading_mode = "paper" # O obtener de self.api_client.get_current_trading_mode() si existe
            result = await self.api_client.update_strategy_status(strategy_id, is_active, trading_mode)
            logger.info(f"Estrategia {strategy_id} actualizada a estado activo: {is_active}.")
            return result
        except APIError as e:
            error_message = f"Error de API al cambiar estado de estrategia {strategy_id}: {e.message} (Código: {e.status_code})"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
        except Exception as e:
            error_message = f"Error inesperado al cambiar estado de estrategia {strategy_id}: {e}"
            logger.error(error_message, exc_info=True)
            self.error_occurred.emit(error_message)
            raise
