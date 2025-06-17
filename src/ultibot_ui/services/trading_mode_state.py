"""
State management service for trading mode selection and propagation.
Manages the global trading mode state across the UI application.
"""
import logging
from typing import Literal, Optional, Callable, List
from PySide6.QtCore import QObject, Signal
from enum import Enum

logger = logging.getLogger(__name__)

# Type alias for trading modes
TradingMode = Literal["paper", "real"]

class TradingModeEnum(Enum):
    """Enum for trading modes with display properties."""
    PAPER = "paper"
    REAL = "real"
    
    @property
    def display_name(self) -> str:
        """Get display-friendly name for the trading mode."""
        if self == TradingModeEnum.PAPER:
            return "Paper Trading"
        elif self == TradingModeEnum.REAL:
            return "Real Trading"
        return self.value
    
    @property
    def color(self) -> str:
        """Get associated color for the trading mode."""
        if self == TradingModeEnum.PAPER:
            return "#4CAF50"  # Green for paper trading
        elif self == TradingModeEnum.REAL:
            return "#FF9800"  # Orange for real trading
        return "#777777"
    
    @property
    def icon(self) -> str:
        """Get icon name for the trading mode."""
        if self == TradingModeEnum.PAPER:
            return "📊"  # Chart icon for paper trading
        elif self == TradingModeEnum.REAL:
            return "💰"  # Money icon for real trading
        return "❓"

class TradingModeStateManager(QObject):
    """
    Centralized state manager for trading mode selection.
    
    This class manages the current trading mode and notifies subscribers
    when the mode changes, enabling synchronized UI updates across components.
    """
    
    # Signal emitted when trading mode changes
    trading_mode_changed = Signal(str)  # Emits the new trading mode as string
    
    def __init__(self, initial_mode: TradingMode = "paper"):
        """
        Initialize the state manager with the specified initial mode.
        
        Args:
            initial_mode: The initial trading mode ('paper' or 'real')
        """
        super().__init__()
        self._current_mode: TradingMode = initial_mode
        self._subscribers: List[Callable[[TradingMode], None]] = []
        logger.info(f"TradingModeStateManager initialized with mode: {initial_mode}")
    
    @property
    def current_mode(self) -> TradingMode:
        """Get the current trading mode."""
        return self._current_mode
    
    @property
    def current_mode_enum(self) -> TradingModeEnum:
        """Get the current trading mode as enum."""
        return TradingModeEnum(self._current_mode)
    
    def set_trading_mode(self, mode: TradingMode) -> None:
        """
        Set the current trading mode and notify all subscribers.
        
        Args:
            mode: The new trading mode ('paper' or 'real')
        """
        if mode not in ["paper", "real"]:
            raise ValueError(f"Invalid trading mode: {mode}. Must be 'paper' or 'real'")
        
        if mode != self._current_mode:
            old_mode = self._current_mode
            self._current_mode = mode
            
            logger.info(f"Trading mode changed from {old_mode} to {mode}")
            
            # Emit Qt signal
            self.trading_mode_changed.emit(mode)
            
            # Notify direct subscribers (callback pattern)
            for subscriber in self._subscribers:
                try:
                    subscriber(mode)
                except Exception as e:
                    logger.error(f"Error notifying subscriber about mode change: {e}", exc_info=True)
    
    def subscribe(self, callback: Callable[[TradingMode], None]) -> None:
        """
        Subscribe to trading mode changes using callback pattern.
        
        Args:
            callback: Function to call when trading mode changes
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.debug(f"Added subscriber: {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")
    
    def unsubscribe(self, callback: Callable[[TradingMode], None]) -> None:
        """
        Unsubscribe from trading mode changes.
        
        Args:
            callback: Function to remove from subscribers
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"Removed subscriber: {callback.__name__ if hasattr(callback, '__name__') else str(callback)}")
    
    def toggle_mode(self) -> TradingMode:
        """
        Toggle between paper and real trading modes.
        
        Returns:
            The new trading mode after toggling
        """
        new_mode: TradingMode = "real" if self._current_mode == "paper" else "paper"
        self.set_trading_mode(new_mode)
        return new_mode
    
    def is_paper_mode(self) -> bool:
        """Check if current mode is paper trading."""
        return self._current_mode == "paper"
    
    def is_real_mode(self) -> bool:
        """Check if current mode is real trading."""
        return self._current_mode == "real"
    
    def get_available_modes(self) -> List[TradingModeEnum]:
        """Get list of available trading modes."""
        return [TradingModeEnum.PAPER, TradingModeEnum.REAL]
    
    def get_mode_display_info(self) -> dict:
        """
        Get display information for the current mode.
        
        Returns:
            Dictionary with display name, color, and icon for current mode
        """
        mode_enum = self.current_mode_enum
        return {
            "mode": self._current_mode,
            "display_name": mode_enum.display_name,
            "color": mode_enum.color,
            "icon": mode_enum.icon
        }
    
    def get_all_modes_info(self) -> List[dict]:
        """
        Get display information for all available modes.
        
        Returns:
            List of dictionaries with mode information
        """
        return [
            {
                "mode": mode.value,
                "display_name": mode.display_name,
                "color": mode.color,
                "icon": mode.icon
            }
            for mode in self.get_available_modes()
        ]
    
    def save_to_config(self, config_dict: dict) -> dict:
        """
        Save current trading mode to configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary to update
            
        Returns:
            Updated configuration dictionary
        """
        config_dict["current_trading_mode"] = self._current_mode
        return config_dict
    
    def load_from_config(self, config_dict: dict) -> None:
        """
        Load trading mode from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary to read from
        """
        if "current_trading_mode" in config_dict:
            mode = config_dict["current_trading_mode"]
            if mode in ["paper", "real"]:
                self.set_trading_mode(mode)
                logger.info(f"Loaded trading mode from config: {mode}")
            else:
                logger.warning(f"Invalid trading mode in config: {mode}. Using default.")

# Global state manager instance
_global_state_manager: "Optional[TradingModeStateManager]" = None

def get_trading_mode_manager() -> "TradingModeStateManager":
    """
    Get the global trading mode state manager instance.
    
    Creates the instance if it doesn't exist (singleton pattern).
    
    Returns:
        The global TradingModeStateManager instance
    """
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = TradingModeStateManager()
        logger.info("Created global trading mode state manager")
    return _global_state_manager

def reset_trading_mode_manager() -> None:
    """Reset the global state manager (mainly for testing purposes)."""
    global _global_state_manager
    _global_state_manager = None
    logger.info("Reset global trading mode state manager")
