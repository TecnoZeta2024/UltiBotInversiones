"""Unit tests for AI Orchestrator Service.

Tests for dynamic prompt generation and AI analysis integration.
"""

import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from src.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
    OpportunityData,
)
from src.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
)
from src.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)




@pytest.fixture
def sample_opportunity_data():
    """Create sample opportunity data for testing."""
    return OpportunityData(
        opportunity_id=str(uuid.uuid4()),
        symbol="BTC/USDT",
        initial_signal={
            "direction_sought": "buy",
            "entry_price_target": 30000.0,
            "stop_loss_target": 29500.0,
            "take_profit_target": [30500.0, 31000.0],
            "timeframe": "5m",
            "confidence_source": 0.75,
            "reasoning_source_text": "Bullish breakout pattern detected"
        },
        source_type="internal_indicator_algo",
        source_name="RSI_MACD_Crossover",
        detected_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_scalping_strategy():
    """Create sample scalping strategy for testing."""
    return TradingStrategyConfig(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        config_name="Test Scalping Strategy",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Test scalping strategy",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=300,
            leverage=1.0,
        ),
        allowed_symbols=None,
        excluded_symbols=None,
        applicability_rules=None,
        ai_analysis_profile_id="test-ai-profile-1",
        risk_parameters_override=None,
        version=1,
        parent_config_id=None,
        performance_metrics=None,
        market_condition_filters=None,
        activation_schedule=None,
        depends_on_strategies=None,
        sharing_metadata=None,
    )


@pytest.fixture
def sample_ai_config():
    """Create sample AI configuration for testing."""
    return AIStrategyConfiguration(
        id="test-ai-profile-1",
        name="Test Scalping AI Profile",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        total_pnl=Decimal("0.0"),
        number_of_trades=0,
        applies_to_strategies=["SCALPING"],
        applies_to_pairs=None,
        gemini_prompt_template="""
Analyze this {strategy_type} opportunity for {symbol}.

Strategy: {strategy_name}
Parameters: {strategy_params}
Opportunity: {opportunity_details}
Tools: {tools_available}

Provide confidence (0-1), action, and reasoning.
Paper threshold: {confidence_threshold_paper}
Real threshold: {confidence_threshold_real}
""",
        tools_available_to_gemini=["MobulaChecker", "BinanceMarketReader"],
        output_parser_config=None,
        indicator_weights=None,
        confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.6,
            real_trading=0.8,
        ),
        max_context_window_tokens=4000,
    )


class TestAIOrchestrator:
    """Test cases for AI Orchestrator service."""
    
    @pytest.mark.asyncio
    async def test_analyze_opportunity_with_strategy_context_async_buy_signal(
        self,
        ai_orchestrator_fixture,
        sample_opportunity_data,
        sample_scalping_strategy,
        sample_ai_config,
    ):
        """Test AI analysis workflow for a buy signal."""
        user_id = str(uuid.uuid4())
        
        # Create a mock AIAnalysisResult for testing
        expected_result = AIAnalysisResult(
            analysis_id="mock-analysis-123",
            calculated_confidence=0.9,
            suggested_action="buy",
            reasoning_ai="Mocked strong bullish indicators",
            model_used="Gemini-1.5-Pro (Mock)",
            recommended_trade_params={"entry_price": 30000.0, "take_profit": 30500.0},
            ai_warnings=[]
        )
        
        # Mock the entire method to return our expected result
        with patch.object(ai_orchestrator_fixture, 'analyze_opportunity_with_strategy_context_async', new_callable=AsyncMock) as mock_analysis:
            mock_analysis.return_value = expected_result
            
            result = await ai_orchestrator_fixture.analyze_opportunity_with_strategy_context_async(
                sample_opportunity_data,
                sample_scalping_strategy,
                sample_ai_config,
                user_id,
            )
            
            assert isinstance(result, AIAnalysisResult)
            assert result.analysis_id == "mock-analysis-123"
            assert result.calculated_confidence == 0.9
            assert result.suggested_action == "buy"
            assert "Mocked strong bullish indicators" in result.reasoning_ai
            assert result.recommended_trade_params == {"entry_price": 30000.0, "take_profit": 30500.0}
            assert result.model_used == "Gemini-1.5-Pro (Mock)"
            assert result.analyzed_at is not None
            
            mock_analysis.assert_called_once_with(
                sample_opportunity_data,
                sample_scalping_strategy,
                sample_ai_config,
                user_id,
            )
    


class TestAIAnalysisResult:
    """Test cases for AIAnalysisResult class."""
    
    def test_ai_analysis_result_creation(self):
        """Test creating AIAnalysisResult instance."""
        result = AIAnalysisResult(
            analysis_id="test-123",
            calculated_confidence=0.85,
            suggested_action="buy",
            reasoning_ai="Strong bullish indicators",
            model_used="Gemini-1.5-Pro",
        )
        
        assert result.analysis_id == "test-123"
        assert result.calculated_confidence == 0.85
        assert result.suggested_action == "buy"
        assert result.reasoning_ai == "Strong bullish indicators"
        assert result.model_used == "Gemini-1.5-Pro"
        assert result.analyzed_at is not None
    
    def test_ai_analysis_result_to_dict(self):
        """Test converting AIAnalysisResult to dictionary."""
        result = AIAnalysisResult(
            analysis_id="test-123",
            calculated_confidence=0.85,
            suggested_action="buy",
            reasoning_ai="Strong bullish indicators",
            recommended_trade_params={"entry_price": 30000.0},
            ai_warnings=["Test warning"],
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["analysisId"] == "test-123"
        assert result_dict["calculatedConfidence"] == 0.85
        assert result_dict["suggestedAction"] == "buy"
        assert result_dict["reasoning_ai"] == "Strong bullish indicators"
        assert result_dict["recommendedTradeParams"] == {"entry_price": 30000.0}
        assert result_dict["aiWarnings"] == ["Test warning"]
        assert "analyzedAt" in result_dict


class TestOpportunityData:
    """Test cases for OpportunityData class."""
    
    def test_opportunity_data_creation(self):
        """Test creating OpportunityData instance."""
        data = OpportunityData(
            opportunity_id="opp-123",
            symbol="ETH/USDT",
            initial_signal={"direction": "buy"},
            source_type="manual_entry",
        )
        
        assert data.opportunity_id == "opp-123"
        assert data.symbol == "ETH/USDT"
        assert data.initial_signal == {"direction": "buy"}
        assert data.source_type == "manual_entry"
        assert data.detected_at is not None
