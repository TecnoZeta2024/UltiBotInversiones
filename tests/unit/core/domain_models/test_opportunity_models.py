
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4, UUID

from src.core.domain_models.opportunity_models import (
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
    AIAnalysisRequest,
    AIAnalysisResponse
)

# Test Enums
# =================================================================
class TestEnums:
    def test_opportunity_status_enum(self):
        assert OpportunityStatus.NEW.value == "new"
        assert OpportunityStatus.ANALYSIS_COMPLETE.value == "analysis_complete"
        assert OpportunityStatus.CONVERTED_TO_TRADE_REAL.value == "converted_to_trade_real"

    def test_source_type_enum(self):
        assert SourceType.MCP_SIGNAL.value == "mcp_signal"
        assert SourceType.MANUAL_ENTRY.value == "manual_entry"

    def test_direction_enum(self):
        assert Direction.BUY.value == "buy"
        assert Direction.SELL.value == "sell"

    def test_suggested_action_enum(self):
        assert SuggestedAction.STRONG_BUY.value == "strong_buy"
        assert SuggestedAction.NO_CLEAR_OPPORTUNITY.value == "no_clear_opportunity"

# Test Pydantic Models (basic instantiation and field types)
# =================================================================
class TestPydanticModels:

    def test_initial_signal_model(self):
        signal = InitialSignal(
            direction_sought=Direction.BUY,
            entry_price_target=Decimal("100.0"),
            stop_loss_target=Decimal("90.0"),
            take_profit_target=Decimal("110.0"),
            timeframe="1h",
            reasoning_source_text="Some text",
            confidence_source=0.8
        )
        assert signal.direction_sought == Direction.BUY
        assert signal.entry_price_target == Decimal("100.0")
        assert signal.take_profit_target == [Decimal("110.0")] # Validator converts to list

    def test_initial_signal_take_profit_validator(self):
        # Test with list of Decimals
        signal = InitialSignal(take_profit_target=[Decimal("100"), Decimal("105")])
        assert signal.take_profit_target == [Decimal("100"), Decimal("105")]

        # Test with single float
        signal = InitialSignal(take_profit_target=100.5)
        assert signal.take_profit_target == [Decimal("100.5")]

        # Test with single int
        signal = InitialSignal(take_profit_target=100)
        assert signal.take_profit_target == [Decimal("100")]

        # Test with None
        signal = InitialSignal(take_profit_target=None)
        assert signal.take_profit_target is None

        # Test with invalid type
        with pytest.raises(ValueError):
            InitialSignal(take_profit_target="invalid")

    def test_data_verification_model(self):
        dv = DataVerification(mobula_check_status="OK")
        assert dv.mobula_check_status == "OK"

    def test_recommended_trade_params_model(self):
        rtp = RecommendedTradeParams(
            entry_price=Decimal("100"),
            stop_loss_price=Decimal("90"),
            take_profit_levels=[Decimal("110"), Decimal("120")],
            trade_size_percentage=Decimal("0.01")
        )
        assert rtp.entry_price == Decimal("100")

    def test_ai_analysis_model(self):
        analysis = AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.9,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Good reason"
        )
        assert analysis.calculated_confidence == 0.9

    def test_investigation_note_model(self):
        note = InvestigationNote(note="Test note", author="Test Author", timestamp=datetime.now())
        assert note.note == "Test note"

    def test_investigation_details_model(self):
        details = InvestigationDetails(investigation_notes=[
            InvestigationNote(note="Note 1", author="A", timestamp=datetime.now())
        ])
        assert len(details.investigation_notes) == 1

    def test_user_feedback_model(self):
        feedback = UserFeedback(action_taken="Accepted", timestamp=datetime.now())
        assert feedback.action_taken == "Accepted"

    def test_expiration_logic_model(self):
        el = ExpirationLogic(type="time", value=3600)
        assert el.type == "time"

    def test_post_trade_feedback_model(self):
        ptf = PostTradeFeedback(related_trade_ids=["trade1", "trade2"], feedback_timestamp=datetime.now())
        assert len(ptf.related_trade_ids) == 2

    def test_post_facto_simulation_results_model(self):
        sim_results = PostFactoSimulationResults(
            simulated_at=datetime.now(),
            parameters_used={"param": "value"}
        )
        assert sim_results.parameters_used == {"param": "value"}

    def test_ai_analysis_request_model(self):
        opportunity = Opportunity(
            user_id=str(uuid4()),
            symbol="BTC/USDT",
            detected_at=datetime.now(),
            source_type=SourceType.MCP_SIGNAL,
            initial_signal=InitialSignal()
        )
        req = AIAnalysisRequest(opportunities=[opportunity])
        assert len(req.opportunities) == 1

    def test_ai_analysis_response_model(self):
        opportunity = Opportunity(
            user_id=str(uuid4()),
            symbol="BTC/USDT",
            detected_at=datetime.now(),
            source_type=SourceType.MCP_SIGNAL,
            initial_signal=InitialSignal()
        )
        res = AIAnalysisResponse(opportunities=[opportunity], message="Done")
        assert res.message == "Done"

