import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, ANY
from uuid import UUID, uuid4 # Import UUID
from decimal import Decimal
from typing import Tuple
from fastapi import FastAPI
from datetime import datetime

from src.services.unified_order_execution_service import UnifiedOrderExecutionService
from src.services.trading_engine_service import TradingEngine
from src.services.config_service import ConfigurationService
from src.adapters.persistence_service import SupabasePersistenceService
from src.core.domain_models.trade_models import TradeOrderDetails, OrderCategory, OrderStatus, OrderType, TradeSide
from src.core.domain_models.opportunity_models import OpportunityStatus, Opportunity, InitialSignal, SourceType, Direction, AIAnalysis, SuggestedAction, RecommendedTradeParams
from src.core.domain_models.user_configuration_models import UserConfiguration, RealTradingSettings, AIStrategyConfiguration, ConfidenceThresholds, RiskProfile, Theme, RiskProfileSettings
from src.dependencies import get_unified_order_execution_service, get_trading_engine_service, get_config_service, get_persistence_service
from src.app_config import get_app_settings

# Sample data fixtures
@pytest.fixture
def sample_market_order_request_data():
    """Provides a sample market order request payload."""
    return {
        "symbol": "BTCUSDT", # Changed to match common symbol format
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

# =================================================================
# Tests for trading endpoints
# =================================================================
class TestTradingEndpoints:

    @pytest.fixture
    def mock_opportunity_pending_confirmation(self, user_id):
        """Provides a mock opportunity in PENDING_USER_CONFIRMATION_REAL status."""
        return Opportunity(
            id=str(uuid4()), # Convert UUID to str
            user_id=str(user_id),
            strategy_id=UUID(str(uuid4())), # Convert str to UUID
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
            linked_trade_ids=None,
            expires_at=None,
            expiration_logic=None,
            post_trade_feedback=None,
            post_facto_simulation_results=None,
        )

    @pytest.fixture
    def mock_user_configuration_real_trading_active(self, user_id):
        """Provides a mock user configuration with real trading active."""
        return UserConfiguration.model_construct(
            id=str(uuid4()), # Convert UUID to str
            user_id=str(user_id),
            telegram_chat_id=None,
            notification_preferences=None,
            enable_telegram_notifications=True,
            default_paper_trading_capital=Decimal("10000.0"),
            paper_trading_active=False, # Important for real trading tests
            paper_trading_assets=[],
            watchlists=[],
            favorite_pairs=["BTCUSDT", "ETHUSDT"],
            risk_profile=RiskProfile.MODERATE,
            risk_profile_settings=RiskProfileSettings(
                daily_capital_risk_percentage=0.02,
                per_trade_capital_risk_percentage=0.01,
                max_drawdown_percentage=0.15,
            ),
            real_trading_settings=RealTradingSettings(
                real_trading_mode_active=True, # Real trading active
                real_trades_executed_count=0,
                max_concurrent_operations=5,
                daily_loss_limit_absolute=Decimal("500.0"),
                daily_profit_target_absolute=Decimal("1000.0"),
                daily_capital_risked_usd=Decimal("0.0"),
                last_daily_reset=datetime.now(),
                asset_specific_stop_loss=None,
                auto_pause_trading_conditions=None,
            ),
            ai_strategy_configurations=[
                AIStrategyConfiguration(
                    id="ai_profile_1",
                    name="Conservative Day Trading AI",
                    is_active_paper_mode=True,
                    is_active_real_mode=False,
                    total_pnl=Decimal("0.0"),
                    number_of_trades=0,
                    applies_to_strategies=None,
                    applies_to_pairs=None,
                    gemini_prompt_template="Analyze this {symbol} opportunity for day trading. Market data: {market_data}. Strategy: {strategy_params}",
                    tools_available_to_gemini=["price_history", "volume_analysis", "technical_indicators"],
                    output_parser_config=None,
                    indicator_weights=None,
                    confidence_thresholds=ConfidenceThresholds(
                        paper_trading=0.65,
                        real_trading=0.80,
                    ),
                    max_context_window_tokens=8000,
                )
            ],
            ai_analysis_confidence_thresholds=ConfidenceThresholds(
                paper_trading=0.60,
                real_trading=0.75,
            ),
            mcp_server_preferences=None,
            selected_theme=Theme.DARK,
            dashboard_layout_profiles=None,
            active_dashboard_layout_profile_id=None,
            dashboard_layout_config=None,
            cloud_sync_preferences=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        trading_engine_fixture: AsyncMock,
        configuration_service_fixture: AsyncMock,
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        mock_user_configuration_real_trading_active,
        user_id,
        sample_trade_order_details
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_trading_engine_service] = lambda: trading_engine_fixture
        app.dependency_overrides[get_config_service] = lambda: configuration_service_fixture
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture

        get_app_settings().FIXED_USER_ID = user_id # Ensure fixed user ID matches test user ID

        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        configuration_service_fixture.get_user_configuration.return_value = mock_user_configuration_real_trading_active
        trading_engine_fixture.execute_trade_from_confirmed_opportunity.return_value = sample_trade_order_details

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
        assert response.json()["message"] == "Real trade execution initiated successfully."
        assert response.json()["trade_details"]["orderId_exchange"] == sample_trade_order_details.orderId_exchange

        persistence_service_fixture.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        configuration_service_fixture.get_user_configuration.assert_called_once_with(str(user_id))
        trading_engine_fixture.execute_trade_from_confirmed_opportunity.assert_called_once_with(mock_opportunity_pending_confirmation)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_id_mismatch(
        self,
        client: Tuple[AsyncClient, FastAPI],
        user_id
    ):
        # Arrange
        http_client, app = client
        get_app_settings().FIXED_USER_ID = user_id

        request_payload = {
            "opportunity_id": str(uuid4()), # Mismatch
            "user_id": str(user_id)
        }
        mismatched_opportunity_id = uuid4()

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mismatched_opportunity_id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Opportunity ID in path and request body do not match."
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_user_id_mismatch(
        self,
        client: Tuple[AsyncClient, FastAPI],
        mock_opportunity_pending_confirmation,
        user_id
    ):
        # Arrange
        http_client, app = client
        get_app_settings().FIXED_USER_ID = user_id

        request_payload = {
            "opportunity_id": str(mock_opportunity_pending_confirmation.id),
            "user_id": str(uuid4()) # Mismatch
        }

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 403
        assert response.json()["detail"] == "User ID in settings does not match user ID in request body."
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_not_found(
        self,
        client: Tuple[AsyncClient, FastAPI],
        persistence_service_fixture: AsyncMock,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        persistence_service_fixture.get_opportunity_by_id.return_value = None # Not found

        opportunity_id = uuid4()
        request_payload = {
            "opportunity_id": str(opportunity_id),
            "user_id": str(user_id)
        }

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{opportunity_id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == f"Opportunity with ID {opportunity_id} not found."
        persistence_service_fixture.get_opportunity_by_id.assert_called_once_with(opportunity_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_unauthorized_user(
        self,
        client: Tuple[AsyncClient, FastAPI],
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = uuid4() # Different user ID in settings

        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation

        request_payload = {
            "opportunity_id": str(mock_opportunity_pending_confirmation.id),
            "user_id": str(get_app_settings().FIXED_USER_ID)
        }

        # Act
        response = await http_client.post(
            f"/api/v1/trading/real/confirm-opportunity/{mock_opportunity_pending_confirmation.id}",
            json=request_payload
        )

        # Assert
        assert response.status_code == 403
        assert response.json()["detail"] == "User not authorized to confirm this opportunity."
        persistence_service_fixture.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_wrong_status(
        self,
        client: Tuple[AsyncClient, FastAPI],
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        mock_opportunity_pending_confirmation.status = OpportunityStatus.NEW # Wrong status
        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation

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
        assert response.status_code == 400
        assert response.json()["detail"] == f"Opportunity {mock_opportunity_pending_confirmation.id} is not in 'pending_user_confirmation_real' status. Current status: {mock_opportunity_pending_confirmation.status}"
        persistence_service_fixture.get_opportunity_by_id.assert_called_once_with(UUID(mock_opportunity_pending_confirmation.id))
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_no_user_config(
        self,
        client: Tuple[AsyncClient, FastAPI],
        trading_engine_fixture: AsyncMock,
        configuration_service_fixture: AsyncMock,
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_trading_engine_service] = lambda: trading_engine_fixture
        app.dependency_overrides[get_config_service] = lambda: configuration_service_fixture
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        configuration_service_fixture.get_user_configuration.return_value = None # No user config

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
        assert response.status_code == 400
        assert response.json()["detail"] == "User configuration or real trading settings not found."
        configuration_service_fixture.get_user_configuration.assert_called_once_with(str(user_id))
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_real_trading_not_active(
        self,
        client: Tuple[AsyncClient, FastAPI],
        trading_engine_fixture: AsyncMock,
        configuration_service_fixture: AsyncMock,
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        mock_user_configuration_real_trading_active,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_trading_engine_service] = lambda: trading_engine_fixture
        app.dependency_overrides[get_config_service] = lambda: configuration_service_fixture
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        mock_user_configuration_real_trading_active.real_trading_settings.real_trading_mode_active = False # Not active
        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        configuration_service_fixture.get_user_configuration.return_value = mock_user_configuration_real_trading_active

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
        assert response.status_code == 403
        assert response.json()["detail"] == "Real trading mode is not active for this user."
        configuration_service_fixture.get_user_configuration.assert_called_once_with(str(user_id))
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_confirm_real_opportunity_execution_failure(
        self,
        client: Tuple[AsyncClient, FastAPI],
        trading_engine_fixture: AsyncMock,
        configuration_service_fixture: AsyncMock,
        persistence_service_fixture: AsyncMock,
        mock_opportunity_pending_confirmation,
        mock_user_configuration_real_trading_active,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_trading_engine_service] = lambda: trading_engine_fixture
        app.dependency_overrides[get_config_service] = lambda: configuration_service_fixture
        app.dependency_overrides[get_persistence_service] = lambda: persistence_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        persistence_service_fixture.get_opportunity_by_id.return_value = mock_opportunity_pending_confirmation
        configuration_service_fixture.get_user_configuration.return_value = mock_user_configuration_real_trading_active
        trading_engine_fixture.execute_trade_from_confirmed_opportunity.return_value = None # Simulate failure

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
        assert response.status_code == 500
        assert "An unexpected error occurred" in response.json()["detail"]
        trading_engine_fixture.execute_trade_from_confirmed_opportunity.assert_called_once_with(mock_opportunity_pending_confirmation)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_market_order_success(
        self, 
        client: Tuple[AsyncClient, FastAPI], 
        unified_order_execution_service_fixture: AsyncMock, 
        sample_market_order_request_data: dict, 
        sample_trade_order_details: TradeOrderDetails
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        
        unified_order_execution_service_fixture.execute_market_order.return_value = sample_trade_order_details
        fixed_user_id = get_app_settings().FIXED_USER_ID
        
        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=sample_market_order_request_data,
            headers={"X-User-ID": str(fixed_user_id)}
        )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        # The mock returns a dynamic ID, so we assert it's a string and not the hardcoded one
        assert isinstance(response_data["orderId_exchange"], str)
        # The mock's side_effect generates a dynamic ID, so we don't assert against the fixture's hardcoded ID.
        # Instead, we assert that the mock was called with the correct parameters.
        assert response_data["status"] == sample_trade_order_details.status
        
        unified_order_execution_service_fixture.execute_market_order.assert_called_once_with(
            user_id=fixed_user_id,
            symbol=sample_market_order_request_data["symbol"],
            side=TradeSide.BUY,
            quantity=Decimal(str(sample_market_order_request_data["quantity"])),
            trading_mode=sample_market_order_request_data["trading_mode"],
            api_key=None,
            api_secret=None,
            oco_order_list_id=None
        )
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_market_order_invalid_data(
        self, 
        client: Tuple[AsyncClient, FastAPI], 
        unified_order_execution_service_fixture: AsyncMock
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        
        invalid_payload = {
            "symbol": "BTC/USDT",
            "side": "INVALID_SIDE", # Invalid side
            "quantity": 0.001,
            "trading_mode": "paper"
        }
        fixed_user_id = get_app_settings().FIXED_USER_ID
        
        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=invalid_payload,
            headers={"X-User-ID": str(fixed_user_id)}
        )
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity
        unified_order_execution_service_fixture.execute_market_order.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_market_order_service_error(
        self, 
        client: Tuple[AsyncClient, FastAPI], 
        unified_order_execution_service_fixture: AsyncMock, 
        sample_market_order_request_data: dict
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        
        unified_order_execution_service_fixture.execute_market_order.side_effect = Exception("Internal service error")
        fixed_user_id = get_app_settings().FIXED_USER_ID
        
        # Act
        response = await http_client.post(
            "/api/v1/trading/market-order",
            json=sample_market_order_request_data,
            headers={"X-User-ID": str(fixed_user_id)}
        )
        
        # Assert
        assert response.status_code == 500
        assert "Internal service error" in response.json()["detail"]
        unified_order_execution_service_fixture.execute_market_order.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_paper_trading_balances_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        mock_balances = {"USDT": Decimal("10000.0"), "BTC": Decimal("0.5")}
        unified_order_execution_service_fixture.get_virtual_balances.return_value = mock_balances

        # Act
        response = await http_client.get("/api/v1/trading/paper-balances")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user_id"] == str(user_id)
        assert response_data["trading_mode"] == "paper"
        assert response_data["balances"]["USDT"] == float(mock_balances["USDT"]) # JSON serializes Decimal to float
        assert response_data["balances"]["BTC"] == float(mock_balances["BTC"])

        unified_order_execution_service_fixture.get_virtual_balances.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_paper_trading_balances_service_error(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture

        unified_order_execution_service_fixture.get_virtual_balances.side_effect = Exception("Failed to fetch balances")

        # Act
        response = await http_client.get("/api/v1/trading/paper-balances")

        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to retrieve paper trading balances: Failed to fetch balances"
        unified_order_execution_service_fixture.get_virtual_balances.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reset_paper_trading_balances_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        initial_capital = 5000.0
        unified_order_execution_service_fixture.reset_virtual_balances = AsyncMock()

        # Act
        response = await http_client.post(f"/api/v1/trading/paper-balances/reset?initial_capital={initial_capital}")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["user_id"] == str(user_id)
        assert response_data["trading_mode"] == "paper"
        assert response_data["message"] == f"Paper trading balances reset to {initial_capital} USDT"
        assert response_data["new_balance"] == initial_capital

        unified_order_execution_service_fixture.reset_virtual_balances.assert_called_once_with(initial_capital=Decimal(str(initial_capital)))
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reset_paper_trading_balances_invalid_capital(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture

        invalid_capital = -100.0

        # Act
        response = await http_client.post(f"/api/v1/trading/paper-balances/reset?initial_capital={invalid_capital}")

        # Assert
        assert response.status_code == 422 # Unprocessable Entity
        unified_order_execution_service_fixture.reset_virtual_balances.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_reset_paper_trading_balances_service_error(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock,
        user_id
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture
        get_app_settings().FIXED_USER_ID = user_id

        initial_capital = 10000.0
        unified_order_execution_service_fixture.reset_virtual_balances.side_effect = Exception("Reset failed")

        # Act
        response = await http_client.post(f"/api/v1/trading/paper-balances/reset?initial_capital={initial_capital}")

        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to reset paper trading balances: Reset failed"
        unified_order_execution_service_fixture.reset_virtual_balances.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_supported_trading_modes_success(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture

        mock_supported_modes = ["paper", "real"]
        unified_order_execution_service_fixture.get_supported_trading_modes.return_value = mock_supported_modes

        # Act
        response = await http_client.get("/api/v1/trading/supported-modes")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["supported_trading_modes"] == mock_supported_modes
        assert "description" in response_data
        assert "paper" in response_data["description"]
        assert "real" in response_data["description"]

        unified_order_execution_service_fixture.get_supported_trading_modes.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_supported_trading_modes_service_error(
        self,
        client: Tuple[AsyncClient, FastAPI],
        unified_order_execution_service_fixture: AsyncMock
    ):
        # Arrange
        http_client, app = client
        app.dependency_overrides[get_unified_order_execution_service] = lambda: unified_order_execution_service_fixture

        unified_order_execution_service_fixture.get_supported_trading_modes.side_effect = Exception("Mode retrieval failed")

        # Act
        response = await http_client.get("/api/v1/trading/supported-modes")

        # Assert
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to retrieve supported trading modes: Mode retrieval failed"
        unified_order_execution_service_fixture.get_supported_trading_modes.assert_called_once()
        app.dependency_overrides.clear()
