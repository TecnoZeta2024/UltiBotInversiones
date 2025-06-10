import logging
import asyncio
from typing import List, Any, Optional, Dict

from PyQt5.QtCore import QObject, pyqtSignal
from pydantic import ValidationError

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.models import BaseMainWindow
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig

logger = logging.getLogger(__name__)

class UIStrategyService(QObject):
    strategies_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, main_window: BaseMainWindow, loop: asyncio.AbstractEventLoop, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.api_client = api_client
        self.main_window = main_window
        self.loop = loop

    def fetch_strategies(self) -> None:
        """
        Inicia la obtención de estrategias desde el backend utilizando el TaskManager central.
        """
        logger.info("UIStrategyService: Iniciando fetch_strategies a través de TaskManager.")
        
        coroutine_factory = lambda client: client.get_strategies()
        
        self.main_window.submit_task(
            coroutine_factory,
            self._handle_strategies_result,
            self._handle_strategies_error
        )
        logger.debug("UIStrategyService: Tarea para fetch_strategies enviada al TaskManager.")

    def _handle_strategies_result(self, response_data: Dict[str, Any]):
        """
        Procesa el resultado exitoso de la obtención de estrategias.
        """
        try:
            strategies_data = response_data.get('strategies', [])
            
            if not isinstance(strategies_data, list):
                logger.warning(f"UIStrategyService: 'strategies' en la respuesta no es una lista. Se recibió {type(strategies_data)}.")
                self.error_occurred.emit("Formato de respuesta de estrategias inesperado.")
                return

            # Parsear los diccionarios a objetos TradingStrategyConfig
            parsed_strategies = [TradingStrategyConfig(**data) for data in strategies_data]
            
            self.strategies_updated.emit(parsed_strategies)
            logger.info(f"UIStrategyService: Se obtuvieron y emitieron {len(parsed_strategies)} estrategias exitosamente.")
        
        except ValidationError as e:
            logger.error(f"UIStrategyService: Error de validación Pydantic al procesar estrategias: {e}", exc_info=True)
            self.error_occurred.emit(f"Error en datos de estrategia recibidos: {str(e)}")
        except Exception as e:
            logger.error(f"UIStrategyService: Error procesando el resultado de las estrategias: {e}", exc_info=True)
            self.error_occurred.emit(f"Error procesando datos de estrategias: {str(e)}")

    def _handle_strategies_error(self, error_message: str):
        """
        Maneja los errores ocurridos durante la obtención de estrategias.
        """
        logger.error(f"UIStrategyService: Fallo al obtener estrategias: {error_message}")
        self.error_occurred.emit(f"Fallo al obtener estrategias: {error_message}")
