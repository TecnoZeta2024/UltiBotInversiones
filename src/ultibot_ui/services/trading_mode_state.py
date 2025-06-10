"""
State management service for trading mode selection and propagation.
Manages the global trading mode state across the UI application by synchronizing with the backend.
"""
import logging
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal
from enum import Enum

from src.ultibot_ui.services.api_client import UltiBotAPIClient, APIError

logger = logging.getLogger(__name__)

class TradingMode(str, Enum):
    """Enum for trading modes, aligned with backend."""
    LIVE = "LIVE"
    PAPER = "PAPER"

    @property
    def display_name(self) -> str:
        """Get display-friendly name for the trading mode."""
        return "Live Trading" if self == TradingMode.LIVE else "Paper Trading"

    @property
    def color(self) -> str:
        """Get associated color for the trading mode."""
        return "#FF9800" if self == TradingMode.LIVE else "#4CAF50"

    @property
    def icon(self) -> str:
        """Get icon name for the trading mode."""
        return "💰" if self == TradingMode.LIVE else "📊"

class TradingModeStateManager(QObject):
    """
    Centralized state manager for trading mode selection.
    Synchronizes the trading mode with the backend.
    """
    trading_mode_changed = pyqtSignal(str)

    def __init__(self, api_client: UltiBotAPIClient, initial_mode: TradingMode = TradingMode.PAPER):
        super().__init__()
        self._api_client = api_client
        self._current_mode: TradingMode = initial_mode
        logger.info(f"TradingModeStateManager initialized with mode: {initial_mode.value}")

    @property
    def current_mode(self) -> TradingMode:
        """Get the current trading mode."""
        return self._current_mode

    async def sync_with_backend(self) -> None:
        """
        Fetches the current trading mode from the backend to initialize the state.
        """
        logger.info("Syncing trading mode with backend...")
        try:
            response = await self._api_client.get_trading_mode()
            mode = TradingMode(response["mode"])
            if mode != self._current_mode:
                self._current_mode = mode
                logger.info(f"Trading mode synced from backend: {self._current_mode.value}")
                self.trading_mode_changed.emit(self._current_mode.value)
        except APIError as e:
            logger.error(f"Failed to sync trading mode from backend: {e}. Defaulting to {self._current_mode.value}.")
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid trading mode data from backend: {e}. Defaulting to {self._current_mode.value}.")

    async def set_trading_mode(self, mode: TradingMode) -> bool:
        """
        Set the current trading mode by calling the backend and notify subscribers on success.
        
        Args:
            mode: The new trading mode.
        
        Returns:
            True if the mode was set successfully, False otherwise.
        """
        if not isinstance(mode, TradingMode):
            raise ValueError(f"Invalid trading mode: {mode}. Must be a TradingMode enum member.")

        if mode == self._current_mode:
            logger.info(f"Trading mode is already {mode.value}. No change needed.")
            return True

        logger.info(f"Attempting to set trading mode to {mode.value} via backend...")
        try:
            await self._api_client.set_trading_mode(mode.value)
            old_mode = self._current_mode
            self._current_mode = mode
            logger.info(f"Trading mode successfully changed from {old_mode.value} to {mode.value}")
            self.trading_mode_changed.emit(mode.value)
            return True
        except APIError as e:
            logger.error(f"Failed to set trading mode to {mode.value}: {e}")
            # Optionally, re-sync with backend to ensure state consistency
            await self.sync_with_backend()
            return False

    def get_available_modes(self) -> List[TradingMode]:
        """Get list of available trading modes."""
        return [TradingMode.LIVE, TradingMode.PAPER]

# Note: The global instance management is now handled by the dependency injection container
# in the main application to ensure the APIClient is properly injected.
