"""
Query Handlers for the core application logic.

This module contains handlers for executing queries. These handlers are
responsible for fetching data and returning it, typically as Data Transfer
Objects (DTOs), without altering the state of the application. They
interact with a read-only interface of the persistence layer.
"""

import logging
from typing import List, Dict, Any
from uuid import UUID

from src.ultibot_backend.core.ports import IUnitOfWork
from src.ultibot_backend.core.queries.trading import (
    GetPortfolioQuery,
    GetOrderHistoryQuery,
    GetTradeDetailsQuery,
)
from src.ultibot_backend.core.domain_models.trading import (
    Order,
    Trade,
)
from src.ultibot_backend.core.domain_models.portfolio import Portfolio

logger = logging.getLogger(__name__)

# ==============================================================================
# Query Handlers
# ==============================================================================

async def handle_get_portfolio(query: GetPortfolioQuery, uow: IUnitOfWork) -> Portfolio:
    """
    Handles the GetPortfolioQuery to retrieve a user's portfolio.

    Args:
        query: The GetPortfolioQuery containing user and trading mode info.
        uow: The unit of work to access the data repository.

    Returns:
        The user's portfolio.
    """
    logger.info(f"Handling GetPortfolioQuery for user {query.user_id} in {query.trading_mode} mode.")
    async with uow:
        # In a real CQRS system, this might use a dedicated read model.
        # For simplicity, we query the main repository.
        portfolio = await uow.repository.find_one(
            Portfolio, user_id=query.user_id, trading_mode=query.trading_mode
        )
        if not portfolio:
            logger.warning(f"No portfolio found for user {query.user_id} in {query.trading_mode} mode.")
            # Depending on requirements, could raise an exception or return a default empty portfolio.
            # For now, let's assume a default or raise.
            raise ValueError(f"Portfolio not found for user {query.user_id}")
        return portfolio


async def handle_get_order_history(query: GetOrderHistoryQuery, uow: IUnitOfWork) -> List[Order]:
    """
    Handles the GetOrderHistoryQuery to retrieve a user's order history.

    Args:
        query: The GetOrderHistoryQuery containing user info.
        uow: The unit of work to access the data repository.

    Returns:
        A list of the user's orders.
    """
    logger.info(f"Handling GetOrderHistoryQuery for user {query.user_id}.")
    async with uow:
        orders = await uow.repository.find(Order, user_id=query.user_id)
        return orders


async def handle_get_trade_details(query: GetTradeDetailsQuery, uow: IUnitOfWork) -> Trade:
    """
    Handles the GetTradeDetailsQuery to retrieve details of a specific trade.

    Args:
        query: The GetTradeDetailsQuery containing the trade ID.
        uow: The unit of work to access the data repository.

    Returns:
        The requested trade details.
    """
    logger.info(f"Handling GetTradeDetailsQuery for trade {query.trade_id}.")
    async with uow:
        trade = await uow.repository.get(Trade, query.trade_id)
        if not trade:
            raise ValueError(f"Trade with ID {query.trade_id} not found.")
        return trade

# ==============================================================================
# Handler Mapping
# ==============================================================================

QUERY_HANDLERS = {
    GetPortfolioQuery: handle_get_portfolio,
    GetOrderHistoryQuery: handle_get_order_history,
    GetTradeDetailsQuery: handle_get_trade_details,
}
