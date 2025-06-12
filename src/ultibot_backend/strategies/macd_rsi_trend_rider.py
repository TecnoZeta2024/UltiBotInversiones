"""
Módulo que implementa la estrategia de trading MACD_RSI_Trend_Rider.
Esta estrategia combina el Moving Average Convergence Divergence (MACD) y el Relative Strength Index (RSI)
para identificar oportunidades de seguimiento de tendencia con confirmación de momentum.
"""

from decimal import Decimal, getcontext
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import Field, ConfigDict

from ultibot_backend.core.domain_models.market import KlineData, MarketSnapshot
from ultibot_backend.core.domain_models.trading import (
    BaseStrategyParameters, AnalysisResult, TradingSignal, OrderSide, OrderType, SignalStrength
)
from ultibot_backend.strategies.base_strategy import BaseStrategy

# Configurar la precisión decimal global
getcontext().prec = 10

class MACDRSIParameters(BaseStrategyParameters): # Heredar de BaseStrategyParameters
    """
    Parámetros de configuración para la estrategia MACD_RSI_Trend_Rider.
    """
    name: str = "MACD_RSI_Trend_Rider" # Asegurar que el nombre esté definido aquí
    macd_fast_period: int = Field(default=12, description="Período para la EMA rápida del MACD.")
    macd_slow_period: int = Field(default=26, description="Período para la EMA lenta del MACD.")
    macd_signal_period: int = Field(default=9, description="Período para la línea de señal del MACD.")
    rsi_period: int = Field(default=14, description="Período para el cálculo del RSI.")
    rsi_overbought: Decimal = Field(default=Decimal('70'), description="Umbral de sobrecompra del RSI.")
    rsi_oversold: Decimal = Field(default=Decimal('30'), description="Umbral de sobreventa del RSI.")
    take_profit_percent: Decimal = Field(default=Decimal('0.02'), description="Porcentaje de take profit (ej. 0.02 para 2%).")
    stop_loss_percent: Decimal = Field(default=Decimal('0.01'), description="Porcentaje de stop loss (ej. 0.01 para 1%).")
    trade_quantity_usd: Decimal = Field(default=Decimal('100'), description="Cantidad a operar en USD.")

    model_config = ConfigDict(frozen=True)

