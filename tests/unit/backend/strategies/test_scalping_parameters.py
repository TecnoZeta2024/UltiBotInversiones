
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import ScalpingParameters

def test_scalping_parameters_valid_data():
    """Test ScalpingParameters with valid data."""
    params = ScalpingParameters(
        profit_target_percentage=0.01,
        stop_loss_percentage=0.005,
        max_holding_time_seconds=300,
        leverage=2.0
    )
    assert params.profit_target_percentage == 0.01
    assert params.stop_loss_percentage == 0.005
    assert params.max_holding_time_seconds == 300
    assert params.leverage == 2.0

def test_scalping_parameters_missing_required_fields():
    """Test ScalpingParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters()
    assert "profit_target_percentage" in str(excinfo.value)
    assert "stop_loss_percentage" in str(excinfo.value)

def test_scalping_parameters_invalid_profit_target_percentage():
    """Test ScalpingParameters with invalid profit_target_percentage."""
    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(profit_target_percentage=1.5, stop_loss_percentage=0.005)
    assert "profit_target_percentage" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(profit_target_percentage=0.0, stop_loss_percentage=0.005)
    assert "profit_target_percentage" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_scalping_parameters_invalid_stop_loss_percentage():
    """Test ScalpingParameters with invalid stop_loss_percentage."""
    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=1.5)
    assert "stop_loss_percentage" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(profit_target_percentage=0.01, stop_loss_percentage=0.0)
    assert "stop_loss_percentage" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_scalping_parameters_invalid_max_holding_time_seconds():
    """Test ScalpingParameters with invalid max_holding_time_seconds."""
    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            max_holding_time_seconds=0
        )
    assert "max_holding_time_seconds" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_scalping_parameters_invalid_leverage():
    """Test ScalpingParameters with invalid leverage."""
    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            leverage=0.0
        )
    assert "leverage" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        ScalpingParameters(
            profit_target_percentage=0.01,
            stop_loss_percentage=0.005,
            leverage=101.0
        )
    assert "leverage" in str(excinfo.value)
    assert "less than or equal to 100" in str(excinfo.value)

def test_scalping_parameters_optional_fields_none():
    """Test ScalpingParameters with optional fields set to None."""
    params = ScalpingParameters(
        profit_target_percentage=0.01,
        stop_loss_percentage=0.005,
        max_holding_time_seconds=None,
        leverage=None
    )
    assert params.profit_target_percentage == 0.01
    assert params.stop_loss_percentage == 0.005
    assert params.max_holding_time_seconds is None
    assert params.leverage is None
