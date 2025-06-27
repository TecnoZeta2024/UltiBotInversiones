import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, ANY
from uuid import uuid4
from decimal import Decimal

from src.ultibot_backend.main import app
from src.ultibot_backend.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.ultibot_backend.core.domain_models.trade_models import TradeOrderDetails, OrderCategory, OrderStatus, OrderType
from src.ultibot_backend.app_config import get_app_settings

# Mock UnifiedOrderExecutionService fixture
@pytest.fixture
def mock_unified_execution_service():
    return AsyncMock(spec=UnifiedOrderExecutionService)

# Fixture for TestClient with mocked UnifiedOrderExecutionService
@pytest.fixture
def client(mock_unified_execution_service):
    app.dependency_overrides[UnifiedOrderExecutionService] = lambda: mock_unified_execution_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}  # Clean up

# Sample data fixtures
@pytest.fixture
def sample_market_order_request_data():
    return {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "quantity": 0.001,
        "trading_mode": "paper"
    }

@pytest.fixture
def sample_trade_order_details():
    return TradeOrderDetails(
        orderId_internal=uuid4(),
        orderId_exchange="12345",
        clientOrderId_exchange=None,
        orderCategory=OrderCategory.ENTRY,
        type=OrderType.MARKET.value,
        status=OrderStatus.FILLED.value,
        requestedPrice=None,
        requestedQuantity=Decimal("0.001"),
        executedQuantity=Decimal("0.001"),
        executedPrice=Decimal("50000.0"),
        cumulativeQuoteQty=None,
        commissions=None,
        commission=None,
        commissionAsset=None,
        submittedAt=None,
        fillTimestamp=None,
        rawResponse=None,
        ocoOrderListId=None,
        price=None,
        stopPrice=None,
        timeInForce=None,
    )

# =================================================================
# Tests for trading endpoints
# =================================================================
class TestTradingEndpoints:

    @pytest.mark.asyncio
    async def test_execute_market_order_success(self, client, mock_unified_execution_service, sample_market_order_request_data, sample_trade_order_details):
        # Arrange
        mock_unified_execution_service.execute_market_order.return_value = sample_trade_order_details
        fixed_user_id = get_app_settings().FIXED_USER_ID
        
        # Act
        response = client.post(
            "/api/v1/market-order",
            json=sample_market_order_request_data
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["orderId_exchange"] == sample_trade_order_details.orderId_exchange
        assert response_data["status"] == sample_trade_order_details.status
        
        mock_unified_execution_service.execute_market_order.assert_called_once_with(
            user_id=fixed_user_id,
            symbol=sample_market_order_request_data["symbol"],
            side=sample_market_order_request_data["side"],
            quantity=Decimal(str(sample_market_order_request_data["quantity"])),
            trading_mode=sample_market_order_request_data["trading_mode"],
            api_key=None,
            api_secret=None
        )

    @pytest.mark.asyncio
    async def test_execute_market_order_invalid_data(self, client, mock_unified_execution_service):
        # Arrange
        invalid_payload = {
            "symbol": "BTCUSDT",
            "side": "INVALID_SIDE", # Invalid side
            "quantity": 0.001,
            "trading_mode": "paper"
        }
        
        # Act
        response = client.post(
            "/api/v1/market-order",
            json=invalid_payload
        )
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity
        mock_unified_execution_service.execute_market_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_market_order_service_error(self, client, mock_unified_execution_service, sample_market_order_request_data):
        # Arrange
        mock_unified_execution_service.execute_market_order.side_effect = Exception("Internal service error")
        
        # Act
        response = client.post(
            "/api/v1/market-order",
            json=sample_market_order_request_data
        )
        
        # Assert
        assert response.status_code == 500
        assert "Internal service error" in response.json()["detail"]
        mock_unified_execution_service.execute_market_order.assert_called_once()
