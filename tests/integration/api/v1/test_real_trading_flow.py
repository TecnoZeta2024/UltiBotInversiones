import pytest
import asyncio
import copy
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import logging
from decimal import Decimal

from core.domain_models.trade_models import TradeSide, PositionStatus, OrderCategory, TradeOrderDetails
from core.domain_models.opportunity_models import Opportunity, OpportunityStatus, AIAnalysis, SourceType, InitialSignal, Direction, SuggestedAction
from core.domain_models.user_configuration_models import UserConfiguration, RiskProfileSettings, RealTradingSettings
from shared.data_types import APICredential, PortfolioSnapshot, PortfolioSummary, ServiceName
from core.domain_models.trading_strategy_models import TradingStrategyConfig

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_complete_real_trading_flow_with_capital_management():
    """
    Test de integración para el flujo completo de operación real con gestión de capital y TSL/TP.
    """
    from services.trading_engine_service import TradingEngine
    from services.config_service import ConfigurationService
    from services.credential_service import CredentialService
    from services.market_data_service import MarketDataService
    from services.portfolio_service import PortfolioService
    from adapters.persistence_service import SupabasePersistenceService
    from services.notification_service import NotificationService
    from services.unified_order_execution_service import UnifiedOrderExecutionService
    from services.ai_orchestrator_service import AIOrchestrator

    # Mock all dependencies
    mock_config_service = AsyncMock(spec=ConfigurationService)
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_persistence_service.upsert_trade = AsyncMock() # Add the correct method to the mock
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_strategy_service = AsyncMock()
    mock_unified_order_execution_service = AsyncMock(spec=UnifiedOrderExecutionService)
    mock_ai_orchestrator = AsyncMock(spec=AIOrchestrator)

    # Instantiate the service with mocked dependencies
    trading_engine = TradingEngine(
        persistence_service=mock_persistence_service,
        market_data_service=mock_market_data_service,
        unified_order_execution_service=mock_unified_order_execution_service,
        credential_service=mock_credential_service,
        notification_service=mock_notification_service,
        strategy_service=mock_strategy_service,
        configuration_service=mock_config_service,
        portfolio_service=mock_portfolio_service,
        ai_orchestrator=mock_ai_orchestrator
    )

    # Test data setup
    user_id = str(uuid4())
    opportunity_id = str(uuid4())
    symbol = "BTCUSDT"
    current_price = Decimal("60000.0")
    expected_capital_to_invest = Decimal("10000.0") * Decimal("0.02")
    executed_quantity = expected_capital_to_invest / current_price

    # Fully populated Opportunity object
    opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        strategy_id=None,
        exchange='BINANCE',
        symbol=symbol,
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.AI_SUGGESTION_PROACTIVE,
        source_name="Test Source",
        source_data={},
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=current_price,
            stop_loss_target=current_price * Decimal("0.985"),
            take_profit_target=[current_price * Decimal("1.03")],
            timeframe="1h",
            reasoning_source_structured={},
            reasoning_source_text="Initial signal from test setup",
            confidence_source=0.95
        ),
        system_calculated_priority_score=80,
        last_priority_calculation_at=datetime.now(timezone.utc),
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        status_reason_code=None,
        status_reason_text=None,
        ai_analysis=AIAnalysis(
            analysis_id=str(uuid4()),
            analyzed_at=datetime.now(timezone.utc),
            model_used="gemini-1.5-pro",
            calculated_confidence=0.98,
            suggested_action=SuggestedAction.BUY,
            recommended_trade_strategy_type="Scalping",
            recommended_trade_params=None,
            reasoning_ai="Strong bullish signals detected",
            data_verification=None,
            processing_time_ms=None,
            ai_warnings=None,
        ),
        investigation_details=None,
        user_feedback=None,
        linked_trade_ids=None,
        expires_at=None,
        expiration_logic=None,
        post_trade_feedback=None,
        post_facto_simulation_results=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = opportunity

    # Fully populated UserConfiguration object
    user_config = UserConfiguration(
        id=user_id,
        user_id=user_id,
        telegram_chat_id=None,
        notification_preferences=None,
        enable_telegram_notifications=True,
        default_paper_trading_capital=None,
        paper_trading_active=False,
        paper_trading_assets=None,
        watchlists=None,
        favorite_pairs=None,
        risk_profile=None,
        risk_profile_settings=RiskProfileSettings(
            daily_capital_risk_percentage=0.50,
            per_trade_capital_risk_percentage=0.02,
            max_drawdown_percentage=0.10
        ),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=True,
            real_trades_executed_count=1,
            max_concurrent_operations=5,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None,
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=None
        ),
        ai_strategy_configurations=None,
        ai_analysis_confidence_thresholds=None,
        mcp_server_preferences=None,
        selected_theme=None,
        dashboard_layout_profiles=None,
        active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None,
        cloud_sync_preferences=None,
        created_at=None,
        updated_at=None
    )
    mock_config_service.get_user_configuration.return_value = user_config

    # Fully populated PortfolioSnapshot object
    portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(
            total_portfolio_value_usd=Decimal("10000.0"),
            available_balance_usdt=Decimal("10000.0"),
            total_assets_value_usd=Decimal("0.0"),
            error_message=None
        ),
        paper_trading=PortfolioSummary(
            total_portfolio_value_usd=Decimal("10000.0"),
            available_balance_usdt=Decimal("10000.0"),
            total_assets_value_usd=Decimal("0.0"),
            error_message=None
        )
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price

    # Fully populated APICredential object
    mock_credential = APICredential(
        id=uuid4(),
        user_id=UUID(user_id),
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot",
        encrypted_api_key="encrypted_key",
        encrypted_api_secret="encrypted_secret",
    )
    mock_credential_service.get_credential.return_value = mock_credential
    mock_credential_service.decrypt_data.side_effect = lambda x: x.replace("encrypted_", "")

    # Fully populated TradeOrderDetails object
    mock_unified_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(),
        orderId_exchange=None,
        clientOrderId_exchange=None,
        orderCategory=OrderCategory.ENTRY,
        type="market",
        status="filled",
        requestedPrice=None,
        requestedQuantity=executed_quantity,
        executedQuantity=executed_quantity,
        executedPrice=current_price,
        cumulativeQuoteQty=executed_quantity * current_price,
        commissions=None,
        commission=None,
        commissionAsset=None,
        timestamp=datetime.now(timezone.utc),
        submittedAt=None,
        fillTimestamp=None,
        rawResponse=None,
        ocoOrderListId=None,
        price=None,
        stopPrice=None,
        timeInForce=None
    )
    mock_unified_order_execution_service.create_oco_order.return_value = {"listClientOrderId": "oco_list_123"}
    mock_strategy_service.get_active_strategies.return_value = [MagicMock(spec=TradingStrategyConfig, id=uuid4(), user_id=UUID(user_id), config_name='test_strategy')]
    
    # Execute the trade
    result_trade = await trading_engine.execute_trade_from_confirmed_opportunity(opportunity)

    # Assertions
    assert result_trade is not None
    assert result_trade.side == TradeSide.BUY
    assert result_trade.positionStatus == PositionStatus.OPEN
    assert result_trade.entryOrder.orderCategory == OrderCategory.ENTRY
    mock_persistence_service.upsert_trade.assert_called_once_with(result_trade)

