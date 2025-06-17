import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.ultibot_backend.services.order_execution_service import OrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter

from src.shared.data_types import (
    Opportunity, AIAnalysis, UserConfiguration, RealTradingSettings, RiskProfileSettings,
    TradeOrderDetails, Trade, OpportunityStatus, OpportunitySourceType, ServiceName,
    PortfolioSnapshot, PortfolioSummary, OrderCategory, APICredential
)


@pytest.mark.asyncio
async def test_complete_real_trading_flow_with_capital_management():
    """
    Test de integración para el flujo completo de operación real con gestión de capital y TSL/TP.
    
    Este test simula el flujo completo desde la confirmación de una oportunidad hasta la 
    ejecución del trade real con TSL/TP, verificando:
    - Gestión de capital (límites diarios y por operación)
    - Ejecución de orden de entrada
    - Configuración de TSL/TP con órdenes OCO
    - Actualización de contadores y configuración
    - Persistencia de datos
    """
    from src.ultibot_backend.services.trading_engine_service import TradingEngineService
    from src.ultibot_backend.services.config_service import ConfigService
    # Setup de servicios simulados
    mock_config_service = AsyncMock(spec=ConfigService)
    mock_order_execution_service = AsyncMock(spec=OrderExecutionService)
    mock_paper_order_execution_service = AsyncMock()
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_binance_adapter = AsyncMock(spec=BinanceAdapter)

    trading_engine = TradingEngineService(
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

    # Datos del test
    user_id = uuid4()
    opportunity_id = uuid4()
    symbol = "BTCUSDT"
    current_price = 60000.0
    
    # 1. Setup de la oportunidad pendiente de confirmación
    opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol=symbol,
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY",
            calculatedConfidence=0.98,
            reasoning_ai="Strong bullish signals detected",
            rawAiOutput=None,
            dataVerification=None,
            ai_model_used="gemini-1.5-pro"
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = opportunity

    # 2. Setup de configuración del usuario con gestión de capital
    user_config = UserConfiguration(
        user_id=user_id,
        paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=1,  # Ya tiene 1 trade ejecutado
            daily_capital_risked_usd=1000.0,  # Ya arriesgó 1000 USD hoy
            last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.50,  # 50% límite diario
            perTradeCapitalRiskPercentage=0.02,  # 2% por trade
            takeProfitPercentage=0.03,  # 3% TP
            trailingStopLossPercentage=0.015,  # 1.5% TSL
            trailingStopCallbackRate=0.005  # 0.5% callback
        )
    )
    mock_config_service.get_user_configuration.return_value = user_config

    # 3. Setup del portafolio con capital real
    portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(
            available_balance_usdt=8000.0,  # 8000 USDT disponibles
            total_assets_value_usd=2000.0,  # 2000 USD en activos
            total_portfolio_value_usd=10000.0,  # 10000 USD total
            assets=[],
            error_message=None
        ),
        paper_trading=PortfolioSummary(
            available_balance_usdt=15000.0,
            total_assets_value_usd=0.0,
            total_portfolio_value_usd=15000.0,
            assets=[],
            error_message=None
        )
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

    # 4. Setup de datos de mercado
    mock_market_data_service.get_latest_price.return_value = current_price

    # 5. Setup de credenciales
    mock_credential = APICredential(
        id=uuid4(),
        user_id=user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot",
        encrypted_api_key="encrypted_key",
        encrypted_api_secret="encrypted_secret",
        status="active",
        last_verified_at=datetime.now(timezone.utc),
        permissions=["SPOT_TRADING"]
    )
    mock_credential_service.get_credential.return_value = mock_credential
    mock_credential_service.decrypt_data.side_effect = lambda x: x.replace("encrypted_", "")

    # 6. Setup de orden de entrada ejecutada
    executed_quantity = 0.0026667  # ~160 USD (2% de 8000 USD)
    entry_order = TradeOrderDetails(
        orderId_internal=uuid4(),
        orderId_exchange="12345678",
        clientOrderId_exchange="client_12345",
        orderCategory=OrderCategory.ENTRY,
        type="market",
        status="filled",
        requestedPrice=current_price,
        requestedQuantity=executed_quantity,
        executedQuantity=executed_quantity,
        executedPrice=current_price,
        cumulativeQuoteQty=executed_quantity * current_price,
        commissions=[{"amount": 0.001, "asset": "USDT"}],
        commission=0.001,
        commissionAsset="USDT",
        timestamp=datetime.now(timezone.utc),
        submittedAt=datetime.now(timezone.utc),
        fillTimestamp=datetime.now(timezone.utc),
        rawResponse={"orderId": "12345678"},
        ocoOrderListId=None
    )
    mock_order_execution_service.execute_market_order.return_value = entry_order

    # 7. Setup de órdenes OCO para TSL/TP
    oco_response = {
        "listClientOrderId": "oco_list_123",
        "listStatusType": "EXECUTING",
        "orderReports": [
            {
                "orderId": "87654321",
                "clientOrderId": "tp_order_123",
                "type": "TAKE_PROFIT_LIMIT",
                "status": "NEW",
                "origQty": str(executed_quantity),
                "executedQty": "0.0",
                "price": str(current_price * 1.03),  # TP al 3%
                "commission": "0.0",
                "commissionAsset": "USDT",
                "updateTime": int(datetime.now(timezone.utc).timestamp() * 1000)
            },
            {
                "orderId": "87654322",
                "clientOrderId": "sl_order_123",
                "type": "STOP_LOSS_LIMIT",
                "status": "NEW",
                "origQty": str(executed_quantity),
                "executedQty": "0.0",
                "price": str(current_price * 0.985),  # SL al 1.5%
                "commission": "0.0",
                "commissionAsset": "USDT",
                "updateTime": int(datetime.now(timezone.utc).timestamp() * 1000)
            }
        ]
    }
    mock_binance_adapter.create_oco_order.return_value = oco_response

    # 8. Ejecutar el flujo completo
    result_trade = await trading_engine.execute_real_trade(opportunity_id, user_id)

    # 9. Verificaciones del flujo completo

    # 9.1 Verificar que se obtuvo la oportunidad correctamente
    mock_persistence_service.get_opportunity_by_id.assert_called_once_with(opportunity_id)

    # 9.2 Verificar que se obtuvo la configuración del usuario
    mock_config_service.get_user_configuration.assert_called_once_with(user_id)

    # 9.3 Verificar que se obtuvo el snapshot del portafolio para gestión de capital
    mock_portfolio_service.get_portfolio_snapshot.assert_called_once_with(user_id)

    # 9.4 Verificar cálculos de gestión de capital
    expected_capital_to_invest = 8000.0 * 0.02  # 2% de 8000 = 160 USD
    expected_daily_limit = 10000.0 * 0.50  # 50% de 10000 = 5000 USD
    expected_new_total_risked = 1000.0 + expected_capital_to_invest  # 1160 USD total
    
    assert expected_new_total_risked < expected_daily_limit, "El test debe estar dentro del límite diario"

    # 9.5 Verificar que se obtuvo el precio de mercado
    mock_market_data_service.get_latest_price.assert_called_once_with(symbol)

    # 9.6 Verificar que se obtuvieron las credenciales
    mock_credential_service.get_credential.assert_called_once_with(
        user_id=user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot"
    )

    # 9.7 Verificar que se ejecutó la orden de entrada
    mock_order_execution_service.execute_market_order.assert_called_once()
    call_args = mock_order_execution_service.execute_market_order.call_args
    assert call_args.kwargs["symbol"] == symbol
    assert call_args.kwargs["side"] == "BUY"
    assert abs(call_args.kwargs["quantity"] - expected_capital_to_invest / current_price) < 0.000001

    # 9.8 Verificar que se crearon las órdenes OCO para TSL/TP
    mock_binance_adapter.create_oco_order.assert_called_once()
    oco_call_args = mock_binance_adapter.create_oco_order.call_args
    assert oco_call_args.kwargs["symbol"] == symbol
    assert oco_call_args.kwargs["side"] == "SELL"  # Lado opuesto para cierre
    assert oco_call_args.kwargs["quantity"] == executed_quantity

    # 9.9 Verificar que se persistió el trade
    mock_persistence_service.upsert_trade.assert_called_once()
    
    # 9.10 Verificar que se actualizó el estado de la oportunidad
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.CONVERTED_TO_TRADE_REAL, pytest.approx(f"Convertida a trade real: {result_trade.id}", abs=0)
    )

    # 9.11 Verificar que se actualizó la configuración del usuario
    mock_config_service.save_user_configuration.assert_called_once()
    saved_config = mock_config_service.save_user_configuration.call_args[0][0]
    assert saved_config.realTradingSettings.real_trades_executed_count == 2  # Incrementó de 1 a 2
    assert abs(saved_config.realTradingSettings.daily_capital_risked_usd - expected_new_total_risked) < 0.01

    # 9.12 Verificar propiedades del trade resultante
    assert result_trade.user_id == user_id
    assert result_trade.mode == "real"
    assert result_trade.symbol == symbol
    assert result_trade.side == "BUY"
    assert result_trade.positionStatus == "open"
    assert result_trade.entryOrder == entry_order
    assert result_trade.ocoOrderListId == "oco_list_123"
    
    # 9.13 Verificar cálculos de TSL/TP
    expected_tp_price = current_price * 1.03  # 3% ganancia
    expected_tsl_activation = current_price * 0.985  # 1.5% pérdida inicial
    
    assert abs(result_trade.takeProfitPrice - expected_tp_price) < 0.01
    assert abs(result_trade.trailingStopActivationPrice - expected_tsl_activation) < 0.01
    assert result_trade.trailingStopCallbackRate == 0.005
    assert abs(result_trade.currentStopPrice_tsl - expected_tsl_activation) < 0.01

    # 9.14 Verificar que se enviaron notificaciones
    assert mock_notification_service.send_real_trade_status_notification.call_count >= 2


