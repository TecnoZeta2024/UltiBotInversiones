"""Unit tests for AI Orchestrator Service.

Tests for dynamic prompt generation and AI analysis integration.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
    OpportunityData,
)
from ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
)
from ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)


@pytest.fixture
def ai_orchestrator():
    """Create an AI Orchestrator instance for testing."""
    return AIOrchestrator()


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
        ),
        ai_analysis_profile_id="test-ai-profile-1",
    )


@pytest.fixture
def sample_ai_config():
    """Create sample AI configuration for testing."""
    return AIStrategyConfiguration(
        id="test-ai-profile-1",
        name="Test Scalping AI Profile",
        applies_to_strategies=["SCALPING"],
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
        confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.6,
            real_trading=0.8,
        ),
        max_context_window_tokens=4000,
    )


class TestAIOrchestrator:
    """Test cases for AI Orchestrator service."""
    
    def test_build_dynamic_prompt_basic(
        self, 
        ai_orchestrator, 
        sample_opportunity_data, 
        sample_scalping_strategy, 
        sample_ai_config
    ):
        """Test basic dynamic prompt generation."""
        prompt = ai_orchestrator._build_dynamic_prompt(
            sample_opportunity_data,
            sample_scalping_strategy,
            sample_ai_config,
        )
        
        # Check that key placeholders were replaced
        assert "SCALPING" in prompt
        assert "BTC/USDT" in prompt
        assert "Test Scalping Strategy" in prompt
        assert "profit_target_percentage" in prompt
        assert "MobulaChecker" in prompt
        assert "0.60" in prompt  # Paper trading threshold
        assert "0.80" in prompt  # Real trading threshold
    
    def test_build_dynamic_prompt_custom_template(
        self, 
        ai_orchestrator, 
        sample_opportunity_data, 
        sample_scalping_strategy, 
        sample_ai_config
    ):
        """Test dynamic prompt generation with custom template."""
        # Modify AI config with custom template
        sample_ai_config.gemini_prompt_template = "Custom template for {strategy_type} with {symbol}"
        
        prompt = ai_orchestrator._build_dynamic_prompt(
            sample_opportunity_data,
            sample_scalping_strategy,
            sample_ai_config,
        )
        
        assert "Custom template for SCALPING with BTC/USDT" in prompt
    
    def test_format_strategy_parameters_scalping(
        self, 
        ai_orchestrator, 
        sample_scalping_strategy
    ):
        """Test formatting of scalping strategy parameters."""
        formatted = ai_orchestrator._format_strategy_parameters(sample_scalping_strategy)
        
        assert "profit_target_percentage: 0.01" in formatted
        assert "stop_loss_percentage: 0.005" in formatted
        assert "max_holding_time_seconds: 300" in formatted
    
    def test_format_opportunity_details(
        self, 
        ai_orchestrator, 
        sample_opportunity_data
    ):
        """Test formatting of opportunity details."""
        formatted = ai_orchestrator._format_opportunity_details(sample_opportunity_data)
        
        assert "Symbol: BTC/USDT" in formatted
        assert "Source: internal_indicator_algo" in formatted
        assert "direction_sought: buy" in formatted
        assert "entry_price_target: 30000.0" in formatted
    
    def test_format_tools_description(self, ai_orchestrator):
        """Test formatting of tools description."""
        tools = ["MobulaChecker", "BinanceMarketReader", "TechnicalIndicators"]
        formatted = ai_orchestrator._format_tools_description(tools)
        
        assert "Real-time price and market data verification" in formatted
        assert "Binance market data and order book analysis" in formatted
        assert "Technical analysis indicators" in formatted
    
    def test_format_tools_description_empty(self, ai_orchestrator):
        """Test formatting of empty tools list."""
        formatted = ai_orchestrator._format_tools_description([])
        assert "No specific tools configured" in formatted
    
    def test_get_confidence_threshold_from_ai_config(
        self, 
        ai_orchestrator, 
        sample_ai_config
    ):
        """Test getting confidence threshold from AI config."""
        paper_threshold = ai_orchestrator._get_confidence_threshold(sample_ai_config, "paper")
        real_threshold = ai_orchestrator._get_confidence_threshold(sample_ai_config, "real")
        
        assert paper_threshold == 0.6
        assert real_threshold == 0.8
    
    def test_get_confidence_threshold_defaults(self, ai_orchestrator):
        """Test getting default confidence thresholds."""
        ai_config = AIStrategyConfiguration(
            id="test",
            name="test",
            confidence_thresholds=None,
        )
        
        paper_threshold = ai_orchestrator._get_confidence_threshold(ai_config, "paper")
        real_threshold = ai_orchestrator._get_confidence_threshold(ai_config, "real")
        
        assert paper_threshold == 0.6  # Default
        assert real_threshold == 0.8   # Default
    
    @pytest.mark.asyncio
    async def test_mock_gemini_analysis_scalping(
        self,
        ai_orchestrator,
        sample_opportunity_data,
        sample_scalping_strategy,
        sample_ai_config,
    ):
        """Test mock Gemini analysis for scalping strategy."""
        analysis_id = "test-analysis-123"
        prompt = "test prompt"
        
        result = await ai_orchestrator._mock_gemini_analysis(
            analysis_id,
            prompt,
            sample_opportunity_data,
            sample_scalping_strategy,
            sample_ai_config,
        )
        
        assert isinstance(result, AIAnalysisResult)
        assert result.analysis_id == analysis_id
        assert 0 <= result.calculated_confidence <= 1
        assert result.suggested_action in ["buy", "sell", "hold_neutral", "further_investigation_needed"]
        assert result.reasoning_ai is not None
        assert result.model_used == "Gemini-1.5-Pro (Mock)"
        assert "mock analysis" in result.ai_warnings[0].lower()
    
    @pytest.mark.asyncio
    async def test_analyze_opportunity_with_strategy_context_async(
        self,
        ai_orchestrator,
        sample_opportunity_data,
        sample_scalping_strategy,
        sample_ai_config,
    ):
        """Test full AI analysis workflow."""
        user_id = str(uuid.uuid4())
        
        result = await ai_orchestrator.analyze_opportunity_with_strategy_context_async(
            sample_opportunity_data,
            sample_scalping_strategy,
            sample_ai_config,
            user_id,
        )
        
        assert isinstance(result, AIAnalysisResult)
        assert result.analysis_id is not None
        assert result.analyzed_at is not None
        assert result.processing_time_ms is not None
        assert result.processing_time_ms > 0
    
    def test_log_prompt_summary(self, ai_orchestrator, caplog):
        """Test prompt summary logging."""
        prompt = "This is a test prompt that is longer than 100 characters and should be truncated in the log for security and readability purposes."
        analysis_id = "test-123"
        
        ai_orchestrator.log_prompt_summary(prompt, analysis_id)
        
        # Check that log was created with truncated prompt
        assert "AI Analysis test-123" in caplog.text
        assert "length: " in caplog.text
        assert "This is a test prompt that is longer than 100 characters and should be truncated in the log" in caplog.text


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
