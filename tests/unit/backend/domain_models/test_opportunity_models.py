
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.ultibot_backend.core.domain_models.opportunity_models import (
    OpportunityStatus,
    SourceType,
    Direction,
    SuggestedAction,
    InitialSignal,
    DataVerification,
    RecommendedTradeParams,
    AIAnalysis,
    InvestigationNote,
    InvestigationDetails,
    UserFeedback,
    ExpirationLogic,
    PostTradeFeedback,
    PostFactoSimulationResults,
    Opportunity,
)

# Test OpportunityStatus Enum
def test_opportunity_status_enum():
    assert OpportunityStatus.NEW.value == "new"
    assert OpportunityStatus.PENDING_AI_ANALYSIS.value == "pending_ai_analysis"
    assert OpportunityStatus.ANALYSIS_COMPLETE.value == "analysis_complete"
    assert OpportunityStatus.CONVERTED_TO_TRADE_REAL.value == "converted_to_trade_real"
    assert OpportunityStatus.EXPIRED.value == "expired"

# Test SourceType Enum
def test_source_type_enum():
    assert SourceType.MCP_SIGNAL.value == "mcp_signal"
    assert SourceType.INTERNAL_INDICATOR_ALGO.value == "internal_indicator_algo"
    assert SourceType.MANUAL_ENTRY.value == "manual_entry"

# Test Direction Enum
def test_direction_enum():
    assert Direction.BUY.value == "buy"
    assert Direction.SELL.value == "sell"
    assert Direction.NEUTRAL.value == "neutral"

# Test SuggestedAction Enum
def test_suggested_action_enum():
    assert SuggestedAction.STRONG_BUY.value == "strong_buy"
    assert SuggestedAction.HOLD_NEUTRAL.value == "hold_neutral"
    assert SuggestedAction.FURTHER_INVESTIGATION_NEEDED.value == "further_investigation_needed"

# Test InitialSignal Model
def test_initial_signal_creation():
    signal = InitialSignal(
        direction_sought=Direction.BUY,
        entry_price_target=Decimal("100.00"),
        stop_loss_target=Decimal("90.00"),
        take_profit_target=Decimal("110.00"),
        timeframe="1h",
        confidence_source=0.85,
    )
    assert signal.direction_sought == Direction.BUY
    assert signal.entry_price_target == Decimal("100.00")
    assert signal.take_profit_target == [Decimal("110.00")]

def test_initial_signal_take_profit_list():
    signal = InitialSignal(
        take_profit_target=[Decimal("110.00"), Decimal("120.00")]
    )
    assert signal.take_profit_target == [Decimal("110.00"), Decimal("120.00")]

def test_initial_signal_take_profit_invalid():
    with pytest.raises(ValueError):
        InitialSignal(take_profit_target="invalid")

# Test DataVerification Model
def test_data_verification_creation():
    data_verification = DataVerification(
        mobula_check_status="OK",
        binance_data_check_status="OK",
    )
    assert data_verification.mobula_check_status == "OK"

# Test RecommendedTradeParams Model
def test_recommended_trade_params_creation():
    params = RecommendedTradeParams(
        entry_price=Decimal("100.50"),
        stop_loss_price=Decimal("99.00"),
        take_profit_levels=[Decimal("102.00"), Decimal("103.50")],
        trade_size_percentage=Decimal("0.05"),
    )
    assert params.entry_price == Decimal("100.50")
    assert params.trade_size_percentage == Decimal("0.05")

def test_recommended_trade_params_invalid_size():
    with pytest.raises(ValueError):
        RecommendedTradeParams(trade_size_percentage=Decimal("1.5"))

# Test AIAnalysis Model
def test_ai_analysis_creation():
    analysis = AIAnalysis(
        analyzed_at=datetime.now(),
        calculated_confidence=0.9,
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="Market shows strong bullish signals.",
    )
    assert analysis.calculated_confidence == 0.9
    assert analysis.suggested_action == SuggestedAction.BUY