@pytest.mark.asyncio
async def test_complete_real_trading_flow_capital_limit_exceeded():
    """
    Test de integración que verifica el comportamiento cuando se excede el límite de capital diario.
    """
    from src.ultibot_backend.services.trading_engine_service import TradingEngineService
    from src.ultibot_backend.services.config_service import ConfigService
    # Setup básico similar al test anterior
    mock_config_service = AsyncMock(spec=ConfigService)
    mock_order_execution_service = AsyncMock(spec=OrderExecutionService)
    mock_paper_order_execution_service = AsyncMock()
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_binance_adapter = AsyncMock(spec=BinanceAdapter)

    trading_engine = TradingEngineService(
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

    user_id = uuid4()
    opportunity_id = uuid4()
    
    # Configurar oportunidad
    opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol="ETHUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY",
            calculatedConfidence=0.96,
            reasoning_ai="Strong momentum",
            rawAiOutput=None,
            dataVerification=None,
            ai_model_used="gemini-1.5-pro"
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = opportunity

    # Configurar usuario con límite de capital casi alcanzado
    user_config = UserConfiguration(
        user_id=user_id,
        paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=2,
            daily_capital_risked_usd=4800.0,  # Ya arriesgó 4800 USD (96% del límite de 5000)
            last_daily_reset=datetime.now(timezone.utc)
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.50,  # 50% límite diario = 5000 USD
            perTradeCapitalRiskPercentage=0.03,  # 3% por trade = 300 USD (excedería el límite)
            takeProfitPercentage=0.025,
            trailingStopLossPercentage=0.015,
            trailingStopCallbackRate=0.005
        )
    )
    mock_config_service.get_user_configuration.return_value = user_config

    # Configurar portafolio
    portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(
            available_balance_usdt=10000.0,
            total_assets_value_usd=0.0,
            total_portfolio_value_usd=10000.0,
            assets=[],
            error_message=None
        ),
        paper_trading=PortfolioSummary(
            available_balance_usdt=15000.0,
            total_assets_value_usd=0.0,
            total_portfolio_value_usd=15000.0,
            assets=[],
            error_message=None
        )
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

    # Configurar precio de mercado
    mock_market_data_service.get_latest_price.return_value = 3000.0

    # Ejecutar y verificar que se lanza excepción por límite excedido
    with pytest.raises(Exception) as exc_info:
        await trading_engine.execute_real_trade(opportunity_id, user_id)
    
    assert "Límite de riesgo de capital diario excedido" in str(exc_info.value)

    # Verificar que se actualizó el estado de la oportunidad a EXECUTION_FAILED
    mock_persistence_service.update_opportunity_status.assert_called_once_with(
        opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Límite de riesgo de capital diario excedido."
    )

    # Verificar que se envió notificación de error
    mock_notification_service.send_real_trade_status_notification.assert_called_once()
    notification_call = mock_notification_service.send_real_trade_status_notification.call_args
    assert "Límite de riesgo de capital diario excedido" in notification_call[0][1]
    assert notification_call[0][2] == "ERROR"

    # Verificar que NO se ejecutó ninguna orden
    mock_order_execution_service.execute_market_order.assert_not_called()
    mock_binance_adapter.create_oco_order.assert_not_called()


