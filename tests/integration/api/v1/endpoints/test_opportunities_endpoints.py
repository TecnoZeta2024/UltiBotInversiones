import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple

from core.domain_models.opportunity_models import (
    AIAnalysisRequest,
    Opportunity,
    OpportunityStatus,
    InitialSignal,
    SourceType,
    Direction,
    SuggestedAction,
    AIAnalysis,
    RecommendedTradeParams,
)
from adapters.persistence_service import SupabasePersistenceService
from services.config_service import ConfigurationService
from core.domain_models.user_configuration_models import UserConfiguration, RealTradingSettings
from fastapi import FastAPI
import dependencies as deps

# Fixtures para datos de prueba (pueden permanecer igual)
@pytest.fixture
def initial_signal_fixture():
    return InitialSignal(
        direction_sought=Direction.BUY,
        entry_price_target=Decimal("100.0"),
        stop_loss_target=Decimal("95.0"),
        take_profit_target=[Decimal("105.0"), Decimal("110.0")],
        timeframe="1h",
        reasoning_source_text="Strong bullish signal from external source.",
        confidence_source=0.9,
        reasoning_source_structured=None,
    )

@pytest.fixture
def ai_analysis_fixture():
    return AIAnalysis(
        analyzed_at=datetime.now(timezone.utc),
        calculated_confidence=0.85,
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="AI detected strong buy signal based on multiple indicators.",
        recommended_trade_params=RecommendedTradeParams(
            entry_price=Decimal("100.5"),
            stop_loss_price=Decimal("98.0"),
            take_profit_levels=[Decimal("103.0"), Decimal("106.0")],
            trade_size_percentage=Decimal("0.05"),
        ),
        analysis_id=None,
        model_used=None,
        recommended_trade_strategy_type=None,
        data_verification=None,
        processing_time_ms=None,
        ai_warnings=None,
    )

@pytest.fixture
def opportunity_fixture(initial_signal_fixture: InitialSignal, ai_analysis_fixture: AIAnalysis):
    return Opportunity(
        id=str(uuid4()),
        user_id=str(uuid4()),
        symbol="BTCUSDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.AI_SUGGESTION_PROACTIVE,
        initial_signal=initial_signal_fixture,
        status=OpportunityStatus.NEW,
        ai_analysis=ai_analysis_fixture,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        strategy_id=None,
        exchange="binance",
        source_name=None,
        source_data=None,
        system_calculated_priority_score=None,
        last_priority_calculation_at=None,
        status_reason_code=None,
        status_reason_text=None,
        investigation_details=None,
        user_feedback=None,
        linked_trade_ids=None,
        expires_at=None,
        expiration_logic=None,
        post_trade_feedback=None,
        post_facto_simulation_results=None,
    )

@pytest.fixture
def ai_analysis_request_fixture(opportunity_fixture: Opportunity):
    return AIAnalysisRequest(opportunities=[opportunity_fixture])