@pytest.mark.asyncio
async def test_capital_management_daily_reset():
    """
    Test que verifica el reinicio automático del capital diario arriesgado.
    """
    from services.trading_engine_service import TradingEngine
    from services.config_service import ConfigurationService
    from services.credential_service import CredentialService
    from services.market_data_service import MarketDataService
    from services.portfolio_service import PortfolioService
    from adapters.persistence_service import SupabasePersistenceService
    from services.notification_service import NotificationService
    from services.unified_order_execution_service import UnifiedOrderExecutionService
    from services.ai_orchestrator_service import AIOrchestrator

    # Mocks
    mock_config_service = AsyncMock(spec=ConfigurationService)
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_persistence_service.upsert_trade = AsyncMock() # Add the correct method to the mock
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_strategy_service = AsyncMock()
    mock_unified_order_execution_service = AsyncMock(spec=UnifiedOrderExecutionService)
    mock_ai_orchestrator = AsyncMock(spec=AIOrchestrator)

    # Service instance
    trading_engine = TradingEngine(
        persistence_service=mock_persistence_service,
        market_data_service=mock_market_data_service,
        unified_order_execution_service=mock_unified_order_execution_service,
        credential_service=mock_credential_service,
        notification_service=mock_notification_service,
        strategy_service=mock_strategy_service,
        configuration_service=mock_config_service,
        portfolio_service=mock_portfolio_service,
        ai_orchestrator=mock_ai_orchestrator
    )

    # Test data
    user_id_str = str(uuid4())
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    # Fully populated Opportunity
    opportunity = Opportunity(
        id=str(uuid4()),
        user_id=user_id_str,
        symbol="ADAUSDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.MANUAL_ENTRY,
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY, 
            entry_price_target=Decimal("0.5"),
            stop_loss_target=None,
            take_profit_target=None,
            timeframe=None,
            reasoning_source_structured=None,
            reasoning_source_text=None,
            confidence_source=None
        ),
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        strategy_id=None, exchange=None, source_name=None, source_data=None,
        system_calculated_priority_score=None, last_priority_calculation_at=None,
        status_reason_code=None, status_reason_text=None, ai_analysis=None,
        investigation_details=None, user_feedback=None, linked_trade_ids=None,
        expires_at=None, expiration_logic=None, post_trade_feedback=None,
        post_facto_simulation_results=None
    )

    # Fully populated UserConfiguration
    user_config = UserConfiguration(
        id=user_id_str,
        user_id=user_id_str,
        risk_profile_settings=RiskProfileSettings(
            daily_capital_risk_percentage=0.50,
            per_trade_capital_risk_percentage=0.02,
            max_drawdown_percentage=0.10
        ),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=True,
            daily_capital_risked_usd=Decimal("100.0"),
            last_daily_reset=yesterday,
            real_trades_executed_count=0,
            max_concurrent_operations=5,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=None
        ),
        telegram_chat_id=None, notification_preferences=None, enable_telegram_notifications=None,
        default_paper_trading_capital=None, paper_trading_active=None, paper_trading_assets=None,
        watchlists=None, favorite_pairs=None, risk_profile=None, ai_strategy_configurations=None,
        ai_analysis_confidence_thresholds=None, mcp_server_preferences=None, selected_theme=None,
        dashboard_layout_profiles=None, active_dashboard_layout_profile_id=None,
        dashboard_layout_config=None, cloud_sync_preferences=None, created_at=None, updated_at=None
    )
    mock_config_service.get_user_configuration.return_value = user_config

    # Fully populated PortfolioSnapshot
    portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(total_portfolio_value_usd=Decimal("5000.0"), available_balance_usdt=Decimal("5000.0"), total_assets_value_usd=Decimal("0.0"), error_message=None),
        paper_trading=PortfolioSummary(total_portfolio_value_usd=Decimal("10000.0"), available_balance_usdt=Decimal("10000.0"), total_assets_value_usd=Decimal("0.0"), error_message=None)
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = Decimal("0.50")
    
    # Fully populated APICredential
    mock_credential = APICredential(
        id=uuid4(), 
        user_id=UUID(user_id_str), 
        service_name=ServiceName.BINANCE_SPOT, 
        credential_label="default_binance_spot",
        encrypted_api_key="key", 
        encrypted_api_secret="secret"
    )
    mock_credential_service.get_credential.return_value = mock_credential
    
    # Fully populated TradeOrderDetails
    mock_unified_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(),
        orderCategory=OrderCategory.ENTRY, 
        type="market", 
        status="filled", 
        requestedQuantity=Decimal("200.0"), 
        executedQuantity=Decimal("200.0"), 
        executedPrice=Decimal("0.50"),
        cumulativeQuoteQty=Decimal("100.0"),
        timestamp=datetime.now(timezone.utc),
        orderId_exchange=None, clientOrderId_exchange=None, requestedPrice=None,
        commissions=None, commission=None, commissionAsset=None, submittedAt=None,
        fillTimestamp=None, rawResponse=None, ocoOrderListId=None, price=None,
        stopPrice=None, timeInForce=None
    )

    # Mock side effect for saving config
    saved_configs_copies = []
    async def save_config_side_effect(config_to_save):
        saved_configs_copies.append(copy.deepcopy(config_to_save))
    mock_config_service.save_user_configuration.side_effect = save_config_side_effect

    mock_strategy_service.get_active_strategies.return_value = [MagicMock(spec=TradingStrategyConfig, id=uuid4(), user_id=UUID(user_id_str), config_name='test_strategy')]
    
    # Execute trade
    await trading_engine.execute_trade_from_confirmed_opportunity(opportunity)

    # Assertions
    assert len(saved_configs_copies) >= 2
    reset_config = saved_configs_copies[0]
    assert reset_config.real_trading_settings.daily_capital_risked_usd == Decimal("0.0")
