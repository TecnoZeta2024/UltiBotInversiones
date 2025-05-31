import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

from src.ultibot_backend.services.trading_engine_service import TradingEngineService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter # Importar BinanceAdapter
from src.ultibot_backend.core.exceptions import OrderExecutionError, ConfigurationError, CredentialError # Importar CredentialError

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
    OrderCategory # Importar OrderCategory
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
def mock_binance_adapter(): # Nuevo fixture para BinanceAdapter
    return AsyncMock(spec=BinanceAdapter)

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
    mock_binance_adapter # Añadir al fixture
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
        binance_adapter=mock_binance_adapter # Pasar el mock
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
    mock_binance_adapter: AsyncMock # Añadir al test
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1 # Asumimos que se calcula esta cantidad

    mock_opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED, # Corregido: Usar enum
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", 
            calculatedConfidence=0.98,
            reasoning_ai=None, # Añadido explícitamente
            rawAiOutput=None, # Añadido explícitamente
            dataVerification=None, # Añadido explícitamente
            ai_model_used=None # Añadido explícitamente
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
            perTradeCapitalRiskPercentage=0.01, # 1% del capital disponible por trade
            takeProfitPercentage=0.05, # 5%
            trailingStopLossPercentage=0.02, # 2%
            trailingStopCallbackRate=0.01 # 1%
        )
    )
    mock_config_service.get_user_configuration.return_value = mock_user_config

    mock_portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None), # Añadido: error_message=None
        paper_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None) # Añadido: error_message=None
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price

    # Mockear credenciales
    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x # Simula la desencriptación

    # Mockear la ejecución de la orden
    entry_order_details = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, # Añadido explícitamente
        commission=None, # Añadido explícitamente
        commissionAsset=None, # Añadido explícitamente
        rawResponse=None, # Añadido explícitamente
        ocoOrderListId=None # Añadido explícitamente
    )
    mock_order_execution_service.execute_market_order.return_value = entry_order_details
    
    # Mockear persistencia de trade y oportunidad
    mock_persistence_service.upsert_trade.return_value = None
    mock_persistence_service.update_opportunity_status.return_value = None
    mock_config_service.save_user_configuration.return_value = None # Para el guardado de daily_capital_risked_usd

    with patch('uuid.uuid4', return_value=uuid4()) as mock_uuid, \
         patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        
        mock_datetime.utcnow.return_value = datetime.now(timezone.utc) # Asegurar que todas las fechas son consistentes

        created_trade = await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert created_trade is not None
    assert created_trade.mode == 'real'
    assert created_trade.symbol == "BTCUSDT"
    assert created_trade.side == "BUY"
    assert created_trade.entryOrder == entry_order_details
    assert created_trade.positionStatus == 'open'

    # Verificar TSL/TP basado en la configuración del usuario
    expected_tp_price = current_price * (1 + 0.05) # 5%
    expected_tsl_activation_price = current_price * (1 - 0.02) # 2%
    expected_tsl_callback_rate = 0.01 # 1%

    assert created_trade.takeProfitPrice == pytest.approx(expected_tp_price)
    assert created_trade.trailingStopActivationPrice == pytest.approx(expected_tsl_activation_price)
    assert created_trade.trailingStopCallbackRate == pytest.approx(expected_tsl_callback_rate)
    assert created_trade.currentStopPrice_tsl == pytest.approx(expected_tsl_activation_price) # Inicialmente es igual al de activación

    mock_persistence_service.get_opportunity_by_id.assert_called_once_with(opportunity_id)
    mock_config_service.get_user_configuration.assert_called_once_with(user_id)
    mock_portfolio_service.get_portfolio_snapshot.assert_called_once_with(user_id)
    mock_market_data_service.get_latest_price.assert_called_once_with("BTCUSDT")
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=user_id, service_name=ServiceName.BINANCE_SPOT, credential_label="default_binance_spot"
    )
    # La cantidad real a invertir es 10000 * 0.01 = 100 USDT. Cantidad de BTC = 100 / 100 = 1.0
    # El mock_order_execution_service.execute_market_order es llamado con la cantidad calculada internamente.
    # No podemos verificar requested_quantity directamente aquí sin replicar el cálculo exacto,
    # pero verificamos que la orden se ejecutó.
    mock_order_execution_service.execute_market_order.assert_called_once() 
    mock_persistence_service.upsert_trade.assert_called_once()
    # Verificar que el trade_id en update_opportunity_status es el del trade creado
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.CONVERTED_TO_TRADE_REAL, f"Convertida a trade real: {created_trade.id}"
    )
    mock_config_service.save_user_configuration.assert_called_once() # Para daily_capital_risked_usd y count
    # No se espera notificación de alta confianza aquí, sino de estado de trade
    mock_notification_service.send_real_trade_status_notification.assert_any_call(
        user_id, f"Orden real enviada para BTCUSDT (BUY). Estado: {entry_order_details.status}", "INFO"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_sets_tsl_tp_from_defaults_if_not_in_config(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 200.0
    requested_quantity_calculated = 0.05

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="ETHUSDT",
        source_type=OpportunitySourceType.AI_GENERATED, # Corregido: Usar enum
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="SELL", 
            calculatedConfidence=0.99,
            reasoning_ai=None, # Añadido explícitamente
            rawAiOutput=None, # Añadido explícitamente
            dataVerification=None, # Añadido explícitamente
            ai_model_used=None # Añadido explícitamente
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    # Configuración de usuario sin RiskProfileSettings o con valores None
    mock_user_config_no_risk_settings = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
                daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
            ),
            # Modificado: Proporcionar RiskProfileSettings con campos TSL/TP en None
            riskProfileSettings=RiskProfileSettings( 
                dailyCapitalRiskPercentage=0.50, # Necesario para pasar la validación inicial
                perTradeCapitalRiskPercentage=0.01, # Necesario para pasar la validación inicial
                takeProfitPercentage=None,
                trailingStopLossPercentage=None,
                trailingStopCallbackRate=None
            )
        )
    mock_config_service.get_user_configuration.return_value = mock_user_config_no_risk_settings

    mock_portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(available_balance_usdt=5000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=5000.0, assets=[], error_message=None), # Añadido: error_message=None
        paper_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None) # Añadido: error_message=None
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price
    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x

    entry_order_details = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, # Añadido explícitamente
        commission=None, # Añadido explícitamente
        commissionAsset=None, # Añadido explícitamente
        rawResponse=None, # Añadido explícitamente
        ocoOrderListId=None # Añadido explícitamente
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
    assert created_trade.side == "SELL"

    # Verificar TSL/TP basado en los valores por defecto de la clase
    expected_tp_price = current_price * (1 - TP_PERCENTAGE_DEFAULT)
    expected_tsl_activation_price = current_price * (1 + TSL_PERCENTAGE_DEFAULT)
    expected_tsl_callback_rate = TSL_CALLBACK_RATE_DEFAULT

    assert created_trade.takeProfitPrice == pytest.approx(expected_tp_price)
    assert created_trade.trailingStopActivationPrice == pytest.approx(expected_tsl_activation_price)
    assert created_trade.trailingStopCallbackRate == pytest.approx(expected_tsl_callback_rate)
    assert created_trade.currentStopPrice_tsl == pytest.approx(expected_tsl_activation_price)

