import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Tuple
from fastapi import FastAPI
from datetime import datetime

from src.core.domain_models.trade_models import TradeOrderDetails, OrderCategory, OrderStatus, OrderType, TradeSide
from src.core.domain_models.opportunity_models import OpportunityStatus, Opportunity, InitialSignal, SourceType, Direction
from src.core.domain_models.user_configuration_models import UserConfiguration, RealTradingSettings, AIStrategyConfiguration, ConfidenceThresholds, RiskProfile, Theme, RiskProfileSettings
from src.dependencies import DependencyContainer

# Sample data fixtures
@pytest.fixture
def sample_market_order_request_data():
    """Provides a sample market order request payload."""
    return {
        "symbol": "BTCUSDT",
        "side": TradeSide.BUY.value,
        "quantity": 0.001,
        "trading_mode": "paper"
    }

@pytest.fixture
def sample_trade_order_details():
    """Provides a sample TradeOrderDetails object for mocking service responses."""
    return TradeOrderDetails(
        orderId_internal=uuid4(),
        orderId_exchange="12345",
        clientOrderId_exchange="my-test-order-1",
        orderCategory=OrderCategory.ENTRY,
        type=OrderType.MARKET.value,
        status=OrderStatus.FILLED.value,
        requestedPrice=None,
        requestedQuantity=Decimal("0.001"),
        executedQuantity=Decimal("0.001"),
        executedPrice=Decimal("50000.0"),
        cumulativeQuoteQty=Decimal("50.0"),
        commissions=None,
        commission=None,
        commissionAsset=None,
        timestamp=datetime.now(),
        submittedAt=datetime.now(),
        fillTimestamp=datetime.now(),
        rawResponse={"msg": "test"},
        ocoOrderListId=None,
        price=None,
        stopPrice=None,
        timeInForce=None,
    )

@pytest.fixture
def mock_opportunity_pending_confirmation(user_id):
    """Provides a mock opportunity in PENDING_USER_CONFIRMATION_REAL status."""
    return Opportunity(
        id=str(uuid4()),
        user_id=str(user_id),
        strategy_id=uuid4(),
        exchange='BINANCE',
        symbol="BTCUSDT",
        detected_at=datetime.now(),
        source_type=SourceType.INTERNAL_INDICATOR_ALGO,
        source_name="test_source",
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=Decimal("50000.0"),
            stop_loss_target=Decimal("49000.0"),
            take_profit_target=[Decimal("51000.0")],
            timeframe="1h",
            confidence_source=0.8,
            reasoning_source_text="Test signal",
            reasoning_source_structured=None
        ),
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        source_data=None,
        system_calculated_priority_score=None,
        last_priority_calculation_at=None,
        status_reason_code=None,
        status_reason_text=None,
        ai_analysis=None,
        investigation_details=None,
        user_feedback=None,
        linked_trade_ids=[],
        expires_at=None,
        expiration_logic=None,
        post_trade_feedback=None,
        post_facto_simulation_results=None,
    )

@pytest.fixture
def mock_user_configuration_real_trading_active(user_id):
    """Provides a mock user configuration with real trading active."""
    return UserConfiguration.model_construct(
        id=str(uuid4()),
        user_id=str(user_id),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=True,
            real_trades_executed_count=0,
            max_concurrent_operations=5,
            daily_loss_limit_absolute=Decimal("500.0"),
            daily_profit_target_absolute=Decimal("1000.0"),
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=datetime.now(),
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None,
        ),
        # Add other fields with default values to satisfy the model
        telegram_chat_id=None,
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=Decimal("10000.0"),
        paper_trading_active=False,
        paper_trading_assets=[],
        watchlists=[],
        favorite_pairs=["BTCUSDT", "ETHUSDT"],
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=RiskProfileSettings(),
        ai_strategy_configurations=[],
        ai_analysis_confidence_thresholds=ConfidenceThresholds(),
        mcp_server_preferences=None,
        selected_theme=Theme.DARK,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

