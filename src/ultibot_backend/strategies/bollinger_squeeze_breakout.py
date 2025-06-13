"""
Módulo que implementa la estrategia de trading Bollinger_Squeeze_Breakout.
Esta estrategia busca períodos de baja volatilidad (squeeze de Bandas de Bollinger)
seguidos de una expansión de la volatilidad (breakout) para identificar oportunidades.
"""

from decimal import Decimal, getcontext
from typing import List, Optional, Dict, Any
from datetime import datetime
import statistics

from pydantic import Field, ConfigDict

from src.ultibot_backend.core.domain_models.market import KlineData, MarketData
from ultibot_backend.core.domain_models.trading import (
    BaseStrategyParameters, AnalysisResult, TradingSignal, OrderSide, OrderType
)
from ultibot_backend.strategies.base_strategy import BaseStrategy

# Configurar la precisión decimal global
getcontext().prec = 10

class BollingerSqueezeParameters(BaseStrategyParameters):
    """
    Parámetros de configuración para la estrategia Bollinger_Squeeze_Breakout.
    """
    bollinger_period: int = Field(default=20, description="Período para el cálculo de las Bandas de Bollinger.")
    std_dev_multiplier: Decimal = Field(default=Decimal('2.0'), description="Multiplicador de la desviación estándar para las bandas.")
    squeeze_threshold: Decimal = Field(default=Decimal('0.01'), description="Umbral para detectar el 'squeeze' (ancho de banda relativo).")
    breakout_threshold: Decimal = Field(default=Decimal('0.02'), description="Umbral para detectar el 'breakout' (cambio de precio relativo).")
    lookback_squeeze_periods: int = Field(default=5, description="Número de períodos para confirmar el squeeze.")
    trade_quantity_usd: Decimal = Field(default=Decimal('100'), description="Cantidad a operar en USD.")

    model_config = ConfigDict(frozen=True)

