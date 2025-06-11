"""Integration tests for Strategy-AI-TradingEngine flow.

Tests for the complete workflow: Strategy -> AI_Orchestrator -> Trading Decision.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from src.ultibot_backend.services.trading_engine_service import (
    TradingEngine,
    TradingDecision,
)
from src.ultibot_backend.services.ai_orchestrator_service import (
    AIOrchestrator,
    AIAnalysisResult,
)
from src.ultibot_backend.core.domain_models.trading_strategy_models import (
    TradingStrategyConfig,
    BaseStrategyType,
    ScalpingParameters,
    DayTradingParameters,
)
from src.ultibot_backend.core.domain_models.user_configuration_models import (
    AIStrategyConfiguration,
    ConfidenceThresholds,
)
from src.ultibot_backend.core.domain_models.opportunity_models import (
    Opportunity,
    OpportunityStatus,
    SourceType,
    Direction,
    InitialSignal,
)


@pytest.fixture
def mock_strategy_service():
    """Create mock strategy service."""
    service = Mock()
    service.strategy_requires_ai_analysis = AsyncMock(return_value=True)
    service.strategy_can_operate_autonomously = AsyncMock(return_value=True)
    service.get_ai_configuration_for_strategy = AsyncMock()
    service.get_effective_confidence_thresholds_for_strategy = AsyncMock()
    return service


@pytest.fixture
def mock_configuration_service():
    """Create mock configuration service."""
    service = Mock()
    return service


@pytest.fixture
def mock_ai_orchestrator():
    """Create mock AI orchestrator."""
    orchestrator = Mock(spec=AIOrchestrator)
    orchestrator.analyze_opportunity_with_strategy_context_async = AsyncMock()
    return orchestrator


@pytest.fixture
def trading_engine(mock_strategy_service, mock_configuration_service, mock_ai_orchestrator):
    """Create trading engine with mocked dependencies."""
    return TradingEngine(
        strategy_service=mock_strategy_service,
        configuration_service=mock_configuration_service,
        ai_orchestrator=mock_ai_orchestrator,
    )


@pytest.fixture
def sample_opportunity():
    """Create sample opportunity for testing."""
    return Opportunity(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        symbol="BTC/USDT",
        detected_at=datetime.now(timezone.utc),
        source_type=SourceType.INTERNAL_INDICATOR_ALGO,
        source_name="RSI_MACD_Signal",
        initial_signal=InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=30000.0,
            stop_loss_target=29500.0,
            take_profit_target=[30500.0, 31000.0],
            timeframe="5m",
            confidence_source=0.75,
            reasoning_source_text="Strong bullish momentum detected",
        ),
        status=OpportunityStatus.NEW,
    )


@pytest.fixture
def scalping_strategy_with_ai():
    """Create scalping strategy configured to use AI."""
    return TradingStrategyConfig(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        config_name="AI-Enhanced Scalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Scalping strategy with AI analysis",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=300,
        ),
        ai_analysis_profile_id="ai-profile-scalping-1",
    )


@pytest.fixture
def scalping_strategy_without_ai():
    """Create scalping strategy configured to operate autonomously."""
    return TradingStrategyConfig(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        config_name="Autonomous Scalping",
        base_strategy_type=BaseStrategyType.SCALPING,
        description="Autonomous scalping strategy",
        is_active_paper_mode=True,
        is_active_real_mode=False,
        parameters=ScalpingParameters(
            profit_target_percentage=0.015,
            stop_loss_percentage=0.008,
        ),
        ai_analysis_profile_id=None,  # No AI configured
    )


@pytest.fixture
def ai_config_scalping():
    """Create AI configuration for scalping."""
    return AIStrategyConfiguration(
        id="ai-profile-scalping-1",
        name="Scalping AI Profile",
        applies_to_strategies=["SCALPING"],
        confidence_thresholds=ConfidenceThresholds(
            paper_trading=0.6,
            real_trading=0.8,
        ),
        tools_available_to_gemini=["MobulaChecker", "BinanceMarketReader"],
    )


class TestStrategyAITradingEngineIntegration:
    """Integration tests for Strategy-AI-TradingEngine workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow_high_confidence(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
        ai_config_scalping,
        mock_strategy_service,
        mock_ai_orchestrator,
    ):
        """Test complete workflow with AI analysis resulting in high confidence trade execution."""
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        
        # Mock AI analysis result with high confidence
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-123",
            calculated_confidence=0.85,
            suggested_action="buy",
            reasoning_ai="Strong bullish indicators with favorable risk/reward ratio",
            recommended_trade_params={"entry_price": 30000.0, "stop_loss": 29500.0},
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Execute evaluation
        decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_with_ai,
            mode="paper",
        )
        
        # Verify decision
        assert isinstance(decision, TradingDecision)
        assert decision.decision == "execute_trade"
        assert decision.confidence == 0.85
        assert decision.ai_analysis_used is True
        assert decision.ai_analysis_profile_id == "ai-profile-scalping-1"
        assert "bullish indicators" in decision.reasoning
        
        # Verify AI orchestrator was called correctly
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_called_once()
        call_args = mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.call_args
        assert call_args[1]["strategy"] == scalping_strategy_with_ai
        assert call_args[1]["ai_config"] == ai_config_scalping
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow_low_confidence(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
        ai_config_scalping,
        mock_strategy_service,
        mock_ai_orchestrator,
    ):
        """Test complete workflow with AI analysis resulting in low confidence rejection."""
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        
        # Mock AI analysis result with low confidence
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-456",
            calculated_confidence=0.4,  # Below paper trading threshold of 0.6
            suggested_action="hold_neutral",
            reasoning_ai="Mixed signals, insufficient confidence for trade execution",
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Execute evaluation
        decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_with_ai,
            mode="paper",
        )
        
        # Verify decision
        assert decision.decision == "reject_opportunity"
        assert decision.confidence == 0.4
        assert decision.ai_analysis_used is True
        assert "below threshold" in decision.reasoning
    
    @pytest.mark.asyncio
    async def test_ai_failure_fallback_to_autonomous(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
        ai_config_scalping,
        mock_strategy_service,
        mock_ai_orchestrator,
    ):
        """Test fallback to autonomous evaluation when AI analysis fails."""
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service.strategy_can_operate_autonomously.return_value = True
        
        # Mock AI orchestrator to raise exception
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.side_effect = (
            Exception("AI service temporarily unavailable")
        )
        
        # Execute evaluation
        decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_with_ai,
            mode="paper",
        )
        
        # Verify fallback to autonomous evaluation
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.decision in ["execute_trade", "reject_opportunity"]  # Depends on autonomous logic
        mock_strategy_service.strategy_can_operate_autonomously.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_autonomous_strategy_evaluation(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_without_ai,
        mock_strategy_service,
        mock_ai_orchestrator,
    ):
        """Test evaluation of strategy configured to operate autonomously."""
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = False
        
        # Execute evaluation
        decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_without_ai,
            mode="paper",
        )
        
        # Verify autonomous evaluation
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.ai_analysis_profile_id is None
        
        # Verify AI orchestrator was not called
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_different_confidence_thresholds_paper_vs_real(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
        ai_config_scalping,
        mock_strategy_service,
        mock_ai_orchestrator,
    ):
        """Test different confidence thresholds for paper vs real trading modes."""
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = True
        mock_strategy_service.get_ai_configuration_for_strategy.return_value = ai_config_scalping
        mock_strategy_service.get_effective_confidence_thresholds_for_strategy.return_value = (
            ai_config_scalping.confidence_thresholds
        )
        
        # Mock AI analysis result with medium confidence (0.7)
        # This should pass paper trading (0.6 threshold) but fail real trading (0.8 threshold)
        ai_result = AIAnalysisResult(
            analysis_id="test-analysis-789",
            calculated_confidence=0.7,
            suggested_action="buy",
            reasoning_ai="Moderate confidence trade opportunity",
            model_used="Gemini-1.5-Pro",
        )
        mock_ai_orchestrator.analyze_opportunity_with_strategy_context_async.return_value = ai_result
        
        # Test paper trading mode
        paper_decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_with_ai,
            mode="paper",
        )
        assert paper_decision.decision == "execute_trade"
        
        # Test real trading mode
        real_decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            scalping_strategy_with_ai,
            mode="real",
        )
        assert real_decision.decision == "reject_opportunity"
        assert "below threshold" in real_decision.reasoning
    
    @pytest.mark.asyncio
    async def test_day_trading_strategy_autonomous_evaluation(
        self,
        trading_engine,
        sample_opportunity,
        mock_strategy_service,
    ):
        """Test autonomous evaluation for day trading strategy."""
        # Create day trading strategy without AI
        day_strategy = TradingStrategyConfig(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            config_name="Day Trading Strategy",
            base_strategy_type=BaseStrategyType.DAY_TRADING,
            description="Autonomous day trading strategy",
            is_active_paper_mode=True,
            is_active_real_mode=False,
            parameters=DayTradingParameters(
                rsi_period=14,
                rsi_overbought=70,
                rsi_oversold=30,
                entry_timeframes=["5m", "15m"],
            ),
            ai_analysis_profile_id=None,
        )
        
        # Setup mocks
        mock_strategy_service.strategy_requires_ai_analysis.return_value = False
        
        # Execute evaluation
        decision = await trading_engine.evaluate_opportunity_with_strategy(
            sample_opportunity,
            day_strategy,
            mode="paper",
        )
        
        # Verify evaluation
        assert isinstance(decision, TradingDecision)
        assert decision.ai_analysis_used is False
        assert decision.strategy_id == day_strategy.id


