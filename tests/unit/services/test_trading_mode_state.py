"""
Tests for TradingModeStateManager and related functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock PyQt5 modules before importing
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from ultibot_ui.services.trading_mode_state import (
    TradingModeStateManager, 
    TradingModeEnum,
    get_trading_mode_manager,
    reset_trading_mode_manager
)

class TestTradingModeEnum:
    """Test cases for TradingModeEnum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert TradingModeEnum.PAPER.value == "paper"
        assert TradingModeEnum.REAL.value == "real"
    
    def test_display_names(self):
        """Test display names are correct."""
        assert TradingModeEnum.PAPER.display_name == "Paper Trading"
        assert TradingModeEnum.REAL.display_name == "Real Trading"
    
    def test_colors(self):
        """Test that colors are defined."""
        assert TradingModeEnum.PAPER.color == "#4CAF50"  # Green
        assert TradingModeEnum.REAL.color == "#FF9800"   # Orange
    
    def test_icons(self):
        """Test that icons are defined."""
        assert TradingModeEnum.PAPER.icon == "📊"
        assert TradingModeEnum.REAL.icon == "💰"

class TestTradingModeStateManager:
    """Test cases for TradingModeStateManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset the global manager before each test
        reset_trading_mode_manager()
        
        # Create a fresh manager for testing
        self.manager = TradingModeStateManager()
        
        # Mock for signal testing - mock the emit method directly
        self.signal_mock = Mock()
        self.manager.trading_mode_changed = Mock()
        self.manager.trading_mode_changed.emit = self.signal_mock
    
    def test_initial_mode(self):
        """Test that initial mode is paper."""
        assert self.manager.current_mode == "paper"
        assert self.manager.is_paper_mode() is True
        assert self.manager.is_real_mode() is False
    
    def test_initial_mode_custom(self):
        """Test that custom initial mode works."""
        manager = TradingModeStateManager(initial_mode="real")
        assert manager.current_mode == "real"
        assert manager.is_real_mode() is True
        assert manager.is_paper_mode() is False
    
    def test_set_trading_mode_valid(self):
        """Test setting valid trading modes."""
        # Change to real
        self.manager.set_trading_mode("real")
        assert self.manager.current_mode == "real"
        self.signal_mock.assert_called_once_with("real")
        
        # Change back to paper
        self.signal_mock.reset_mock()
        self.manager.set_trading_mode("paper")
        assert self.manager.current_mode == "paper"
        self.signal_mock.assert_called_once_with("paper")
    
    def test_set_trading_mode_invalid(self):
        """Test setting invalid trading mode raises error."""
        with pytest.raises(ValueError, match="Invalid trading mode"):
            self.manager.set_trading_mode("invalid")  # type: ignore
    
    def test_set_same_mode_no_signal(self):
        """Test that setting same mode doesn't emit signal."""
        # Initially paper, set to paper again
        self.manager.set_trading_mode("paper")
        self.signal_mock.assert_not_called()
    
    def test_toggle_mode(self):
        """Test toggle functionality."""
        # Start with paper, toggle to real
        result = self.manager.toggle_mode()
        assert result == "real"
        assert self.manager.current_mode == "real"
        self.signal_mock.assert_called_once_with("real")
        
        # Toggle back to paper
        self.signal_mock.reset_mock()
        result = self.manager.toggle_mode()
        assert result == "paper"
        assert self.manager.current_mode == "paper"
        self.signal_mock.assert_called_once_with("paper")
    
    def test_current_mode_enum(self):
        """Test current_mode_enum property."""
        assert self.manager.current_mode_enum == TradingModeEnum.PAPER
        
        self.manager.set_trading_mode("real")
        assert self.manager.current_mode_enum == TradingModeEnum.REAL
    
    def test_get_available_modes(self):
        """Test getting available modes."""
        modes = self.manager.get_available_modes()
        assert len(modes) == 2
        assert TradingModeEnum.PAPER in modes
        assert TradingModeEnum.REAL in modes
    
    def test_get_mode_display_info(self):
        """Test getting display info for current mode."""
        info = self.manager.get_mode_display_info()
        
        expected_keys = ['mode', 'display_name', 'color', 'icon']
        for key in expected_keys:
            assert key in info
        
        assert info['mode'] == 'paper'
        assert info['display_name'] == 'Paper Trading'
        assert info['color'] == '#4CAF50'
        assert info['icon'] == '📊'
        
        # Test for real mode
        self.manager.set_trading_mode("real")
        info = self.manager.get_mode_display_info()
        assert info['mode'] == 'real'
        assert info['display_name'] == 'Real Trading'
    
    def test_get_all_modes_info(self):
        """Test getting info for all modes."""
        all_info = self.manager.get_all_modes_info()
        assert len(all_info) == 2
        
        # Check that both modes are present
        modes = [info['mode'] for info in all_info]
        assert 'paper' in modes
        assert 'real' in modes
    
    def test_subscribe_unsubscribe(self):
        """Test callback subscription mechanism."""
        callback_mock = Mock()
        
        # Subscribe
        self.manager.subscribe(callback_mock)
        
        # Change mode should call callback
        self.manager.set_trading_mode("real")
        callback_mock.assert_called_once_with("real")
        
        # Unsubscribe
        self.manager.unsubscribe(callback_mock)
        callback_mock.reset_mock()
        
        # Change mode should not call callback anymore
        self.manager.set_trading_mode("paper")
        callback_mock.assert_not_called()
    
    def test_subscribe_error_handling(self):
        """Test that subscription errors are handled gracefully."""
        def failing_callback(mode):
            raise Exception("Test error")
        
        # Subscribe failing callback
        self.manager.subscribe(failing_callback)
        
        # This should not raise an exception
        self.manager.set_trading_mode("real")
        
        # Manager should still work normally
        assert self.manager.current_mode == "real"
        
        # Clean up the failing subscriber
        self.manager.unsubscribe(failing_callback)
    
    def test_save_load_config(self):
        """Test configuration save and load."""
        config = {}
        
        # Set to real and save
        self.manager.set_trading_mode("real")
        config = self.manager.save_to_config(config)
        
        assert config['current_trading_mode'] == 'real'
        
        # Create new manager and load config
        new_manager = TradingModeStateManager()
        assert new_manager.current_mode == 'paper'  # Default
        
        new_manager.load_from_config(config)
        assert new_manager.current_mode == 'real'  # Loaded from config
    
    def test_load_config_invalid_mode(self):
        """Test loading config with invalid mode."""
        config = {'current_trading_mode': 'invalid'}
        
        # Should not change mode and not raise error
        original_mode = self.manager.current_mode
        self.manager.load_from_config(config)
        assert self.manager.current_mode == original_mode

class TestGlobalStateManager:
    """Test the global state manager singleton."""
    
    def setup_method(self):
        """Reset global state before each test."""
        reset_trading_mode_manager()
    
    def test_singleton_behavior(self):
        """Test that get_trading_mode_manager returns same instance."""
        manager1 = get_trading_mode_manager()
        manager2 = get_trading_mode_manager()
        
        assert manager1 is manager2
    
    def test_reset_functionality(self):
        """Test that reset creates new instance."""
        manager1 = get_trading_mode_manager()
        manager1.set_trading_mode("real")
        
        reset_trading_mode_manager()
        
        manager2 = get_trading_mode_manager()
        assert manager1 is not manager2
        assert manager2.current_mode == "paper"  # New instance has default
    
    def test_state_persistence_across_calls(self):
        """Test that state persists across multiple get calls."""
        manager = get_trading_mode_manager()
        manager.set_trading_mode("real")
        
        # Get again and verify state persisted
        same_manager = get_trading_mode_manager()
        assert same_manager.current_mode == "real"
