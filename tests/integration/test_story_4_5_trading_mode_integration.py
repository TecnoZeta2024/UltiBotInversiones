"""
Integration tests for Story 4.5: Trading Mode Differentiation
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os
from uuid import UUID, uuid4

# Mock PyQt5 modules before importing
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.ultibot_ui.services.api_client import UltiBotAPIClient
from src.ultibot_ui.services.trading_mode_state import get_trading_mode_manager, reset_trading_mode_manager

class TestTradingModeAPIIntegration:
    """Integration tests for trading mode aware API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_client = UltiBotAPIClient(base_url="http://test-backend:8000")
        self.user_id = uuid4()
        reset_trading_mode_manager()
    
    @pytest.mark.asyncio
    async def test_portfolio_snapshot_with_trading_mode(self):
        """Test portfolio snapshot API with trading mode parameter."""
        # Mock the HTTP request
        mock_response = {
            "paper_trading": {
                "available_balance_usdt": 10000.0,
                "total_assets_value_usd": 5000.0,
                "total_portfolio_value_usd": 15000.0,
                "assets": [],
                "error_message": None
            },
            "real_trading": {
                "available_balance_usdt": 1000.0,
                "total_assets_value_usd": 500.0,
                "total_portfolio_value_usd": 1500.0,
                "assets": [],
                "error_message": None
            }
        }
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            # Test paper mode
            result = await self.api_client.get_portfolio_snapshot(self.user_id, "paper")
            
            mock_request.assert_called_once_with(
                "GET", 
                f"/api/v1/portfolio/snapshot/{self.user_id}",
                params={"trading_mode": "paper"}
            )
            assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_market_order_execution_paper_mode(self):
        """Test market order execution in paper mode."""
        order_data = {
            "user_id": str(self.user_id),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "trading_mode": "paper"
        }
        
        mock_response = {
            "order_id": "paper_order_123",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "price": 45000.0,
            "status": "FILLED",
            "trading_mode": "paper",
            "timestamp": "2025-01-06T10:30:00Z",
            "total_value": 45.0
        }
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await self.api_client.execute_market_order(order_data)
            
            mock_request.assert_called_once_with(
                "POST",
                "/api/v1/trading/market-order",
                json=order_data
            )
            assert result == mock_response
            assert result["trading_mode"] == "paper"
    
    @pytest.mark.asyncio
    async def test_market_order_execution_real_mode(self):
        """Test market order execution in real mode with credentials."""
        order_data = {
            "user_id": str(self.user_id),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "trading_mode": "real",
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        }
        
        mock_response = {
            "order_id": "real_order_456",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "price": 45000.0,
            "status": "FILLED",
            "trading_mode": "real",
            "timestamp": "2025-01-06T10:30:00Z",
            "total_value": 45.0
        }
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await self.api_client.execute_market_order(order_data)
            
            mock_request.assert_called_once_with(
                "POST",
                "/api/v1/trading/market-order",
                json=order_data
            )
            assert result == mock_response
            assert result["trading_mode"] == "real"
    
    @pytest.mark.asyncio
    async def test_market_order_real_mode_missing_credentials(self):
        """Test that real mode requires credentials."""
        order_data = {
            "user_id": str(self.user_id),
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "trading_mode": "real"
            # Missing api_key and api_secret
        }
        
        with pytest.raises(ValueError, match="API key y secret son requeridos"):
            await self.api_client.execute_market_order(order_data)
    
    @pytest.mark.asyncio
    async def test_get_open_trades_by_mode(self):
        """Test getting open trades filtered by trading mode."""
        mock_paper_trades = [
            {
                "trade_id": "paper_trade_1",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.001,
                "trading_mode": "paper"
            }
        ]
        
        mock_real_trades = [
            {
                "trade_id": "real_trade_1",
                "symbol": "ETHUSDT",
                "side": "SELL",
                "quantity": 0.1,
                "trading_mode": "real"
            }
        ]
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            # Test paper mode filter
            mock_request.return_value = mock_paper_trades
            result = await self.api_client.get_open_trades_by_mode(self.user_id, "paper")
            
            mock_request.assert_called_with(
                "GET",
                f"/api/v1/trades/trades/{self.user_id}/open",
                params={"trading_mode": "paper"}
            )
            assert result == mock_paper_trades
            
            # Test real mode filter
            mock_request.return_value = mock_real_trades
            result = await self.api_client.get_open_trades_by_mode(self.user_id, "real")
            
            assert result == mock_real_trades