class TestOpportunitiesEndpoints:
    """Integration tests for the opportunities endpoints, aligned with actual implementation."""

    async def test_get_gemini_opportunities_success(
        self, client_with_db: AsyncClient, persistence_service_fixture: MagicMock, opportunity_fixture: Opportunity
    ):
        """Test GET /api/v1/gemini/opportunities - currently returns an empty list."""
        # El endpoint real devuelve una lista vacía por ahora.
        response = await client_with_db.get("/api/v1/gemini/opportunities")
        assert response.status_code == 200
        assert response.json() == []

    async def test_post_gemini_opportunities_success(
        self,
        client_with_db: AsyncClient,
        ai_analysis_request_fixture: AIAnalysisRequest,
    ):
        """
        Test POST /api/v1/gemini/opportunities for success.
        The endpoint currently echoes the request's opportunities.
        """
        # El endpoint real devuelve las oportunidades del request con un mensaje.
        response = await client_with_db.post(
            "/api/v1/gemini/opportunities", json=ai_analysis_request_fixture.model_dump(mode='json')
        )
        assert response.status_code == 200 # El endpoint devuelve 200, no 201
        
        response_data = response.json()
        assert response_data["message"] == "AI analysis processed successfully"
        # Compara el contenido de las oportunidades
        assert response_data["opportunities"] == ai_analysis_request_fixture.model_dump(mode='json')["opportunities"]

    async def test_post_gemini_opportunities_invalid_data(
        self,
        client_with_db: AsyncClient,
    ):
        """
        Test POST /api/v1/gemini/opportunities with invalid data.
        """
        invalid_payload = {
            "opportunities": [
                {
                    "id": "invalid-uuid", # Invalid UUID
                    "symbol": "BTCUSDT",
                    "detected_at": "not-a-date", # Invalid date
                    "source_type": "INVALID_SOURCE", # Invalid enum
                    "initial_signal": {}, # Missing required fields
                    "status": "NEW"
                }
            ]
        }
        response = await client_with_db.post(
            "/api/v1/gemini/opportunities", json=invalid_payload
        )
        assert response.status_code == 422 # Unprocessable Entity
        response_data = response.json()
        assert "detail" in response_data
        assert any("value is not a valid uuid" in error["msg"] for error in response_data["detail"])
        assert any("invalid datetime format" in error["msg"] for error in response_data["detail"])
        assert any("value is not a valid enumeration member" in error["msg"] for error in response_data["detail"])
        assert any("field required" in error["msg"] for error in response_data["detail"])

    async def test_get_real_trading_candidates_success(
        self, client: Tuple[AsyncClient, FastAPI], mock_user_config: UserConfiguration, opportunity_fixture: Opportunity
    ):
        """Test GET /api/v1/opportunities/real-trading-candidates for success."""
        http_client, app = client
        mock_persistence = AsyncMock(spec=SupabasePersistenceService)
        mock_config = AsyncMock(spec=ConfigurationService)

        if mock_user_config.real_trading_settings is None:
            mock_user_config.real_trading_settings = RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_concurrent_operations=0,
                daily_loss_limit_absolute=None,
                daily_profit_target_absolute=None,
                asset_specific_stop_loss=None,
                auto_pause_trading_conditions=None,
                daily_capital_risked_usd=Decimal("0"),
                last_daily_reset=None
            )
        mock_user_config.real_trading_settings.real_trading_mode_active = True
        
        mock_config.get_user_configuration.return_value = mock_user_config
        mock_persistence.get_all.return_value = [opportunity_fixture]

        app.dependency_overrides[deps.get_persistence_service] = lambda: mock_persistence
        app.dependency_overrides[deps.get_config_service] = lambda: mock_config

        response = await http_client.get("/api/v1/opportunities/real-trading-candidates")
        
        assert response.status_code == 200
        assert response.json() == [opportunity_fixture.model_dump(mode='json')]
        
        mock_config.get_user_configuration.assert_called_once()
        mock_persistence.get_all.assert_called_once_with(
            table_name="opportunities",
            condition="status = :status",
            params={"status": OpportunityStatus.PENDING_USER_CONFIRMATION_REAL.value}
        )

        app.dependency_overrides.clear()

    async def test_get_real_trading_candidates_service_error(
        self, client: Tuple[AsyncClient, FastAPI], mock_user_config: UserConfiguration
    ):
        """Test GET /api/v1/opportunities/real-trading-candidates when persistence service fails."""
        http_client, app = client
        mock_persistence = AsyncMock(spec=SupabasePersistenceService)
        mock_config = AsyncMock(spec=ConfigurationService)

        if mock_user_config.real_trading_settings is None:
            mock_user_config.real_trading_settings = RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_concurrent_operations=0,
                daily_loss_limit_absolute=None,
                daily_profit_target_absolute=None,
                asset_specific_stop_loss=None,
                auto_pause_trading_conditions=None,
                daily_capital_risked_usd=Decimal("0"),
                last_daily_reset=None
            )
        mock_user_config.real_trading_settings.real_trading_mode_active = True # Ensure active for this test
        
        mock_config.get_user_configuration.return_value = mock_user_config
        mock_persistence.get_all.side_effect = Exception("Database connection failed")

        app.dependency_overrides[deps.get_persistence_service] = lambda: mock_persistence
        app.dependency_overrides[deps.get_config_service] = lambda: mock_config

        response = await http_client.get("/api/v1/opportunities/real-trading-candidates")
        
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]
        
        mock_config.get_user_configuration.assert_called_once()
        mock_persistence.get_all.assert_called_once()

        app.dependency_overrides.clear()

    async def test_get_real_trading_candidates_mode_inactive(
        self, client: Tuple[AsyncClient, FastAPI], mock_user_config: UserConfiguration
    ):
        """Test GET /api/v1/opportunities/real-trading-candidates when real trading mode is inactive."""
        http_client, app = client
        mock_config = AsyncMock(spec=ConfigurationService)
        
        if mock_user_config.real_trading_settings is None:
            mock_user_config.real_trading_settings = RealTradingSettings(
                real_trading_mode_active=False,
                real_trades_executed_count=0,
                max_concurrent_operations=0,
                daily_loss_limit_absolute=None,
                daily_profit_target_absolute=None,
                asset_specific_stop_loss=None,
                auto_pause_trading_conditions=None,
                daily_capital_risked_usd=Decimal("0"),
                last_daily_reset=None
            )
        mock_user_config.real_trading_settings.real_trading_mode_active = False
        mock_config.get_user_configuration.return_value = mock_user_config

        app.dependency_overrides[deps.get_config_service] = lambda: mock_config

        response = await http_client.get("/api/v1/opportunities/real-trading-candidates")
        
        assert response.status_code == 403
        assert response.json() == {"detail": "El modo de trading real no está activo para este usuario."}

        app.dependency_overrides.clear()
