# src/ultibot_backend/services/simulated_portfolio_service.py
"""
Service to manage the state of the virtual portfolio for paper trading.
"""
import logging
from typing import Dict, Any
from decimal import Decimal

logger = logging.getLogger(__name__)

class SimulatedPortfolioService:
    """
    Manages a virtual portfolio for paper trading.

    This includes tracking balances, positions, and calculating performance metrics.
    """

    def __init__(self, initial_balance: Decimal = Decimal("100000.0")):
        self._initial_balance = initial_balance
        self._cash_balance = initial_balance
        self._positions: Dict[str, Dict[str, Decimal]] = {}  # e.g., {"BTC": {"quantity": 1.5, "avg_price": 50000}}
        logger.info(f"SimulatedPortfolioService initialized with initial balance: {initial_balance}")

    async def get_snapshot(self) -> Dict[str, Any]:
        """
        Provides a snapshot of the current virtual portfolio.
        """
        # In a real implementation, this would calculate total portfolio value
        # based on current market prices.
        total_value = self._cash_balance # Simplified for now
        for position in self._positions.values():
             # This is incorrect, needs market data. Placeholder logic.
            total_value += position["quantity"] * position["avg_price"]

        return {
            "cash_balance": self._cash_balance,
            "positions": self._positions,
            "total_value": total_value,
            "pnl": total_value - self._initial_balance
        }

    async def update_from_trade(self, trade: Dict[str, Any]) -> None:
        """
        Updates the portfolio based on a simulated trade execution.

        Args:
            trade: A dictionary representing a filled trade.
        """
        logger.info(f"Updating simulated portfolio from trade: {trade}")
        # This is where the logic to update cash and positions would go.
        # It needs to handle buys and sells, calculate new average prices, etc.
        # This will be implemented in more detail later.
        pass

# Singleton instance for dependency injection
simulated_portfolio_service = SimulatedPortfolioService()

def get_simulated_portfolio_service() -> SimulatedPortfolioService:
    """
    Dependency injector for the SimulatedPortfolioService.
    """
    return simulated_portfolio_service