class MACDRSITrendRider(BaseStrategy):
    """
    Estrategia de trading que utiliza MACD y RSI para identificar tendencias.
    """
    def __init__(self, parameters: MACDRSIParameters):
        """
        Inicializa la estrategia MACDRSITrendRider.

        Args:
            parameters (MACDRSIParameters): Parámetros específicos de la estrategia.
        """
        super().__init__(parameters)
        self.params: MACDRSIParameters = parameters

    async def setup(self) -> None:
        """
        Configuración inicial de la estrategia.
        En este caso, no se requiere una configuración asíncrona compleja.
        """
        # Podría cargar datos históricos aquí si fuera necesario para pre-cálculos
        pass

    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Analiza el estado actual del mercado utilizando MACD y RSI.

        Args:
            market_snapshot (MarketSnapshot): Una instantánea del estado actual del mercado.

        Returns:
            AnalysisResult: El resultado del análisis, incluyendo la confianza y los indicadores.
        """
        if not market_snapshot.klines or len(market_snapshot.klines) < max(self.params.macd_slow_period, self.params.rsi_period) + self.params.macd_signal_period:
            return AnalysisResult(
                confidence=Decimal('0.0'),
                indicators={"error": "Not enough kline data for analysis."}
            )

        closes = [kline.close for kline in market_snapshot.klines]
        
        macd_line, signal_line, hist = self._calculate_macd(
            closes,
            self.params.macd_fast_period,
            self.params.macd_slow_period,
            self.params.macd_signal_period
        )
        
        rsi_value = self._calculate_rsi(closes, self.params.rsi_period)

        indicators = {
            "macd_line": macd_line[-1] if macd_line else None,
            "signal_line": signal_line[-1] if signal_line else None,
            "macd_histogram": hist[-1] if hist else None,
            "rsi": rsi_value[-1] if rsi_value else None,
            "current_price": market_snapshot.ticker.price
        }
        
        confidence = self._calculate_confidence(indicators)
        
        # Generar señal dentro de analyze
        signal = None
        if confidence >= Decimal('0.7'): # Umbral de confianza para generar señal
            macd_line_val = indicators.get("macd_line")
            signal_line_val = indicators.get("signal_line")
            rsi_val = indicators.get("rsi")
            current_price = indicators.get("current_price")
            symbol = market_snapshot.symbol # Usar el símbolo del snapshot

            if macd_line_val is not None and signal_line_val is not None and rsi_val is not None and current_price is not None:
                if macd_line_val > signal_line_val and rsi_val < self.params.rsi_overbought:
                    # Señal de compra: MACD cruza por encima de la línea de señal y RSI no está sobrecomprado
                    quantity = self.params.trade_quantity_usd / current_price
                    signal = self._create_trading_signal(
                        symbol=symbol,
                        side=OrderSide.BUY,
                        quantity=quantity,
                        order_type=OrderType.MARKET,
                        timestamp=market_snapshot.timestamp # Pasar timestamp
                    )
                elif macd_line_val < signal_line_val and rsi_val > self.params.rsi_oversold:
                    # Señal de venta: MACD cruza por debajo de la línea de señal y RSI no está sobrevendido
                    quantity = self.params.trade_quantity_usd / current_price
                    signal = self._create_trading_signal(
                        symbol=symbol,
                        side=OrderSide.SELL,
                        quantity=quantity,
                        order_type=OrderType.MARKET,
                        timestamp=market_snapshot.timestamp # Pasar timestamp
                    )
        
        return AnalysisResult(
            confidence=confidence,
            indicators=indicators,
            signal=signal
        )

    def _calculate_ema(self, prices: List[Decimal], period: int) -> List[Decimal]:
        """Calcula la Media Móvil Exponencial (EMA)."""
        if not prices or len(prices) < period:
            return []
        
        ema_values = []
        sma = sum(prices[:period]) / Decimal(period)
        ema_values.append(sma)
        
        multiplier = Decimal('2') / Decimal(period + 1)
        
        for i in range(period, len(prices)):
            ema = (prices[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
            
        return ema_values

    def _calculate_macd(self, closes: List[Decimal], fast_period: int, slow_period: int, signal_period: int) -> tuple[List[Decimal], List[Decimal], List[Decimal]]:
        """Calcula MACD, línea de señal e histograma."""
        if len(closes) < slow_period + signal_period:
            return [], [], []

        ema_fast = self._calculate_ema(closes, fast_period)
        ema_slow = self._calculate_ema(closes, slow_period)

        # Asegurarse de que las listas tienen la misma longitud para el cálculo de MACD
        min_len = min(len(ema_fast), len(ema_slow))
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(min_len)]

        if len(macd_line) < signal_period:
            return macd_line, [], []

        signal_line = self._calculate_ema(macd_line, signal_period)
        
        # Asegurarse de que las listas tienen la misma longitud para el cálculo del histograma
        min_len_hist = min(len(macd_line), len(signal_line))
        hist = [macd_line[i] - signal_line[i] for i in range(min_len_hist)]

        return macd_line, signal_line, hist

    def _calculate_rsi(self, closes: List[Decimal], period: int) -> List[Decimal]:
        """Calcula el Relative Strength Index (RSI)."""
        if len(closes) < period + 1:
            return []

        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(Decimal('0'))
            else:
                gains.append(Decimal('0'))
                losses.append(abs(change))

        avg_gains = []
        avg_losses = []

        # Primer promedio simple
        avg_gains.append(sum(gains[:period]) / Decimal(period))
        avg_losses.append(sum(losses[:period]) / Decimal(period))

        # Promedio exponencial para el resto
        for i in range(period, len(gains)):
            avg_gains.append(((avg_gains[-1] * (period - 1)) + gains[i]) / Decimal(period))
            avg_losses.append(((avg_losses[-1] * (period - 1)) + losses[i]) / Decimal(period))

        rs_values = []
        for i in range(len(avg_gains)):
            if avg_losses[i] == 0:
                rs_values.append(Decimal('1000000')) # Evitar división por cero, valor alto para RSI = 100
            else:
                rs_values.append(avg_gains[i] / avg_losses[i])

        rsi_values = []
        for rs in rs_values:
            rsi = Decimal('100') - (Decimal('100') / (Decimal('1') + rs))
            rsi_values.append(rsi)
            
        return rsi_values[len(rsi_values) - len(closes) + period:] # Ajustar para que la longitud coincida con los precios de entrada

    def _calculate_confidence(self, indicators: Dict[str, Any]) -> Decimal:
        """
        Calcula un nivel de confianza basado en los indicadores.
        Esta es una lógica simplificada y puede ser mejorada.
        """
        macd_line = indicators.get("macd_line")
        signal_line = indicators.get("signal_line")
        rsi = indicators.get("rsi")

        if macd_line is None or signal_line is None or rsi is None:
            return Decimal('0.0')

        confidence = Decimal('0.0')

        # Confianza basada en el cruce de MACD
        if macd_line > signal_line:
            confidence += Decimal('0.4') # Tendencia alcista
        elif macd_line < signal_line:
            confidence += Decimal('0.4') # Tendencia bajista

        # Confianza basada en RSI
        if rsi < self.params.rsi_oversold:
            confidence += Decimal('0.3') # Potencial de rebote (compra)
        elif rsi > self.params.rsi_overbought:
            confidence += Decimal('0.3') # Potencial de corrección (venta)
        
        # Ajuste basado en la distancia del cruce MACD
        macd_diff = abs(macd_line - signal_line)
        if macd_diff > Decimal('0.0'): # Evitar log(0)
            confidence += Decimal(min(Decimal('0.3'), macd_diff * Decimal('10'))) # Más diferencia, más confianza

        return min(Decimal('1.0'), confidence) # Asegurar que la confianza no exceda 1.0