class BollingerSqueezeBreakout(BaseStrategy):
    """
    Estrategia de trading que identifica el 'squeeze' y 'breakout' de las Bandas de Bollinger.
    """
    def __init__(self, parameters: BollingerSqueezeParameters):
        """
        Inicializa la estrategia BollingerSqueezeBreakout.

        Args:
            parameters (BollingerSqueezeParameters): Parámetros específicos de la estrategia.
        """
        super().__init__(parameters)
        self.params: BollingerSqueezeParameters = parameters
        self._is_squeezed: bool = False

    async def setup(self) -> None:
        """
        Configuración inicial de la estrategia.
        """
        pass

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza el estado actual del mercado para detectar el squeeze y el breakout.

        Args:
            market_snapshot (MarketData): Una instantánea del estado actual del mercado.

        Returns:
            AnalysisResult: El resultado del análisis.
        """
        required_klines = self.params.bollinger_period + self.params.lookback_squeeze_periods
        if not market_snapshot.klines or len(market_snapshot.klines) < required_klines:
            return AnalysisResult(
                confidence=Decimal('0.0'),
                indicators={"error": "Not enough kline data for Bollinger Bands calculation."}
            )

        closes = [kline.close for kline in market_snapshot.klines]
        
        upper_band, middle_band, lower_band, band_width = self._calculate_bollinger_bands(
            closes,
            self.params.bollinger_period,
            self.params.std_dev_multiplier
        )

        current_band_width = band_width[-1] if band_width else Decimal('0')
        current_price = market_snapshot.ticker.price

        # Detectar squeeze
        is_squeezed_now = False
        if current_band_width > Decimal('0'): # Evitar división por cero
            relative_band_width = current_band_width / middle_band[-1] if middle_band else Decimal('0')
            if relative_band_width < self.params.squeeze_threshold:
                is_squeezed_now = True
        
        # Confirmar squeeze en períodos anteriores
        squeezed_history = []
        for i in range(len(band_width) - self.params.lookback_squeeze_periods, len(band_width) -1):
            if band_width[i] > Decimal('0') and middle_band[i] > Decimal('0'):
                squeezed_history.append((band_width[i] / middle_band[i]) < self.params.squeeze_threshold)
            else:
                squeezed_history.append(False)
        
        # Si ha estado en squeeze y ahora no, o si está en squeeze ahora
        if all(squeezed_history) and not is_squeezed_now:
            self._is_squeezed = False # Squeeze ha terminado
        elif is_squeezed_now:
            self._is_squeezed = True # Estamos en squeeze

        # Detectar breakout
        is_breakout = False
        if not self._is_squeezed and len(closes) >= 2: # Solo si no estamos en squeeze y hay suficientes datos
            price_change = (current_price - closes[-2]) / closes[-2]
            if abs(price_change) > self.params.breakout_threshold:
                is_breakout = True

        indicators = {
            "upper_band": upper_band[-1] if upper_band else None,
            "middle_band": middle_band[-1] if middle_band else None,
            "lower_band": lower_band[-1] if lower_band else None,
            "band_width": current_band_width,
            "is_squeezed": self._is_squeezed,
            "is_breakout": is_breakout,
            "current_price": current_price
        }
        
        confidence = self._calculate_confidence(indicators)
        
        return AnalysisResult(
            confidence=confidence,
            indicators=indicators
        )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera una señal de trading si se detecta un breakout después de un squeeze.

        Args:
            analysis (AnalysisResult): El resultado del análisis de mercado.

        Returns:
            Optional[TradingSignal]: Una señal de trading si se detecta una oportunidad, de lo contrario None.
        """
        if not analysis.indicators.get("is_breakout") or analysis.confidence < Decimal('0.7'):
            return None

        current_price = analysis.indicators.get("current_price")
        symbol = self.parameters.name.split('_')[0] # Asumiendo que el nombre de la estrategia contiene el símbolo
        
        if current_price is None:
            return None

        # Determinar la dirección del breakout
        # Si el precio actual es mayor que la banda superior, es un breakout alcista
        # Si el precio actual es menor que la banda inferior, es un breakout bajista
        upper_band = analysis.indicators.get("upper_band")
        lower_band = analysis.indicators.get("lower_band")

        signal = None
        if upper_band is not None and current_price > upper_band:
            quantity = self.params.trade_quantity_usd / current_price
            signal = self._create_trading_signal(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
        elif lower_band is not None and current_price < lower_band:
            quantity = self.params.trade_quantity_usd / current_price
            signal = self._create_trading_signal(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=quantity,
                order_type=OrderType.MARKET
            )
        
        return signal

    def _calculate_bollinger_bands(self, closes: List[Decimal], period: int, std_dev_multiplier: Decimal) -> tuple[List[Decimal], List[Decimal], List[Decimal], List[Decimal]]:
        """Calcula las Bandas de Bollinger (Upper, Middle, Lower) y el ancho de banda."""
        if len(closes) < period:
            return [], [], [], []

        middle_band = []
        upper_band = []
        lower_band = []
        band_width = []

        for i in range(len(closes) - period + 1):
            window = closes[i : i + period]
            
            # SMA (Middle Band)
            sma = sum(window) / Decimal(period)
            middle_band.append(sma)

            # Desviación estándar
            if len(window) > 1:
                std_dev = Decimal(statistics.stdev(float(x) for x in window))
            else:
                std_dev = Decimal('0')

            # Bandas
            upper = sma + (std_dev * std_dev_multiplier)
            lower = sma - (std_dev * std_dev_multiplier)
            
            upper_band.append(upper)
            lower_band.append(lower)
            
            # Ancho de banda
            width = upper - lower
            band_width.append(width)

        return upper_band, middle_band, lower_band, band_width

    def _calculate_confidence(self, indicators: Dict[str, Any]) -> Decimal:
        """
        Calcula un nivel de confianza basado en los indicadores de Bollinger.
        """
        is_squeezed = indicators.get("is_squeezed")
        is_breakout = indicators.get("is_breakout")
        band_width = indicators.get("band_width")
        current_price = indicators.get("current_price")
        middle_band = indicators.get("middle_band")

        confidence = Decimal('0.0')

        if is_squeezed:
            confidence += Decimal('0.3') # Alta confianza en que la volatilidad es baja

        if is_breakout:
            confidence += Decimal('0.5') # Alta confianza en que hay un movimiento direccional

            # Ajustar confianza según la dirección del breakout
            if current_price > middle_band: # Breakout alcista
                confidence += Decimal('0.1')
            elif current_price < middle_band: # Breakout bajista
                confidence += Decimal('0.1')
        
        # Si el ancho de banda es muy pequeño, aumenta la confianza en el squeeze
        if band_width is not None and middle_band is not None and middle_band > Decimal('0'):
            relative_width = band_width / middle_band
            if relative_width < self.params.squeeze_threshold * Decimal('0.8'): # Más apretado
                confidence += Decimal('0.1')

        return min(Decimal('1.0'), confidence)
