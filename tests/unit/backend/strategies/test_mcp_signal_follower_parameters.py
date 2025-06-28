
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import MCPSignalFollowerParameters

def test_mcp_signal_follower_parameters_valid_data():
    """Test MCPSignalFollowerParameters with valid data."""
    params = MCPSignalFollowerParameters(
        mcp_source_config_id="some_config_id",
        allowed_signal_types=["BUY", "SELL"]
    )
    assert params.mcp_source_config_id == "some_config_id"
    assert params.allowed_signal_types == ["BUY", "SELL"]

def test_mcp_signal_follower_parameters_missing_required_fields():
    """Test MCPSignalFollowerParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        MCPSignalFollowerParameters()
    assert "mcp_source_config_id" in str(excinfo.value)

def test_mcp_signal_follower_parameters_optional_fields_none():
    """Test MCPSignalFollowerParameters with optional fields set to None."""
    params = MCPSignalFollowerParameters(
        mcp_source_config_id="some_config_id",
        allowed_signal_types=None
    )
    assert params.mcp_source_config_id == "some_config_id"
    assert params.allowed_signal_types is None
