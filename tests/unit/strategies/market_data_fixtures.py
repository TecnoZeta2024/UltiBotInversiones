"""
Fixtures de datos de mercado sintéticos para tests de estrategias.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from typing import List
import pytest

from src.ultibot_backend.core.domain_models.market import KlineData, MarketSnapshot, TickerData


class MarketDataFixtures:
    """
    Generador de datos de mercado sintéticos para tests.
    """
    
    @staticmethod
    def generate_trending_up_klines(
        base_price: Decimal = Decimal('50000'),
        count: int = 100,
        trend_strength: Decimal = Decimal('0.02')
    ) -> List[KlineData]:
        """
        Genera datos de velas con tendencia alcista.
        
        Args:
            base_price: Precio base inicial
            count: Número de velas a generar
            trend_strength: Fuerza de la tendencia (0.02 = 2% por vela)
        """
        klines = []
        current_time = datetime.now() - timedelta(hours=count)
        
        for i in range(count):
            # Tendencia alcista con ruido
            trend_factor = Decimal(1) + (trend_strength * Decimal(i) / Decimal(count))
            noise = Decimal('0.005') * (Decimal(i % 3) - Decimal('1'))  # Ruido ±0.5%
            
            open_price = base_price * trend_factor * (Decimal('1') + noise)
            close_price = open_price * (Decimal('1') + Decimal('0.001'))  # Ligero sesgo alcista
            high_price = max(open_price, close_price) * Decimal('1.002')
            low_price = min(open_price, close_price) * Decimal('0.998')
            
            klines.append(KlineData(
                open_time=current_time + timedelta(hours=i),
                close_time=current_time + timedelta(hours=i+1),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=Decimal('1000') + Decimal(i * 10),  # Volumen creciente
                trades_count=100 + i,
                base_asset_volume=Decimal('500') + Decimal(i * 5),
                quote_asset_volume=Decimal('25000000') + Decimal(i * 250000)
            ))
        
        return klines
    
    @staticmethod
    def generate_trending_down_klines(
        base_price: Decimal = Decimal('50000'),
        count: int = 100,
        trend_strength: Decimal = Decimal('0.02')
    ) -> List[KlineData]:
        """
        Genera datos de velas con tendencia bajista.
        """
        klines = []
        current_time = datetime.now() - timedelta(hours=count)
        
        for i in range(count):
            # Tendencia bajista con ruido
            trend_factor = Decimal(1) - (trend_strength * Decimal(i) / Decimal(count))
            noise = Decimal('0.005') * (Decimal(i % 3) - Decimal('1'))
            
            open_price = base_price * trend_factor * (Decimal('1') + noise)
            close_price = open_price * (Decimal('1') - Decimal('0.001'))  # Ligero sesgo bajista
            high_price = max(open_price, close_price) * Decimal('1.002')
            low_price = min(open_price, close_price) * Decimal('0.998')
            
            klines.append(KlineData(
                open_time=current_time + timedelta(hours=i),
                close_time=current_time + timedelta(hours=i+1),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=Decimal('1000') + Decimal(i * 10),
                trades_count=100 + i,
                base_asset_volume=Decimal('500') + Decimal(i * 5),
                quote_asset_volume=Decimal('25000000') + Decimal(i * 250000)
            ))
        
        return klines
    
    @staticmethod
    def generate_sideways_klines(
        base_price: Decimal = Decimal('50000'),
        count: int = 100,
        volatility: Decimal = Decimal('0.01')
    ) -> List[KlineData]:
        """
        Genera datos de velas con movimiento lateral.
        """
        klines = []
        current_time = datetime.now() - timedelta(hours=count)
        
        for i in range(count):
            # Movimiento lateral con volatilidad
            noise = volatility * (Decimal(i % 7) - Decimal('3')) / Decimal('3')
            
            open_price = base_price * (Decimal('1') + noise)
            close_price = open_price * (Decimal('1') + (Decimal(i % 5) - Decimal('2')) * Decimal('0.002'))
            high_price = max(open_price, close_price) * Decimal('1.005')
            low_price = min(open_price, close_price) * Decimal('0.995')
            
            klines.append(KlineData(
                open_time=current_time + timedelta(hours=i),
                close_time=current_time + timedelta(hours=i+1),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=Decimal('800') + Decimal(i % 20 * 10),  # Volumen variable
                trades_count=80 + (i % 20),
                base_asset_volume=Decimal('400') + Decimal(i % 20 * 5),
                quote_asset_volume=Decimal('20000000') + Decimal(i % 20 * 200000)
            ))
        
        return klines
    
    @staticmethod
    def generate_bollinger_squeeze_klines(
        base_price: Decimal = Decimal('50000'),
        count: int = 50
    ) -> List[KlineData]:
        """
        Genera datos que simulan un 'squeeze' de Bandas de Bollinger seguido de breakout.
        """
        klines = []
        current_time = datetime.now() - timedelta(hours=count)
        
        for i in range(count):
            if i < count * 0.7:  # 70% del tiempo en squeeze (baja volatilidad)
                volatility = Decimal('0.002')  # 0.2% volatilidad
                noise = volatility * (Decimal(i % 3) - Decimal('1'))
                open_price = base_price * (Decimal('1') + noise)
                close_price = open_price * (Decimal('1') + noise * Decimal('0.5'))
            else:  # 30% final con breakout (alta volatilidad)
                volatility = Decimal('0.015')  # 1.5% volatilidad
                trend = Decimal('0.005')  # Tendencia alcista en el breakout
                noise = volatility * (Decimal(i % 5) - Decimal('2')) / Decimal('2')
                open_price = base_price * (Decimal('1') + trend + noise)
                close_price = open_price * (Decimal('1') + trend)
            
            high_price = max(open_price, close_price) * Decimal('1.003')
            low_price = min(open_price, close_price) * Decimal('0.997')
            
            klines.append(KlineData(
                open_time=current_time + timedelta(hours=i),
                close_time=current_time + timedelta(hours=i+1),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=Decimal('1000') if i < count * 0.7 else Decimal('2000'),  # Volumen sube en breakout
                trades_count=100 if i < count * 0.7 else 200,
                base_asset_volume=Decimal('500') if i < count * 0.7 else Decimal('1000'),
                quote_asset_volume=Decimal('25000000') if i < count * 0.7 else Decimal('50000000')
            ))
        
        return klines
    
    @staticmethod
    def generate_market_snapshot(
        symbol: str = "BTCUSDT",
        klines: List[KlineData] = None,
        ticker_price: Decimal = None
    ) -> MarketSnapshot:
        """
        Genera un MarketSnapshot completo para tests.
        """
        if klines is None:
            klines = MarketDataFixtures.generate_sideways_klines()
        
        if ticker_price is None:
            ticker_price = klines[-1].close if klines else Decimal('50000')
        
        ticker = TickerData(
            symbol=symbol,
            price=ticker_price,
            price_change=ticker_price - klines[-2].close if len(klines) > 1 else Decimal('0'),
            price_change_percent=Decimal('0.1'),
            high_24h=max(k.high for k in klines[-24:]) if len(klines) >= 24 else ticker_price * Decimal('1.02'),
            low_24h=min(k.low for k in klines[-24:]) if len(klines) >= 24 else ticker_price * Decimal('0.98'),
            volume_24h=sum(k.volume for k in klines[-24:]) if len(klines) >= 24 else Decimal('50000'),
            quote_volume_24h=sum(k.quote_asset_volume for k in klines[-24:]) if len(klines) >= 24 else Decimal('2500000000'),
            trades_count_24h=sum(k.trades_count for k in klines[-24:]) if len(klines) >= 24 else 2400,
            timestamp=datetime.now()
        )
        
        return MarketSnapshot(
            symbol=symbol,
            timestamp=datetime.now(),
            ticker=ticker,
            klines=klines
        )


# Fixtures para pytest
@pytest.fixture
def trending_up_snapshot():
    """Fixture para snapshot con tendencia alcista."""
    klines = MarketDataFixtures.generate_trending_up_klines(count=50)
    return MarketDataFixtures.generate_market_snapshot(klines=klines)


@pytest.fixture
def trending_down_snapshot():
    """Fixture para snapshot con tendencia bajista."""
    klines = MarketDataFixtures.generate_trending_down_klines(count=50)
    return MarketDataFixtures.generate_market_snapshot(klines=klines)


@pytest.fixture
def sideways_snapshot():
    """Fixture para snapshot con movimiento lateral."""
    klines = MarketDataFixtures.generate_sideways_klines(count=50)
    return MarketDataFixtures.generate_market_snapshot(klines=klines)


@pytest.fixture
def bollinger_squeeze_snapshot():
    """Fixture para snapshot con squeeze de Bollinger."""
    klines = MarketDataFixtures.generate_bollinger_squeeze_klines(count=50)
    return MarketDataFixtures.generate_market_snapshot(klines=klines)


@pytest.fixture
def insufficient_data_snapshot():
    """Fixture para snapshot con datos insuficientes."""
    klines = MarketDataFixtures.generate_sideways_klines(count=5)  # Pocos datos
    return MarketDataFixtures.generate_market_snapshot(klines=klines)
