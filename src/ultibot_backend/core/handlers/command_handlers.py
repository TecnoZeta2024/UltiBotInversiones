"""
Command Handlers for the core application logic.

This module contains the handlers for executing commands. These handlers
are the entry points for changing the state of the application. They
orchestrate the domain models and services to fulfill the commands'
intent, adhering to the principles of Clean Architecture. The core
domain logic resides here and is kept independent of external frameworks
and UI.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from ultibot_backend.core.ports import (
    IUnitOfWork,
    IEventBroker,
    ITradingEngine,
    IAIOrchestrator,
    IPortfolioManager,
)
from ultibot_backend.core.commands.trading import (
    PlaceOrderCommand,
    CancelOrderCommand,
    UpdatePortfolioCommand,
)
from ultibot_backend.core.commands.ai import (
    TriggerAIAnalysisCommand,
)
from ultibot_backend.core.domain_models.trading import Order
from ultibot_backend.core.domain_models.portfolio import Portfolio
from ultibot_backend.core.domain_models.events import (
    OrderPlacedEvent,
    PortfolioUpdatedEvent,
    AIAnalysisTriggeredEvent,
)

# Se asume que OrderCancelledEvent está en events.py, si no, se necesitará añadir.
# from ultibot_backend.core.domain_models.events import OrderCancelledEvent

logger = logging.getLogger(__name__)

# ==============================================================================
# Trading Command Handlers
# ==============================================================================

async def handle_place_order(command: PlaceOrderCommand, uow: IUnitOfWork, trading_engine: ITradingEngine, event_broker: IEventBroker):
    """
    Handles the execution of a PlaceOrderCommand.

    Args:
        command: The PlaceOrderCommand to be handled.
        uow: The unit of work for database transactions.
        trading_engine: The trading engine service for order execution.
        event_broker: The event broker for publishing domain events.
    """
    logger.info(f"Handling PlaceOrderCommand for symbol {command.symbol}")
    async with uow:
        # Delegate order execution to the trading engine
        order_result = await trading_engine.execute_order(
            symbol=command.symbol,
            order_type=command.order_type,
            side=command.side,
            quantity=command.quantity,
            price=command.price,
            trading_mode=command.trading_mode,
            user_id=command.user_id,
        )

        # Persist the order
        # uow.repository.add(order_result) # La persistencia debe manejarse dentro del motor o en un paso posterior
        await uow.commit()

        # Publish an event
        event = OrderPlacedEvent(
            order=order_result
        )
        await event_broker.publish(event)
        logger.info(f"Order {order_result.id} placed and event published.")


async def handle_cancel_order(command: CancelOrderCommand, uow: IUnitOfWork, trading_engine: ITradingEngine, event_broker: IEventBroker):
    """
    Handles the execution of a CancelOrderCommand.

    Args:
        command: The CancelOrderCommand to be handled.
        uow: The unit of work for database transactions.
        trading_engine: The trading engine service for order cancellation.
        event_broker: The event broker for publishing domain events.
    """
    logger.info(f"Handling CancelOrderCommand for order {command.order_id}")
    async with uow:
        # Delegate order cancellation to the trading engine
        cancellation_status = await trading_engine.cancel_order(
            order_id=command.order_id,
            user_id=command.user_id,
        )

        if cancellation_status:
            # The trading engine should handle status updates.
            # The handler's job is to orchestrate and publish events.
            logger.info(f"Order {command.order_id} cancellation requested successfully.")
            # Event publishing might be handled by the engine itself
            # to ensure it happens only on successful cancellation.
        else:
            logger.warning(f"Failed to cancel order {command.order_id}")


async def handle_update_portfolio(command: UpdatePortfolioCommand, uow: IUnitOfWork, portfolio_manager: IPortfolioManager, event_broker: IEventBroker):
    """
    Handles the execution of an UpdatePortfolioCommand.

    Args:
        command: The UpdatePortfolioCommand to be handled.
        uow: The unit of work for database transactions.
        portfolio_manager: The portfolio management service.
        event_broker: The event broker for publishing domain events.
    """
    logger.info(f"Handling UpdatePortfolioCommand for user {command.user_id}")
    async with uow:
        # Delegate portfolio update to the portfolio manager
        updated_portfolio = await portfolio_manager.update_portfolio_snapshot(
            user_id=command.user_id,
            trading_mode=command.trading_mode,
        )

        # Persist the updated portfolio
        # uow.repository.add(updated_portfolio) # Persistencia manejada por el portfolio_manager
        await uow.commit()

        # Publish an event
        event = PortfolioUpdatedEvent(
            portfolio_data=updated_portfolio.dict()
        )
        await event_broker.publish(event)
        logger.info(f"Portfolio for user {command.user_id} updated and event published.")


# ==============================================================================
# AI Command Handlers
# ==============================================================================

async def handle_trigger_ai_analysis(command: TriggerAIAnalysisCommand, ai_orchestrator: IAIOrchestrator, event_broker: IEventBroker):
    """
    Handles the execution of a TriggerAIAnalysisCommand.

    Args:
        command: The TriggerAIAnalysisCommand to be handled.
        ai_orchestrator: The AI orchestrator service.
        event_broker: The event broker for publishing domain events.
    """
    logger.info(f"Handling TriggerAIAnalysisCommand for opportunity {command.opportunity_id}")

    # Delegate the analysis to the AI orchestrator
    analysis_result = await ai_orchestrator.analyze_opportunity(
        opportunity_id=command.opportunity_id,
        market_data=command.market_data,
    )

    # Publish an event with the analysis result
    event = AIAnalysisTriggeredEvent(
        opportunity_id=command.opportunity_id,
        analysis_result=analysis_result.dict(),
        decision="N/A" # El resultado del análisis ya contiene la decisión
    )
    await event_broker.publish(event)
    logger.info(f"AI analysis for opportunity {command.opportunity_id} triggered and event published.")

# ==============================================================================
# Handler Mapping
# ==============================================================================

COMMAND_HANDLERS = {
    PlaceOrderCommand: handle_place_order,
    CancelOrderCommand: handle_cancel_order,
    UpdatePortfolioCommand: handle_update_portfolio,
    TriggerAIAnalysisCommand: handle_trigger_ai_analysis,
}