class TestTradeCreationFromDecision:
    """Test trade creation from trading decisions."""
    
    @pytest.mark.asyncio
    async def test_create_trade_from_ai_decision(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
    ):
        """Test creating a trade from an AI-influenced decision."""
        # Create an AI-influenced decision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.85,
            reasoning="AI recommends strong buy with high confidence",
            opportunity_id=sample_opportunity.id,
            strategy_id=scalping_strategy_with_ai.id,
            ai_analysis_used=True,
            ai_analysis_profile_id="ai-profile-scalping-1",
            recommended_trade_params={
                "entry_price": 30000.0,
                "stop_loss": 29500.0,
                "take_profit": [30500.0],
            },
        )
        
        # Add AI analysis to opportunity
        from src.ultibot_backend.core.domain_models.opportunity_models import (
            AIAnalysis,
            SuggestedAction,
        )
        sample_opportunity.ai_analysis = AIAnalysis(
            analyzed_at=datetime.now(timezone.utc),
            calculated_confidence=0.85,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Strong bullish indicators with favorable risk/reward ratio",
            model_used="Gemini-1.5-Pro",
        )
        
        # Create trade from decision
        trade = await trading_engine.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_with_ai,
        )
        
        # Verify trade creation
        assert trade is not None
        assert trade.symbol == sample_opportunity.symbol
        assert trade.strategy_id == scalping_strategy_with_ai.id
        assert trade.opportunity_id == sample_opportunity.id
        assert trade.is_ai_influenced() is True
        
        # Verify AI influence details
        ai_details = trade.ai_influence_details
        assert ai_details is not None
        assert ai_details.ai_analysis_profile_id == "ai-profile-scalping-1"
        assert ai_details.ai_confidence == 0.85
        assert ai_details.ai_suggested_action == "buy"
        assert "bullish indicators" in ai_details.ai_reasoning_summary
    
    @pytest.mark.asyncio
    async def test_create_trade_from_autonomous_decision(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_without_ai,
    ):
        """Test creating a trade from an autonomous decision."""
        # Create an autonomous decision
        decision = TradingDecision(
            decision="execute_trade",
            confidence=0.7,
            reasoning="Autonomous scalping strategy identifies good opportunity",
            opportunity_id=sample_opportunity.id,
            strategy_id=scalping_strategy_without_ai.id,
            ai_analysis_used=False,
        )
        
        # Create trade from decision
        trade = await trading_engine.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_without_ai,
        )
        
        # Verify trade creation
        assert trade is not None
        assert trade.is_ai_influenced() is False
        assert trade.ai_influence_details is None
        assert "Autonomous scalping" in trade.notes
    
    @pytest.mark.asyncio
    async def test_no_trade_creation_for_reject_decision(
        self,
        trading_engine,
        sample_opportunity,
        scalping_strategy_with_ai,
    ):
        """Test that no trade is created for reject decisions."""
        # Create a reject decision
        decision = TradingDecision(
            decision="reject_opportunity",
            confidence=0.3,
            reasoning="Insufficient confidence for trade execution",
            opportunity_id=sample_opportunity.id,
            strategy_id=scalping_strategy_with_ai.id,
            ai_analysis_used=True,
        )
        
        # Attempt to create trade from decision
        trade = await trading_engine.create_trade_from_decision(
            decision,
            sample_opportunity,
            scalping_strategy_with_ai,
        )
        
        # Verify no trade was created
        assert trade is None
