"""
Unit tests for the TradingModeStateManager.
"""
import pytest
from unittest.mock import MagicMock

# Mock PyQt5 modules before importing UI components
import sys
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()

from ultibot_ui.services.trading_mode_state import (
    TradingModeStateManager,
    TradingModeEnum,
    get_trading_mode_manager,
    reset_trading_mode_manager,
)

class TestTradingModeStateManager:
    """
    Tests the functionality of the TradingModeStateManager singleton.
    """

    def setup_method(self):
        """
        Ensure a clean state for each test by resetting the singleton.
        """
        reset_trading_mode_manager()
        self.manager = get_trading_mode_manager()

    def test_initial_state_is_paper(self):
        """
        Verify that the initial trading mode is 'paper'.
        """
        assert self.manager.trading_mode == TradingModeEnum.PAPER

    def test_set_trading_mode(self):
        """
        Test setting a new trading mode and verifying the state change.
        """
        self.manager.trading_mode = TradingModeEnum.REAL
        assert self.manager.trading_mode == TradingModeEnum.REAL

    def test_signal_emitted_on_change(self):
        """
        Verify that the 'trading_mode_changed' signal is emitted when the mode changes.
        """
        # Mock the signal's emit method
        self.manager.trading_mode_changed.emit = MagicMock()

        # Act
        self.manager.trading_mode = TradingModeEnum.REAL

        # Assert
        self.manager.trading_mode_changed.emit.assert_called_once_with(TradingModeEnum.REAL.value)

    def test_signal_not_emitted_on_no_change(self):
        """
        Verify that the signal is not emitted if the mode is set to its current value.
        """
        # Arrange
        self.manager.trading_mode = TradingModeEnum.REAL
        self.manager.trading_mode_changed.emit = MagicMock()

        # Act
        self.manager.trading_mode = TradingModeEnum.REAL

        # Assert
        self.manager.trading_mode_changed.emit.assert_not_called()

    def test_singleton_instance_is_consistent(self):
        """
        Test that get_trading_mode_manager always returns the same instance.
        """
        instance1 = get_trading_mode_manager()
        instance2 = get_trading_mode_manager()
        assert instance1 is instance2

        instance1.trading_mode = TradingModeEnum.REAL
        assert instance2.trading_mode == TradingModeEnum.REAL

    def test_reset_singleton(self):
        """
        Test that the reset function creates a new instance.
        """
        instance1 = get_trading_mode_manager()
        reset_trading_mode_manager()
        instance2 = get_trading_mode_manager()

        assert instance1 is not instance2
        assert instance2.trading_mode == TradingModeEnum.PAPER # Should be back to default

    def test_invalid_mode_type_raises_error(self):
        """
        Test that setting an invalid type for the mode raises a TypeError.
        """
        with pytest.raises(TypeError, match="Trading mode must be a TradingModeEnum member"):
            self.manager.trading_mode = "not_a_valid_mode"
