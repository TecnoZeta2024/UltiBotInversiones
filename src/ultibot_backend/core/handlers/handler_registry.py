"""
Módulo que implementa el HandlerRegistry.
Este registro permite el dispatch automático de comandos y consultas a sus
respectivos manejadores, y la suscripción de handlers a eventos,
desacoplando la capa de aplicación de la lógica de negocio.
"""

import logging
from typing import Any, Callable, Dict, List, Type, TypeVar, Coroutine, Optional

from pydantic import BaseModel

from src.ultibot_backend.core.domain_models.events import (
    OrderPlacedEvent,
    TradeExecutedEvent,
    OrderStatusChangedEvent,
    PortfolioChangedEvent,
    AlertTriggeredEvent,
    StrategyActivatedEvent,
    ScanCompletedEvent,
    AIAnalysisCompletedEvent,
    BaseEvent
)
from src.ultibot_backend.core.exceptions import HandlerNotFoundError, InvalidHandlerError
from src.ultibot_backend.core.services.event_broker import AsyncEventBroker
from src.ultibot_backend.core.handlers.event_handlers import (
    TradingEventHandlers,
    PortfolioEventHandlers,
    StrategyEventHandlers,
    GeneralEventHandlers,
)

logger = logging.getLogger(__name__)

# Definir un tipo genérico para los comandos/consultas/eventos
T = TypeVar('T', bound=BaseModel)

# Definir un tipo para los manejadores
HandlerCallable = Callable[[T], Coroutine[Any, Any, Any]]

class HandlerRegistry:
    """
    Registro centralizado para mapear tipos de comandos/consultas a sus manejadores
    y para registrar handlers de eventos con el EventBroker.
    """
    def __init__(self):
        """
        Inicializa el HandlerRegistry.
        """
        self._command_handlers: Dict[Type[BaseModel], HandlerCallable] = {}
        self._query_handlers: Dict[Type[BaseModel], HandlerCallable] = {}
        self._event_broker: Optional[AsyncEventBroker] = None
        logger.info("HandlerRegistry inicializado.")

    def register_command_handler(self, command_type: Type[BaseModel], handler: HandlerCallable) -> None:
        """
        Registra un manejador para un tipo de comando específico.
        """
        if command_type in self._command_handlers:
            raise InvalidHandlerError(f"Handler ya registrado para el comando: {command_type.__name__}")
        self._command_handlers[command_type] = handler
        logger.info(f"Handler registrado para el comando: {command_type.__name__}")

    def register_query_handler(self, query_type: Type[BaseModel], handler: HandlerCallable) -> None:
        """
        Registra un manejador para un tipo de consulta específico.
        """
        if query_type in self._query_handlers:
            raise InvalidHandlerError(f"Handler ya registrado para la consulta: {query_type.__name__}")
        self._query_handlers[query_type] = handler
        logger.info(f"Handler registrado para la consulta: {query_type.__name__}")

    def register_event_handlers(
        self,
        event_broker: AsyncEventBroker,
        trading_handlers: TradingEventHandlers,
        portfolio_handlers: PortfolioEventHandlers,
        strategy_handlers: StrategyEventHandlers,
        general_handlers: GeneralEventHandlers,
    ) -> None:
        """
        Registra los handlers de eventos con el EventBroker de forma dinámica y correcta.
        """
        self._event_broker = event_broker
        logger.info("Registrando handlers de eventos con el EventBroker...")

        # Mapeo de eventos a sus manejadores correspondientes
        event_handler_map = {
            # Trading Events
            OrderPlacedEvent: trading_handlers.handle_order_placed_event,
            TradeExecutedEvent: trading_handlers.handle_trade_executed_event,
            OrderStatusChangedEvent: trading_handlers.handle_order_status_changed_event,
            
            # Portfolio Events
            PortfolioChangedEvent: portfolio_handlers.handle_portfolio_changed_event,
            
            # Strategy Events
            StrategyActivatedEvent: strategy_handlers.handle_strategy_activated_event,
            AIAnalysisCompletedEvent: strategy_handlers.handle_ai_analysis_completed_event,
            ScanCompletedEvent: strategy_handlers.handle_scan_completed_event,

            # General Events
            AlertTriggeredEvent: general_handlers.handle_alert_triggered_event,
        }

        for event_type, handler in event_handler_map.items():
            event_broker.subscribe(event_type, handler)
            logger.info(f"Suscrito handler '{handler.__name__}' al evento '{event_type.__name__}'")

        logger.info("Todos los handlers de eventos han sido registrados.")

    async def dispatch_command(self, command: BaseModel) -> Any:
        """
        Despacha un comando a su manejador registrado.
        """
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise HandlerNotFoundError(f"No se encontró manejador para el comando: {type(command).__name__}")
        return await handler(command)

    async def dispatch_query(self, query: BaseModel) -> Any:
        """
        Despacha una consulta a su manejador registrado.
        """
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise HandlerNotFoundError(f"No se encontró manejador para la consulta: {type(query).__name__}")
        return await handler(query)

    def get_command_handler(self, command_type: Type[BaseModel]) -> HandlerCallable:
        """
        Obtiene el manejador registrado para un tipo de comando.
        """
        handler = self._command_handlers.get(command_type)
        if not handler:
            raise HandlerNotFoundError(f"No se encontró manejador para el comando: {command_type.__name__}")
        return handler

    def get_query_handler(self, query_type: Type[BaseModel]) -> HandlerCallable:
        """
        Obtiene el manejador registrado para un tipo de consulta.
        """
        handler = self._query_handlers.get(query_type)
        if not handler:
            raise HandlerNotFoundError(f"No se encontró manejador para la consulta: {query_type.__name__}")
        return handler

    def list_registered_commands(self) -> List[str]:
        """
        Lista los nombres de todos los comandos registrados.
        """
        return [cmd.__name__ for cmd in self._command_handlers.keys()]

    def list_registered_queries(self) -> List[str]:
        """
        Lista los nombres de todas las consultas registradas.
        """
        return [query.__name__ for query in self._query_handlers.keys()]
