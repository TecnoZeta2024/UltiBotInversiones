"""
Módulo de inicialización para el paquete de handlers.

Este módulo exporta todos los handlers de comandos, consultas y eventos
definidos en los submódulos para facilitar su importación desde un único punto.
"""

from .command_handlers import (
    handle_place_order,
    handle_cancel_order,
    handle_update_portfolio,
    handle_trigger_ai_analysis,
    COMMAND_HANDLERS,
)
from .query_handlers import (
    handle_get_portfolio,
    handle_get_order_history,
    handle_get_trade_details,
    QUERY_HANDLERS,
)
from .event_handlers import (
    TradingEventHandlers,
    PortfolioEventHandlers,
    StrategyEventHandlers,
    GeneralEventHandlers,
)

__all__ = [
    # Command Handlers
    "handle_place_order",
    "handle_cancel_order",
    "handle_update_portfolio",
    "handle_trigger_ai_analysis",
    "COMMAND_HANDLERS",
    # Query Handlers
    "handle_get_portfolio",
    "handle_get_order_history",
    "handle_get_trade_details",
    "QUERY_HANDLERS",
    # Event Handlers
    "TradingEventHandlers",
    "PortfolioEventHandlers",
    "StrategyEventHandlers",
    "GeneralEventHandlers",
]
