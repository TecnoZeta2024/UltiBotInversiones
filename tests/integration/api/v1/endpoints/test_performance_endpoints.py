import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
from httpx import AsyncClient
from typing import Tuple
from fastapi import FastAPI

from src.dependencies import get_performance_service
from src.api.v1.models.performance_models import StrategyPerformanceData, OperatingMode

# No se necesitan más importaciones de dominio o servicio, ya que el servicio está completamente mockeado.

@pytest.mark.asyncio
@patch('services.performance_service.PerformanceService.get_all_strategies_performance', new_callable=AsyncMock)
async def test_get_strategies_performance_endpoint_no_data(
    mock_get_all_perf: AsyncMock,
    client: Tuple[AsyncClient, FastAPI],
    user_id: UUID
):
    """
    Test GET /api/v1/performance/strategies when no performance data is available.
    Verifies the endpoint correctly calls the service and returns an empty list.
    """
    test_client, app = client
    
    # Arrange: Configure the mock provided by the @patch decorator
    mock_get_all_perf.return_value = []
    
    # Act: Call the endpoint
    response = await test_client.get("/api/v1/performance/strategies")
    
    # Assert: Check the response and that the service was called correctly
    assert response.status_code == 200
    assert response.json() == []
    mock_get_all_perf.assert_called_once_with(user_id=user_id, mode_filter=None)


@pytest.mark.asyncio
@patch('services.performance_service.PerformanceService.get_all_strategies_performance', new_callable=AsyncMock)
async def test_get_strategies_performance_endpoint_with_paper_data(
    mock_get_all_perf: AsyncMock,
    client: Tuple[AsyncClient, FastAPI],
    user_id: UUID
):
    """
    Test GET /api/v1/performance/strategies filtering by 'paper' mode.
    Verifies the endpoint calls the service with the correct mode and returns the mocked data.
    """
    test_client, app = client

    # Arrange: Configure the mock
    paper_performance = [
        StrategyPerformanceData(
            strategyId=UUID("11111111-1111-1111-1111-111111111111"),
            strategyName="Paper Strategy 1",
            mode=OperatingMode.PAPER,
            totalOperations=5,
            totalPnl=500.0,
            win_rate=80.0
        )
    ]
    mock_get_all_perf.return_value = paper_performance
    
    # Act: Call the endpoint with the 'paper' filter
    response = await test_client.get("/api/v1/performance/strategies?mode=paper")
    
    # Assert: Check the response and that the service was called correctly
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["strategyId"] == "11111111-1111-1111-1111-111111111111"
    assert data[0]["mode"] == "paper"
    mock_get_all_perf.assert_called_once_with(user_id=user_id, mode_filter='paper')


@pytest.mark.asyncio
@patch('services.performance_service.PerformanceService.get_all_strategies_performance', new_callable=AsyncMock)
async def test_get_strategies_performance_endpoint_with_real_data(
    mock_get_all_perf: AsyncMock,
    client: Tuple[AsyncClient, FastAPI],
    user_id: UUID
):
    """
    Test GET /api/v1/performance/strategies filtering by 'real' mode.
    Verifies the endpoint calls the service with the correct mode and returns the mocked data.
    """
    test_client, app = client

    # Arrange: Configure the mock
    real_performance = [
        StrategyPerformanceData(
            strategyId=UUID("22222222-2222-2222-2222-222222222222"),
            strategyName="Real Strategy 1",
            mode=OperatingMode.REAL,
            totalOperations=3,
            totalPnl=750.0,
            win_rate=100.0
        )
    ]
    mock_get_all_perf.return_value = real_performance
    
    # Act: Call the endpoint with the 'real' filter
    response = await test_client.get("/api/v1/performance/strategies?mode=real")
    
    # Assert: Check the response and that the service was called correctly
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["strategyId"] == "22222222-2222-2222-2222-222222222222"
    assert data[0]["mode"] == "real"
    mock_get_all_perf.assert_called_once_with(user_id=user_id, mode_filter='real')


@pytest.mark.asyncio
@patch('services.performance_service.PerformanceService.get_all_strategies_performance', new_callable=AsyncMock)
async def test_get_strategies_performance_endpoint_no_mode_filter(
    mock_get_all_perf: AsyncMock,
    client: Tuple[AsyncClient, FastAPI],
    user_id: UUID
):
    """
    Test GET /api/v1/performance/strategies without the 'mode' query parameter.
    It should return performance data for all modes.
    """
    test_client, app = client

    # Arrange: Configure mock to return data for multiple modes
    all_performance = [
        StrategyPerformanceData(
            strategyId=UUID("11111111-1111-1111-1111-111111111111"),
            strategyName="Paper Strategy 1",
            mode=OperatingMode.PAPER,
            totalOperations=5,
            totalPnl=500.0,
            win_rate=80.0
        ),
        StrategyPerformanceData(
            strategyId=UUID("22222222-2222-2222-2222-222222222222"),
            strategyName="Real Strategy 1",
            mode=OperatingMode.REAL,
            totalOperations=3,
            totalPnl=750.0,
            win_rate=100.0
        )
    ]
    mock_get_all_perf.return_value = all_performance
    
    # Act: Call the endpoint without the 'mode' filter
    response = await test_client.get("/api/v1/performance/strategies")
    
    # Assert: Check the response and that the service was called correctly
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    mock_get_all_perf.assert_called_once_with(user_id=user_id, mode_filter=None)


@pytest.mark.asyncio
async def test_get_strategies_performance_endpoint_invalid_mode_parameter(client: Tuple[AsyncClient, FastAPI]):
    """
    Test GET /api/v1/performance/strategies with an invalid 'mode' query parameter.
    FastAPI should return a 422 Unprocessable Entity error.
    This test uses the standard 'client' fixture as it doesn't need DB or dependency overrides.
    """
    test_client, _ = client
    # Act: Call the endpoint with an invalid mode
    response = await test_client.get("/api/v1/performance/strategies?mode=invalid_mode")
    
    # Assert: Check for the validation error
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert any(
        err["type"] == "enum" and err["loc"] == ["query", "mode"]
        for err in data["detail"]
    )
