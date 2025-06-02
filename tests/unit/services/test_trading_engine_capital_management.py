import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta

from src.ultibot_backend.services.trading_engine_service import TradingEngineService
from src.ultibot_backend.services.config_service import ConfigService
from src.ultibot_backend.services.order_execution_service import OrderExecutionService
from src.ultibot_backend.services.credential_service import CredentialService
from src.ultibot_backend.services.market_data_service import MarketDataService
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.notification_service import NotificationService
from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
from src.ultibot_backend.core.exceptions import OrderExecutionError

from src.shared.data_types import (
    UserConfiguration, RealTradingSettings, RiskProfileSettings,
    PortfolioSnapshot, PortfolioSummary, Opportunity, AIAnalysis,
    OpportunityStatus, OpportunitySourceType
)


@pytest.fixture
def trading_engine_service():
    """Fixture que crea una instancia de TradingEngineService con mocks."""
    mock_config_service = AsyncMock(spec=ConfigService)
    mock_order_execution_service = AsyncMock(spec=OrderExecutionService)
    mock_paper_order_execution_service = AsyncMock()
    mock_credential_service = AsyncMock(spec=CredentialService)
    mock_market_data_service = AsyncMock(spec=MarketDataService)
    mock_portfolio_service = AsyncMock(spec=PortfolioService)
    mock_persistence_service = AsyncMock(spec=SupabasePersistenceService)
    mock_notification_service = AsyncMock(spec=NotificationService)
    mock_binance_adapter = AsyncMock(spec=BinanceAdapter)

    service = TradingEngineService(
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
    
    # Attachar los mocks al servicio para fácil acceso en tests
    service._mock_config_service = mock_config_service
    service._mock_portfolio_service = mock_portfolio_service
    service._mock_persistence_service = mock_persistence_service
    service._mock_notification_service = mock_notification_service
    service._mock_market_data_service = mock_market_data_service
    
    return service


@pytest.mark.asyncio
class TestCapitalManagementLogic:
    """Tests unitarios específicos para la lógica de gestión de capital."""

    async def test_daily_capital_risk_calculation_basic(self, trading_engine_service):
        """Test básico del cálculo de riesgo de capital diario."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="BTCUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.98,
                reasoning_ai="Test",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración con valores específicos para el test
        user_config = UserConfiguration(
            user_id=user_id,
            paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True,
                max_real_trades=10,
                real_trades_executed_count=3,
                daily_capital_risked_usd=1500.0,  # Ya arriesgó 1500 USD
                last_daily_reset=datetime.now(timezone.utc)
            ),
            riskProfileSettings=RiskProfileSettings(
                dailyCapitalRiskPercentage=0.40,  # 40% límite diario
                perTradeCapitalRiskPercentage=0.025,  # 2.5% por trade
                takeProfitPercentage=0.03,
                trailingStopLossPercentage=0.015,
                trailingStopCallbackRate=0.005
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Portafolio con capital total conocido
        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=7000.0,  # Disponible
                total_assets_value_usd=3000.0,  # En activos
                total_portfolio_value_usd=10000.0,  # Total = 10000 USD
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        # Precio de mercado
        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 50000.0

        # Cálculos esperados:
        # - Capital total: 10000 USD
        # - Límite diario (40%): 4000 USD  
        # - Ya arriesgado: 1500 USD
        # - Capital disponible para trade: 7000 USD
        # - Capital para este trade (2.5% de disponible): 175 USD
        # - Total después del trade: 1500 + 175 = 1675 USD (< 4000 límite) ✓

        # Ejecutar hasta el punto donde se calcula el capital (simulamos que falla en credenciales)
        trading_engine_service._mock_credential_service.get_credential.return_value = None

        with pytest.raises(Exception) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # La excepción debe ser por credenciales, no por límite de capital
        assert "credenciales" in str(exc_info.value).lower()

        # Verificar que se obtuvieron los datos necesarios para el cálculo
        trading_engine_service._mock_config_service.get_user_configuration.assert_called_once_with(user_id)
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.assert_called_once_with(user_id)

    async def test_daily_capital_limit_boundary_conditions(self, trading_engine_service):
        """Test de condiciones límite para el capital diario."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="ETHUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="SELL",
                calculatedConfidence=0.96,
                reasoning_ai="Test boundary",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración que llevará exactamente al límite
        user_config = UserConfiguration(
            user_id=user_id,
            paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True,
                max_real_trades=5,
                real_trades_executed_count=1,
                daily_capital_risked_usd=2400.0,  # Ya arriesgó 2400 USD
                last_daily_reset=datetime.now(timezone.utc)
            ),
            riskProfileSettings=RiskProfileSettings(
                dailyCapitalRiskPercentage=0.50,  # 50% límite diario = 2500 USD
                perTradeCapitalRiskPercentage=0.02,  # 2% por trade = 100 USD
                takeProfitPercentage=0.025,
                trailingStopLossPercentage=0.01,
                trailingStopCallbackRate=0.005
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Capital total que permite exactamente 100 USD más (2400 + 100 = 2500 = límite)
        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=5000.0,  # 2% de 5000 = 100 USD
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=5000.0,  # Límite diario = 2500 USD
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 3000.0

        # Este trade debería ser permitido exactamente (2400 + 100 = 2500 = límite)
        # Simular fallo en credenciales para verificar que llega hasta el cálculo de capital
        trading_engine_service._mock_credential_service.get_credential.return_value = None

        with pytest.raises(Exception) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # Debe fallar por credenciales, no por capital
        assert "credenciales" in str(exc_info.value).lower()

        # Ahora probar con 1 USD adicional que excedería el límite
        user_config.realTradingSettings.daily_capital_risked_usd = 2401.0  # 2401 + 100 = 2501 > 2500

        with pytest.raises(OrderExecutionError) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # Ahora debe fallar por límite de capital
        assert "Límite de riesgo de capital diario excedido" in str(exc_info.value)

    async def test_daily_capital_reset_edge_cases(self, trading_engine_service):
        """Test de casos edge para el reinicio del capital diario."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="ADAUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.99,
                reasoning_ai="Test reset edge case",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Test case 1: Último reset hace exactamente 24 horas
        exactly_24h_ago = datetime.now(timezone.utc) - timedelta(hours=24, minutes=0, seconds=1)
        
        user_config = UserConfiguration(
            user_id=user_id,
            paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True,
                max_real_trades=5,
                real_trades_executed_count=0,
                daily_capital_risked_usd=1000.0,  # Debería reiniciarse
                last_daily_reset=exactly_24h_ago
            ),
            riskProfileSettings=RiskProfileSettings(
                dailyCapitalRiskPercentage=0.50,
                perTradeCapitalRiskPercentage=0.01,
                takeProfitPercentage=0.02,
                trailingStopLossPercentage=0.01,
                trailingStopCallbackRate=0.005
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=2000.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=2000.0,
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 0.40

        # Simular fallo después del reset para verificar que ocurrió
        trading_engine_service._mock_credential_service.get_credential.return_value = None

        with pytest.raises(Exception):
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # Verificar que se guardó la configuración (indica que hubo reset)
        trading_engine_service._mock_config_service.save_user_configuration.assert_called()
        saved_config = trading_engine_service._mock_config_service.save_user_configuration.call_args[0][0]
        
        # El capital debería haberse reiniciado a 0
        assert saved_config.realTradingSettings.daily_capital_risked_usd == 0.0
        assert saved_config.realTradingSettings.last_daily_reset.date() == datetime.now(timezone.utc).date()

    async def test_capital_calculation_with_zero_available_balance(self, trading_engine_service):
        """Test del comportamiento cuando el saldo disponible es cero."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="DOTUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.97,
                reasoning_ai="Test zero balance",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración válida
        user_config = UserConfiguration(
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
                perTradeCapitalRiskPercentage=0.05,  # 5% - normalmente sería válido
                takeProfitPercentage=0.02,
                trailingStopLossPercentage=0.01,
                trailingStopCallbackRate=0.005
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Portafolio con saldo disponible cero
        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=0.0,  # Sin saldo disponible
                total_assets_value_usd=5000.0,  # Pero con activos
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 25.0

        # Debe fallar por capital insuficiente
        with pytest.raises(OrderExecutionError) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        assert "Capital insuficiente para la operación real" in str(exc_info.value)

        # Verificar que se actualizó el estado de la oportunidad
        trading_engine_service._mock_persistence_service.update_opportunity_status.assert_called_once_with(
            opportunity_id, OpportunityStatus.EXECUTION_FAILED, "Capital insuficiente para la operación real."
        )

    async def test_capital_calculation_with_extreme_percentages(self, trading_engine_service):
        """Test con porcentajes extremos de gestión de capital."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="SOLUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.98,
                reasoning_ai="Test extreme percentages",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración con porcentajes muy pequeños
        user_config = UserConfiguration(
            user_id=user_id,
            paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True,
                max_real_trades=100,
                real_trades_executed_count=0,
                daily_capital_risked_usd=0.0,
                last_daily_reset=datetime.now(timezone.utc)
            ),
            riskProfileSettings=RiskProfileSettings(
                dailyCapitalRiskPercentage=0.95,  # 95% límite diario (extremo alto)
                perTradeCapitalRiskPercentage=0.001,  # 0.1% por trade (extremo bajo)
                takeProfitPercentage=0.01,
                trailingStopLossPercentage=0.005,
                trailingStopCallbackRate=0.002
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Portafolio grande
        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=100000.0,  # 100k disponible
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=100000.0,
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 120.0

        # Cálculos esperados:
        # - Capital total: 100,000 USD
        # - Límite diario (95%): 95,000 USD
        # - Capital para trade (0.1% de 100k): 100 USD
        # - Cantidad: 100 / 120 = 0.833... tokens

        # Simular fallo en credenciales para verificar que los cálculos son correctos
        trading_engine_service._mock_credential_service.get_credential.return_value = None

        with pytest.raises(Exception) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # Debe fallar por credenciales, no por capital (verificando que los cálculos extremos funcionan)
        assert "credenciales" in str(exc_info.value).lower()

    async def test_max_real_trades_limit_enforcement(self, trading_engine_service):
        """Test del cumplimiento del límite máximo de trades reales."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="LINKUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.99,
                reasoning_ai="Test max trades limit",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración en el límite máximo de trades
        user_config = UserConfiguration(
            user_id=user_id,
            paperTradingActive=False,
            realTradingSettings=RealTradingSettings(
                real_trading_mode_active=True,
                max_real_trades=3,  # Límite máximo
                real_trades_executed_count=3,  # Ya alcanzó el límite
                daily_capital_risked_usd=100.0,
                last_daily_reset=datetime.now(timezone.utc)
            ),
            riskProfileSettings=RiskProfileSettings(
                dailyCapitalRiskPercentage=0.50,
                perTradeCapitalRiskPercentage=0.05,
                takeProfitPercentage=0.025,
                trailingStopLossPercentage=0.015,
                trailingStopCallbackRate=0.005
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Portafolio con capital suficiente
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 15.0

        # Debe fallar por límite de trades, no por capital
        with pytest.raises(OrderExecutionError) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        assert "Límite de operaciones reales alcanzado" in str(exc_info.value)

    async def test_default_risk_percentages_fallback(self, trading_engine_service):
        """Test del uso de valores por defecto cuando faltan configuraciones de riesgo."""
        user_id = uuid4()
        opportunity_id = uuid4()
        
        # Setup de oportunidad
        opportunity = Opportunity(
            id=opportunity_id,
            user_id=user_id,
            symbol="MATICUSDT",
            source_type=OpportunitySourceType.AI_GENERATED,
            status=OpportunityStatus.PENDING_USER_CONFIRMATION_REAL,
            ai_analysis=AIAnalysis(
                suggestedAction="BUY",
                calculatedConfidence=0.96,
                reasoning_ai="Test default percentages",
                rawAiOutput=None,
                dataVerification=None,
                ai_model_used="test"
            ),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        trading_engine_service._mock_persistence_service.get_opportunity_by_id.return_value = opportunity

        # Configuración con valores None que deben usar defaults
        user_config = UserConfiguration(
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
                dailyCapitalRiskPercentage=None,  # Debería usar 0.50 por defecto
                perTradeCapitalRiskPercentage=None,  # Debería usar 0.25 por defecto
                takeProfitPercentage=None,
                trailingStopLossPercentage=None,
                trailingStopCallbackRate=None
            )
        )
        trading_engine_service._mock_config_service.get_user_configuration.return_value = user_config

        # Portafolio
        portfolio_snapshot = PortfolioSnapshot(
            real_trading=PortfolioSummary(
                available_balance_usdt=1000.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=1000.0,
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
        trading_engine_service._mock_portfolio_service.get_portfolio_snapshot.return_value = portfolio_snapshot

        trading_engine_service._mock_market_data_service.get_latest_price.return_value = 1.0

        # Simular fallo en credenciales para verificar que llegamos hasta el cálculo
        trading_engine_service._mock_credential_service.get_credential.return_value = None

        with pytest.raises(Exception) as exc_info:
            await trading_engine_service.execute_real_trade(opportunity_id, user_id)

        # Los valores por defecto deberían permitir el cálculo sin problemas
        # dailyCapitalRiskPercentage = 0.50 (por defecto) => límite diario = 500 USD
        # perTradeCapitalRiskPercentage = 0.25 (por defecto) => capital por trade = 250 USD
        # 0 + 250 = 250 < 500 ✓

        # Debe fallar por credenciales, no por capital
        assert "credenciales" in str(exc_info.value).lower()
