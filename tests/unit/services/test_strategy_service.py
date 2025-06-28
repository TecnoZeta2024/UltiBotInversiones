import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import UUID, uuid4
from decimal import Decimal

from fastapi import HTTPException
from pydantic import ValidationError

from src.adapters.persistence_service import SupabasePersistenceService
from src.core.domain_models.trading_strategy_models import (
    BaseStrategyType,
    TradingStrategyConfig,
    ScalpingParameters,
    DayTradingParameters,
    Timeframe,
    PerformanceMetrics,
    ApplicabilityRules,
    DynamicFilter,
    RiskParametersOverride,
    MarketConditionFilter,
    ActivationSchedule,
    StrategyDependency,
    SharingMetadata,
)
from src.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
    ConfidenceThresholds,
    RiskProfile,
    RiskProfileSettings,
    Theme,
    NotificationPreference,
    NotificationChannel,
    RealTradingSettings,
    AutoPauseTradingConditions,
    Watchlist,
    MCPServerPreference,
    DashboardLayoutProfile,
    CloudSyncPreferences,
    PaperTradingAsset,
)
from src.services.config_service import ConfigurationService
from src.services.strategy_service import StrategyService


@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_configuration_service():
    return AsyncMock(spec=ConfigurationService)

@pytest.fixture
def strategy_service(mock_persistence_service, mock_configuration_service):
    return StrategyService(mock_persistence_service, mock_configuration_service)

@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def sample_strategy_id():
    return str(uuid4())

@pytest.fixture
def sample_ai_strategy_config_id():
    return str(uuid4())

@pytest.fixture
def sample_scalping_strategy_data(sample_user_id):
    return {
        "config_name": "Test Scalping Strategy",
        "base_strategy_type": BaseStrategyType.SCALPING.value,
        "parameters": {
            "profit_target_percentage": 0.01,
            "stop_loss_percentage": 0.005,
        },
        "user_id": sample_user_id,
    }

@pytest.fixture
def sample_day_trading_strategy_data(sample_user_id):
    return {
        "config_name": "Test Day Trading Strategy",
        "base_strategy_type": BaseStrategyType.DAY_TRADING.value,
        "parameters": {
            "entry_timeframes": [Timeframe.FIFTEEN_MINUTES.value],
            "rsi_period": 14,
            "rsi_overbought": 70.0,
            "rsi_oversold": 30.0,
            "macd_fast_period": 12,
            "macd_slow_period": 26,
            "macd_signal_period": 9,
        },
        "user_id": sample_user_id,
    }

@pytest.fixture
def sample_ai_strategy_config(sample_ai_strategy_config_id):
    """Provides a more complete AIStrategyConfiguration fixture."""
    return AIStrategyConfiguration(
        id=sample_ai_strategy_config_id,
        name="Test AI Profile",
        is_active_paper_mode=False,
        is_active_real_mode=False,
        total_pnl=Decimal("0.0"),
        number_of_trades=0,
        applies_to_strategies=None,
        applies_to_pairs=["BTC/USDT"],
        gemini_prompt_template="Analyze {symbol} for a {strategy_type} strategy.",
        tools_available_to_gemini=["MobulaChecker"],
        output_parser_config={"type": "json"},
        indicator_weights={"RSI": 0.8},
        confidence_thresholds=ConfidenceThresholds(paper_trading=0.7, real_trading=0.8),
        max_context_window_tokens=4096,
    )

