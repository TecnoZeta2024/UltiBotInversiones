import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

from src.ultibot_backend.services.trading_engine_service import TradingEngine
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError, CredentialError, MarketDataError

from src.shared.data_types import (
    Opportunity,
    AIAnalysis,
    UserConfiguration,
    RealTradingSettings,
    RiskProfileSettings,
    TradeOrderDetails,
    Trade,
    OpportunityStatus,
    OpportunitySourceType,
    ServiceName,
    PortfolioSnapshot,
    PortfolioSummary,
    OrderCategory
)

# Valores por defecto de TradingEngineService para TSL/TP
TP_PERCENTAGE_DEFAULT = 0.02
TSL_PERCENTAGE_DEFAULT = 0.01
TSL_CALLBACK_RATE_DEFAULT = 0.005

@pytest.fixture
def mock_config_service():
    return AsyncMock(spec=ConfigService)

@pytest.fixture
def mock_order_execution_service():
    return AsyncMock(spec=OrderExecutionService)

@pytest.fixture
def mock_paper_order_execution_service():
    return AsyncMock()

@pytest.fixture
def mock_credential_service():
    return AsyncMock(spec=CredentialService)

@pytest.fixture
def mock_market_data_service():
    return AsyncMock(spec=MarketDataService)

@pytest.fixture
def mock_portfolio_service():
    return AsyncMock(spec=PortfolioService)

@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_notification_service():
    return AsyncMock(spec=NotificationService)

@pytest.fixture
def mock_binance_adapter():
    mock = AsyncMock(spec=BinanceAdapter)
    # Configurar el mock para create_oco_order
    mock.create_oco_order.return_value = {
        'listClientOrderId': 'test_oco_123',
        'orderReports': [
            {
                'orderId': '123456',
                'clientOrderId': 'sl_order',
                'type': 'STOP_LOSS_LIMIT',
                'status': 'NEW',
                'origQty': '0.1',
                'executedQty': '0.0',
                'price': '98.0',
                'commission': '0.0',
                'commissionAsset': 'USDT',
                'updateTime': int(datetime.now(timezone.utc).timestamp() * 1000),
                'cummulativeQuoteQty': '0.0'
            },
            {
                'orderId': '123457',
                'clientOrderId': 'tp_order',
                'type': 'TAKE_PROFIT_LIMIT',
                'status': 'NEW',
                'origQty': '0.1',
                'executedQty': '0.0',
                'price': '105.0',
                'commission': '0.0',
                'commissionAsset': 'USDT',
                'updateTime': int(datetime.now(timezone.utc).timestamp() * 1000),
                'cummulativeQuoteQty': '0.0'
            }
        ]
    }
    return mock

@pytest.fixture
def trading_engine_service(
    mock_config_service,
    mock_order_execution_service,
    mock_paper_order_execution_service,
    mock_credential_service,
    mock_market_data_service,
    mock_portfolio_service,
    mock_persistence_service,
    mock_notification_service,
    mock_binance_adapter
):
    return TradingEngineService(
        config_service=mock_config_service,
        order_execution_service=mock_order_execution_service,
        paper_order_execution_service=mock_paper_order_execution_service,
        credential_service=mock_credential_service,
        market_data_service=mock_market_data_service,
        portfolio_service=mock_portfolio_service,
        persistence_service=mock_persistence_service,
        notification_service=mock_notification_service,
        binance_adapter=mock_binance_adapter
    )

