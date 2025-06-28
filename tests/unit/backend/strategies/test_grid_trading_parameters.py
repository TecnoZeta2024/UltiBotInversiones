
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import GridTradingParameters

def test_grid_trading_parameters_valid_data():
    """Test GridTradingParameters with valid data."""
    params = GridTradingParameters(
        grid_upper_price=100.0,
        grid_lower_price=50.0,
        grid_levels=10,
        profit_per_grid=0.01
    )
    assert params.grid_upper_price == 100.0
    assert params.grid_lower_price == 50.0
    assert params.grid_levels == 10
    assert params.profit_per_grid == 0.01

def test_grid_trading_parameters_missing_required_fields():
    """Test GridTradingParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters()
    assert "grid_upper_price" in str(excinfo.value)
    assert "grid_lower_price" in str(excinfo.value)
    assert "grid_levels" in str(excinfo.value)
    assert "profit_per_grid" in str(excinfo.value)

def test_grid_trading_parameters_invalid_grid_prices():
    """Test GridTradingParameters with invalid grid prices (upper <= lower)."""
    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters(
            grid_upper_price=50.0,
            grid_lower_price=50.0,
            grid_levels=10,
            profit_per_grid=0.01
        )
    assert "Grid upper price must be greater than lower price" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters(
            grid_upper_price=40.0,
            grid_lower_price=50.0,
            grid_levels=10,
            profit_per_grid=0.01
        )
    assert "Grid upper price must be greater than lower price" in str(excinfo.value)

def test_grid_trading_parameters_invalid_grid_levels():
    """Test GridTradingParameters with invalid grid_levels."""
    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters(
            grid_upper_price=100.0,
            grid_lower_price=50.0,
            grid_levels=2,
            profit_per_grid=0.01
        )
    assert "grid_levels" in str(excinfo.value)
    assert "greater than or equal to 3" in str(excinfo.value)

def test_grid_trading_parameters_invalid_profit_per_grid():
    """Test GridTradingParameters with invalid profit_per_grid."""
    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters(
            grid_upper_price=100.0,
            grid_lower_price=50.0,
            grid_levels=10,
            profit_per_grid=0.0
        )
    assert "profit_per_grid" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        GridTradingParameters(
            grid_upper_price=100.0,
            grid_lower_price=50.0,
            grid_levels=10,
            profit_per_grid=1.1
        )
    assert "profit_per_grid" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)
