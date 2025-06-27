import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from pydantic import ValidationError

from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend.services.config_service import ConfigurationService
from src.ultibot_backend.core.domain_models import trading_strategy_models
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
    ArbitrageSimpleParameters,
    CustomAIDrivenParameters,
    MCPSignalFollowerParameters,
    GridTradingParameters,
    DCAInvestingParameters,
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    UserConfiguration,
    AIStrategyConfiguration,
)

# Fixtures for mocking dependencies
@pytest.fixture
def mock_persistence_service():
    return AsyncMock(spec=SupabasePersistenceService)

@pytest.fixture
def mock_configuration_service():
    return AsyncMock(spec=ConfigurationService)

@pytest.fixture
def strategy_service(mock_persistence_service, mock_configuration_service):
    return StrategyService(mock_persistence_service, mock_configuration_service)

# Sample data for tests
@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def sample_strategy_id():
    return str(uuid4())

@pytest.fixture
def sample_ai_config_id():
    return str(uuid4())

@pytest.fixture
def sample_scalping_strategy_data(sample_user_id):
    return {
        "user_id": sample_user_id,
        "config_name": "Test Scalping Strategy",
        "base_strategy_type": BaseStrategyType.SCALPING.value,
        "parameters": {
            "profit_target_percentage": 0.01,
            "stop_loss_percentage": 0.005
        }
    }