@pytest.mark.asyncio
async def test_monitor_real_trade_adjusts_tsl_for_buy_trade_favorably(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    initial_stop_price = entry_price * (1 - initial_tsl_percentage) # 100 * 0.98 = 98.0

    mock_trade = Trade(
        id=trade_id,
        user_id=user_id,
        mode='real',
        symbol='BTCUSDT',
        side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, # Añadido explícitamente
            commission=None, # Añadido explícitamente
            commissionAsset=None, # Añadido explícitamente
            rawResponse=None, # Añadido explícitamente
            ocoOrderListId=None # Añadido explícitamente
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10, # 10% TP
        trailingStopActivationPrice=initial_stop_price, # Activado
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc),
        opened_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        opportunityId=None, # Añadido explícitamente
        aiAnalysisConfidence=None, # Añadido explícitamente
        pnl_usd=None, # Añadido explícitamente
        pnl_percentage=None, # Añadido explícitamente
        closingReason=None, # Añadido explícitamente
        closed_at=None # Añadido explícitamente
    )

    # Simular que el precio actual sube favorablemente
    favorable_current_price = 105.0
    mock_market_data_service.get_latest_price.return_value = favorable_current_price

    # Mockear datetime para controlar el timestamp en riskRewardAdjustments
    fixed_now = datetime.now(timezone.utc)
    with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

    # Verificar que el TSL se ajustó
    # Nuevo TSL = 105.0 * (1 - 0.01) = 105.0 * 0.99 = 103.95
    expected_new_tsl = favorable_current_price * (1 - tsl_callback_rate)
    assert mock_trade.currentStopPrice_tsl == pytest.approx(expected_new_tsl)
    
    # Verificar que se llamó a persistencia
    mock_persistence_service.upsert_trade.assert_called_once()
    # El primer argumento de la llamada a upsert_trade es user_id, el segundo es el trade_data
    called_trade_data = mock_persistence_service.upsert_trade.call_args[0][1]
    assert called_trade_data['id'] == str(trade_id) # UUID se convierte a str en model_dump
    assert called_trade_data['currentStopPrice_tsl'] == pytest.approx(expected_new_tsl)
    
    # Comparar objetos datetime en lugar de sus representaciones ISO string directamente
    # para evitar problemas con 'Z' vs '+00:00'
    assert datetime.fromisoformat(called_trade_data['updated_at']) == fixed_now

    # Verificar que se añadió un ajuste de riesgo/recompensa
    assert len(mock_trade.riskRewardAdjustments) == 1
    adjustment = mock_trade.riskRewardAdjustments[0]
    assert adjustment['type'] == "TSL_ADJUSTMENT_REAL"
    assert adjustment['new_stop_price'] == pytest.approx(expected_new_tsl)
    assert adjustment['current_price'] == pytest.approx(favorable_current_price)
    assert adjustment['timestamp'] == fixed_now.isoformat()

