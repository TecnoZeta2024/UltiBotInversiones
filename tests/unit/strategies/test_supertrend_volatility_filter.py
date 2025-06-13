"""
Unit tests for the refactored SuperTrendVolatilityFilter strategy.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone # ADDED timezone
from typing import List, Optional, Tuple
import random

from ultibot_backend.core.domain_models.market import MarketData, KlineData
from ultibot_backend.core.domain_models.trading import SuperTrendParameters, OrderSide, SignalStrength, TickerData
from ultibot_backend.strategies.supertrend_volatility_filter import SuperTrendVolatilityFilter

def create_mock_klines(
    start_price: float,
    num_klines: int,
    trend: str = "sideways",
    volatility_factor: float = 0.005,
    trend_strength_factor: float = 0.001,
    random_seed: Optional[int] = None # Add random seed for reproducibility
) -> List[KlineData]:
    """
    Generates a list of mock KlineData for testing with controlled trend and volatility.
    Adjusted to create clearer trends for SuperTrend tests and better control volatility.
    """
    if random_seed is not None:
        random.seed(random_seed)

    klines = []
    current_time = datetime.now(timezone.utc) # MODIFIED
    price = start_price

    for i in range(num_klines):
        # Base price movement
        if trend == "up":
            price *= (1 + trend_strength_factor + (random.random() * 0.0005))
        elif trend == "down":
            price *= (1 - trend_strength_factor - (random.random() * 0.0005))
        else: # Sideways
            price *= (1 + (random.uniform(-0.0001, 0.0001))) # Very slight random movement

        open_price = price
        
        # Introduce more controlled volatility around the price
        # Ensure high and low are always around the current price, with controlled spread
        high_offset = price * volatility_factor * random.uniform(0.9, 1.1) # Más consistente
        low_offset = price * volatility_factor * random.uniform(0.9, 1.1) # Más consistente
        
        high = open_price + high_offset
        low = open_price - low_offset

        # Ensure close is within high/low range and reflects trend
        if trend == "up":
            close_price = random.uniform(open_price, high)
        elif trend == "down":
            close_price = random.uniform(low, open_price)
        else:
            close_price = random.uniform(low, high)

        # Ensure high is max of open, close, and calculated high
        high = max(open_price, close_price, high)
        # Ensure low is min of open, close, and calculated low
        low = min(open_price, close_price, low)

        kline = KlineData(
            timestamp=current_time + timedelta(minutes=i),
            open=Decimal(str(open_price)),
            high=Decimal(str(high)),
            low=Decimal(str(low)),
            close=Decimal(str(close_price)),
            volume=Decimal(str(1000 + i * 10))
        )
        klines.append(kline)
        price = float(close_price) # Next open price based on current close
        
    return klines

def create_market_snapshot(klines: List[KlineData]) -> MarketData:
    """Creates a MarketData from a list of klines."""
    last_kline = klines[-1]
    ticker_data = TickerData(
        symbol="BTCUSDT",
        price=last_kline.close,
        volume_24h=Decimal("50000"),
        price_change_24h=Decimal("100.0"),
    )
    return MarketData(
        symbol="BTCUSDT",
        ticker=ticker_data,
        klines=klines,
    )

@pytest.fixture
def default_params() -> SuperTrendParameters:
    """Default parameters for the SuperTrend strategy."""
    return SuperTrendParameters(
        atr_period=10,
        atr_multiplier=3.0,
        min_volatility_percentile=0.0, # Ajustado para tests (siempre pasa)
        max_volatility_percentile=100.0, # Ajustado para tests (siempre pasa)
        volatility_lookback=50,
        min_trend_strength=0.6,
        position_size_pct=0.01,
        risk_reward_ratio=2.0
    )

@pytest.fixture
def strategy(default_params: SuperTrendParameters) -> SuperTrendVolatilityFilter:
    """Fixture for the SuperTrendVolatilityFilter strategy."""
    return SuperTrendVolatilityFilter(default_params)

@pytest.mark.asyncio
async def test_strategy_initialization(strategy: SuperTrendVolatilityFilter, default_params: SuperTrendParameters):
    assert strategy.name == "SuperTrend_Volatility_Filter"
    assert strategy.parameters == default_params

@pytest.mark.asyncio
async def test_analyze_insufficient_data(strategy: SuperTrendVolatilityFilter):
    klines = create_mock_klines(50000, 10, trend="sideways", volatility_factor=0.01)
    snapshot = create_market_snapshot(klines)
    result = await strategy.analyze(snapshot)
    assert result.confidence == 0.0
    assert result.metadata["error"] == "Datos insuficientes para análisis"

@pytest.mark.asyncio
async def test_analyze_volatility_filter_fails():
    # Generar klines con volatilidad extremadamente baja para que el filtro falle
    klines = create_mock_klines(50000, 100, trend="sideways", volatility_factor=0.000001, random_seed=1)
    snapshot = create_market_snapshot(klines)
    
    # Crear una estrategia con percentiles que hagan que el filtro falle para esta volatilidad
    params = SuperTrendParameters(
        atr_period=10,
        atr_multiplier=3.0,
        min_volatility_percentile=10.0, # Establecer un umbral mínimo más alto
        max_volatility_percentile=90.0, # Establecer un umbral máximo más bajo
        volatility_lookback=50,
        min_trend_strength=0.6,
        position_size_pct=0.01,
        risk_reward_ratio=2.0
    )
    strategy = SuperTrendVolatilityFilter(params)
    
    result = await strategy.analyze(snapshot)
    assert result.indicators["volatility_filter_passed"] is False
    assert result.confidence == 0.0

@pytest.mark.asyncio
async def test_analyze_generates_buy_signal(strategy: SuperTrendVolatilityFilter):
    # Generar klines con tendencia alcista y volatilidad moderada para que el filtro pase
    klines = create_mock_klines(50000, 200, trend="up", volatility_factor=0.01, trend_strength_factor=0.01, random_seed=2) # Aumentar trend_strength_factor
    snapshot = create_market_snapshot(klines)
    result = await strategy.analyze(snapshot)
    assert result.indicators["volatility_filter_passed"] is True
    assert result.confidence > strategy.parameters.min_trend_strength
    assert result.signal is not None
    assert result.signal.side == OrderSide.BUY

@pytest.mark.asyncio
async def test_analyze_generates_sell_signal(strategy: SuperTrendVolatilityFilter):
    # Generar klines con tendencia bajista y volatilidad moderada para que el filtro pase
    klines = create_mock_klines(50000, 200, trend="down", volatility_factor=0.01, trend_strength_factor=0.01, random_seed=4) # Aumentar trend_strength_factor
    snapshot = create_market_snapshot(klines)
    result = await strategy.analyze(snapshot)
    assert result.indicators["volatility_filter_passed"] is True
    assert result.confidence > strategy.parameters.min_trend_strength
    assert result.signal is not None
    assert result.signal.side == OrderSide.SELL

def test_atr_calculation(strategy: SuperTrendVolatilityFilter):
    klines = create_mock_klines(100, 20)
    atr_values = strategy._calculate_atr(klines, period=14)
    assert len(atr_values) == 20
    assert all(isinstance(v, float) for v in atr_values)
    assert atr_values[-1] > 0

def test_supertrend_calculation(strategy: SuperTrendVolatilityFilter):
    klines = create_mock_klines(100, 50)
    atr_values = strategy._calculate_atr(klines, period=14)
    st_data = strategy._calculate_supertrend(klines, atr_values, multiplier=3.0)
    assert "values" in st_data
    assert "direction" in st_data
    assert len(st_data["values"]) == 50

def test_take_profit_calculation(strategy: SuperTrendVolatilityFilter):
    tp_buy = strategy._calculate_take_profit(100.0, Decimal("90.0"), OrderSide.BUY)
    assert tp_buy == Decimal("120.0")
    tp_sell = strategy._calculate_take_profit(100.0, Decimal("110.0"), OrderSide.SELL)
    assert tp_sell == Decimal("80.0")
