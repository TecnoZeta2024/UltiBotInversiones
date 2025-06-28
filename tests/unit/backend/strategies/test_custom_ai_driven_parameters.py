
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import CustomAIDrivenParameters

def test_custom_ai_driven_parameters_valid_data():
    """Test CustomAIDrivenParameters with valid data."""
    params = CustomAIDrivenParameters(
        primary_objective_prompt="Optimize for maximum profit with minimal risk.",
        context_window_configuration={"key": "value"},
        decision_model_parameters={"model_name": "GPT-4"},
        max_tokens_for_response=1000
    )
    assert params.primary_objective_prompt == "Optimize for maximum profit with minimal risk."
    assert params.context_window_configuration == {"key": "value"}
    assert params.decision_model_parameters == {"model_name": "GPT-4"}
    assert params.max_tokens_for_response == 1000

def test_custom_ai_driven_parameters_missing_required_fields():
    """Test CustomAIDrivenParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        CustomAIDrivenParameters()
    assert "primary_objective_prompt" in str(excinfo.value)

def test_custom_ai_driven_parameters_invalid_primary_objective_prompt():
    """Test CustomAIDrivenParameters with invalid primary_objective_prompt (too short)."""
    with pytest.raises(ValidationError) as excinfo:
        CustomAIDrivenParameters(primary_objective_prompt="short")
    assert "primary_objective_prompt" in str(excinfo.value)
    assert "String should have at least 10 characters" in str(excinfo.value)

def test_custom_ai_driven_parameters_invalid_max_tokens_for_response():
    """Test CustomAIDrivenParameters with invalid max_tokens_for_response."""
    with pytest.raises(ValidationError) as excinfo:
        CustomAIDrivenParameters(
            primary_objective_prompt="Optimize for maximum profit with minimal risk.",
            max_tokens_for_response=0
        )
    assert "max_tokens_for_response" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_custom_ai_driven_parameters_optional_fields_none():
    """Test CustomAIDrivenParameters with optional fields set to None."""
    params = CustomAIDrivenParameters(
        primary_objective_prompt="Optimize for maximum profit with minimal risk.",
        context_window_configuration=None,
        decision_model_parameters=None,
        max_tokens_for_response=None
    )
    assert params.primary_objective_prompt == "Optimize for maximum profit with minimal risk."
    assert params.context_window_configuration is None
    assert params.decision_model_parameters is None
    assert params.max_tokens_for_response is None
