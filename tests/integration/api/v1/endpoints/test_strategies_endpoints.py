
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import HTTPException

from src.ultibot_backend.main import app
from tests.conftest import mock_strategy_service_integration
from src.ultibot_backend.services.strategy_service import StrategyService
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig, BaseStrategyType, ScalpingParameters

# Fixture for TestClient
@pytest.fixture(scope="module")
def client(mock_strategy_service_integration):
    app.dependency_overrides[StrategyService] = lambda: mock_strategy_service_integration
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {} # Clean up overrides after tests

# Sample data
@pytest.fixture
def sample_user_id():
    return str(uuid4())

@pytest.fixture
def sample_strategy_config(sample_user_id):
    return TradingStrategyConfig(
        id=str(uuid4()),
        user_id=sample_user_id,
        config_name="Test Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        parameters=ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.005)
    )

# Tests for strategies endpoints
# =================================================================
class TestStrategiesEndpoints:

    @pytest.mark.asyncio
    async def test_create_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service_integration.create_strategy_config.return_value = sample_strategy_config

        response = client.post(
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

    @pytest.mark.asyncio
    async def test_create_strategy_invalid_data(self, client, mock_strategy_service_integration, sample_user_id):
        response = client.post(
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

    @pytest.mark.asyncio
    async def test_create_strategy_service_error(self, client, mock_strategy_service_integration, sample_user_id):
        mock_strategy_service_integration.create_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.post(
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

    @pytest.mark.asyncio
    async def test_list_strategies_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service_integration.list_strategy_configs.return_value = [sample_strategy_config]

        response = client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert len(response.json()["strategies"]) == 1
        assert response.json()["strategies"][0]["config_name"] == "Test Strategy"
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_list_strategies_empty(self, client, mock_strategy_service_integration, sample_user_id):
        mock_strategy_service_integration.list_strategy_configs.return_value = []

        response = client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert len(response.json()["strategies"]) == 0
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_list_strategies_service_error(self, client, mock_strategy_service_integration, sample_user_id):
        mock_strategy_service_integration.list_strategy_configs.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.get(
            "/api/v1/strategies",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service_integration.list_strategy_configs.assert_called_once_with(sample_user_id)

    @pytest.mark.asyncio
    async def test_get_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service_integration.get_strategy_config.return_value = sample_strategy_config

        response = client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 200
        assert response.json()["id"] == sample_strategy_config.id
        mock_strategy_service_integration.get_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_strategy_not_found(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service_integration.get_strategy_config.return_value = None

        response = client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_strategy_service.get_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_get_strategy_service_error(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service_integration.get_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.get(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service.get_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_update_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        updated_config = sample_strategy_config.model_copy(update={"config_name": "Truly Updated Strategy"})
        mock_strategy_service.update_strategy_config.return_value = updated_config

        response = client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Truly Updated Strategy"
            }
        )

        assert response.status_code == 200
        assert response.json()["config_name"] == "Truly Updated Strategy"
        mock_strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_strategy_not_found(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.update_strategy_config.return_value = None

        response = client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Non Existent Strategy"
            }
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_strategy_invalid_data(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        response = client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "", # Invalid data
            }
        )

        assert response.status_code == 422 # Pydantic validation error
        mock_strategy_service.update_strategy_config.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_strategy_service_error(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.update_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.put(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id},
            json={
                "config_name": "Some Name"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service.update_strategy_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.delete_strategy_config.return_value = True

        response = client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 204 # No Content
        mock_strategy_service.delete_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_delete_strategy_not_found(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.delete_strategy_config.return_value = False

        response = client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_strategy_service.delete_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_delete_strategy_service_error(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.delete_strategy_config.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.delete(
            f"/api/v1/strategies/{sample_strategy_config.id}",
            headers={"X-User-ID": sample_user_id}
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service.delete_strategy_config.assert_called_once_with(sample_strategy_config.id, sample_user_id)

    @pytest.mark.asyncio
    async def test_activate_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        updated_config = sample_strategy_config.model_copy(update={"is_active_paper_mode": True})
        mock_strategy_service.activate_strategy.return_value = updated_config

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 200
        assert response.json()["strategy_id"] == sample_strategy_config.id
        assert response.json()["is_active"] is True
        mock_strategy_service.activate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

    @pytest.mark.asyncio
    async def test_activate_strategy_not_found(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.activate_strategy.return_value = None

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_strategy_service.activate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

    @pytest.mark.asyncio
    async def test_activate_strategy_invalid_mode(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "invalid"
            }
        )

        assert response.status_code == 400
        assert "Mode must be 'paper' or 'real'" in response.json()["detail"]
        mock_strategy_service.activate_strategy.assert_not_called()

    @pytest.mark.asyncio
    async def test_activate_strategy_service_error(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.activate_strategy.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/activate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service.activate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

    @pytest.mark.asyncio
    async def test_deactivate_strategy_success(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        updated_config = sample_strategy_config.model_copy(update={"is_active_paper_mode": False})
        mock_strategy_service.deactivate_strategy.return_value = updated_config

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 200
        assert response.json()["strategy_id"] == sample_strategy_config.id
        assert response.json()["is_active"] is False
        mock_strategy_service.deactivate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

    @pytest.mark.asyncio
    async def test_deactivate_strategy_not_found(self, client, mock_strategy_service_integration, sample_user_id, sample_strategy_config):
        mock_strategy_service.deactivate_strategy.return_value = None

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 404
        assert "Strategy not found" in response.json()["detail"]
        mock_strategy_service.deactivate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

    @pytest.mark.asyncio
    async def test_deactivate_strategy_invalid_mode(self, client, mock_strategy_service, sample_user_id, sample_strategy_config):
        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "invalid"
            }
        )

        assert response.status_code == 400
        assert "Mode must be 'paper' or 'real'" in response.json()["detail"]
        mock_strategy_service.deactivate_strategy.assert_not_called()

    @pytest.mark.asyncio
    async def test_deactivate_strategy_service_error(self, client, mock_strategy_service, sample_user_id, sample_strategy_config):
        mock_strategy_service.deactivate_strategy.side_effect = HTTPException(status_code=500, detail="Service error")

        response = client.patch(
            f"/api/v1/strategies/{sample_strategy_config.id}/deactivate",
            headers={"X-User-ID": sample_user_id},
            json={
                "mode": "paper"
            }
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Service error"
        mock_strategy_service.deactivate_strategy.assert_called_once_with(sample_strategy_config.id, sample_user_id, "paper")

