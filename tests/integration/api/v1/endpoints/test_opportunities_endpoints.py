import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from ultibot_backend.api.v1.services.opportunities import OpportunitiesService
from ultibot_backend.api.v1.models.opportunities import AIAnalysisRequest, Opportunity

@pytest.fixture
def mock_opportunities_service():
    service = AsyncMock(spec=OpportunitiesService)
    return service

@pytest.fixture
def client(app, mock_opportunities_service):
    app.dependency_overrides[OpportunitiesService] = lambda: mock_opportunities_service
    with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_ai_analysis_request():
    return AIAnalysisRequest(
        symbol="BTCUSDT",
        interval="1h",
        strategy_name="test_strategy",
        parameters={"param1": "value1"},
        ai_model_name="test_model",
        ai_model_version="1.0",
        analysis_data={"data": "sample"},
        timestamp="2023-01-01T00:00:00Z"
    )

@pytest.fixture
def sample_opportunity():
    return Opportunity(
        id="test_id",
        symbol="BTCUSDT",
        interval="1h",
        strategy_name="test_strategy",
        entry_price=100.0,
        take_profit_price=110.0,
        stop_loss_price=90.0,
        timestamp="2023-01-01T00:00:00Z",
        status="open",
        ai_analysis_id="ai_analysis_123"
    )

class TestOpportunitiesEndpoints:
    async def test_create_ai_analysis_success(self, client, mock_opportunities_service, sample_ai_analysis_request):
        mock_opportunities_service.create_ai_analysis.return_value = {"message": "Analysis created successfully"}
        response = await client.post("/api/v1/gemini/opportunities", json=sample_ai_analysis_request.model_dump())
        assert response.status_code == 201
        assert response.json() == {"message": "Analysis created successfully"}
        mock_opportunities_service.create_ai_analysis.assert_called_once_with(sample_ai_analysis_request)

    async def test_create_ai_analysis_validation_error(self, client, mock_opportunities_service):
        response = await client.post("/api/v1/gemini/opportunities", json={})
        assert response.status_code == 422
        mock_opportunities_service.create_ai_analysis.assert_not_called()

    async def test_create_ai_analysis_internal_error(self, client, mock_opportunities_service, sample_ai_analysis_request):
        mock_opportunities_service.create_ai_analysis.side_effect = Exception("Internal server error")
        response = await client.post("/api/v1/gemini/opportunities", json=sample_ai_analysis_request.model_dump())
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    async def test_get_real_trading_candidates_success(self, client, mock_opportunities_service, sample_opportunity):
        mock_opportunities_service.get_real_trading_candidates.return_value = [sample_opportunity]
        response = await client.get("/api/v1/opportunities/real-trading-candidates")
        assert response.status_code == 200
        assert response.json() == [sample_opportunity.model_dump()]
        mock_opportunities_service.get_real_trading_candidates.assert_called_once()

    async def test_get_real_trading_candidates_no_candidates(self, client, mock_opportunities_service):
        mock_opportunities_service.get_real_trading_candidates.return_value = []
        response = await client.get("/api/v1/opportunities/real-trading-candidates")
        assert response.status_code == 200
        assert response.json() == []
        mock_opportunities_service.get_real_trading_candidates.assert_called_once()

    async def test_get_real_trading_candidates_internal_error(self, client, mock_opportunities_service):
        mock_opportunities_service.get_real_trading_candidates.side_effect = Exception("Database error")
        response = await client.get("/api/v1/opportunities/real-trading-candidates")
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]