@pytest.fixture
def sample_scalping_strategy_config(sample_user_id, sample_strategy_id):
    return trading_strategy_models.TradingStrategyConfig(
        id=sample_strategy_id,
        user_id=sample_user_id,
        config_name="Test Scalping Strategy",
        base_strategy_type=trading_strategy_models.BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@pytest.fixture
def sample_user_config_with_ai_profile(sample_user_id, sample_ai_config_id):
    return UserConfiguration(
        user_id=sample_user_id,
        ai_strategy_configurations=[
            AIStrategyConfiguration(
                id=sample_ai_config_id,
                name="My AI Profile",
                is_active_paper_mode=True,
                total_pnl=Decimal("0.0"),
                number_of_trades=0
            )
        ]
    )

# Tests for StrategyService
# =================================================================
class TestStrategyService:

    @pytest.mark.asyncio
    async def test_create_strategy_config_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_strategy_data):
        mock_persistence_service.upsert_strategy_config.return_value = None
        
        strategy = await strategy_service.create_strategy_config(sample_user_id, sample_scalping_strategy_data)
        assert strategy.__class__.__name__ == "TradingStrategyConfig"
        assert strategy.user_id == sample_user_id
        assert strategy.config_name == "Test Scalping Strategy"
        mock_persistence_service.upsert_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_strategy_config_invalid_data(self, strategy_service, sample_user_id):
        invalid_data = {"user_id": sample_user_id, "config_name": "", "base_strategy_type": "SCALPING", "parameters": {}}
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_id, invalid_data)
        assert exc_info.value.status_code == 400
        assert "Invalid strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_strategy_config_with_ai_profile_success(self, strategy_service, mock_persistence_service, mock_configuration_service, sample_user_id, sample_scalping_strategy_data, sample_ai_config_id, sample_user_config_with_ai_profile):
        sample_scalping_strategy_data["ai_analysis_profile_id"] = sample_ai_config_id
        mock_configuration_service.get_user_configuration.return_value = sample_user_config_with_ai_profile
        mock_persistence_service.upsert_strategy_config.return_value = None

        strategy = await strategy_service.create_strategy_config(sample_user_id, sample_scalping_strategy_data)

        assert strategy.__class__.__name__ == "TradingStrategyConfig"
        assert strategy.ai_analysis_profile_id == sample_ai_config_id
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)
        mock_persistence_service.upsert_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_strategy_config_with_invalid_ai_profile(self, strategy_service, mock_configuration_service, sample_user_id, sample_scalping_strategy_data):
        sample_scalping_strategy_data["ai_analysis_profile_id"] = "non_existent_ai_id"
        mock_configuration_service.get_user_configuration.return_value = UserConfiguration(user_id=sample_user_id, ai_strategy_configurations=[])

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.create_strategy_config(sample_user_id, sample_scalping_strategy_data)
        assert exc_info.value.status_code == 400
        assert "AI analysis profile 'non_existent_ai_id' does not exist" in exc_info.value.detail
        mock_configuration_service.get_user_configuration.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_strategy_config_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)

        assert strategy == sample_scalping_strategy_config
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_get_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        strategy = await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)

        assert strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_get_strategy_config_persistence_error(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.get_strategy_config_by_id.side_effect = Exception("DB Error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.get_strategy_config(sample_strategy_id, sample_user_id)
        assert exc_info.value.status_code == 500
        assert "Failed to retrieve strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_strategy_configs_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_scalping_strategy_config):
        mock_persistence_service.list_strategy_configs_by_user.return_value = [sample_scalping_strategy_config]

        strategies = await strategy_service.list_strategy_configs(sample_user_id)

        assert len(strategies) == 1
        assert strategies[0] == sample_scalping_strategy_config
        mock_persistence_service.list_strategy_configs_by_user.assert_called_once_with(UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_list_strategy_configs_empty(self, strategy_service, mock_persistence_service, sample_user_id):
        mock_persistence_service.list_strategy_configs_by_user.return_value = []

        strategies = await strategy_service.list_strategy_configs(sample_user_id)

        assert len(strategies) == 0
        mock_persistence_service.list_strategy_configs_by_user.assert_called_once_with(UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_list_strategy_configs_persistence_error(self, strategy_service, mock_persistence_service, sample_user_id):
        mock_persistence_service.list_strategy_configs_by_user.side_effect = Exception("DB Error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.list_strategy_configs(sample_user_id)
        assert exc_info.value.status_code == 500
        assert "Failed to list strategy configurations" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_update_strategy_config_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config
        mock_persistence_service.upsert_strategy_config.return_value = None

        updated_data = {"config_name": "Updated Scalping Strategy"}
        updated_strategy = await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, updated_data)

        assert updated_strategy.__class__.__name__ == "TradingStrategyConfig"
        assert updated_strategy.config_name == "Updated Scalping Strategy"
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))
        mock_persistence_service.upsert_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        updated_data = {"config_name": "Updated Scalping Strategy"}
        updated_strategy = await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, updated_data)

        assert updated_strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))
        mock_persistence_service.upsert_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_strategy_config_invalid_data(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config
        invalid_data = {"config_name": "", "parameters": {}}

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, invalid_data)
        assert exc_info.value.status_code == 400
        assert "Invalid strategy configuration" in exc_info.value.detail
        mock_persistence_service.upsert_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_strategy_config_persistence_error(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config
        mock_persistence_service.upsert_strategy_config.side_effect = Exception("DB Error")

        updated_data = {"config_name": "Updated Scalping Strategy"}
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.update_strategy_config(sample_strategy_id, sample_user_id, updated_data)
        assert exc_info.value.status_code == 500
        assert "Failed to update strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_delete_strategy_config_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.delete_strategy_config.return_value = True

        deleted = await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)

        assert deleted is True
        mock_persistence_service.delete_strategy_config.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_delete_strategy_config_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.delete_strategy_config.return_value = False

        deleted = await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)

        assert deleted is False
        mock_persistence_service.delete_strategy_config.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_delete_strategy_config_persistence_error(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.delete_strategy_config.side_effect = Exception("DB Error")

        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.delete_strategy_config(sample_strategy_id, sample_user_id)
        assert exc_info.value.status_code == 500
        assert "Failed to delete strategy configuration" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_strategy_paper_mode_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config, mocker):
        sample_scalping_strategy_config.is_active_paper_mode = False
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock, return_value=sample_scalping_strategy_config)

        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")

        assert activated_strategy.is_active_paper_mode is True
        mock_update_strategy_config.assert_called_once()
        call_args = mock_update_strategy_config.call_args[0]
        assert call_args[0] == sample_strategy_id
        assert call_args[1] == sample_user_id
        assert call_args[2]["is_active_paper_mode"] is True

    @pytest.mark.asyncio
    async def test_activate_strategy_real_mode_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config, mocker):
        sample_scalping_strategy_config.is_active_real_mode = False
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock, return_value=sample_scalping_strategy_config)

        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "real")

        assert activated_strategy.is_active_real_mode is True
        mock_update_strategy_config.assert_called_once()
        call_args = mock_update_strategy_config.call_args[0]
        assert call_args[0] == sample_strategy_id
        assert call_args[1] == sample_user_id
        assert call_args[2]["is_active_real_mode"] is True

    @pytest.mark.asyncio
    async def test_activate_strategy_invalid_mode(self, strategy_service, sample_user_id, sample_strategy_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_activate_strategy_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, mocker):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock)

        activated_strategy = await strategy_service.activate_strategy(sample_strategy_id, sample_user_id, "paper")

        assert activated_strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))
        mock_update_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_paper_mode_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config, mocker):
        sample_scalping_strategy_config.is_active_paper_mode = True
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock, return_value=sample_scalping_strategy_config)

        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "paper")

        assert deactivated_strategy.is_active_paper_mode is False
        mock_update_strategy_config.assert_called_once()
        call_args = mock_update_strategy_config.call_args[0]
        assert call_args[0] == sample_strategy_id
        assert call_args[1] == sample_user_id
        assert call_args[2]["is_active_paper_mode"] is False

    @pytest.mark.asyncio
    async def test_deactivate_strategy_real_mode_success(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config, mocker):
        sample_scalping_strategy_config.is_active_real_mode = True
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock, return_value=sample_scalping_strategy_config)

        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "real")

        assert deactivated_strategy.is_active_real_mode is False
        mock_update_strategy_config.assert_called_once()
        call_args = mock_update_strategy_config.call_args[0]
        assert call_args[0] == sample_strategy_id
        assert call_args[1] == sample_user_id
        assert call_args[2]["is_active_real_mode"] is False

    @pytest.mark.asyncio
    async def test_deactivate_strategy_invalid_mode(self, strategy_service, sample_user_id, sample_strategy_id):
        with pytest.raises(HTTPException) as exc_info:
            await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "invalid_mode")
        assert exc_info.value.status_code == 400
        assert "Mode must be 'paper' or 'real'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_strategy_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, mocker):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        mock_update_strategy_config = mocker.patch.object(strategy_service, 'update_strategy_config', new_callable=AsyncMock)

        deactivated_strategy = await strategy_service.deactivate_strategy(sample_strategy_id, sample_user_id, "paper")

        assert deactivated_strategy is None
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))
        mock_update_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_true(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.ai_analysis_profile_id = None
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)

        assert can_operate is True
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_false(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.ai_analysis_profile_id = str(uuid4())
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)

        assert can_operate is False
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_strategy_can_operate_autonomously_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        can_operate = await strategy_service.strategy_can_operate_autonomously(sample_strategy_id, sample_user_id)

        assert can_operate is False
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_success_no_filters(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.allowed_symbols = None
        sample_scalping_strategy_config.excluded_symbols = None
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")

        assert is_applicable is True
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_success_allowed_list(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.allowed_symbols = ["BTC/USDT", "ETH/USDT"]
        sample_scalping_strategy_config.excluded_symbols = None
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")

        assert is_applicable is True

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_fail_allowed_list(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.allowed_symbols = ["ETH/USDT"]
        sample_scalping_strategy_config.excluded_symbols = None
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")

        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_fail_excluded_list(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id, sample_scalping_strategy_config):
        sample_scalping_strategy_config.allowed_symbols = None
        sample_scalping_strategy_config.excluded_symbols = ["BTC/USDT"]
        mock_persistence_service.get_strategy_config_by_id.return_value = sample_scalping_strategy_config

        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")

        assert is_applicable is False

    @pytest.mark.asyncio
    async def test_is_strategy_applicable_to_symbol_not_found(self, strategy_service, mock_persistence_service, sample_user_id, sample_strategy_id):
        mock_persistence_service.get_strategy_config_by_id.return_value = None

        is_applicable = await strategy_service.is_strategy_applicable_to_symbol(sample_strategy_id, sample_user_id, "BTC/USDT")

        assert is_applicable is False
        mock_persistence_service.get_strategy_config_by_id.assert_called_once_with(UUID(sample_strategy_id), UUID(sample_user_id))