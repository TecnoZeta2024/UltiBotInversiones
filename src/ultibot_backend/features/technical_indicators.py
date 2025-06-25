import pandas as pd
from typing import List, Optional
from decimal import Decimal

from ultibot_backend.core.domain_models.market_data_models import MarketDataORM

def calculate_sma(data: List[MarketDataORM], window: int) -> List[Optional[Decimal]]:
    """
    Calculates the Simple Moving Average (SMA) for a list of market data points.
    """
    if len(data) < window:
        return []
    
    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    sma = series.rolling(window=window).mean().tolist()
    return [Decimal(str(val)) if pd.notna(val) else None for val in sma]

def calculate_ema(data: List[MarketDataORM], window: int) -> List[Optional[Decimal]]:
    """
    Calculates the Exponential Moving Average (EMA) for a list of market data points.
    """
    if len(data) < window:
        return []

    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    ema = series.ewm(span=window, adjust=False).mean().tolist()
    return [Decimal(str(val)) if pd.notna(val) else None for val in ema]


def calculate_volatility(data: List[MarketDataORM], window: int) -> List[Optional[Decimal]]:
    """
    Calculates the rolling volatility (standard deviation) of the price.
    """
    if len(data) < window:
        return []

    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    volatility = series.rolling(window=window).std().tolist()
    return [Decimal(str(val)) if pd.notna(val) else None for val in volatility]


def calculate_roc(data: List[MarketDataORM], window: int) -> List[Optional[Decimal]]:
    """
    Calculates the Rate of Change (ROC) of the price.
    """
    if len(data) < window:
        return []

    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    roc = series.pct_change(periods=window).tolist()
    return [Decimal(str(val)) if pd.notna(val) else None for val in roc]


def calculate_rsi(data: List[MarketDataORM], window: int = 14) -> List[Optional[Decimal]]:
    """
    Calculates the Relative Strength Index (RSI).
    """
    if len(data) < window:
        return []

    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    delta = series.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return [Decimal(str(val)) if pd.notna(val) else None for val in rsi.tolist()]


def calculate_macd(data: List[MarketDataORM], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculates the Moving Average Convergence Divergence (MACD).
    Returns a DataFrame with 'MACD', 'Signal', and 'Histogram' columns.
    """
    if len(data) < slow_period:
        return pd.DataFrame()

    prices = [float(d.price) for d in data]
    series = pd.Series(prices)
    
    ema_fast = series.ewm(span=fast_period, adjust=False).mean()
    ema_slow = series.ewm(span=slow_period, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    
    df = pd.DataFrame({
        'MACD': [Decimal(str(val)) if pd.notna(val) else None for val in macd_line],
        'Signal': [Decimal(str(val)) if pd.notna(val) else None for val in signal_line],
        'Histogram': [Decimal(str(val)) if pd.notna(val) else None for val in histogram]
    })
    
    return df