@pytest.fixture
def sample_user_config(sample_user_id, sample_ai_strategy_config):
    return UserConfiguration(
        id=str(uuid4()),
        user_id=sample_user_id,
        telegram_chat_id="123456789",
        notification_preferences=[
            NotificationPreference(event_type="REAL_TRADE_EXECUTED", channel=NotificationChannel.TELEGRAM, is_enabled=True, min_confidence=None, min_profitability=None)
        ],
        enable_telegram_notifications=True,
        default_paper_trading_capital=Decimal("10000.00"),
        paper_trading_active=True,
        paper_trading_assets=[
            PaperTradingAsset(asset="BTC", quantity=Decimal("0.5"), entry_price=Decimal("30000.00"))
        ],
        watchlists=[
            Watchlist(id=str(uuid4()), name="Crypto Watchlist", pairs=["BTC/USDT", "ETH/USDT"], default_alert_profile_id=None, default_ai_analysis_profile_id=None)
        ],
        favorite_pairs=["BTC/USDT"],
        risk_profile=RiskProfile.MODERATE,
        risk_profile_settings=RiskProfileSettings(
            daily_capital_risk_percentage=0.01,
            per_trade_capital_risk_percentage=0.005,
            max_drawdown_percentage=0.10
        ),
        real_trading_settings=RealTradingSettings(
            real_trading_mode_active=False,
            real_trades_executed_count=0,
            max_concurrent_operations=None,
            daily_loss_limit_absolute=None,
            daily_profit_target_absolute=None,
            asset_specific_stop_loss=None,
            auto_pause_trading_conditions=AutoPauseTradingConditions(
                on_max_daily_loss_reached=True,
                on_max_drawdown_reached=None,
                on_consecutive_losses=None,
                on_market_volatility_index_exceeded=None
            ),
            daily_capital_risked_usd=Decimal("0.0"),
            last_daily_reset=None
        ),
        ai_strategy_configurations=[sample_ai_strategy_config],
        ai_analysis_confidence_thresholds=ConfidenceThresholds(paper_trading=0.6, real_trading=0.75),
        mcp_server_preferences=[
            MCPServerPreference(id=str(uuid4()), type="ccxt", url="http://localhost:8080", api_key=None, is_enabled=True, query_frequency_seconds=None, reliability_weight=None, custom_parameters=None)
        ],
        selected_theme=Theme.DARK,
        dashboard_layout_profiles={
            "default": DashboardLayoutProfile(name="Default Layout", configuration={"widgets": []})
        },
        active_dashboard_layout_profile_id="default",
        dashboard_layout_config={"current_layout": "default"},
        cloud_sync_preferences=CloudSyncPreferences(is_enabled=False, last_successful_sync=None),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def sample_scalping_config(sample_user_id, sample_strategy_id, sample_ai_strategy_config_id) -> TradingStrategyConfig:
    return TradingStrategyConfig(
        id=sample_strategy_id,
        user_id=sample_user_id,
        config_name="Sample Scalping Config",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005, max_holding_time_seconds=None, leverage=None),
        description="A sample scalping strategy for testing.",
        is_active_paper_mode=False,
        is_active_real_mode=False,
        allowed_symbols=["BTC/USDT"],
        excluded_symbols=[],
        applicability_rules=ApplicabilityRules(
            include_all_spot=False,
            dynamic_filter=DynamicFilter(min_daily_volatility_percentage=0.001, max_daily_volatility_percentage=None, min_market_cap_usd=None, included_watchlist_ids=None, asset_categories=None)
        ),
        ai_analysis_profile_id=None, # Modificado para test_update_strategy_config_generic_exception
        risk_parameters_override=RiskParametersOverride(per_trade_capital_risk_percentage=0.006, max_concurrent_trades_for_this_strategy=None, max_capital_allocation_quote=None),
        version=1,
        parent_config_id=None,
        performance_metrics=PerformanceMetrics(total_trades_executed=10, winning_trades=7, losing_trades=3, win_rate=None, cumulative_pnl_quote=None, average_winning_trade_pnl=None, average_losing_trade_pnl=None, profit_factor=None, sharpe_ratio=None, last_calculated_at=None),
        market_condition_filters=[
            MarketConditionFilter(filter_type="volatility", source_id=None, condition="greater_than", threshold_value=0.02, action_on_trigger="pause")
        ],
        activation_schedule=ActivationSchedule(cron_expression="0 9 * * 1-5", time_zone="America/New_York", event_triggers=None),
        depends_on_strategies=[],
        sharing_metadata=SharingMetadata(is_template=False, author_user_id=sample_user_id, shared_at=None, user_rating_average=None, download_or_copy_count=None, tags=None),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

@pytest.fixture
def sample_day_trading_config(sample_user_id, sample_strategy_id, sample_ai_strategy_config_id) -> TradingStrategyConfig:
    return TradingStrategyConfig(
        id=sample_strategy_id,
        user_id=sample_user_id,
        config_name="Sample Day Trading Config",
        base_strategy_type=BaseStrategyType.DAY_TRADING,
        parameters=DayTradingParameters(
            entry_timeframes=[Timeframe.FIFTEEN_MINUTES],
            rsi_period=14,
            rsi_overbought=70.0,
            rsi_oversold=30.0,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            exit_timeframes=None
        ),
        description="A sample day trading strategy for testing.",
        is_active_paper_mode=False,
        is_active_real_mode=False,
        allowed_symbols=["ETH/USDT"],
        excluded_symbols=[],
        applicability_rules=ApplicabilityRules(
            include_all_spot=False,
            dynamic_filter=DynamicFilter(min_daily_volatility_percentage=0.005, max_daily_volatility_percentage=None, min_market_cap_usd=None, included_watchlist_ids=None, asset_categories=None)
        ),
        ai_analysis_profile_id=sample_ai_strategy_config_id,
        risk_parameters_override=RiskParametersOverride(max_concurrent_trades_for_this_strategy=2, per_trade_capital_risk_percentage=None, max_capital_allocation_quote=None),
        version=1,
        parent_config_id=None,
        performance_metrics=PerformanceMetrics(total_trades_executed=5, winning_trades=3, losing_trades=2, win_rate=None, cumulative_pnl_quote=None, average_winning_trade_pnl=None, average_losing_trade_pnl=None, profit_factor=None, sharpe_ratio=None, last_calculated_at=None),
        market_condition_filters=[],
        activation_schedule=ActivationSchedule(cron_expression="0 10 * * 1-5", time_zone="America/New_York", event_triggers=None),
        depends_on_strategies=[],
        sharing_metadata=SharingMetadata(is_template=False, author_user_id=sample_user_id, shared_at=None, user_rating_average=None, download_or_copy_count=None, tags=None),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestStrategyService:

    @pytest.mark.asyncio
    async def test_create_strategy_config_success(self, strategy_service, mock_persistence_service, sample_scalping_strategy_data):
        mock_persistence_service.upsert_strategy_config.return_value = None
        
        strategy = await strategy_service.create_strategy_config(
            sample_scalping_strategy_data["user_id"],
            sample_scalping_strategy_data
        )
        
        assert strategy.config_name == "Test Scalping Strategy"
        mock_persistence_service.upsert_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_strategy_config_invalid_data(self, strategy_service, sample_user_id, sample_scalping_strategy_data):
        invalid_data = sample_scalping_strategy_data.copy()
        invalid_data["parameters"]["profit_target_percentage"] = 2.0 # Invalid percentage
        
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_id, invalid_data)
        
        assert exc_info.value.status_code == 400
        assert "Invalid strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_strategy_config_generic_exception(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_strategy_data):
        mock_persistence_service.upsert_strategy_config.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_id, sample_scalping_strategy_data)

        assert exc_info.value.status_code == 500
        assert "Failed to create strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_strategy_config_generic_exception(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.side_effect = Exception("DB connection error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_strategy_configs_generic_exception(self, strategy_service, mock_persistence_service, sample_user_id):
        mock_persistence_service.list_strategy_configs_by_user.side_effect = Exception("DB connection error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.list_strategy_configs(sample_user_id)

        assert exc_info.value.status_code == 500
        assert "Failed to list strategy configurations" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_strategy_config_invalid_data(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        
        invalid_update_data = {"parameters": {"profit_target_percentage": 2.0}} # Invalid percentage
        
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, invalid_update_data)
        
        assert exc_info.value.status_code == 400
        assert "Invalid strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_strategy_config_generic_exception(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        mock_persistence_service.upsert_strategy_config.side_effect = Exception("Database error")

        update_data = {"config_name": "New Name"}
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)

        assert exc_info.value.status_code == 500
        assert "Failed to update strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_strategy_config_generic_exception(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.delete_strategy_config.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)

        assert exc_info.value.status_code == 500
        assert "Failed to delete strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_strategy_invalid_mode(self, strategy_service, sample_strategy_id, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_strategy_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")
        
        assert activated_strategy is None

    @pytest.mark.asyncio
    async def test_deactivate_strategy_invalid_mode(self, strategy_service, sample_strategy_id, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_strategy_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "paper")
        
        assert deactivated_strategy is None

    @pytest.mark.asyncio
    async def test_get_active_strategies_invalid_mode(self, strategy_service, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.get_active_strategies(sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_strategy_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")
        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_invalid_parameters_json(self, strategy_service):
        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "base_strategy_type": BaseStrategyType.SCALPING.value,
            "parameters": "invalid json string",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            strategy_service._db_format_to_strategy_config(db_record)
        
        assert exc_info.value.status_code == 500
        assert "Failed to load strategy configuration due to invalid data format." in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_non_dict_parameters(self, strategy_service):
        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "base_strategy_type": BaseStrategyType.SCALPING.value,
            "parameters": 123, # Not a dict or string
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            strategy_service._db_format_to_strategy_config(db_record)
        
        assert exc_info.value.status_code == 500
        assert "Failed to load strategy configuration due to invalid data format." in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_invalid_base_strategy_type(self, strategy_service):
        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "base_strategy_type": "INVALID_TYPE",
            "parameters": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        strategy_config = strategy_service._db_format_to_strategy_config(db_record)
        assert strategy_config.base_strategy_type == BaseStrategyType.UNKNOWN

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_missing_base_strategy_type(self, strategy_service):
        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "parameters": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        strategy_config = strategy_service._db_format_to_strategy_config(db_record)
        assert strategy_config.base_strategy_type == BaseStrategyType.UNKNOWN

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_validation_error(self, strategy_service):
        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "base_strategy_type": BaseStrategyType.SCALPING.value,
            "parameters": {"profit_target_percentage": 2.0}, # Invalid parameter
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            strategy_service._db_format_to_strategy_config(db_record)
        
        assert exc_info.value.status_code == 500
        assert "Failed to load strategy configuration due to invalid data format." in exc_info.value.detail

    # @pytest.mark.asyncio
    # async def test_db_format_to_strategy_config_unexpected_error(self, strategy_service, mocker):
    #     # Simulate an unexpected error during TradingStrategyConfig instantiation
    #     mocker.patch('src.core.domain_models.trading_strategy_models.TradingStrategyConfig', side_effect=Exception("Simulated unexpected error"))

    #     db_record = {
    #         "id": str(uuid4()),
    #         "user_id": str(uuid4()),
    #         "config_name": "Test Strategy",
    #         "base_strategy_type": BaseStrategyType.SCALPING.value,
    #         "parameters": {"profit_target_percentage": 0.01, "stop_loss_percentage": 0.005},
    #         "created_at": datetime.now(timezone.utc).isoformat(),
    #         "updated_at": datetime.now(timezone.utc).isoformat(),
    #     }
        
    #     with pytest.raises(HTTPException) as exc_info:
    #         strategy_service._db_format_to_strategy_config(db_record)
        
    #     assert exc_info.value.status_code == 500
    #     assert "An unexpected error occurred while loading the strategy configuration." in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_convert_parameters_by_type_unknown_type(self, strategy_service):
        parameters_data = {"key": "value"}
        result = strategy_service._convert_parameters_by_type(BaseStrategyType.UNKNOWN, parameters_data)
        assert result == parameters_data

    @pytest.mark.asyncio
    async def test_convert_parameters_by_type_validation_failure(self, strategy_service):
        parameters_data = {"profit_target_percentage": 2.0} # Invalid for ScalpingParameters
        result = strategy_service._convert_parameters_by_type(BaseStrategyType.SCALPING, parameters_data)
        assert result == parameters_data # Should return raw data on validation failure

    @pytest.mark.asyncio
    async def test_convert_parameters_by_type_no_specific_class(self, strategy_service):
        # Simulate a new BaseStrategyType that is not in param_map
        from enum import Enum
        class UnknownBaseStrategyType(str, Enum):
            NEW_TYPE = "NEW_TYPE"

        parameters_data = {"some_param": "some_value"}
        result = strategy_service._convert_parameters_by_type(UnknownBaseStrategyType.NEW_TYPE, parameters_data)
        assert result == parameters_data # Should return raw data if no specific class found

    @pytest.mark.asyncio
    async def test_create_strategy_config_with_ai_profile_success(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_scalping_strategy_data, sample_user_config, sample_ai_strategy_config):
        mock_configuration_service.get_user_configuration.return_value = sample_user_config
        mock_persistence_service.upsert_strategy_config.return_value = None

        strategy_data = sample_scalping_strategy_data.copy()
        strategy_data["ai_analysis_profile_id"] = sample_ai_strategy_config.id

        strategy = await strategy_service.create_strategy_config(
            sample_user_config.user_id,
            strategy_data
        )
        
        assert strategy.ai_analysis_profile_id == sample_ai_strategy_config.id
        mock_persistence_service.upsert_strategy_config.assert_called_once()
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_config.user_id)

    @pytest.mark.asyncio
    async def test_create_strategy_config_with_ai_profile_validation_fail(self, strategy_service, mock_configuration_service, sample_scalping_strategy_data, sample_user_config):
        mock_configuration_service.get_user_configuration.return_value = sample_user_config
        
        strategy_data = sample_scalping_strategy_data.copy()
        strategy_data["ai_analysis_profile_id"] = str(uuid4()) # Non-existent AI profile

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_config.user_id, strategy_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_create_strategy_config_with_ai_profile_no_user_config(self, strategy_service, mock_configuration_service, sample_scalping_strategy_data, sample_user_id):
        mock_configuration_service.get_user_configuration.return_value = None
        
        strategy_data = sample_scalping_strategy_data.copy()
        strategy_data["ai_analysis_profile_id"] = str(uuid4()) # AI profile, but no user config

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_id, strategy_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_strategy_config_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        
        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)
        
        assert strategy == sample_scalping_config
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_get_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)
        
        assert strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_list_strategy_configs_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_config, sample_day_trading_config):
        mock_strategies = [sample_scalping_config, sample_day_trading_config]
        mock_persistence_service.list_strategy_configs_by_user.return_value = mock_strategies
        
        strategies = await strategy_service.list_strategy_configs(sample_user_id)
        
        assert strategies == mock_strategies
        assert len(strategies) == 2
        mock_persistence_service.list_strategy_configs_by_user.assert_called_once_with(UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_update_strategy_config_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        mock_persistence_service.upsert_strategy_config.return_value = None
        
        update_data = {"config_name": "New Name", "is_active_paper_mode": True}
        updated_strategy = await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert updated_strategy.config_name == "New Name"
        assert updated_strategy.is_active_paper_mode is True
        mock_persistence_service.upsert_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_strategy_config_not_found_path(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        update_data = {"config_name": "New Name"}
        updated_strategy = await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert updated_strategy is None
        mock_persistence_service.upsert_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_strategy_config_with_invalid_ai_profile(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id, sample_user_config, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        mock_configuration_service.get_user_configuration.return_value = sample_user_config
        
        update_data = {"ai_analysis_profile_id": str(uuid4())} # Non-existent AI profile

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_strategy_config_with_ai_profile_no_user_config(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        mock_configuration_service.get_user_configuration.return_value = None # No user config found
        
        update_data = {"ai_analysis_profile_id": str(uuid4())} # AI profile, but no user config

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_strategy_config_with_ai_profile_empty_ai_configs(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_config
        # Proporcionar todos los campos obligatorios o con valores por defecto para UserConfiguration
        mock_configuration_service.get_user_configuration.return_value = UserConfiguration(
            id=str(uuid4()),
            user_id=sample_user_id,
            telegram_chat_id="123456789",
            notification_preferences=[],
            enable_telegram_notifications=True,
            default_paper_trading_capital=Decimal("10000.00"),
            paper_trading_active=True,
            paper_trading_assets=[],
            watchlists=[],
            favorite_pairs=[],
            risk_profile=RiskProfile.MODERATE,
            risk_profile_settings=RiskProfileSettings(),
            real_trading_settings=RealTradingSettings(),
            ai_strategy_configurations=[], # User config with empty AI configs
            ai_analysis_confidence_thresholds=ConfidenceThresholds(),
            mcp_server_preferences=[],
            selected_theme=Theme.DARK,
            dashboard_layout_profiles={},
            active_dashboard_layout_profile_id=None,
            dashboard_layout_config={},
            cloud_sync_preferences=CloudSyncPreferences(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        update_data = {"ai_analysis_profile_id": str(uuid4())} # AI profile, but empty AI configs

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_delete_strategy_config_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.delete_strategy_config.return_value = True
        
        deleted = await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)
        
        assert deleted is True
        mock_persistence_service.delete_strategy_config.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_delete_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.delete_strategy_config.return_value = False
        
        deleted = await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)
        
        assert deleted is False
        mock_persistence_service.delete_strategy_config.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_activate_strategy_paper_mode_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        existing_strategy = sample_scalping_config.model_copy(update={"is_active_paper_mode": False})
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_persistence_service.upsert_strategy_config.return_value = None
        
        strategy_service.update_strategy_config = AsyncMock(return_value=existing_strategy.model_copy(update={"is_active_paper_mode": True}))

        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")
        
        assert activated_strategy.is_active_paper_mode is True
        strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_real_mode_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        existing_strategy = sample_scalping_config.model_copy(update={"is_active_real_mode": True})
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_persistence_service.upsert_strategy_config.return_value = None

        strategy_service.update_strategy_config = AsyncMock(return_value=existing_strategy.model_copy(update={"is_active_real_mode": False}))

        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "real")
        
        assert deactivated_strategy.is_active_real_mode is False
        strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_true(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy_without_ai = sample_scalping_config.model_copy(update={"ai_analysis_profile_id": None})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy_without_ai
        
        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)
        
        assert can_operate is True

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_false(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy_with_ai = sample_scalping_config.model_copy(update={"ai_analysis_profile_id": str(uuid4())})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy_with_ai
        
        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)
        
        assert can_operate is False

    @pytest.mark.asyncio
    async def test_activate_strategy_invalid_mode_path(self, strategy_service, sample_strategy_id, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_strategy_not_found_path(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")
        
        assert activated_strategy is None

    @pytest.mark.asyncio
    async def test_deactivate_strategy_invalid_mode_path(self, strategy_service, sample_strategy_id, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_active_strategies_invalid_mode_path(self, strategy_service, sample_user_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.get_active_strategies(sample_user_id, "invalid_mode")
        
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_active_strategies_paper_mode(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_config):
        active_paper_strategy = sample_scalping_config.model_copy(update={"is_active_paper_mode": True, "config_name": "Active Paper"})
        inactive_paper_strategy = sample_scalping_config.model_copy(update={"is_active_paper_mode": False, "config_name": "Inactive Paper"})
        active_real_strategy = sample_scalping_config.model_copy(update={"is_active_real_mode": True, "config_name": "Active Real"})
        
        mock_persistence_service.list_strategy_configs_by_user.return_value = [
            active_paper_strategy, inactive_paper_strategy, active_real_strategy
        ]
        
        active_strategies = await strategy_service.get_active_strategies(sample_user_id, "paper")
        
        assert len(active_strategies) == 1
        assert active_strategies[0].config_name == "Active Paper"

    @pytest.mark.asyncio
    async def test_get_active_strategies_real_mode_path(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_config):
        active_paper_strategy = sample_scalping_config.model_copy(update={"is_active_paper_mode": True, "config_name": "Active Paper"})
        inactive_paper_strategy = sample_scalping_config.model_copy(update={"is_active_paper_mode": False, "config_name": "Inactive Paper"})
        active_real_strategy = sample_scalping_config.model_copy(update={"is_active_real_mode": True, "config_name": "Active Real"})

        mock_persistence_service.list_strategy_configs_by_user.return_value = [
            active_paper_strategy, inactive_paper_strategy, active_real_strategy
        ]
        
        active_strategies = await strategy_service.get_active_strategies(sample_user_id, "real")
        
        assert len(active_strategies) == 1
        assert active_strategies[0].config_name == "Active Real"

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_allowed(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy = sample_scalping_config.model_copy(update={"allowed_symbols": ["BTC/USDT", "ETH/USDT"]})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")
        assert is_applicable is True

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_not_allowed(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy = sample_scalping_config.model_copy(update={"allowed_symbols": ["BTC/USDT", "ETH/USDT"]})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "XRP/USDT")
        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_excluded(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy = sample_scalping_config.model_copy(update={"excluded_symbols": ["XRP/USDT"]})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "XRP/USDT")
        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_not_excluded(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy = sample_scalping_config.model_copy(update={"excluded_symbols": ["XRP/USDT"]})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")
        assert is_applicable is True

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_no_lists(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id, sample_scalping_config):
        strategy = sample_scalping_config.model_copy(update={"allowed_symbols": None, "excluded_symbols": None})
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "ANY/SYMBOL")
        assert is_applicable is True
