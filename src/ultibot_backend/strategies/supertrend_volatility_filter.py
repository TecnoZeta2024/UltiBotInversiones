"""
SuperTrend Volatility Filter Strategy (Refactored)

Esta estrategia sigue tendencias marcadas por el indicador SuperTrend, pero solo si la volatilidad
(ATR) está dentro de un rango específico. Combina trend following con gestión de riesgo basada en volatilidad.
Ahora alineada con la arquitectura hexagonal y BaseStrategy.

Author: UltiBotInversiones
Version: 2.1
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
import statistics
from datetime import datetime # Importar datetime

from .base_strategy import BaseStrategy
from ..core.domain_models.market import MarketSnapshot, KlineData
from ..core.domain_models.trading import (
    AnalysisResult, TradingSignal, SuperTrendParameters, OrderSide, SignalStrength
)

logger = logging.getLogger(__name__)

class SuperTrendVolatilityFilter(BaseStrategy):
    """
    Estrategia SuperTrend con filtro de volatilidad, alineada con la arquitectura base.
    """
    
    def __init__(self, parameters: SuperTrendParameters):
        super().__init__(parameters)
        self._atr_history: List[float] = []

    async def setup(self) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con parámetros: {self.parameters}")
        pass

    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Analiza el mercado usando SuperTrend con filtro de volatilidad.
        """
        try:
            params = self.parameters
            if len(market_snapshot.klines) < params.volatility_lookback:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            atr_values = self._calculate_atr(market_snapshot.klines, params.atr_period)
            current_atr = atr_values[-1]
            
            supertrend_data = self._calculate_supertrend(market_snapshot.klines, atr_values, params.atr_multiplier)
            current_supertrend = supertrend_data["values"][-1]
            trend_direction = supertrend_data["direction"][-1]
            
            volatility_filter_passed = self._apply_volatility_filter(
                atr_values, params.volatility_lookback, params.min_volatility_percentile, params.max_volatility_percentile
            )
            
            trend_strength = self._calculate_trend_strength(market_snapshot.klines, supertrend_data["values"])
            
            confidence = self._calculate_confidence(
                trend_direction, trend_strength, volatility_filter_passed
            )
            
            current_price = float(market_snapshot.klines[-1].close)
            
            indicators = {
                "supertrend": current_supertrend,
                "trend_direction": trend_direction,
                "atr": current_atr,
                "trend_strength": trend_strength,
                "volatility_filter_passed": volatility_filter_passed,
                "price": current_price
            }
            
            metadata = {
                "atr_period": params.atr_period,
                "atr_multiplier": params.atr_multiplier,
                "volatility_percentile": self._get_volatility_percentile(atr_values, params.volatility_lookback)
            }

            signal = None
            if confidence > params.min_trend_strength and volatility_filter_passed:
                signal = self._generate_signal_from_analysis(indicators, market_snapshot.symbol, market_snapshot.timestamp) # Pasar timestamp

            return AnalysisResult(
                confidence=confidence,
                indicators=indicators,
                metadata=metadata,
                signal=signal
            )
            
        except Exception as e:
            logger.error(f"Error en análisis SuperTrend: {e}", exc_info=True)
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    def _generate_signal_from_analysis(self, indicators: Dict[str, Any], symbol: str, timestamp: datetime) -> Optional[TradingSignal]: # Añadir timestamp
        """Genera una señal de trading basada en el resultado del análisis."""
        trend_direction = indicators.get("trend_direction", 0)
        current_price = indicators.get("price", 0)
        supertrend = indicators.get("supertrend", 0)
        
        side = None
        if trend_direction == 1 and current_price > supertrend:
            side = OrderSide.BUY
        elif trend_direction == -1 and current_price < supertrend:
            side = OrderSide.SELL

        if side:
            confidence = indicators.get("trend_strength", 0.0) # Usar trend_strength como base para la señal
            signal_strength = self._get_signal_strength(confidence)
            position_size = self._calculate_position_size(signal_strength)
            stop_loss = Decimal(str(supertrend))
            take_profit = self._calculate_take_profit(current_price, stop_loss, side)
            
            return self._create_trading_signal(
                symbol=symbol,
                side=side,
                quantity=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strength=signal_strength,
                reasoning=f"SuperTrend {side.value} signal with favorable volatility. Price: {current_price:.4f}, SuperTrend: {supertrend:.4f}",
                timestamp=timestamp # Pasar timestamp a _create_trading_signal
            )
        return None

    def _calculate_atr(self, klines: List[KlineData], period: int) -> List[float]:
        """Calcula Average True Range."""
        atr_values = []
        if not klines:
            return []

        highs = [float(k.high) for k in klines]
        lows = [float(k.low) for k in klines]
        closes = [float(k.close) for k in klines]

        for i in range(len(klines)):
            if i == 0:
                true_range = highs[i] - lows[i]
            else:
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_range = max(tr1, tr2, tr3)
            
            if not atr_values:
                atr_values.append(true_range)
            else:
                atr = (atr_values[-1] * (period - 1) + true_range) / period
                atr_values.append(atr)
        
        return atr_values

    def _calculate_supertrend(self, klines: List[KlineData], atr_values: List[float], multiplier: float) -> Dict[str, List[Any]]:
        """Calcula el indicador SuperTrend."""
        hl2 = [(float(k.high) + float(k.low)) / 2 for k in klines]
        closes = [float(k.close) for k in klines]
        
        # Initialize bands and direction
        upper_band = [0.0] * len(klines)
        lower_band = [0.0] * len(klines)
        supertrend = [0.0] * len(klines)
        direction = [0] * len(klines) # 1 for uptrend, -1 for downtrend

        for i in range(len(klines)):
            # Calculate basic upper and lower bands
            basic_upper_band = hl2[i] + multiplier * atr_values[i]
            basic_lower_band = hl2[i] - multiplier * atr_values[i]

            if i == 0:
                upper_band[i] = basic_upper_band
                lower_band[i] = basic_lower_band
                direction[i] = 1 # Assume uptrend initially
            else:
                # Update upper band
                upper_band[i] = min(basic_upper_band, upper_band[i-1]) if closes[i-1] > upper_band[i-1] else basic_upper_band
                # Update lower band
                lower_band[i] = max(basic_lower_band, lower_band[i-1]) if closes[i-1] < lower_band[i-1] else basic_lower_band

                # Determine SuperTrend direction and value
                if direction[i-1] == 1: # Previous trend was up
                    if closes[i] < lower_band[i]: # Price crosses below lower band
                        direction[i] = -1 # Trend changes to down
                    else:
                        direction[i] = 1 # Trend remains up
                else: # Previous trend was down (-1)
                    if closes[i] > upper_band[i]: # Price crosses above upper band
                        direction[i] = 1 # Trend changes to up
                    else:
                        direction[i] = -1 # Trend remains down
            
            # Calculate SuperTrend value based on current direction
            if direction[i] == 1:
                supertrend[i] = lower_band[i]
            else:
                supertrend[i] = upper_band[i]

            # Adjust SuperTrend value if price crosses it
            if i > 0:
                if supertrend[i] > supertrend[i-1] and closes[i] < supertrend[i]:
                    supertrend[i] = supertrend[i-1]
                elif supertrend[i] < supertrend[i-1] and closes[i] > supertrend[i]:
                    supertrend[i] = supertrend[i-1]

        return {"values": supertrend, "direction": direction}

    def _apply_volatility_filter(self, atr_values: List[float], lookback: int, min_percentile: float, max_percentile: float) -> bool:
        """Aplica filtro de volatilidad basado en percentiles."""
        if len(atr_values) < lookback:
            return False
            
        recent_atr = atr_values[-lookback:]
        current_atr = atr_values[-1]
        
        try:
            if min_percentile == 0.0:
                min_threshold = min(recent_atr)
            else:
                min_threshold = statistics.quantiles(recent_atr, n=100)[int(min_percentile) - 1] # Adjust index for 1-based percentile

            if max_percentile == 100.0:
                max_threshold = max(recent_atr)
            else:
                max_threshold = statistics.quantiles(recent_atr, n=100)[int(max_percentile) - 1] # Adjust index for 1-based percentile
        except IndexError:
            return False # Not enough data points for quantiles or invalid percentile

        return min_threshold <= current_atr <= max_threshold

    def _calculate_trend_strength(self, klines: List[KlineData], supertrend_values: List[float]) -> float:
        """Calcula la fuerza de la tendencia."""
        if len(klines) < 20 or len(supertrend_values) < 20:
            return 0.0
            
        recent_klines = klines[-20:]
        recent_supertrend = supertrend_values[-20:]
        
        trend_aligned_count = 0
        for kline, st_value in zip(recent_klines, recent_supertrend):
            close_price = float(kline.close)
            if close_price > st_value:
                trend_aligned_count += 1
            elif close_price < st_value:
                trend_aligned_count -= 1
        
        return abs(trend_aligned_count / len(recent_klines))

    def _calculate_confidence(self, trend_direction: int, trend_strength: float, volatility_filter_passed: bool) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        if not volatility_filter_passed:
            return 0.0
        
        confidence = 0.5
        confidence += trend_strength * 0.4
        if abs(trend_direction) == 1:
            confidence += 0.1
        
        return min(1.0, confidence)

    def _get_volatility_percentile(self, atr_values: List[float], lookback: int) -> float:
        """Obtiene el percentil de volatilidad actual."""
        if len(atr_values) < lookback:
            return 50.0
            
        recent_atr = sorted(atr_values[-lookback:])
        current_atr = atr_values[-1]
        
        rank = sum(1 for atr in recent_atr if atr < current_atr)
        return (rank / len(recent_atr)) * 100

    def _get_signal_strength(self, confidence: float) -> SignalStrength:
        """Convierte confianza a fuerza de señal."""
        if confidence >= 0.8:
            return SignalStrength.STRONG
        elif confidence >= 0.6:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength) -> Decimal:
        """Calcula el tamaño de posición basado en la fuerza de la señal."""
        base_size = self.parameters.position_size_pct
        
        if signal_strength == SignalStrength.STRONG:
            multiplier = 1.5
        elif signal_strength == SignalStrength.MODERATE:
            multiplier = 1.0
        else:
            multiplier = 0.5
            
        return Decimal(str(base_size * multiplier))

    def _calculate_take_profit(self, entry_price: float, stop_loss: Decimal, side: OrderSide) -> Decimal:
        """Calcula take profit usando el ratio riesgo-recompensa de los parámetros."""
        risk = abs(Decimal(str(entry_price)) - stop_loss)
        reward = risk * Decimal(str(self.parameters.risk_reward_ratio))
        
        if side == OrderSide.BUY:
            return Decimal(str(entry_price)) + reward
        else:
            return Decimal(str(entry_price)) - reward
