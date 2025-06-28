
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    BaseStrategyType,
    TradingStrategyConfig,
    ScalpingParameters,
    DayTradingParameters,
    Timeframe,
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
)
from src.ultibot_backend.services.config_service import ConfigurationService
from src.ultibot_backend.services.strategy_service import StrategyService


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
            "rsi_period": 14,
            "entry_timeframes": [Timeframe.FIFTEEN_MINUTES.value],
        },
        "user_id": sample_user_id,
    }

@pytest.fixture
def sample_ai_strategy_config():
    return AIStrategyConfiguration(
        id=str(uuid4()),
        name="Test AI Profile",
        prompt_template="Analyze {symbol}",
        max_tokens_for_context=1000,
    )

@pytest.fixture
def sample_user_config(sample_user_id, sample_ai_strategy_config):
    return UserConfiguration(
        user_id=sample_user_id,
        ai_strategy_configurations=[sample_ai_strategy_config],
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
    async def test_update_strategy_config_invalid_data(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        
        invalid_update_data = {"parameters": {"profit_target_percentage": 2.0}} # Invalid percentage
        
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, invalid_update_data)
        
        assert exc_info.value.status_code == 400
        assert "Invalid strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_strategy_config_generic_exception(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
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

    @pytest.mark.asyncio
    async def test_db_format_to_strategy_config_unexpected_error(self, strategy_service, mocker):
        # Simulate an unexpected error during TradingStrategyConfig instantiation
        mocker.patch('src.ultibot_backend.core.domain_models.trading_strategy_models.TradingStrategyConfig.__init__', side_effect=Exception("Simulated unexpected error"))

        db_record = {
            "id": str(uuid4()),
            "user_id": str(uuid4()),
            "config_name": "Test Strategy",
            "base_strategy_type": BaseStrategyType.SCALPING.value,
            "parameters": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            strategy_service._db_format_to_strategy_config(db_record)
        
        assert exc_info.value.status_code == 500
        assert "Failed to load strategy configuration due to invalid data format." in exc_info.value.detail # This is the actual error detail due to validation failing first

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
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_config.user_id)

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
    async def test_get_strategy_config_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_strategy_config = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Fetched Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = mock_strategy_config
        
        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)
        
        assert strategy == mock_strategy_config
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_get_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None
        
        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)
        
        assert strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_list_strategy_configs_success(self, strategy_service, mock_persistence_service, sample_user_id):
        mock_strategies = [
            TradingStrategyConfig(
                id=str(uuid4()),
                user_id=sample_user_id,
                config_name="Strategy 1",
                base_strategy_type=BaseStrategyType.SCALPING,
                parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
            ),
            TradingStrategyConfig(
                id=str(uuid4()),
                user_id=sample_user_id,
                config_name="Strategy 2",
                base_strategy_type=BaseStrategyType.DAY_TRADING,
                parameters=DayTradingParameters(entry_timeframes=[Timeframe.FIVE_MINUTES])
            ),
        ]
        mock_persistence_service.list_strategy_configs_by_user.return_value = mock_strategies
        
        strategies = await strategy_service.list_strategy_configs(sample_user_id)
        
        assert strategies == mock_strategies
        assert len(strategies) == 2
        mock_persistence_service.list_strategy_configs_by_user.assert_called_once_with(UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_update_strategy_config_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
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
    async def test_update_strategy_config_with_invalid_ai_profile(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id, sample_user_config):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_configuration_service.get_user_configuration.return_value = sample_user_config
        
        update_data = {"ai_analysis_profile_id": str(uuid4())} # Non-existent AI profile

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_strategy_config_with_ai_profile_no_user_config(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_configuration_service.get_user_configuration.return_value = None # No user config found
        
        update_data = {"ai_analysis_profile_id": str(uuid4())} # AI profile, but no user config

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, update_data)
        
        assert exc_info.value.status_code == 400
        assert "AI analysis profile" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_update_strategy_config_with_ai_profile_empty_ai_configs(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Old Name",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_configuration_service.get_user_configuration.return_value = UserConfiguration(user_id=sample_user_id, ai_strategy_configurations=[]) # User config with empty AI configs
        
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
    async def test_activate_strategy_paper_mode_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Test Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_paper_mode=False,
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_persistence_service.upsert_strategy_config.return_value = None # Mock upsert to return nothing, as it's a side effect
        
        # Mock the update_strategy_config to return the modified strategy
        strategy_service.update_strategy_config = AsyncMock(return_value=existing_strategy.model_copy(update={"is_active_paper_mode": True}))

        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")
        
        assert activated_strategy.is_active_paper_mode is True
        strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_real_mode_success(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        existing_strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Test Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_real_mode=True,
            created_at=datetime.now(timezone.utc)
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = existing_strategy
        mock_persistence_service.upsert_strategy_config.return_value = None # Mock upsert to return nothing, as it's a side effect

        # Mock the update_strategy_config to return the modified strategy
        strategy_service.update_strategy_config = AsyncMock(return_value=existing_strategy.model_copy(update={"is_active_real_mode": False}))

        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "real")
        
        assert deactivated_strategy.is_active_real_mode is False
        strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_true(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy_without_ai = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Autonomous Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            ai_analysis_profile_id=None
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy_without_ai
        
        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)
        
        assert can_operate is True

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_false(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy_with_ai = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="AI Dependent Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            ai_analysis_profile_id=str(uuid4())
        )
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
    async def test_get_active_strategies_paper_mode(self, strategy_service, mock_persistence_service, sample_user_id):
        active_paper_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Active Paper",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_paper_mode=True
        )
        inactive_paper_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Inactive Paper",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_paper_mode=False
        )
        active_real_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Active Real",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_real_mode=True
        )
        mock_persistence_service.list_strategy_configs_by_user.return_value = [
            active_paper_strategy, inactive_paper_strategy, active_real_strategy
        ]
        
        active_strategies = await strategy_service.get_active_strategies(sample_user_id, "paper")
        
        assert len(active_strategies) == 1
        assert active_strategies[0].config_name == "Active Paper"

    @pytest.mark.asyncio
    async def test_get_active_strategies_real_mode_path(self, strategy_service, mock_persistence_service, sample_user_id):
        active_paper_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Active Paper",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_paper_mode=True
        )
        inactive_paper_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Inactive Paper",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_paper_mode=False
        )
        active_real_strategy = TradingStrategyConfig(
            id=str(uuid4()),
            user_id=sample_user_id,
            config_name="Active Real",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            is_active_real_mode=True
        )
        mock_persistence_service.list_strategy_configs_by_user.return_value = [
            active_paper_strategy, inactive_paper_strategy, active_real_strategy
        ]
        
        active_strategies = await strategy_service.get_active_strategies(sample_user_id, "real")
        
        assert len(active_strategies) == 1
        assert active_strategies[0].config_name == "Active Real"

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_allowed(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Symbol Specific",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            allowed_symbols=["BTC/USDT", "ETH/USDT"]
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")
        assert is_applicable is True

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_not_allowed(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Symbol Specific",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            allowed_symbols=["BTC/USDT", "ETH/USDT"]
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "XRP/USDT")
        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_excluded(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Symbol Specific",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            excluded_symbols=["XRP/USDT"]
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "XRP/USDT")
        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_not_excluded(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="Symbol Specific",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            excluded_symbols=["XRP/USDT"]
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")
        assert is_applicable is True

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_no_lists(self, strategy_service, mock_persistence_service, sample_strategy_id, sample_user_id):
        strategy = TradingStrategyConfig(
            id=sample_strategy_id,
            user_id=sample_user_id,
            config_name="General Strategy",
            base_strategy_type=BaseStrategyType.SCALPING,
            parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005),
            allowed_symbols=None,
            excluded_symbols=None
        )
        mock_persistence_service.get_strategy_config_by_id.return_value = strategy
        
        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "ANY/SYMBOL")
        assert is_applicable is True
