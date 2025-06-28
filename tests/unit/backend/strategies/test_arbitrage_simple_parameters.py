
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import ArbitrageSimpleParameters

def test_arbitrage_simple_parameters_valid_data():
    """Test ArbitrageSimpleParameters with valid data."""
    params = ArbitrageSimpleParameters(
        price_difference_percentage_threshold=0.001,
        min_trade_volume_quote=10.0,
        exchange_a_credential_label="binance_spot_a",
        exchange_b_credential_label="binance_spot_b"
    )
    assert params.price_difference_percentage_threshold == 0.001
    assert params.min_trade_volume_quote == 10.0
    assert params.exchange_a_credential_label == "binance_spot_a"
    assert params.exchange_b_credential_label == "binance_spot_b"

def test_arbitrage_simple_parameters_missing_required_fields():
    """Test ArbitrageSimpleParameters with missing required fields."""
    with pytest.raises(ValidationError) as excinfo:
        ArbitrageSimpleParameters()
    assert "price_difference_percentage_threshold" in str(excinfo.value)
    assert "exchange_a_credential_label" in str(excinfo.value)
    assert "exchange_b_credential_label" in str(excinfo.value)

def test_arbitrage_simple_parameters_invalid_price_difference_percentage_threshold():
    """Test ArbitrageSimpleParameters with invalid price_difference_percentage_threshold."""
    with pytest.raises(ValidationError) as excinfo:
        ArbitrageSimpleParameters(
            price_difference_percentage_threshold=0.0,
            exchange_a_credential_label="binance_spot_a",
            exchange_b_credential_label="binance_spot_b"
        )
    assert "price_difference_percentage_threshold" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        ArbitrageSimpleParameters(
            price_difference_percentage_threshold=1.1,
            exchange_a_credential_label="binance_spot_a",
            exchange_b_credential_label="binance_spot_b"
        )
    assert "price_difference_percentage_threshold" in str(excinfo.value)
    assert "less than or equal to 1" in str(excinfo.value)

def test_arbitrage_simple_parameters_invalid_min_trade_volume_quote():
    """Test ArbitrageSimpleParameters with invalid min_trade_volume_quote."""
    with pytest.raises(ValidationError) as excinfo:
        ArbitrageSimpleParameters(
            price_difference_percentage_threshold=0.001,
            min_trade_volume_quote=0.0,
            exchange_a_credential_label="binance_spot_a",
            exchange_b_credential_label="binance_spot_b"
        )
    assert "min_trade_volume_quote" in str(excinfo.value)
    assert "greater than 0" in str(excinfo.value)

def test_arbitrage_simple_parameters_optional_fields_none():
    """Test ArbitrageSimpleParameters with optional fields set to None."""
    params = ArbitrageSimpleParameters(
        price_difference_percentage_threshold=0.001,
        min_trade_volume_quote=None,
        exchange_a_credential_label="binance_spot_a",
        exchange_b_credential_label="binance_spot_b"
    )
    assert params.price_difference_percentage_threshold == 0.001
    assert params.min_trade_volume_quote is None
    assert params.exchange_a_credential_label == "binance_spot_a"
    assert params.exchange_b_credential_label == "binance_spot_b"
