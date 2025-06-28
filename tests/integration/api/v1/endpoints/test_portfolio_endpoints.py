import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from decimal import Decimal
from uuid import uuid4
from typing import Tuple
from fastapi import FastAPI

from shared.data_types import PortfolioSummary, PortfolioAsset, PortfolioSnapshot
from dependencies import get_portfolio_service

# Marcar todos los tests de este módulo como tests de integración
pytestmark = pytest.mark.integration

@pytest.fixture
def mock_portfolio_summary() -> PortfolioSummary:
    """
    Crea un objeto PortfolioSummary de ejemplo para usar en los mocks.
    """
    return PortfolioSummary(
        available_balance_usdt=Decimal('10000.00'),
        total_assets_value_usd=Decimal('5000.00'),
        total_portfolio_value_usd=Decimal('15000.00'),
        assets=[
            PortfolioAsset(
                symbol='BTC',
                quantity=Decimal('0.1'),
                entry_price=Decimal('45000.00'),
                current_price=Decimal('50000.00'),
                current_value_usd=Decimal('5000.00'),
                unrealized_pnl_usd=Decimal('500.00'),
                unrealized_pnl_percentage=Decimal('0.1')
            )
        ],
        error_message=None
    )

async def test_get_portfolio_summary_paper_success(
    client: Tuple[AsyncClient, FastAPI],
    mocker,
    mock_portfolio_summary: PortfolioSummary
):
    """
    Prueba que el endpoint /summary con trading_mode=paper responde correctamente.
    """
    http_client, app = client
    # 1. Mockear el servicio de portafolio
    mock_service = AsyncMock()
    mock_service._get_paper_trading_summary.return_value = mock_portfolio_summary
    
    # Sobrescribir la dependencia en la app
    app.dependency_overrides[get_portfolio_service] = lambda: mock_service
    
    # 2. Hacer la llamada a la API
    response = await http_client.get("/api/v1/portfolio/summary?trading_mode=paper")
    
    # 3. Verificar la respuesta
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["total_portfolio_value_usd"]) == mock_portfolio_summary.total_portfolio_value_usd
    assert len(data["assets"]) == 1
    assert data["assets"][0]["symbol"] == "BTC"
    
    # 4. Verificar que los mocks fueron llamados
    mock_service.initialize_portfolio.assert_awaited_once()
    mock_service._get_paper_trading_summary.assert_awaited_once()
    
    # Limpiar el override
    app.dependency_overrides = {}

async def test_get_portfolio_snapshot_success(
    client: Tuple[AsyncClient, FastAPI],
    mocker,
    mock_portfolio_snapshot: PortfolioSnapshot
):
    """
    Prueba que el endpoint /snapshot/{user_id} responde correctamente.
    """
    http_client, app = client
    user_id = uuid4()

    mock_service = AsyncMock()
    # El servicio debe devolver el objeto Pydantic completo
    mock_service.get_portfolio_snapshot.return_value = mock_portfolio_snapshot

    app.dependency_overrides[get_portfolio_service] = lambda: mock_service

    response = await http_client.get(f"/api/v1/portfolio/snapshot/{user_id}?trading_mode=both")

    assert response.status_code == 200
    data = response.json()
    
    # Verificar la estructura completa y los valores correctos
    assert "paper_trading" in data
    assert "real_trading" in data
    assert Decimal(data["paper_trading"]["total_portfolio_value_usd"]) == mock_portfolio_snapshot.paper_trading.total_portfolio_value_usd
    assert Decimal(data["real_trading"]["total_portfolio_value_usd"]) == mock_portfolio_snapshot.real_trading.total_portfolio_value_usd
    
    mock_service.get_portfolio_snapshot.assert_awaited_once_with(user_id, "both")

    app.dependency_overrides = {}
