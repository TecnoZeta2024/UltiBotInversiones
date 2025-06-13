"""
Módulo de inicialización para el paquete de eventos de dominio.

Este módulo exporta todos los eventos definidos en los submódulos
para facilitar su importación desde un único punto.
"""

from .trading_events import (
    TradingEvent,
    OrderPlacedEvent,
    OrderFilledEvent,
    OrderCanceledEvent,
    PriceUpdateEvent,
    MarketDataReceivedEvent,
)
from .portfolio_events import (
    PortfolioEvent,
    BalanceUpdatedEvent,
    AssetAddedToPortfolioEvent,
    AssetRemovedFromPortfolioEvent,
    PortfolioSnapshotEvent,
)
from .strategy_events import (
    StrategyEvent,
    StrategyActivatedEvent,
    StrategyDeactivatedEvent,
    SignalDetectedEvent,
    StrategyErrorEvent,
    StrategyPerformanceUpdateEvent,
)

__all__ = [
    "TradingEvent",
    "OrderPlacedEvent",
    "OrderFilledEvent",
    "OrderCanceledEvent",
    "PriceUpdateEvent",
    "MarketDataReceivedEvent",
    "PortfolioEvent",
    "BalanceUpdatedEvent",
    "AssetAddedToPortfolioEvent",
    "AssetRemovedFromPortfolioEvent",
    "PortfolioSnapshotEvent",
    "StrategyEvent",
    "StrategyActivatedEvent",
    "StrategyDeactivatedEvent",
    "SignalDetectedEvent",
    "StrategyErrorEvent",
    "StrategyPerformanceUpdateEvent",
]