@pytest.mark.asyncio
async def test_monitor_real_trade_adjusts_tsl_for_sell_trade_favorably(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    # Para una operación SELL, el TSL se activa por encima del precio de entrada
    initial_stop_price = entry_price * (1 + initial_tsl_percentage) # 100 * 1.02 = 102.0

    mock_trade = Trade(
        id=trade_id,
        user_id=user_id,
        mode='real',
        symbol='BTCUSDT',
        side='SELL', # Operación de venta
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 0.90, # 10% TP (por debajo del precio de entrada para SELL)
        trailingStopActivationPrice=initial_stop_price, # Activado
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc),
        opened_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual baja favorablemente para una venta
    favorable_current_price = 95.0
    mock_market_data_service.get_latest_price.return_value = favorable_current_price

    fixed_now = datetime.now(timezone.utc)
    with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

    # Verificar que el TSL se ajustó
    # Nuevo TSL = 95.0 * (1 + 0.01) = 95.0 * 1.01 = 95.95
    expected_new_tsl = favorable_current_price * (1 + tsl_callback_rate)
    assert mock_trade.currentStopPrice_tsl == pytest.approx(expected_new_tsl)
    
    mock_persistence_service.upsert_trade.assert_called_once()
    called_trade_data = mock_persistence_service.upsert_trade.call_args[0][1]
    assert called_trade_data['id'] == str(trade_id)
    assert called_trade_data['currentStopPrice_tsl'] == pytest.approx(expected_new_tsl)
    assert datetime.fromisoformat(called_trade_data['updated_at']) == fixed_now

    assert len(mock_trade.riskRewardAdjustments) == 1
    adjustment = mock_trade.riskRewardAdjustments[0]
    assert adjustment['type'] == "TSL_ADJUSTMENT_REAL"
    assert adjustment['new_stop_price'] == pytest.approx(expected_new_tsl)
    assert adjustment['current_price'] == pytest.approx(favorable_current_price)
    assert adjustment['timestamp'] == fixed_now.isoformat()

@pytest.mark.asyncio
async def test_monitor_real_trade_does_not_adjust_tsl_for_buy_trade_unfavorably(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    initial_stop_price = entry_price * (1 - initial_tsl_percentage) # 100 * 0.98 = 98.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=initial_stop_price,
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual baja desfavorablemente para una compra, pero no lo suficiente para TSL hit
    unfavorable_current_price = 99.0 # Todavía por encima del TSL (98.0)
    mock_market_data_service.get_latest_price.return_value = unfavorable_current_price

    fixed_now = datetime.now(timezone.utc)
    with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

    # Verificar que el TSL NO se ajustó
    assert mock_trade.currentStopPrice_tsl == pytest.approx(initial_stop_price)
    
    # Verificar que NO se llamó a persistencia (porque no hubo cambio)
    mock_persistence_service.upsert_trade.assert_not_called()
    assert len(mock_trade.riskRewardAdjustments) == 0

@pytest.mark.asyncio
async def test_monitor_real_trade_does_not_adjust_tsl_for_sell_trade_unfavorably(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    initial_stop_price = entry_price * (1 + initial_tsl_percentage) # 100 * 1.02 = 102.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='SELL',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 0.90,
        trailingStopActivationPrice=initial_stop_price,
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual sube desfavorablemente para una venta, pero no lo suficiente para TSL hit
    unfavorable_current_price = 101.0 # Todavía por debajo del TSL (102.0)
    mock_market_data_service.get_latest_price.return_value = unfavorable_current_price

    fixed_now = datetime.now(timezone.utc)
    with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

    # Verificar que el TSL NO se ajustó
    assert mock_trade.currentStopPrice_tsl == pytest.approx(initial_stop_price)
    
    # Verificar que NO se llamó a persistencia (porque no hubo cambio)
    mock_persistence_service.upsert_trade.assert_not_called()
    assert len(mock_trade.riskRewardAdjustments) == 0

@pytest.mark.asyncio
async def test_monitor_real_trade_detects_tp_hit_for_buy_trade(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_credential_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    take_profit_price = 105.0 # TP a 105

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=take_profit_price,
        trailingStopActivationPrice=None, # No TSL para esta prueba
        trailingStopCallbackRate=None,
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual alcanza o supera el TP
    current_price_at_tp = 105.5
    mock_market_data_service.get_latest_price.return_value = current_price_at_tp

    # Mockear _close_real_trade para verificar que se llama
    with patch.object(trading_engine_service, '_close_real_trade', new_callable=AsyncMock) as mock_close_real_trade:
        mock_close_real_trade.return_value = None # No necesitamos un valor de retorno específico para esta prueba
        
        fixed_now = datetime.now(timezone.utc)
        with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now
            await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        # Verificar que _close_real_trade fue llamado con el trade y la razón correcta
        mock_close_real_trade.assert_called_once_with(mock_trade, current_price_at_tp, "TP_HIT")
        
        # Verificar que el estado del trade se actualizó a 'closed' y la razón
        assert mock_trade.positionStatus == 'closed'
        assert mock_trade.closingReason == 'TP_HIT'
        assert mock_trade.closed_at == fixed_now
        assert len(mock_trade.exitOrders) == 1 # Se añadió una orden de salida

@pytest.mark.asyncio
async def test_monitor_real_trade_detects_tp_hit_for_sell_trade(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_credential_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    take_profit_price = 95.0 # TP a 95 para una venta

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='SELL',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=take_profit_price,
        trailingStopActivationPrice=None,
        trailingStopCallbackRate=None,
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual alcanza o baja del TP para una venta
    current_price_at_tp = 94.5
    mock_market_data_service.get_latest_price.return_value = current_price_at_tp

    with patch.object(trading_engine_service, '_close_real_trade', new_callable=AsyncMock) as mock_close_real_trade:
        mock_close_real_trade.return_value = None
        
        fixed_now = datetime.now(timezone.utc)
        with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now
            await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        mock_close_real_trade.assert_called_once_with(mock_trade, current_price_at_tp, "TP_HIT")
        assert mock_trade.positionStatus == 'closed'
        assert mock_trade.closingReason == 'TP_HIT'
        assert mock_trade.closed_at == fixed_now
        assert len(mock_trade.exitOrders) == 1 # Se añadió una orden de salida

@pytest.mark.asyncio
async def test_monitor_real_trade_detects_tsl_hit_for_buy_trade(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_credential_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    # TSL activado en 98.0
    initial_stop_price = entry_price * (1 - initial_tsl_percentage) # 98.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=initial_stop_price,
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price, # TSL actual en 98.0
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual cae por debajo del TSL
    current_price_below_tsl = 97.5
    mock_market_data_service.get_latest_price.return_value = current_price_below_tsl

    with patch.object(trading_engine_service, '_close_real_trade', new_callable=AsyncMock) as mock_close_real_trade:
        mock_close_real_trade.return_value = None
        
        fixed_now = datetime.now(timezone.utc)
        with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now
            await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        mock_close_real_trade.assert_called_once_with(mock_trade, current_price_below_tsl, "TSL_HIT")
        assert mock_trade.positionStatus == 'closed'
        assert mock_trade.closingReason == 'TSL_HIT'
        assert mock_trade.closed_at == fixed_now
        assert len(mock_trade.exitOrders) == 1 # Se añadió una orden de salida

@pytest.mark.asyncio
async def test_monitor_real_trade_detects_tsl_hit_for_sell_trade(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_credential_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    initial_tsl_percentage = 0.02 # 2%
    tsl_callback_rate = 0.01 # 1%

    # TSL activado en 102.0 para una venta
    initial_stop_price = entry_price * (1 + initial_tsl_percentage) # 102.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='SELL',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 0.90,
        trailingStopActivationPrice=initial_stop_price,
        trailingStopCallbackRate=tsl_callback_rate,
        currentStopPrice_tsl=initial_stop_price, # TSL actual en 102.0
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que el precio actual sube por encima del TSL para una venta
    current_price_above_tsl = 102.5
    mock_market_data_service.get_latest_price.return_value = current_price_above_tsl

    with patch.object(trading_engine_service, '_close_real_trade', new_callable=AsyncMock) as mock_close_real_trade:
        mock_close_real_trade.return_value = None
        
        fixed_now = datetime.now(timezone.utc)
        with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_now
            await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        mock_close_real_trade.assert_called_once_with(mock_trade, current_price_above_tsl, "TSL_HIT")
        assert mock_trade.positionStatus == 'closed'
        assert mock_trade.closingReason == 'TSL_HIT'
        assert mock_trade.closed_at == fixed_now
        assert len(mock_trade.exitOrders) == 1 # Se añadió una orden de salida

@pytest.mark.asyncio
async def test_monitor_real_trade_handles_no_tsl_configured(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, # No TSL configurado
        trailingStopCallbackRate=None,
        currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_market_data_service.get_latest_price.return_value = 101.0 # Precio irrelevante para esta prueba

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        # Verificar que se registró un warning
        mock_logger.warning.assert_called_once_with(
            f"Trade {trade_id} no tiene TSL configurado. No se realizará monitoreo de TSL."
        )
    
    # Verificar que no se intentó actualizar el trade en persistencia por TSL
    mock_persistence_service.upsert_trade.assert_not_called()
    assert len(mock_trade.riskRewardAdjustments) == 0
    assert mock_trade.positionStatus == 'open' # El trade sigue abierto

@pytest.mark.asyncio
async def test_monitor_real_trade_handles_market_data_service_failure(
    trading_engine_service: TradingEngineService,
    mock_market_data_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=1.0, executedQuantity=1.0, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=entry_price * 0.98,
        trailingStopCallbackRate=0.01,
        currentStopPrice_tsl=entry_price * 0.98,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Simular que get_latest_price falla
    mock_market_data_service.get_latest_price.side_effect = Exception("Error de conexión a datos de mercado")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        await trading_engine_service.monitor_and_manage_real_trade_exit(mock_trade)

        # Verificar que se registró un error
        mock_logger.error.assert_called_once_with(
            f"Error al obtener precio para {mock_trade.symbol} durante monitoreo de trade {trade_id}: Error de conexión a datos de mercado"
        )
    
    # Verificar que no se intentó actualizar el trade en persistencia
    mock_persistence_service.upsert_trade.assert_not_called()
    assert mock_trade.positionStatus == 'open' # El trade sigue abierto

@pytest.mark.asyncio
async def test_close_real_trade_successful_execution(
    trading_engine_service: TradingEngineService,
    mock_order_execution_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_notification_service: AsyncMock,
    mock_credential_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    # Mockear credenciales
    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x

    # Mockear la ejecución de la orden de cierre
    exit_order_details = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
        requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
        executedPrice=105.0, timestamp=datetime.now(timezone.utc), # Precio de cierre
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_order_execution_service.execute_market_order.return_value = exit_order_details
    
    # Mockear servicios de persistencia, portafolio y notificación
    mock_persistence_service.upsert_trade.return_value = None
    mock_portfolio_service.update_real_portfolio_after_exit.return_value = None
    mock_notification_service.send_real_trade_exit_notification.return_value = None

    fixed_now = datetime.now(timezone.utc)
    with patch('src.ultibot_backend.services.trading_engine_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = fixed_now
        await trading_engine_service._close_real_trade(mock_trade, exit_order_details.executedPrice, closing_reason)

    # Verificar llamadas a servicios
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=user_id, service_name=ServiceName.BINANCE_SPOT, credential_label="default_binance_spot"
    )
    mock_order_execution_service.execute_market_order.assert_called_once_with(
        api_key="key", api_secret="secret", symbol=mock_trade.symbol,
        side="SELL", # Para cerrar una compra, se vende
        quantity=mock_trade.entryOrder.executedQuantity
    )
    mock_persistence_service.upsert_trade.assert_called_once()
    mock_portfolio_service.update_real_portfolio_after_exit.assert_called_once_with(mock_trade) # Solo trade
    mock_notification_service.send_real_trade_exit_notification.assert_called_once_with(mock_trade) # Solo trade

    # Verificar que el trade se actualizó correctamente
    assert mock_trade.positionStatus == 'closed'
    assert mock_trade.exitOrders[0] == exit_order_details # Acceder como lista
    assert mock_trade.closingReason == closing_reason
    assert mock_trade.closed_at == fixed_now
    assert mock_trade.pnl_usd is not None
    assert mock_trade.pnl_percentage is not None

@pytest.mark.asyncio
async def test_close_real_trade_handles_credential_error(
    trading_engine_service: TradingEngineService,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_credential_service.get_credential.side_effect = Exception("Error de credenciales")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        with pytest.raises(CredentialError) as excinfo: # Esperar CredentialError
            await trading_engine_service._close_real_trade(mock_trade, 105.0, closing_reason) # Pasar executed_price

        assert "No se encontraron credenciales de Binance para cerrar trade" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            f"No se encontraron credenciales de Binance para cerrar trade {trade_id}."
        )
    
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, f"Error al cerrar trade real {mock_trade.symbol} por {closing_reason}: No se encontraron credenciales de Binance para cerrar trade {trade_id}.", "ERROR" # Mensaje de error más específico
    )
    assert mock_trade.positionStatus == 'open' # El trade no se cerró
    assert mock_trade.closingReason is None
    assert mock_trade.closed_at is None

@pytest.mark.asyncio
async def test_close_real_trade_handles_order_execution_error(
    trading_engine_service: TradingEngineService,
    mock_order_execution_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x
    mock_order_execution_service.execute_market_order.side_effect = OrderExecutionError("Fallo al ejecutar orden de cierre")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        with pytest.raises(OrderExecutionError) as excinfo: # Esperar OrderExecutionError
            await trading_engine_service._close_real_trade(mock_trade, 105.0, closing_reason) # Pasar executed_price

        assert "Fallo al enviar orden de cierre real para trade" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            f"Fallo al enviar orden de cierre real para trade {trade_id}: Fallo al ejecutar orden de cierre"
        )
    
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, f"Error al cerrar trade real {mock_trade.symbol} por {closing_reason}: Fallo al ejecutar orden de cierre", "ERROR"
    )
    assert mock_trade.positionStatus == 'open'
    assert mock_trade.closingReason is None
    assert mock_trade.closed_at is None

@pytest.mark.asyncio
async def test_close_real_trade_handles_persistence_error(
    trading_engine_service: TradingEngineService,
    mock_order_execution_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
        requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
        executedPrice=105.0, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.side_effect = Exception("Error de persistencia")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        with pytest.raises(OrderExecutionError) as excinfo: # Esperar OrderExecutionError
            await trading_engine_service._close_real_trade(mock_trade, 105.0, closing_reason) # Pasar executed_price

        assert "Orden real cerrada pero fallo al persistir el trade" in str(excinfo.value)
        mock_logger.error.assert_called_once_with(
            f"Error al persistir el trade REAL cerrado {trade_id}: Error de persistencia"
        )
    
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, f"Error crítico: Trade real cerrado en Binance pero fallo al persistir {trade_id}: Error de persistencia", "CRITICAL"
    )
    assert mock_trade.positionStatus == 'closed' # El trade se marcó como cerrado, pero no se persistió
    assert mock_trade.closingReason == closing_reason
    assert mock_trade.closed_at is not None # Se intentó cerrar

@pytest.mark.asyncio
async def test_close_real_trade_handles_portfolio_update_error(
    trading_engine_service: TradingEngineService,
    mock_order_execution_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
        requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
        executedPrice=105.0, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.return_value = None
    mock_portfolio_service.update_real_portfolio_after_exit.side_effect = Exception("Error al actualizar portafolio")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        # Definir exit_order_details aquí para que esté disponible
        exit_order_details = TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
            executedPrice=105.0, timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        )
        await trading_engine_service._close_real_trade(mock_trade, exit_order_details.executedPrice, closing_reason)

        mock_logger.error.assert_called_once_with(
            f"Error al actualizar portafolio real para trade {trade_id}: Error al actualizar portafolio"
        )
    
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, f"Error crítico al cerrar trade {trade_id} (BTCUSDT): Error al actualizar portafolio", "ERROR"
    )
    assert mock_trade.positionStatus == 'closed'
    assert mock_trade.closingReason == closing_reason
    assert mock_trade.closed_at is not None

@pytest.mark.asyncio
async def test_close_real_trade_handles_notification_error(
    trading_engine_service: TradingEngineService,
    mock_order_execution_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    trade_id = uuid4()
    entry_price = 100.0
    executed_quantity = 1.0
    closing_reason = "TP_HIT"

    mock_trade = Trade(
        id=trade_id, user_id=user_id, mode='real', symbol='BTCUSDT', side='BUY',
        entryOrder=TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type='market', status='filled',
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity, executedPrice=entry_price,
            timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        ),
        positionStatus='open',
        takeProfitPrice=entry_price * 1.10,
        trailingStopActivationPrice=None, trailingStopCallbackRate=None, currentStopPrice_tsl=None,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc), opened_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        opportunityId=None, aiAnalysisConfidence=None, pnl_usd=None, pnl_percentage=None,
        closingReason=None, closed_at=None
    )

    mock_credential_service.get_credential.return_value = MagicMock(encrypted_api_key="key", encrypted_api_secret="secret")
    mock_credential_service.decrypt_data.side_effect = lambda x: x
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
        requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
        executedPrice=105.0, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.return_value = None
    mock_portfolio_service.update_real_portfolio_after_exit.return_value = None
    mock_notification_service.send_real_trade_exit_notification.side_effect = Exception("Error de notificación")

    with patch('src.ultibot_backend.services.trading_engine_service.logger') as mock_logger:
        # Definir exit_order_details aquí para que esté disponible
        exit_order_details = TradeOrderDetails(
            orderId_internal=uuid4(), orderCategory=OrderCategory.MANUAL_CLOSE, type="market", status="filled",
            requestedQuantity=executed_quantity, executedQuantity=executed_quantity,
            executedPrice=105.0, timestamp=datetime.now(timezone.utc),
            exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
            ocoOrderListId=None
        )
        await trading_engine_service._close_real_trade(mock_trade, exit_order_details.executedPrice, closing_reason)

        mock_logger.error.assert_called_once_with(
            f"Error al enviar notificación de cierre para trade {trade_id}: Error de notificación"
        )
    
    # Aunque la notificación falle, el trade debería haberse cerrado y persistido
    assert mock_trade.positionStatus == 'closed'
    assert mock_trade.closingReason == closing_reason
    assert mock_trade.closed_at is not None

@pytest.mark.asyncio
async def test_execute_real_trade_fails_if_opportunity_not_pending_confirmation(
    trading_engine_service: TradingEngineService,
    mock_persistence_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()

    # Simular una oportunidad con un estado incorrecto
    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.NEW, # Estado incorrecto
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    with pytest.raises(ConfigurationError) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "La oportunidad no está en estado PENDING_USER_CONFIRMATION_REAL" in str(excinfo.value)
    mock_persistence_service.get_opportunity_by_id.assert_called_once_with(opportunity_id)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: La oportunidad no está en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: {OpportunityStatus.NEW.value}", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "La oportunidad no está en estado PENDING_USER_CONFIRMATION_REAL. Estado actual: new"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_fails_if_user_config_missing(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity
    mock_config_service.get_user_configuration.return_value = None # Simular que no hay configuración

    with pytest.raises(ConfigurationError) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Configuración de usuario no encontrada para el usuario" in str(excinfo.value)
    mock_config_service.get_user_configuration.assert_called_once_with(user_id)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Configuración de usuario no encontrada para el usuario {user_id}", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, f"Configuración de usuario no encontrada para el usuario {user_id}"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_fails_if_daily_capital_limit_exceeded(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=900.0, # Ya se han arriesgado 900 USD
            last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10, # 10% del capital total
            perTradeCapitalRiskPercentage=0.01, # 1% del capital disponible
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

    # El capital máximo a arriesgar es 10000 * 0.10 = 1000 USD.
    # Ya se arriesgaron 900 USD. El trade actual intentaría arriesgar 10000 * 0.01 = 100 USD.
    # Total arriesgado sería 900 + 100 = 1000 USD, lo que está en el límite.
    # Si el trade actual intentara arriesgar más de 100 USD, fallaría.
    # Para esta prueba, haremos que el capital disponible sea menor para que el 1% exceda el límite.
    mock_portfolio_snapshot.real_trading.available_balance_usdt = 10000.0 # Capital disponible
    mock_user_config.riskProfileSettings.perTradeCapitalRiskPercentage = 0.02 # 2% del capital disponible = 200 USD
    # Esto haría que el total arriesgado sea 900 + 200 = 1100 USD, excediendo el límite de 1000 USD.
    # Asegurarse de que riskProfileSettings no sea None antes de acceder a sus atributos
    if mock_user_config.riskProfileSettings is None:
        mock_user_config.riskProfileSettings = RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10, # Añadir estos valores
            perTradeCapitalRiskPercentage=0.01, # Añadir estos valores
            takeProfitPercentage=TP_PERCENTAGE_DEFAULT,
            trailingStopLossPercentage=TSL_PERCENTAGE_DEFAULT,
            trailingStopCallbackRate=TSL_CALLBACK_RATE_DEFAULT
        )

    with pytest.raises(ConfigurationError) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Excede el límite de capital diario arriesgado" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Excede el límite de capital diario arriesgado.", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Excede el límite de capital diario arriesgado."
    )

@pytest.mark.asyncio
async def test_execute_real_trade_fails_if_capital_to_invest_is_zero_or_negative(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
            perTradeCapitalRiskPercentage=0.01,
            takeProfitPercentage=0.05,
            trailingStopLossPercentage=0.02,
            trailingStopCallbackRate=0.01
        )
    )
    mock_config_service.get_user_configuration.return_value = mock_user_config

    mock_portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(available_balance_usdt=0.0, total_assets_value_usd=0.0, total_portfolio_value_usd=0.0, assets=[], error_message=None), # Capital disponible 0
        paper_trading=PortfolioSummary(available_balance_usdt=10000.0, total_assets_value_usd=0.0, total_portfolio_value_usd=10000.0, assets=[], error_message=None)
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot
    mock_market_data_service.get_latest_price.return_value = current_price

    with pytest.raises(ConfigurationError) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Capital a invertir es cero o negativo" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Capital a invertir es cero o negativo.", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Capital a invertir es cero o negativo."
    )

@pytest.mark.asyncio
async def test_execute_real_trade_handles_market_data_error(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_market_data_service.get_latest_price.side_effect = Exception("Error de datos de mercado")

    with pytest.raises(Exception) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Error de datos de mercado" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Error al obtener precio de mercado para BTCUSDT: Error de datos de mercado", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Error al obtener precio de mercado para BTCUSDT: Error de datos de mercado"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_handles_credential_error(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_credential_service.get_credential.side_effect = Exception("Error de credenciales")

    with pytest.raises(Exception) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Error de credenciales" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Error al obtener credenciales de Binance: Error de credenciales", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Error al obtener credenciales de Binance: Error de credenciales"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_handles_order_execution_error(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_order_execution_service.execute_market_order.side_effect = OrderExecutionError("Fallo de ejecución de orden")

    with pytest.raises(OrderExecutionError) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Fallo de ejecución de orden" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Fallo de ejecución de orden", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Fallo de ejecución de orden"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_handles_persistence_error_after_order(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.side_effect = Exception("Error al persistir trade")

    with pytest.raises(Exception) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Error al persistir trade" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Error al persistir el trade: Error al persistir trade", 
        "ERROR"
    )
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Error al persistir el trade: Error al persistir trade"
    )

@pytest.mark.asyncio
async def test_execute_real_trade_handles_opportunity_status_update_error(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.return_value = None
    mock_persistence_service.update_opportunity_status.side_effect = Exception("Error al actualizar estado de oportunidad")

    with pytest.raises(Exception) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Error al actualizar estado de oportunidad" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Error al actualizar el estado de la oportunidad: Error al actualizar estado de oportunidad", 
        "ERROR"
    )
    # No se llama a update_opportunity_status con EXECUTION_FAILED porque el error ya ocurrió
    mock_persistence_service.update_opportunity_status.assert_called_once()

@pytest.mark.asyncio
async def test_execute_real_trade_handles_config_save_error(
    trading_engine_service: TradingEngineService,
    mock_config_service: AsyncMock,
    mock_persistence_service: AsyncMock,
    mock_portfolio_service: AsyncMock,
    mock_market_data_service: AsyncMock,
    mock_credential_service: AsyncMock,
    mock_order_execution_service: AsyncMock,
    mock_notification_service: AsyncMock
):
    user_id = uuid4()
    opportunity_id = uuid4()
    current_price = 100.0
    requested_quantity_calculated = 0.1

    mock_opportunity = Opportunity(
        id=opportunity_id, user_id=user_id, symbol="BTCUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY", calculatedConfidence=0.98,
            reasoning_ai=None, rawAiOutput=None, dataVerification=None, ai_model_used=None
        ),
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = mock_opportunity

    mock_user_config = UserConfiguration(
        user_id=user_id, paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True, max_real_trades=5, real_trades_executed_count=0,
            daily_capital_risked_usd=0.0, last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.10,
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
    mock_order_execution_service.execute_market_order.return_value = TradeOrderDetails(
        orderId_internal=uuid4(), orderCategory=OrderCategory.ENTRY, type="market", status="filled",
        requestedQuantity=requested_quantity_calculated, executedQuantity=requested_quantity_calculated,
        executedPrice=current_price, timestamp=datetime.now(timezone.utc),
        exchangeOrderId=None, commission=None, commissionAsset=None, rawResponse=None,
        ocoOrderListId=None
    )
    mock_persistence_service.upsert_trade.return_value = None
    mock_persistence_service.update_opportunity_status.return_value = None
    mock_config_service.save_user_configuration.side_effect = Exception("Error al guardar configuración")

    with pytest.raises(Exception) as excinfo:
        await trading_engine_service.execute_real_trade(opportunity_id, user_id)

    assert "Error al guardar configuración" in str(excinfo.value)
    mock_notification_service.send_real_trade_status_notification.assert_called_once_with(
        user_id, 
        f"Error al ejecutar trade real para oportunidad {opportunity_id}: Error al actualizar la configuración del usuario: Error al guardar configuración", 
        "ERROR"
    )
    mock_config_service.save_user_configuration.assert_called_once()

</final_file_content>

IMPORTANT: For any future changes to this file, use the final_file_content shown above as your reference. This content reflects the current state of the file, including any auto-formatting (e.g., if you used single quotes but the formatter converted them to double quotes). Always base your SEARCH/REPLACE operations on this final version to ensure accuracy.



New problems detected after saving the file:
tests/unit/services/test_trading_engine_service.py
- [Pylance Error] Line 1383: "perTradeCapitalRiskPercentage" is not a known attribute of "None"<environment_details>
# VSCode Visible Files
tests/unit/services/test_trading_engine_service.py

# VSCode Open Tabs
../OneDrive/Documentos/Cline/Rules/limitar_tokens_350k_newtask.md
.clinerules/workspace.rules.md
src/ultibot_backend/services/portfolio_service.py
src/ultibot_backend/services/notification_service.py
pyproject.toml
tests/unit/services/test_trading_report_service.py
.clinerules/limitar_tokens_350k_newtask.md
.clinerules/token-limit.md
docs/stories/4.4.story.md
src/ultibot_backend/main.py
src/ultibot_backend/adapters/binance_adapter.py
src/shared/data_types.py
src/ultibot_backend/services/trading_engine_service.py
src/ultibot_backend/adapters/persistence_service.py
tests/unit/services/test_trading_engine_service.py
tests/unit/adapters/test_binance_adapter.py
tests/unit/adapters/test_persistence_service.py

# Current Time
5/31/2025, 3:57:15 PM (America/La_Paz, UTC-4:00)

# Context Window Usage
789,452 / 1,048.576K tokens used (75%)

# Current Mode
ACT MODE
</environment_details>
