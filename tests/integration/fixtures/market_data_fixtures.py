"""
Fixtures de datos de mercado para tests de integración.

Este módulo proporciona datos de mercado sintéticos y realistas para 
testing de estrategias y flujos de trading.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import List
import random

from ultibot_backend.core.domain_models.market import TickerData, KlineData
from ultibot_backend.core.domain_models.trading import MarketSnapshot

def create_mock_ticker_data(
    symbol: str = "BTCUSDT",
    price: float = 45000.0,
    change_24h: float = 2.5,
    volume_24h: float = 50000000.0
) -> TickerData:
    """Crea datos de ticker mock para testing."""
    return TickerData(
        symbol=symbol,
        price=Decimal(str(price)),
        price_change_24h=Decimal(str(change_24h)),
        price_change_percent_24h=Decimal(str(change_24h / price * 100)),
        volume_24h=Decimal(str(volume_24h)),
        high_24h=Decimal(str(price * 1.05)),
        low_24h=Decimal(str(price * 0.95)),
        open_24h=Decimal(str(price * 0.98)),
        timestamp=datetime.utcnow()
    )

def create_mock_kline_data(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    periods: int = 100,
    base_price: float = 45000.0,
    trend: str = "bullish"  # "bullish", "bearish", "sideways"
) -> List[KlineData]:
    """
    Crea datos de velas (klines) mock para testing.
    
    Args:
        symbol: Par de trading
        interval: Intervalo de tiempo
        periods: Número de períodos a generar
        base_price: Precio base inicial
        trend: Tendencia del mercado
    """
    klines = []
    current_time = datetime.utcnow() - timedelta(hours=periods)
    current_price = base_price
    
    # Configuración de tendencia
    trend_factor = {
        "bullish": 0.002,    # 0.2% promedio por período
        "bearish": -0.002,   # -0.2% promedio por período
        "sideways": 0.0      # Sin tendencia
    }.get(trend, 0.0)
    
    for i in range(periods):
        # Simulación de movimiento de precio realista
        noise = random.uniform(-0.01, 0.01)  # Ruido de ±1%
        price_change = trend_factor + noise
        
        # Calcular precios OHLC
        open_price = current_price
        close_price = open_price * (1 + price_change)
        
        # High y Low basados en volatilidad realista
        volatility = random.uniform(0.005, 0.02)  # 0.5% a 2% de volatilidad
        high_price = max(open_price, close_price) * (1 + volatility)
        low_price = min(open_price, close_price) * (1 - volatility)
        
        # Volumen aleatorio pero realista
        base_volume = 1000000
        volume_multiplier = random.uniform(0.5, 2.0)
        volume = base_volume * volume_multiplier
        
        kline = KlineData(
            symbol=symbol,
            interval=interval,
            open_time=current_time,
            close_time=current_time + timedelta(hours=1),
            open_price=Decimal(f"{open_price:.2f}"),
            high_price=Decimal(f"{high_price:.2f}"),
            low_price=Decimal(f"{low_price:.2f}"),
            close_price=Decimal(f"{close_price:.2f}"),
            volume=Decimal(f"{volume:.2f}"),
            quote_volume=Decimal(f"{volume * close_price:.2f}"),
            trades_count=random.randint(5000, 15000)
        )
        
        klines.append(kline)
        current_price = close_price
        current_time += timedelta(hours=1)
    
    return klines

def create_bullish_market_snapshot(symbol: str = "BTCUSDT") -> MarketSnapshot:
    """Crea un snapshot de mercado alcista para testing."""
    ticker = create_mock_ticker_data(
        symbol=symbol,
        price=45000.0,
        change_24h=1125.0,  # +2.5%
        volume_24h=75000000.0  # Alto volumen
    )
    
    klines = create_mock_kline_data(
        symbol=symbol,
        periods=50,
        base_price=43000.0,  # Precio inicial más bajo
        trend="bullish"
    )
    
    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        ticker_data=ticker,
        klines=klines,
        timeframe="1h",
        indicators={
            "rsi": 65.5,           # RSI alcista pero no sobrecomprado
            "macd": 150.0,         # MACD positivo
            "macd_signal": 120.0,  # Señal por debajo de MACD (bullish)
            "bb_upper": 46000.0,   # Bollinger Bands
            "bb_middle": 45000.0,
            "bb_lower": 44000.0,
            "volume_sma": 25000000.0,
            "atr": 800.0           # Average True Range
        },
        volume_data={
            "current_volume": 2500000,
            "avg_volume_1h": 1500000,
            "volume_trend": "increasing"
        }
    )

def create_bearish_market_snapshot(symbol: str = "BTCUSDT") -> MarketSnapshot:
    """Crea un snapshot de mercado bajista para testing."""
    ticker = create_mock_ticker_data(
        symbol=symbol,
        price=43000.0,
        change_24h=-1075.0,  # -2.5%
        volume_24h=85000000.0  # Alto volumen en venta
    )
    
    klines = create_mock_kline_data(
        symbol=symbol,
        periods=50,
        base_price=45000.0,  # Precio inicial más alto
        trend="bearish"
    )
    
    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        ticker_data=ticker,
        klines=klines,
        timeframe="1h",
        indicators={
            "rsi": 35.5,           # RSI bajista pero no sobrevendido
            "macd": -150.0,        # MACD negativo
            "macd_signal": -120.0, # Señal por encima de MACD (bearish)
            "bb_upper": 44000.0,   # Bollinger Bands
            "bb_middle": 43000.0,
            "bb_lower": 42000.0,
            "volume_sma": 30000000.0,
            "atr": 900.0           # Mayor volatilidad en bajada
        },
        volume_data={
            "current_volume": 3500000,
            "avg_volume_1h": 2000000,
            "volume_trend": "increasing"  # Volumen alto en venta
        }
    )

def create_sideways_market_snapshot(symbol: str = "BTCUSDT") -> MarketSnapshot:
    """Crea un snapshot de mercado lateral para testing."""
    ticker = create_mock_ticker_data(
        symbol=symbol,
        price=44000.0,
        change_24h=50.0,    # +0.11% (muy poco cambio)
        volume_24h=25000000.0  # Volumen bajo
    )
    
    klines = create_mock_kline_data(
        symbol=symbol,
        periods=50,
        base_price=44000.0,
        trend="sideways"
    )
    
    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        ticker_data=ticker,
        klines=klines,
        timeframe="1h",
        indicators={
            "rsi": 50.0,           # RSI neutral
            "macd": 5.0,           # MACD casi neutral
            "macd_signal": 3.0,    # Señales muy cerca
            "bb_upper": 44500.0,   # Bollinger Bands estrechas
            "bb_middle": 44000.0,
            "bb_lower": 43500.0,
            "volume_sma": 15000000.0,
            "atr": 300.0           # Baja volatilidad
        },
        volume_data={
            "current_volume": 800000,
            "avg_volume_1h": 750000,
            "volume_trend": "stable"
        }
    )

def create_high_volatility_snapshot(symbol: str = "BTCUSDT") -> MarketSnapshot:
    """Crea un snapshot de mercado con alta volatilidad para testing."""
    ticker = create_mock_ticker_data(
        symbol=symbol,
        price=44000.0,
        change_24h=2200.0,  # +5% (alta volatilidad)
        volume_24h=150000000.0  # Volumen muy alto
    )
    
    # Klines con alta volatilidad
    klines = []
    base_time = datetime.utcnow() - timedelta(hours=20)
    
    # Simular movimientos bruscos de precio
    prices = [42000, 43500, 41500, 44000, 46000, 43000, 45000, 44000]
    
    for i, price in enumerate(prices):
        open_price = prices[i-1] if i > 0 else 42000
        close_price = price
        
        # Alta volatilidad en High/Low
        high_price = max(open_price, close_price) * 1.03
        low_price = min(open_price, close_price) * 0.97
        
        kline = KlineData(
            symbol=symbol,
            interval="1h",
            open_time=base_time + timedelta(hours=i),
            close_time=base_time + timedelta(hours=i+1),
            open_price=Decimal(f"{open_price:.2f}"),
            high_price=Decimal(f"{high_price:.2f}"),
            low_price=Decimal(f"{low_price:.2f}"),
            close_price=Decimal(f"{close_price:.2f}"),
            volume=Decimal("5000000.0"),  # Alto volumen
            quote_volume=Decimal(f"{5000000 * close_price:.2f}"),
            trades_count=25000
        )
        klines.append(kline)
    
    return MarketSnapshot(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        ticker_data=ticker,
        klines=klines,
        timeframe="1h",
        indicators={
            "rsi": 75.0,           # RSI sobrecomprado
            "macd": 300.0,         # MACD muy positivo
            "macd_signal": 200.0,
            "bb_upper": 47000.0,   # Bollinger Bands amplias
            "bb_middle": 44000.0,
            "bb_lower": 41000.0,
            "volume_sma": 20000000.0,
            "atr": 1500.0          # ATR muy alto
        },
        volume_data={
            "current_volume": 8000000,
            "avg_volume_1h": 3000000,
            "volume_trend": "explosive"
        }
    )

def create_arbitrage_opportunity_snapshots() -> tuple[MarketSnapshot, MarketSnapshot, MarketSnapshot]:
    """
    Crea snapshots para testing de arbitraje triangular.
    Retorna 3 snapshots que forman una oportunidad de arbitraje.
    """
    # BTC/USDT
    btc_usdt = create_mock_ticker_data(
        symbol="BTCUSDT",
        price=45000.0,
        volume_24h=50000000.0
    )
    
    # ETH/USDT  
    eth_usdt = create_mock_ticker_data(
        symbol="ETHUSDT", 
        price=3000.0,
        volume_24h=40000000.0
    )
    
    # BTC/ETH (oportunidad de arbitraje: ligeramente desbalanceado)
    btc_eth = create_mock_ticker_data(
        symbol="BTCETH",
        price=15.05,  # Precio ligeramente alto (45000/3000 = 15.0)
        volume_24h=5000000.0
    )
    
    # Crear snapshots completos
    snapshots = []
    for ticker in [btc_usdt, eth_usdt, btc_eth]:
        klines = create_mock_kline_data(
            symbol=ticker.symbol,
            periods=20,
            base_price=float(ticker.price),
            trend="sideways"  # Mercado estable para arbitraje
        )
        
        snapshot = MarketSnapshot(
            symbol=ticker.symbol,
            timestamp=datetime.utcnow(),
            ticker_data=ticker,
            klines=klines,
            timeframe="5m",  # Timeframe corto para arbitraje
            indicators={
                "rsi": 50.0,
                "volume_sma": float(ticker.volume_24h) / 24,
                "atr": float(ticker.price) * 0.01
            },
            volume_data={
                "current_volume": float(ticker.volume_24h) / 24 / 12,
                "avg_volume_1h": float(ticker.volume_24h) / 24,
                "volume_trend": "stable"
            }
        )
        snapshots.append(snapshot)
    
    return tuple(snapshots)

def create_news_sentiment_spike_data(symbol: str = "BTCUSDT") -> dict:
    """
    Crea datos de sentimiento de noticias para testing de la estrategia 
    News Sentiment Spike Trader.
    """
    return {
        "market_snapshot": create_high_volatility_snapshot(symbol),
        "sentiment_data": {
            "overall_score": 0.85,  # Muy positivo
            "confidence": 0.9,
            "sources_count": 25,
            "positive_mentions": 18,
            "negative_mentions": 3,
            "neutral_mentions": 4,
            "trending_keywords": ["bullish", "breakout", "institutional", "adoption"],
            "news_velocity": 15,  # Noticias por hora
            "sentiment_change_1h": 0.25,  # Cambio significativo
            "major_sources": ["coindesk", "cointelegraph", "bloomberg"],
            "timestamp": datetime.utcnow()
        },
        "volume_spike_data": {
            "current_volume": 8000000,
            "avg_volume_24h": 2000000,
            "spike_ratio": 4.0,  # 4x el volumen normal
            "spike_duration_minutes": 45,
            "volume_trend": "explosive"
        }
    }

def create_onchain_metrics_data(symbol: str = "BTCUSDT") -> dict:
    """
    Crea datos de métricas on-chain para testing de la estrategia
    OnChain Metrics Divergence.
    """
    return {
        "market_snapshot": create_bullish_market_snapshot(symbol),
        "onchain_data": {
            "whale_activity": {
                "large_transactions_24h": 156,
                "whale_net_flow": 2450.5,  # BTC entrando a wallets de ballenas
                "whale_accumulation_score": 0.78
            },
            "network_metrics": {
                "hash_rate": 450e18,  # Hash rate en H/s
                "difficulty": 55.6e12,
                "active_addresses": 950000,
                "transaction_count_24h": 280000,
                "fees_usd_24h": 15000000
            },
            "exchange_flows": {
                "exchange_inflow_24h": -1200.5,  # Negativo = salida de exchanges
                "exchange_outflow_24h": 1850.3,
                "net_flow": -649.8,  # Neto saliendo (bullish)
                "major_exchanges_balance_change": -2.1  # % cambio
            },
            "derivatives": {
                "funding_rate": 0.0001,  # Funding rate neutral
                "open_interest": 12500000000,  # USD en contratos abiertos
                "long_short_ratio": 1.35,  # Más longs que shorts
                "liquidations_24h": 25000000  # USD en liquidaciones
            },
            "social_metrics": {
                "social_dominance": 4.2,  # % de menciones en crypto
                "sentiment_score": 0.72,
                "fear_greed_index": 68,  # Greed territory
                "google_trends": 85
            },
            "timestamp": datetime.utcnow()
        }
    }

# Funciones de utilidad para tests

def assert_realistic_market_data(snapshot: MarketSnapshot):
    """Valida que los datos de mercado sean realistas."""
    assert snapshot.ticker_data.price > 0
    assert snapshot.ticker_data.volume_24h > 0
    assert len(snapshot.klines) > 0
    
    # Validar que los precios OHLC sean consistentes
    for kline in snapshot.klines:
        assert kline.low_price <= kline.open_price <= kline.high_price
        assert kline.low_price <= kline.close_price <= kline.high_price
        assert kline.volume > 0

def get_test_symbols() -> list[str]:
    """Retorna lista de símbolos para testing."""
    return [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT",
        "LINKUSDT", "LTCUSDT", "BCHUSDT", "XLMUSDT", "EOSUSDT"
    ]

def create_multi_timeframe_data(symbol: str = "BTCUSDT") -> dict:
    """Crea datos para múltiples timeframes."""
    return {
        "5m": create_mock_kline_data(symbol, "5m", 288, trend="bullish"),    # 1 día
        "15m": create_mock_kline_data(symbol, "15m", 96, trend="bullish"),   # 1 día  
        "1h": create_mock_kline_data(symbol, "1h", 168, trend="bullish"),    # 1 semana
        "4h": create_mock_kline_data(symbol, "4h", 42, trend="bullish"),     # 1 semana
        "1d": create_mock_kline_data(symbol, "1d", 30, trend="bullish")      # 1 mes
    }
