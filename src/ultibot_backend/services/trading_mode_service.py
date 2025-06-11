# src/ultibot_backend/services/trading_mode_service.py
"""
Service to manage the application's trading mode.
"""
from enum import Enum
from typing import Literal

class TradingMode(str, Enum):
    """Enumeration for the trading modes."""
    LIVE = "LIVE"
    PAPER = "PAPER"

class TradingModeService:
    """
    Manages the trading mode state for the application.
    
    This service acts as a singleton to hold the current trading mode.
    """
    _instance = None
    _current_mode: TradingMode = TradingMode.PAPER  # Default to paper trading for safety

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TradingModeService, cls).__new__(cls)
        return cls._instance

    def set_mode(self, mode: Literal[TradingMode.LIVE, TradingMode.PAPER]) -> None:
        """
        Sets the current trading mode.

        Args:
            mode: The trading mode to set. Must be one of the TradingMode enum values.
        """
        if not isinstance(mode, TradingMode):
            raise TypeError("Mode must be an instance of TradingMode Enum")
        self._current_mode = mode
        print(f"Trading mode set to: {self._current_mode.value}")

    def get_mode(self) -> TradingMode:
        """
        Retrieves the current trading mode.

        Returns:
            The current trading mode.
        """
        return self._current_mode

# Singleton instance for dependency injection
trading_mode_service = TradingModeService()

def get_trading_mode_service() -> TradingModeService:
    """
    Dependency injector for the TradingModeService.
    """
    return trading_mode_service