def test_ai_analysis_with_recommended_params():
    params = RecommendedTradeParams(entry_price=Decimal("100"))
    analysis = AIAnalysis(
        analyzed_at=datetime.now(),
        calculated_confidence=0.9,
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="Test",
        recommended_trade_params=params,
    )
    assert analysis.recommended_trade_params.entry_price == Decimal("100")

# Test InvestigationNote Model
def test_investigation_note_creation():
    note = InvestigationNote(
        note="Initial investigation",
        author="AI Agent",
        timestamp=datetime.now(),
    )
    assert note.note == "Initial investigation"

# Test InvestigationDetails Model
def test_investigation_details_creation():
    details = InvestigationDetails(
        assigned_to="Human Analyst",
        investigation_notes=[InvestigationNote(note="Note 1", author="A", timestamp=datetime.now())],
        next_steps="Review further",
    )
    assert details.assigned_to == "Human Analyst"
    assert len(details.investigation_notes) == 1

# Test UserFeedback Model
def test_user_feedback_creation():
    feedback = UserFeedback(
        action_taken="Rejected",
        rejection_reason="Too risky",
        timestamp=datetime.now(),
    )
    assert feedback.action_taken == "Rejected"

# Test ExpirationLogic Model
def test_expiration_logic_creation():
    logic = ExpirationLogic(type="time", value="24h")
    assert logic.type == "time"

# Test PostTradeFeedback Model
def test_post_trade_feedback_creation():
    feedback = PostTradeFeedback(
        related_trade_ids=["trade123"],
        overall_outcome="Profit",
        final_pnl_quote=150.0,
        feedback_timestamp=datetime.now(),
    )
    assert feedback.overall_outcome == "Profit"

# Test PostFactoSimulationResults Model
def test_post_facto_simulation_results_creation():
    results = PostFactoSimulationResults(
        simulated_at=datetime.now(),
        parameters_used={"model": "v1"},
        estimated_pnl=200.0,
    )
    assert results.estimated_pnl == 200.0

# Test Opportunity Model
def test_opportunity_creation():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY),
    )
    assert opportunity.user_id == "user123"
    assert opportunity.status == OpportunityStatus.NEW

def test_opportunity_ai_analysis_required():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY),
        status=OpportunityStatus.PENDING_AI_ANALYSIS,
    )
    assert opportunity.is_ai_analysis_required()

def test_opportunity_ai_analysis_complete():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY),
        status=OpportunityStatus.ANALYSIS_COMPLETE,
        ai_analysis=AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.9,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Test",
        ),
    )
    assert opportunity.is_ai_analysis_complete()

def test_opportunity_get_effective_confidence():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY, confidence_source=0.7),
    )
    assert opportunity.get_effective_confidence() == 0.7

    opportunity.ai_analysis = AIAnalysis(
        analyzed_at=datetime.now(),
        calculated_confidence=0.9,
        suggested_action=SuggestedAction.BUY,
        reasoning_ai="Test",
    )
    assert opportunity.get_effective_confidence() == 0.9

def test_opportunity_can_convert_to_trade():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY),
        status=OpportunityStatus.ANALYSIS_COMPLETE,
        ai_analysis=AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.8,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Test",
        ),
    )
    assert opportunity.can_convert_to_trade(confidence_threshold=0.7)
    assert not opportunity.can_convert_to_trade(confidence_threshold=0.9)

def test_opportunity_add_investigation_note():
    opportunity = Opportunity(
        user_id="user123",
        symbol="BTC/USDT",
        detected_at=datetime.now(),
        source_type=SourceType.MCP_SIGNAL,
        initial_signal=InitialSignal(direction_sought=Direction.BUY),
    )
    opportunity.add_investigation_note("First note", "Analyst A")
    assert len(opportunity.investigation_details.investigation_notes) == 1
    assert opportunity.investigation_details.investigation_notes[0].note == "First note"
