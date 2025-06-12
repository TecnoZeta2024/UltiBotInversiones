# src/ultibot_ui/services/trading_mode_state.py
from PySide6.QtCore import QObject, Signal as pyqtSignal
from enum import Enum
from typing import Optional

class TradingModeEnum(str, Enum):
    """
    Enumeration for the trading modes.
    """
    PAPER = "paper"
    REAL = "real"

class TradingModeStateManager(QObject):
    """
    Manages the state of the trading mode (e.g., 'real' or 'paper').
    
    Emits signals when the trading mode changes, allowing different
    parts of the UI to react accordingly.
    """
    
    trading_mode_changed = pyqtSignal(str)

    def __init__(self, initial_mode: TradingModeEnum = TradingModeEnum.PAPER):
        """
        Initializes the TradingModeStateManager.
        
        Args:
            initial_mode: The initial trading mode.
        """
        super().__init__()
        self._trading_mode = initial_mode

    @property
    def trading_mode(self) -> TradingModeEnum:
        """Gets the current trading mode."""
        return self._trading_mode

    @trading_mode.setter
    def trading_mode(self, mode: TradingModeEnum) -> None:
        """
        Sets the trading mode and emits a signal if it changes.
        
        Args:
            mode: The new trading mode.
        """
        if not isinstance(mode, TradingModeEnum):
            raise TypeError("Trading mode must be a TradingModeEnum member")
        
        if self._trading_mode != mode:
            self._trading_mode = mode
            self.trading_mode_changed.emit(self._trading_mode.value)

# Singleton instance
_trading_mode_manager_instance: Optional[TradingModeStateManager] = None

def get_trading_mode_manager() -> TradingModeStateManager:
    """
    Provides a singleton instance of the TradingModeStateManager.
    
    This ensures that all parts of the application share the same
    trading mode state.
    
    Returns:
        The singleton TradingModeStateManager instance.
    """
    global _trading_mode_manager_instance
    if _trading_mode_manager_instance is None:
        _trading_mode_manager_instance = TradingModeStateManager()
    return _trading_mode_manager_instance

def reset_trading_mode_manager():
    """
    Resets the singleton instance. Useful for testing purposes.
    """
    global _trading_mode_manager_instance
    _trading_mode_manager_instance = None