@pytest.mark.asyncio
async def test_execute_real_trade_sets_tsl_tp_from_user_config(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_binance_adapter: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1

    mock_opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", 
            calculatedConfidence=0.98,
            reasoning_ai=None,
            rawAiOutput=None,
            dataVerification=None,
            ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id,
        paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=0,
            daily_capital_risked_usd=0.0,
            last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.50,
            perTradeCapitalRiskPercentage=0.01,
            takeProfitPercentage=0.05,
            trailingStopLossPercentage=0.02,
            trailingStopCallbackRate=0.01
        )
    )
    mock_config_service.get_user_configuration.return_value = mock_user_config

    mock_portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None),
        paper_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None)
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x

    entry_order_details = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        orderId_exchange=None,
        clientOrderId_exchange=None,
        requestedPrice=current_price,
        cumulativeQuoteQty=requested_quantity_calculated * current_price,
        commissions=[],
        commission=None,
        commissionAsset=None,
        submittedAt=datetime.now(timezone.utc),
        fillTimestamp=datetime.now(timezone.utc),
        rawResponse=None,
        ocoOrderListId=None
    )
    mock_order_execution_service.execute_market_order.return_value = entry_order_details
    
    mock_persistence_service.upsert_trade.return_value = None
    mock_persistence_service.update_opportunity_status.return_value = None
    mock_config_service.save_user_configuration.return_value = None

    with patch('uuid.uuid4', return_value=uuid4()), \
         patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        
        mock_datetime.utcnow.return_value = datetime.now(timezone.utc)

        created_trade = await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert created_trade is not None
    assert created_trade.mode == 'real'
    assert created_trade.symbol == "BTCUSDT"
    assert created_trade.side == "BUY"
    assert created_trade.entryOrder == entry_order_details
    assert created_trade.positionStatus == 'open'

    expected_tp_price = current_price * (1 + 0.05)
    expected_tsl_activation_price = current_price * (1 - 0.02)
    expected_tsl_callback_rate = 0.01

    assert created_trade.takeProfitPrice == pytest.approx(expected_tp_price)
    assert created_trade.trailingStopActivationPrice == pytest.approx(expected_tsl_activation_price)
    assert created_trade.trailingStopCallbackRate == pytest.approx(expected_tsl_callback_rate)
    assert created_trade.currentStopPrice_tsl == pytest.approx(expected_tsl_activation_price)

    # Verificar que se crearon las órdenes OCO
    assert created_trade.ocoOrderListId == 'test_oco_123'
    assert len(created_trade.exitOrders) == 2

    mock_persistence_service.get_opportunity_by_id.assert_called_once_with(opportunity_id)
    mock_config_service.get_user_configuration.assert_called_once_with(user_id)
    mock_portfolio_service.get_portfolio_snapshot.assert_called_once_with(user_id)
    mock_market_data_service.get_latest_price.assert_called_once_with("BTCUSDT")
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=user_id, service_name=ServiceName.BINANCE_SPOT, credential_label="default_binance_spot"
    )
    mock_order_execution_service.execute_market_order.assert_called_once() 
    mock_binance_adapter.create_oco_order.assert_called_once()
    mock_persistence_service.upsert_trade.assert_called_once()
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.CONVERTED_TO_TRADE_REAL, f"Convertida a trade real: {created_trade.id}"
    )
    mock_config_service.save_user_configuration.assert_called_once()
    # Verificar notificaciones
    assert mock_notification_service.send_real_trade_status_notification.call_count >= 2

@pytest.mark.asyncio  
async def test_execute_real_trade_handles_oco_order_failure(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_binance_adapter: AsyncMock
):
    """Test que verifica que el trade se ejecuta correctamente incluso si falla la creación de órdenes OCO"""
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1

    mock_opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", 
            calculatedConfidence=0.98,
            reasoning_ai=None,
            rawAiOutput=None,
            dataVerification=None,
            ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id,
        paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=0,
            daily_capital_risked_usd=0.0,
            last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.50,
            perTradeCapitalRiskPercentage=0.01,
            takeProfitPercentage=0.05,
            trailingStopLossPercentage=0.02,
            trailingStopCallbackRate=0.01
        )
    )
    mock_config_service.get_user_configuration.return_value = mock_user_config

    mock_portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None),
        paper_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None)
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x

    entry_order_details = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        orderId_exchange=None,
        clientOrderId_exchange=None,
        requestedPrice=current_price,
        cumulativeQuoteQty=requested_quantity_calculated * current_price,
        commissions=[],
        commission=None,
        commissionAsset=None,
        submittedAt=datetime.now(timezone.utc),
        fillTimestamp=datetime.now(timezone.utc),
        rawResponse=None,
        ocoOrderListId=None
    )
    mock_order_execution_service.execute_market_order.return_value = entry_order_details
    
    # Hacer que el create_oco_order falle
    mock_binance_adapter.create_oco_order.side_effect = Exception("Error al crear órdenes OCO")
    
    mock_persistence_service.upsert_trade.return_value = None
    mock_persistence_service.update_opportunity_status.return_value = None
    mock_config_service.save_user_configuration.return_value = None

    with patch('uuid.uuid4', return_value=uuid4()), \
         patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        
        mock_datetime.utcnow.return_value = datetime.now(timezone.utc)

        created_trade = await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    # El trade debe ejecutarse exitosamente incluso si las órdenes OCO fallan
    assert created_trade is not None
    assert created_trade.mode == 'real'
    assert created_trade.symbol == "BTCUSDT"
    assert created_trade.side == "BUY"
    assert created_trade.positionStatus == 'open'
    
    # Las órdenes OCO deben estar vacías debido al fallo
    assert created_trade.ocoOrderListId is None
    assert len(created_trade.exitOrders) == 0
    
    # Debe haber enviado una notificación de error sobre las órdenes OCO
    error_notification_calls = [
        call for call in mock_notification_service.send_real_trade_status_notification.call_args_list
        if "Error al enviar órdenes OCO" in str(call)
    ]
    assert len(error_notification_calls) > 0