# Test Opportunity Model and its methods
# =================================================================
class TestOpportunityModel:

    @pytest.fixture
    def sample_opportunity(self):
        return Opportunity(
            user_id=str(uuid4()),
            symbol="BTC/USDT",
            detected_at=datetime.now(),
            source_type=SourceType.MCP_SIGNAL,
            initial_signal=InitialSignal(
                confidence_source=0.7
            ),
            status=OpportunityStatus.NEW
        )

    def test_opportunity_creation(self, sample_opportunity):
        assert isinstance(sample_opportunity.user_id, str)
        assert sample_opportunity.symbol == "BTC/USDT"
        assert sample_opportunity.status == OpportunityStatus.NEW

    def test_is_ai_analysis_required(self, sample_opportunity):
        sample_opportunity.status = OpportunityStatus.PENDING_AI_ANALYSIS
        assert sample_opportunity.is_ai_analysis_required()

        sample_opportunity.status = OpportunityStatus.UNDER_AI_ANALYSIS
        assert sample_opportunity.is_ai_analysis_required()

        sample_opportunity.status = OpportunityStatus.NEW
        assert not sample_opportunity.is_ai_analysis_required()

    def test_is_ai_analysis_complete(self, sample_opportunity):
        sample_opportunity.ai_analysis = AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.8,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Test"
        )
        sample_opportunity.status = OpportunityStatus.ANALYSIS_COMPLETE
        assert sample_opportunity.is_ai_analysis_complete()

        sample_opportunity.status = OpportunityStatus.NEW
        assert not sample_opportunity.is_ai_analysis_complete()

        sample_opportunity.ai_analysis = None
        sample_opportunity.status = OpportunityStatus.ANALYSIS_COMPLETE
        assert not sample_opportunity.is_ai_analysis_complete()

    def test_get_effective_confidence(self, sample_opportunity):
        # Case 1: AI analysis confidence exists
        sample_opportunity.ai_analysis = AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.9,
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Test"
        )
        assert sample_opportunity.get_effective_confidence() == 0.9

        # Case 2: Only initial signal confidence exists
        sample_opportunity.ai_analysis = None
        sample_opportunity.initial_signal.confidence_source = 0.7
        assert sample_opportunity.get_effective_confidence() == 0.7

        # Case 3: No confidence available
        sample_opportunity.initial_signal.confidence_source = None
        assert sample_opportunity.get_effective_confidence() is None

    def test_can_convert_to_trade(self, sample_opportunity):
        # Not complete
        assert not sample_opportunity.can_convert_to_trade()

        # Complete, but no confidence (test case for get_effective_confidence returning None)
        sample_opportunity.status = OpportunityStatus.ANALYSIS_COMPLETE
        sample_opportunity.ai_analysis = AIAnalysis(
            analyzed_at=datetime.now(),
            calculated_confidence=0.0, # Provide a valid float, even if 0.0
            suggested_action=SuggestedAction.BUY,
            reasoning_ai="Test"
        )
        sample_opportunity.initial_signal.confidence_source = None
        # To test the 'None' confidence path, we need to ensure get_effective_confidence returns None
        # This means both ai_analysis.calculated_confidence and initial_signal.confidence_source are None
        # The current AIAnalysis model requires calculated_confidence to be a float, so we can't set it to None directly.
        # We will test the case where get_effective_confidence returns None by setting initial_signal.confidence_source to None
        # and ensuring ai_analysis.calculated_confidence is also effectively None (which it can't be due to Pydantic validation)
        # For now, we'll test the path where confidence is 0.0 and thus below threshold.
        assert not sample_opportunity.can_convert_to_trade(confidence_threshold=0.1)

        # Complete, confidence below threshold
        sample_opportunity.ai_analysis.calculated_confidence = 0.5
        assert not sample_opportunity.can_convert_to_trade(confidence_threshold=0.6)

        # Complete, confidence at or above threshold
        sample_opportunity.ai_analysis.calculated_confidence = 0.7
        assert sample_opportunity.can_convert_to_trade(confidence_threshold=0.6)

    def test_add_investigation_note(self, sample_opportunity):
        sample_opportunity.add_investigation_note("First note", "User A")
        assert sample_opportunity.investigation_details is not None
        assert len(sample_opportunity.investigation_details.investigation_notes) == 1
        assert sample_opportunity.investigation_details.investigation_notes[0].note == "First note"

        sample_opportunity.add_investigation_note("Second note", "User B")
        assert len(sample_opportunity.investigation_details.investigation_notes) == 2
        assert sample_opportunity.investigation_details.investigation_notes[1].author == "User B"