@pytest.mark.asyncio  
async def test_complete_real_trading_tsl_monitoring_and_execution():
    """
    Test de integración para el monitoreo y ejecución de TSL/TP en operaciones reales.
    
    Simula un trade real abierto y el monitoreo que detecta la ejecución del TSL.
    """
    from src.ultibot_backend.services.trading_engine_service import TradingEngineService
    from src.ultibot_backend.services.config_service import ConfigService
    # Setup de servicios
    mock_config_service = AsyncMock(spec=ConfigService)
    mock_order_execution_service = AsyncMock(spec=OrderExecutionService)
    mock_paper_order_execution_service = AsyncMock()
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_binance_adapter = AsyncMock(spec=BinanceAdapter)

    trading_engine = TradingEngineService(
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

    user_id = uuid4()
    trade_id = uuid4()
    
    # Crear un trade real abierto con TSL configurado
    entry_order = TradeOrderDetails(
        orderId_internal=uuid4(),
        orderId_exchange="12345678",
        orderCategory=OrderCategory.ENTRY,
        type="market",
        status="filled",
        requestedQuantity=0.001,
        executedQuantity=0.001,
        executedPrice=60000.0,
        timestamp=datetime.now(timezone.utc),
        rawResponse=None,
        ocoOrderListId=None
    )

    trade = Trade(
        id=trade_id,
        user_id=user_id,
        mode="real",
        symbol="BTCUSDT",
        side="BUY",
        entryOrder=entry_order,
        exitOrders=[],
        positionStatus="open",
        ocoOrderListId="oco_list_456",
        takeProfitPrice=61800.0,  # 3% ganancia
        trailingStopActivationPrice=59400.0,  # 1% pérdida inicial
        trailingStopCallbackRate=0.005,  # 0.5% callback
        currentStopPrice_tsl=59400.0,
        riskRewardAdjustments=[],
        created_at=datetime.now(timezone.utc),
        opened_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        closed_at=None
    )

    # Simular que la orden OCO fue ejecutada (TSL hit)
    oco_status_response = {
        "listStatusType": "ALL_DONE",
        "orderReports": [
            {
                "orderId": "87654321",
                "clientOrderId": "tp_order_456",
                "type": "TAKE_PROFIT_LIMIT",
                "status": "CANCELED",  # TP cancelado porque se ejecutó SL
                "origQty": "0.001",
                "executedQty": "0.0",
                "price": "61800.0",
                "updateTime": int(datetime.now(timezone.utc).timestamp() * 1000)
            },
            {
                "orderId": "87654322",
                "clientOrderId": "sl_order_456", 
                "type": "STOP_LOSS_LIMIT",
                "status": "FILLED",  # SL ejecutado
                "origQty": "0.001",
                "executedQty": "0.001",
                "price": "59400.0",
                "commission": "0.0001",
                "commissionAsset": "USDT",
                "cummulativeQuoteQty": "59.4",
                "updateTime": int(datetime.now(timezone.utc).timestamp() * 1000)
            }
        ]
    }
    mock_binance_adapter.get_oco_order_by_list_client_order_id.return_value = oco_status_response

    # Setup de credenciales para el monitoreo
    mock_credential = APICredential(
        id=uuid4(),
        user_id=user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot",
        encrypted_api_key="encrypted_key",
        encrypted_api_secret="encrypted_secret",
        status="active",
        last_verified_at=datetime.now(timezone.utc),
        permissions=["SPOT_TRADING"]
    )
    mock_credential_service.get_credential.return_value = mock_credential
    mock_credential_service.decrypt_data.side_effect = lambda x: x.replace("encrypted_", "")

    # Ejecutar el monitoreo de órdenes OCO
    await trading_engine._monitor_binance_oco_orders(trade, "key", "secret")

    # Verificaciones

    # 1. Verificar que se consultó el estado de la orden OCO
    mock_binance_adapter.get_oco_order_by_list_client_order_id.assert_called_once_with(
        api_key="key",
        api_secret="secret", 
        listClientOrderId="oco_list_456"
    )

    # 2. Verificar que se detectó correctamente la ejecución del SL
    assert trade.positionStatus == "closed"
    assert trade.closingReason == "SL_HIT"
    assert trade.closed_at is not None

    # 3. Verificar que se calculó el P&L correctamente
    # BUY: PnL = (exit_value - entry_value) = (59.4 - 60.0) = -0.6 USD
    expected_pnl = 59.4 - 60.0  # exit_value - entry_value para BUY
    assert abs(trade.pnl_usd - expected_pnl) < 0.01
    assert trade.pnl_percentage < 0  # Debe ser pérdida

    # 4. Verificar que se añadió la orden de salida al trade
    assert len(trade.exitOrders) == 1
    exit_order = trade.exitOrders[0]
    assert exit_order.orderCategory == OrderCategory.STOP_LOSS
    assert exit_order.status == "filled"
    assert exit_order.executedPrice == 59400.0

    # 5. Verificar que se persistió el trade actualizado
    mock_persistence_service.upsert_trade.assert_called_once_with(
        trade.user_id, trade.model_dump(mode='json', by_alias=True, exclude_none=True)
    )

    # 6. Verificar que se actualizó el portafolio
    mock_portfolio_service.update_real_portfolio_after_exit.assert_called_once_with(trade)

    # 7. Verificar que se envió notificación
    mock_notification_service.send_real_trade_exit_notification.assert_called_once_with(trade)


@pytest.mark.asyncio
async def test_capital_management_daily_reset():
    """
    Test que verifica el reinicio automático del capital diario arriesgado.
    """
    from src.ultibot_backend.services.trading_engine_service import TradingEngineService
    from src.ultibot_backend.services.config_service import ConfigService
    mock_config_service = AsyncMock(spec=ConfigService)
    mock_order_execution_service = AsyncMock(spec=OrderExecutionService)
    mock_paper_order_execution_service = AsyncMock()
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_binance_adapter = AsyncMock(spec=BinanceAdapter)

    trading_engine = TradingEngineService(
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

    user_id = uuid4()
    opportunity_id = uuid4()

    # Configurar oportunidad
    opportunity = Opportunity(
        id=opportunity_id,
        user_id=user_id,
        symbol="ADAUSDT",
        source_type=OpportunitySourceType.AI_GENERATED,
        status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
        ai_analysis=AIAnalysis(
            suggestedAction="BUY",
            calculatedConfidence=0.97,
            reasoning_ai="Technical breakout",
            rawAiOutput=None,
            dataVerification=None,
            ai_model_used="gemini-1.5-pro"
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    mock_persistence_service.get_opportunity_by_id.return_value = opportunity

    # Configurar usuario con fecha de último reinicio diferente (día anterior)
    yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = yesterday.replace(day=yesterday.day - 1)
    
    user_config = UserConfiguration(
        user_id=user_id,
        paperTradingActive=False,
        realTradingSettings=RealTradingSettings(
            real_trading_mode_active=True,
            max_real_trades=5,
            real_trades_executed_count=0,
            daily_capital_risked_usd=2000.0,  # Debería reiniciarse a 0
            last_daily_reset=yesterday  # Fecha anterior
        ),
        riskProfileSettings=RiskProfileSettings(
            dailyCapitalRiskPercentage=0.50,
            perTradeCapitalRiskPercentage=0.02,
            takeProfitPercentage=0.025,
            trailingStopLossPercentage=0.015,
            trailingStopCallbackRate=0.005
        )
    )
    mock_config_service.get_user_configuration.return_value = user_config

    # Setup de mocks restantes para completar el flujo
    portfolio_snapshot = PortfolioSnapshot(
        real_trading=PortfolioSummary(
            available_balance_usdt=5000.0,
            total_assets_value_usd=0.0,
            total_portfolio_value_usd=5000.0,
            assets=[],
            error_message=None
        ),
        paper_trading=PortfolioSummary(
            available_balance_usdt=15000.0,
            total_assets_value_usd=0.0,
            total_portfolio_value_usd=15000.0,
            assets=[],
            error_message=None
        )
    )
    mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

    mock_market_data_service.get_latest_price.return_value = 0.50
    
    mock_credential = APICredential(
        id=uuid4(),
        user_id=user_id,
        service_name=ServiceName.BINANCE_SPOT,
        credential_label="default_binance_spot",
        encrypted_api_key="encrypted_key",
        encrypted_api_secret="encrypted_secret",
        status="active",
        last_verified_at=datetime.now(timezone.utc),
        permissions=["SPOT_TRADING"]
    )
    mock_credential_service.get_credential.return_value = mock_credential
    mock_credential_service.decrypt_data.side_effect = lambda x: x.replace("encrypted_", "")

    entry_order = TradeOrderDetails(
        orderId_internal=uuid4(),
        orderCategory=OrderCategory.ENTRY,
        type="market",
        status="filled",
        requestedQuantity=200.0,
        executedQuantity=200.0,
        executedPrice=0.50,
        timestamp=datetime.now(timezone.utc),
        rawResponse=None,
        ocoOrderListId=None
    )
    mock_order_execution_service.execute_market_order.return_value = entry_order

    oco_response = {
        "listClientOrderId": "oco_reset_test",
        "orderReports": []
    }
    mock_binance_adapter.create_oco_order.return_value = oco_response

    # Ejecutar el trade
    result_trade = await trading_engine.execute_real_trade(opportunity_id, user_id)

    # Verificaciones

    # 1. Verificar que la configuración se guardó (indicando que hubo reset)
    mock_config_service.save_user_configuration.assert_called()
    saved_configs = [call[0][0] for call in mock_config_service.save_user_configuration.call_args_list]
    
    # 2. Encontrar la configuración después del reset (primera llamada)
    reset_config = saved_configs[0]
    assert reset_config.realTradingSettings.daily_capital_risked_usd == 0.0
    assert reset_config.realTradingSettings.last_daily_reset.date() == datetime.now(timezone.utc).date()

    # 3. Verificar la configuración final después del trade
    final_config = saved_configs[-1]
    expected_capital_invested = 5000.0 * 0.02  # 2% de 5000 = 100 USD
    assert abs(final_config.realTradingSettings.daily_capital_risked_usd - expected_capital_invested) < 0.01

    # 4. Verificar que el trade se ejecutó correctamente
    assert result_trade is not None
    assert result_trade.mode == "real"
    assert result_trade.user_id == user_id
