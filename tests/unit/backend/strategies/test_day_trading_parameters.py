
import pytest
from pydantic import ValidationError
from src.core.domain_models.trading_strategy_models import DayTradingParameters, Timeframe

def test_day_trading_parameters_valid_data():
    """Test DayTradingParameters with valid data."""
    params = DayTradingParameters(
        entry_timeframes=[Timeframe.ONE_MINUTE, Timeframe.FIVE_MINUTES],
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        exit_timeframes=[Timeframe.ONE_HOUR]
    )
    assert params.entry_timeframes == [Timeframe.ONE_MINUTE, Timeframe.FIVE_MINUTES]
    assert params.rsi_period == 14

def test_day_trading_parameters_missing_entry_timeframes():
    """Test DayTradingParameters with missing entry_timeframes."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            entry_timeframes=[]
        )
    assert "entry_timeframes" in str(excinfo.value)
    assert "Entry timeframes cannot be empty" in str(excinfo.value)

def test_day_trading_parameters_invalid_rsi_overbought():
    """Test DayTradingParameters with invalid rsi_overbought (less than oversold)."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_MINUTE],
            rsi_overbought=20, # Invalid: less than rsi_oversold default of 30
            rsi_oversold=30,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9
        )
    assert "rsi_overbought" in str(excinfo.value)
    assert "Input should be greater than or equal to 50" in str(excinfo.value)

def test_day_trading_parameters_invalid_macd_slow_period():
    """Test DayTradingParameters with invalid macd_slow_period (less than or equal to fast)."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_MINUTE],
            macd_fast_period=12,
            macd_slow_period=10, # Invalid: less than macd_fast_period
            macd_signal_period=9
        )
    assert "macd_slow_period" in str(excinfo.value)
    assert "MACD slow period must be greater than fast period" in str(excinfo.value)

def test_day_trading_parameters_duplicate_entry_timeframes():
    """Test DayTradingParameters with duplicate entry_timeframes."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_MINUTE, Timeframe.ONE_MINUTE],
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9
        )
    assert "entry_timeframes" in str(excinfo.value)
    assert "Duplicate timeframe found" in str(excinfo.value)

def test_day_trading_parameters_duplicate_exit_timeframes():
    """Test DayTradingParameters with duplicate exit_timeframes."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            entry_timeframes=[Timeframe.ONE_MINUTE],
            exit_timeframes=[Timeframe.ONE_HOUR, Timeframe.ONE_HOUR],
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9
        )
    assert "exit_timeframes" in str(excinfo.value)
    assert "Duplicate timeframe found" in str(excinfo.value)

def test_day_trading_parameters_invalid_timeframe_member():
    """Test DayTradingParameters with invalid timeframe member."""
    with pytest.raises(ValidationError) as excinfo:
        DayTradingParameters(
            entry_timeframes=["invalid_timeframe"], # type: ignore
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9
        )
    assert "entry_timeframes" in str(excinfo.value)
    assert "Input should be '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w' or '1M'" in str(excinfo.value)

def test_day_trading_parameters_optional_fields_none():
    """Test DayTradingParameters with optional fields set to None."""
    params = DayTradingParameters(
        entry_timeframes=[Timeframe.ONE_MINUTE],
        rsi_period=None,
        rsi_overbought=None,
        rsi_oversold=None,
        macd_fast_period=None,
        macd_slow_period=None,
        macd_signal_period=None,
        exit_timeframes=None
    )
    assert params.entry_timeframes == [Timeframe.ONE_MINUTE]
    assert params.rsi_period is None
    assert params.exit_timeframes is None
