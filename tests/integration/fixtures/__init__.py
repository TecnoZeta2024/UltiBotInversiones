"""
Fixtures para tests de integración.

Este paquete contiene datos sintéticos y utilidades para testing
de componentes del sistema UltiBotInversiones.
"""

from .market_data_fixtures import (
    create_mock_ticker_data,
    create_mock_kline_data,
    create_bullish_market_snapshot,
    create_bearish_market_snapshot,
    create_sideways_market_snapshot,
    create_high_volatility_snapshot,
    create_arbitrage_opportunity_snapshots,
    create_news_sentiment_spike_data,
    create_onchain_metrics_data,
    assert_realistic_market_data,
    get_test_symbols,
    create_multi_timeframe_data
)

__all__ = [
    "create_mock_ticker_data",
    "create_mock_kline_data", 
    "create_bullish_market_snapshot",
    "create_bearish_market_snapshot",
    "create_sideways_market_snapshot",
    "create_high_volatility_snapshot",
    "create_arbitrage_opportunity_snapshots",
    "create_news_sentiment_spike_data",
    "create_onchain_metrics_data",
    "assert_realistic_market_data",
    "get_test_symbols",
    "create_multi_timeframe_data"
]
