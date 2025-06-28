
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import DCAInvestingParameters

def test_dca_investing_parameters_valid_data():
    """Test DCAInvestingParameters with valid data."""
    params = DCAInvestingParameters(
        investment_amount=100.0,
        investment_interval_hours=24,
        max_total_investment=1000.0,
        price_deviation_trigger=0.05
    )
    assert params.investment_amount == 100.0
    assert params.investment_interval_hours == 24
    assert params.max_total_investment == 1000.0
    assert params.price_deviation_trigger == 0.05

def test_dca_investing_parameters_missing_required_fields():
    """Test DCAInvestingParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters()
    assert "investment_amount" in str(excinfo.value)
    assert "investment_interval_hours" in str(excinfo.value)

def test_dca_investing_parameters_invalid_investment_amount():
    """Test DCAInvestingParameters with invalid investment_amount."""
    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters(
            investment_amount=0.0,
            investment_interval_hours=24
        )
    assert "investment_amount" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_dca_investing_parameters_invalid_investment_interval_hours():
    """Test DCAInvestingParameters with invalid investment_interval_hours."""
    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters(
            investment_amount=100.0,
            investment_interval_hours=0
        )
    assert "investment_interval_hours" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_dca_investing_parameters_invalid_max_total_investment():
    """Test DCAInvestingParameters with invalid max_total_investment."""
    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters(
            investment_amount=100.0,
            investment_interval_hours=24,
            max_total_investment=0.0
        )
    assert "max_total_investment" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_dca_investing_parameters_invalid_price_deviation_trigger():
    """Test DCAInvestingParameters with invalid price_deviation_trigger."""
    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters(
            investment_amount=100.0,
            investment_interval_hours=24,
            price_deviation_trigger=0.0
        )
    assert "price_deviation_trigger" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        DCAInvestingParameters(
            investment_amount=100.0,
            investment_interval_hours=24,
            price_deviation_trigger=1.1
        )
    assert "price_deviation_trigger" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)

def test_dca_investing_parameters_optional_fields_none():
    """Test DCAInvestingParameters with optional fields set to None."""
    params = DCAInvestingParameters(
        investment_amount=100.0,
        investment_interval_hours=24,
        max_total_investment=None,
        price_deviation_trigger=None
    )
    assert params.investment_amount == 100.0
    assert params.investment_interval_hours == 24
    assert params.max_total_investment is None
    assert params.price_deviation_trigger is None
