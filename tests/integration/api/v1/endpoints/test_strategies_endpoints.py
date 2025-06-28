import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException, FastAPI
from datetime import datetime
from typing import Tuple

from services.strategy_service import StrategyService
from core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType, ScalpingParameters
from dependencies import get_strategy_service

# Sample data
@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def sample_strategy_config(sample_user_id):
    """Provides a valid trading strategy configuration object."""
    return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=sample_user_id,
        config_name="Test Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="A test strategy for scalping.",
        is_active_paper_mode=False,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=3600,
            leverage=1.0
        ),
        allowed_symbols=["BTC/USDT", "ETH/USDT"],
        excluded_symbols=None,
        applicability_rules=None,
        ai_analysis_profile_id=None,
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# Tests for strategies endpoints
# =================================================================
class TestStrategiesEndpoints:

    @pytest.mark.asyncio
    async def test_create_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.create_strategy_config.return_value = sample_strategy_config

        response = await http_client.post(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Test Strategy",
                "base_strategy_type": "SCALPING",
                "parameters": {
                    "profit_target_percentage": 0.01,
                    "stop_loss_percentage": 0.005
                }
            }
        )

        assert response.status_code == 201
        assert response.json()["config_name"] == "Test Strategy"
        mock_strategy_service_integration.create_strategy_config.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_strategy_invalid_data(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        response = await http_client.post(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "", # Invalid data
                "base_strategy_type": "SCALPING",
                "parameters": {
                    "profit_target_percentage": 0.01,
                    "stop_loss_percentage": 0.005
                }
            }
        )

        assert response.status_code == 422 # Pydantic validation error
        mock_strategy_service_integration.create_strategy_config.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.create_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.post(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Test Strategy",
                "base_strategy_type": "SCALPING",
                "parameters": {
                    "profit_target_percentage": 0.01,
                    "stop_loss_percentage": 0.005
                }
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.create_strategy_config.assert_called_once()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_strategies_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.list_strategy_configs.return_value = [sample_strategy_config]

        response = await http_client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert len(response.json()["strategies"]) == 1
        assert response.json()["strategies"][0]["config_name"] == "Test Strategy"
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_strategies_empty(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.list_strategy_configs.return_value = []

        response = await http_client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert len(response.json()["strategies"]) == 0
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_list_strategies_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.list_strategy_configs.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.get_strategy_config.return_value = sample_strategy_config

        response = await http_client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert response.json()["id"] == sample_strategy_config.id
        mock_strategy_service_integration.get_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_strategy_not_found(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.get_strategy_config.return_value = None

        response = await http_client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 404
        assert f"Strategy {sample_strategy_config.id} not found" in response.json()["detail"]
        mock_strategy_service_integration.get_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.get_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.get_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        updated_config = sample_strategy_config.model_copy(update={"config_name": "Truly Updated Strategy"})
        mock_strategy_service_integration.update_strategy_config.return_value = updated_config

        response = await http_client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Truly Updated Strategy"
            }
        )

        assert response.status_code == 200
        assert response.json()["config_name"] == "Truly Updated Strategy"
        mock_strategy_service_integration.update_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, strategy_data={"config_name": "Truly Updated Strategy"})
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_strategy_not_found(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.update_strategy_config.return_value = None

        response = await http_client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Non Existent Strategy"
            }
        )

        assert response.status_code == 404
        assert f"Strategy {sample_strategy_config.id} not found" in response.json()["detail"]
        mock_strategy_service_integration.update_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, strategy_data={"config_name": "Non Existent Strategy"})
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_strategy_invalid_data(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        response = await http_client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "", # Invalid data
            }
        )

        assert response.status_code == 422 # Pydantic validation error
        mock_strategy_service_integration.update_strategy_config.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.update_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Some Name"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.update_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, strategy_data={"config_name": "Some Name"})
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.delete_strategy_config.return_value = True

        response = await http_client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 204 # No Content
        mock_strategy_service_integration.delete_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_strategy_not_found(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.delete_strategy_config.return_value = False

        response = await http_client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 404
        assert f"Strategy {sample_strategy_config.id} not found" in response.json()["detail"]
        mock_strategy_service_integration.delete_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.delete_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.delete_strategy_config.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        updated_config = sample_strategy_config.model_copy(update={"is_active_paper_mode": True})
        mock_strategy_service_integration.activate_strategy.return_value = updated_config

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 200
        assert response.json()["strategy_id"] == sample_strategy_config.id
        assert response.json()["is_active"] is True
        mock_strategy_service_integration.activate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_strategy_not_found(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.activate_strategy.return_value = None

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 404
        assert f"Strategy {sample_strategy_config.id} not found" in response.json()["detail"]
        mock_strategy_service_integration.activate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_strategy_invalid_mode(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "invalid"
            }
        )

        assert response.status_code == 422
        assert any('Value error, Mode must be "paper" or "real"' in err["msg"] for err in response.json()["detail"])
        mock_strategy_service_integration.activate_strategy.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_activate_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.activate_strategy.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.activate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_success(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        updated_config = sample_strategy_config.model_copy(update={"is_active_paper_mode": False})
        mock_strategy_service_integration.deactivate_strategy.return_value = updated_config

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 200
        assert response.json()["strategy_id"] == sample_strategy_config.id
        assert response.json()["is_active"] is False
        mock_strategy_service_integration.deactivate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_not_found(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.deactivate_strategy.return_value = None

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 404
        assert f"Strategy {sample_strategy_config.id} not found" in response.json()["detail"]
        mock_strategy_service_integration.deactivate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_invalid_mode(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "invalid"
            }
        )

        assert response.status_code == 422
        assert any('Value error, Mode must be "paper" or "real"' in err["msg"] for err in response.json()["detail"])
        mock_strategy_service_integration.deactivate_strategy.assert_not_called()
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_service_error(self, client: Tuple[AsyncClient, FastAPI], mock_strategy_service_integration: AsyncMock, sample_user_id: str, sample_strategy_config: TradingStrategyConfig):
        http_client, app = client
        app.dependency_overrides[get_strategy_service] = lambda: mock_strategy_service_integration
        mock_strategy_service_integration.deactivate_strategy.side_effect = HTTPException(status_code=500, detail="Service error")

        response = await http_client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.deactivate_strategy.assert_called_once_with(strategy_id=sample_strategy_config.id, user_id=sample_user_id, mode="paper")
        app.dependency_overrides.clear()