# =================================================================
# Tests for trading endpoints
# =================================================================
class TestTradingEndpoints:

    async def test_confirm_real_opportunity_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        mock_opportunity_pending_confirmation: Opportunity,
        mock_user_configuration_real_trading_active: UserConfiguration,
        user_id: UUID,
        sample_trade_order_details: TradeOrderDetails
    ):
        # Arrange
        http_client, _ = client

        # Configure the mocked services within the container
        mock_dependency_container.persistence_service.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        mock_dependency_container.config_service.get_user_configuration.return_value = mock_user_configuration_real_trading_active
        mock_dependency_container.trading_engine_service.execute_trade_from_confirmed_opportunity.return_value = sample_trade_order_details

        request_payload = {
            "opportunity_id": str(mock_opportunity_pending_confirmation.id),
            "user_id": str(user_id)
        }

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["message"] == "Real trade execution initiated successfully."
        assert response_data["trade_details"]["orderId_exchange"] == sample_trade_order_details.orderId_exchange
        
        # Verify service calls on the mocked container's attributes
        mock_dependency_container.persistence_service.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        mock_dependency_container.config_service.get_user_configuration.assert_called_once_with(str(user_id))
        mock_dependency_container.trading_engine_service.execute_trade_from_confirmed_opportunity.assert_called_once_with(mock_opportunity_pending_confirmation)

    async def test_confirm_real_opportunity_id_mismatch(
        self, client: Tuple[AsyncClient, FastAPI], user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        request_payload = {"opportunity_id": str(uuid4()), "user_id": str(user_id)}
        path_opportunity_id = uuid4()

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{path_opportunity_id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Opportunity ID in path and request body do not match."

    async def test_confirm_real_opportunity_not_found(
        self, client: Tuple[AsyncClient, FastAPI], mock_dependency_container: AsyncMock, user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_dependency_container.persistence_service.get_opportunity_by_id.return_value = None
        
        opportunity_id = uuid4()
        request_payload = {"opportunity_id": str(opportunity_id), "user_id": str(user_id)}

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{opportunity_id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Opportunity with ID {opportunity_id} not found."
        mock_dependency_container.persistence_service.get_opportunity_by_id.assert_called_once_with(opportunity_id)

    async def test_confirm_real_opportunity_wrong_status(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        mock_opportunity_pending_confirmation: Opportunity,
        user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_opportunity_pending_confirmation.status = OpportunityStatus.NEW
        mock_dependency_container.persistence_service.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        
        request_payload = {"opportunity_id": str(mock_opportunity_pending_confirmation.id), "user_id": str(user_id)}

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 400
        # The API should return the string value of the enum.
        # We assert against the known value 'new' directly to avoid issues with the mock object's state.
        expected_status_value = OpportunityStatus.NEW.value
        assert response.json()["detail"] == f"Opportunity {mock_opportunity_pending_confirmation.id} is not in 'pending_user_confirmation_real' status. Current status: {expected_status_value}"
        mock_dependency_container.persistence_service.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))

    async def test_confirm_real_opportunity_no_user_config(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        mock_opportunity_pending_confirmation: Opportunity,
        user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_dependency_container.persistence_service.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        mock_dependency_container.config_service.get_user_configuration.return_value = None
        
        request_payload = {"opportunity_id": str(mock_opportunity_pending_confirmation.id), "user_id": str(user_id)}

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "User configuration or real trading settings not found."
        mock_dependency_container.persistence_service.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        mock_dependency_container.config_service.get_user_configuration.assert_called_once_with(str(user_id))

    async def test_confirm_real_opportunity_real_trading_not_active(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        mock_opportunity_pending_confirmation: Opportunity,
        mock_user_configuration_real_trading_active: UserConfiguration,
        user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_user_configuration_real_trading_active.real_trading_settings.real_trading_mode_active = False
        mock_dependency_container.persistence_service.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        mock_dependency_container.config_service.get_user_configuration.return_value = mock_user_configuration_real_trading_active
        
        request_payload = {"opportunity_id": str(mock_opportunity_pending_confirmation.id), "user_id": str(user_id)}

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 403
        assert response.json()["detail"] == "Real trading mode is not active for this user."
        mock_dependency_container.persistence_service.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        mock_dependency_container.config_service.get_user_configuration.assert_called_once_with(str(user_id))

    async def test_execute_market_order_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        sample_market_order_request_data: dict,
        sample_trade_order_details: TradeOrderDetails,
        user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_execution_service = mock_dependency_container.unified_order_execution_service
        mock_execution_service.validate_trading_mode.return_value = True  # Mock sync method
        mock_execution_service.execute_market_order.return_value = sample_trade_order_details
        
        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=sample_market_order_request_data,
            headers={"X-User-ID": str(user_id)}
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert isinstance(response_data["orderId_exchange"], str)
        assert response_data["status"] == sample_trade_order_details.status
        mock_execution_service.validate_trading_mode.assert_called_once_with(sample_market_order_request_data["trading_mode"])
        mock_execution_service.execute_market_order.assert_called_once_with(
            user_id=user_id,
            symbol=sample_market_order_request_data["symbol"],
            side=TradeSide.BUY,
            quantity=Decimal(str(sample_market_order_request_data["quantity"])),
            trading_mode=sample_market_order_request_data["trading_mode"],
            api_key=None,
            api_secret=None,
            oco_order_list_id=None
        )

    async def test_execute_market_order_invalid_data(
        self, client: Tuple[AsyncClient, FastAPI], user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        invalid_payload = {"symbol": "BTC/USDT", "side": "INVALID_SIDE", "quantity": 0.001, "trading_mode": "paper"}

        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=invalid_payload,
            headers={"X-User-ID": str(user_id)}
        )

        # Assert
        assert response.status_code == 422

    async def test_execute_market_order_service_error(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_dependency_container: AsyncMock,
        sample_market_order_request_data: dict,
        user_id: UUID
    ):
        # Arrange
        http_client, _ = client
        mock_execution_service = mock_dependency_container.unified_order_execution_service
        mock_execution_service.validate_trading_mode.return_value = True  # Mock sync method
        mock_execution_service.execute_market_order.side_effect = Exception("Internal service error")
        
        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=sample_market_order_request_data,
            headers={"X-User-ID": str(user_id)}
        )

        # Assert
        assert response.status_code == 500
        assert "Internal service error" in response.json()["detail"]
