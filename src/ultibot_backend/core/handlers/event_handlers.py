"""
Módulo que define los handlers para los eventos de dominio.

Estos handlers reaccionan a los eventos publicados por el EventBroker,
ejecutando lógica de negocio secundaria o actualizando el estado del sistema.
"""

import logging
from typing import Any

from src.ultibot_backend.core.domain_models.events import (
    OrderPlacedEvent,
    TradeExecutedEvent,
    OrderStatusChangedEvent,
    PortfolioChangedEvent,
    AlertTriggeredEvent,
    StrategyActivatedEvent,
    ScanCompletedEvent,
    AIAnalysisCompletedEvent,
)
from src.ultibot_backend.core.ports import IPersistencePort, INotificationPort

logger = logging.getLogger(__name__)

class TradingEventHandlers:
    """
    Handlers para eventos relacionados con operaciones de trading.
    """
    def __init__(self, persistence_port: IPersistencePort, notification_port: INotificationPort) -> None:
        self._persistence_port = persistence_port
        self._notification_port = notification_port
        logger.info("TradingEventHandlers inicializado.")

    async def handle_order_placed_event(self, event: OrderPlacedEvent) -> None:
        """Maneja el evento OrderPlacedEvent."""
        logger.info(f"Handler: Orden colocada - ID: {event.order.id}, Símbolo: {event.order.symbol}, Cantidad: {event.order.quantity}")
        await self._notification_port.send_alert(
            f"Orden {event.order.id} de {event.order.quantity} {event.order.symbol} ({event.order.side}) colocada.",
            "LOW"
        )

    async def handle_trade_executed_event(self, event: TradeExecutedEvent) -> None:
        """Maneja el evento TradeExecutedEvent."""
        logger.info(f"Handler: Trade ejecutado - ID: {event.trade.id}, Símbolo: {event.trade.symbol}, Cantidad: {event.trade.quantity}, Precio: {event.trade.price}")
        await self._notification_port.send_alert(
            f"Trade {event.trade.id} de {event.trade.symbol} ejecutado. Cantidad: {event.trade.quantity}, Precio: {event.trade.price}.",
            "MEDIUM"
        )
        # Aquí se podría añadir lógica para actualizar el portafolio, calcular PnL, persistir el trade, etc.

    async def handle_order_status_changed_event(self, event: OrderStatusChangedEvent) -> None:
        """Maneja el evento OrderStatusChangedEvent."""
        logger.info(f"Handler: Estado de orden cambiado - ID: {event.order_id}, Nuevo Estado: {event.new_status}")
        await self._notification_port.send_alert(
            f"Orden {event.order_id} cambió a estado: {event.new_status}.",
            "LOW"
        )

class PortfolioEventHandlers:
    """
    Handlers para eventos relacionados con la gestión de portafolios.
    """
    def __init__(self, persistence_port: IPersistencePort, notification_port: INotificationPort) -> None:
        self._persistence_port = persistence_port
        self._notification_port = notification_port
        logger.info("PortfolioEventHandlers inicializado.")

    async def handle_portfolio_changed_event(self, event: PortfolioChangedEvent) -> None:
        """Maneja el evento PortfolioChangedEvent."""
        logger.info(f"Handler: Portafolio cambiado - Snapshot: {event.portfolio_snapshot}")
        # Lógica para persistir el snapshot o notificar a la UI.

class StrategyEventHandlers:
    """
    Handlers para eventos relacionados con la ejecución y gestión de estrategias.
    """
    def __init__(self, notification_port: INotificationPort) -> None:
        self._notification_port = notification_port
        logger.info("StrategyEventHandlers inicializado.")

    async def handle_strategy_activated_event(self, event: StrategyActivatedEvent) -> None:
        """Maneja el evento StrategyActivatedEvent."""
        logger.info(f"Handler: Estrategia activada - Nombre: {event.strategy_name}")
        await self._notification_port.send_alert(
            f"Estrategia '{event.strategy_name}' activada.",
            "LOW"
        )

    async def handle_ai_analysis_completed_event(self, event: AIAnalysisCompletedEvent) -> None:
        """Maneja el evento AIAnalysisCompletedEvent."""
        logger.info(f"Handler: Análisis de IA completado - Símbolo: {event.symbol}, Decisión: {event.decision}")
        await self._notification_port.send_alert(
            f"Análisis de IA para {event.symbol} completado. Decisión: {event.decision}",
            "MEDIUM"
        )

    async def handle_scan_completed_event(self, event: ScanCompletedEvent) -> None:
        """Maneja el evento ScanCompletedEvent."""
        logger.info(f"Handler: Escaneo de mercado completado - Preset: {event.preset_name}, Oportunidades: {event.opportunities_found}")
        # Lógica para notificar o registrar los resultados del escaneo.

class GeneralEventHandlers:
    """
    Handlers para eventos generales del sistema.
    """
    def __init__(self, notification_port: INotificationPort) -> None:
        self._notification_port = notification_port
        logger.info("GeneralEventHandlers inicializado.")

    async def handle_alert_triggered_event(self, event: AlertTriggeredEvent) -> None:
        """Maneja el evento AlertTriggeredEvent."""
        logger.warning(f"Handler: Alerta disparada - Nombre: {event.alert_name}, Mensaje: {event.message}")
        await self._notification_port.send_alert(
            f"ALERTA: {event.alert_name} - {event.message}",
            "HIGH"
        )