class TestTradingModeStateIntegration:
    """Integration tests for trading mode state management with UI components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_trading_mode_manager()
        self.mode_manager = get_trading_mode_manager()
        self.signal_received = None
        self.signal_count = 0
    
    def signal_handler(self, mode: str):
        """Handler for mode change signals."""
        self.signal_received = mode
        self.signal_count += 1
    
    def test_state_propagation(self):
        """Test that state changes propagate correctly."""
        # Mock the signal mechanism
        self.mode_manager.trading_mode_changed = Mock()
        self.mode_manager.trading_mode_changed.emit = Mock(side_effect=self.signal_handler)
        
        # Change mode and verify signal
        self.mode_manager.set_trading_mode("real")
        
        assert self.signal_received == "real"
        assert self.signal_count == 1
        assert self.mode_manager.current_mode == "real"
    
    def test_multiple_components_sync(self):
        """Test that multiple components stay in sync."""
        # Simulate multiple components subscribing
        component1_mode = None
        component2_mode = None
        
        def component1_handler(mode):
            nonlocal component1_mode
            component1_mode = mode
        
        def component2_handler(mode):
            nonlocal component2_mode
            component2_mode = mode
        
        # Mock signal mechanism for multiple handlers
        def mock_emit(mode):
            component1_handler(mode)
            component2_handler(mode)
        
        self.mode_manager.trading_mode_changed = Mock()
        self.mode_manager.trading_mode_changed.emit = mock_emit
        
        # Change mode
        self.mode_manager.set_trading_mode("real")
        
        # Both components should receive the update
        assert component1_mode == "real"
        assert component2_mode == "real"
        
        # Change back to paper
        self.mode_manager.set_trading_mode("paper")
        
        assert component1_mode == "paper"
        assert component2_mode == "paper"

class TestEndToEndTradingModeFlow:
    """End-to-end tests for the complete trading mode workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_trading_mode_manager()
        self.mode_manager = get_trading_mode_manager()
        self.api_client = UltiBotAPIClient(base_url="http://test-backend:8000")
        self.user_id = uuid4()
    
    @pytest.mark.asyncio
    async def test_complete_paper_trading_workflow(self):
        """Test complete workflow: set paper mode -> view portfolio -> execute order."""
        # 1. Set trading mode to paper
        self.mode_manager.set_trading_mode("paper")
        assert self.mode_manager.current_mode == "paper"
        
        # 2. Mock portfolio data request
        mock_portfolio = {
            "paper_trading": {
                "available_balance_usdt": 10000.0,
                "total_portfolio_value_usd": 10000.0,
                "assets": []
            }
        }
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_portfolio
            
            # 3. Get portfolio for current mode
            portfolio = await self.api_client.get_portfolio_snapshot(
                self.user_id, 
                self.mode_manager.current_mode
            )
            
            assert portfolio == mock_portfolio
            
            # 4. Execute order in paper mode
            order_data = {
                "user_id": str(self.user_id),
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.001,
                "trading_mode": self.mode_manager.current_mode
            }
            
            mock_order_result = {
                "order_id": "paper_order_123",
                "trading_mode": "paper",
                "status": "FILLED"
            }
            
            mock_request.return_value = mock_order_result
            order_result = await self.api_client.execute_market_order(order_data)
            
            assert order_result["trading_mode"] == "paper"
            assert order_result["status"] == "FILLED"
    
    @pytest.mark.asyncio
    async def test_complete_real_trading_workflow(self):
        """Test complete workflow: set real mode -> view portfolio -> execute order with credentials."""
        # 1. Set trading mode to real
        self.mode_manager.set_trading_mode("real")
        assert self.mode_manager.current_mode == "real"
        
        # 2. Mock portfolio data request for real mode
        mock_portfolio = {
            "real_trading": {
                "available_balance_usdt": 1000.0,
                "total_portfolio_value_usd": 1500.0,
                "assets": []
            }
        }
        
        with patch.object(self.api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_portfolio
            
            # 3. Get portfolio for current mode
            portfolio = await self.api_client.get_portfolio_snapshot(
                self.user_id, 
                self.mode_manager.current_mode
            )
            
            assert portfolio == mock_portfolio
            
            # 4. Execute order in real mode with credentials
            order_data = {
                "user_id": str(self.user_id),
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.001,
                "trading_mode": self.mode_manager.current_mode,
                "api_key": "real_api_key",
                "api_secret": "real_api_secret"
            }
            
            mock_order_result = {
                "order_id": "real_order_456",
                "trading_mode": "real",
                "status": "FILLED"
            }
            
            mock_request.return_value = mock_order_result
            order_result = await self.api_client.execute_market_order(order_data)
            
            assert order_result["trading_mode"] == "real"
            assert order_result["status"] == "FILLED"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
