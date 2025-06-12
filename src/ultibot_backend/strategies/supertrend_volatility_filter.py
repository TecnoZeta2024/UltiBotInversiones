"""
SuperTrend Volatility Filter Strategy

Esta estrategia sigue tendencias marcadas por el indicador SuperTrend, pero solo si la volatilidad
(ATR) está dentro de un rango específico. Combina trend following con gestión de riesgo basada en volatilidad.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
import statistics

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from ..core.domain_models.market import MarketSnapshot, KlineData

logger = logging.getLogger(__name__)


class SuperTrendParameters:
    """Parámetros configurables para SuperTrend Volatility Filter."""
    
    def __init__(
        self,
        atr_period: int = 14,
        atr_multiplier: float = 3.0,
        min_volatility_percentile: float = 20.0,
        max_volatility_percentile: float = 80.0,
        volatility_lookback: int = 100,
        min_trend_strength: float = 0.7,
        position_size_pct: float = 0.02
    ):
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.min_volatility_percentile = min_volatility_percentile
        self.max_volatility_percentile = max_volatility_percentile
        self.volatility_lookback = volatility_lookback
        self.min_trend_strength = min_trend_strength
        self.position_size_pct = position_size_pct


class SuperTrendVolatilityFilter(BaseStrategy):
    """
    Estrategia SuperTrend con filtro de volatilidad.
    
    Entra en tendencias marcadas por SuperTrend, pero solo si la volatilidad actual
    está dentro del rango especificado (ni muy baja ni muy alta).
    """
    
    def __init__(self, parameters: SuperTrendParameters):
        super().__init__("SuperTrend_Volatility_Filter", parameters)
        self.atr_period = parameters.atr_period
        self.atr_multiplier = parameters.atr_multiplier
        self.min_volatility_percentile = parameters.min_volatility_percentile
        self.max_volatility_percentile = parameters.max_volatility_percentile
        self.volatility_lookback = parameters.volatility_lookback
        self.min_trend_strength = parameters.min_trend_strength
        self.position_size_pct = parameters.position_size_pct
        
        self._atr_history = []
        self._supertrend_history = []

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con ATR period={self.atr_period}, multiplier={self.atr_multiplier}")

    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Analiza el mercado usando SuperTrend con filtro de volatilidad.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis de SuperTrend y volatilidad
        """
        try:
            if len(market_snapshot.klines) < self.volatility_lookback:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Calcular ATR
            atr_values = self._calculate_atr(market_snapshot.klines)
            current_atr = atr_values[-1]
            
            # Calcular SuperTrend
            supertrend_data = self._calculate_supertrend(market_snapshot.klines, atr_values)
            current_supertrend = supertrend_data["values"][-1]
            trend_direction = supertrend_data["direction"][-1]
            
            # Filtro de volatilidad
            volatility_filter = self._apply_volatility_filter(atr_values)
            
            # Calcular fuerza de la tendencia
            trend_strength = self._calculate_trend_strength(market_snapshot.klines, supertrend_data["values"])
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                trend_direction, trend_strength, volatility_filter, current_atr
            )
            
            current_price = float(market_snapshot.klines[-1].close)
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "supertrend": current_supertrend,
                    "trend_direction": trend_direction,  # 1: uptrend, -1: downtrend
                    "atr": current_atr,
                    "trend_strength": trend_strength,
                    "volatility_filter": volatility_filter,
                    "price": current_price
                },
                metadata={
                    "atr_period": self.atr_period,
                    "atr_multiplier": self.atr_multiplier,
                    "volatility_percentile": self._get_volatility_percentile(atr_values)
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis SuperTrend: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de trading basada en el análisis SuperTrend.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se cumplen las condiciones, None en caso contrario
        """
        try:
            if analysis.confidence < self.min_trend_strength:
                return None
                
            indicators = analysis.indicators
            trend_direction = indicators.get("trend_direction", 0)
            volatility_filter = indicators.get("volatility_filter", False)
            
            if not volatility_filter:
                logger.debug("Señal filtrada por volatilidad fuera de rango")
                return None
                
            current_price = indicators.get("price", 0)
            supertrend = indicators.get("supertrend", 0)
            
            if trend_direction == 1 and current_price > supertrend:
                # Señal de compra
                signal_strength = self._get_signal_strength(analysis.confidence)
                position_size = self._calculate_position_size(signal_strength)
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=Decimal(str(supertrend)),
                    take_profit=self._calculate_take_profit(current_price, supertrend, "BUY"),
                    position_size=position_size,
                    reasoning=f"SuperTrend uptrend signal with favorable volatility. Price: {current_price:.4f}, SuperTrend: {supertrend:.4f}"
                )
                
            elif trend_direction == -1 and current_price < supertrend:
                # Señal de venta
                signal_strength = self._get_signal_strength(analysis.confidence)
                position_size = self._calculate_position_size(signal_strength)
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=Decimal(str(supertrend)),
                    take_profit=self._calculate_take_profit(current_price, supertrend, "SELL"),
                    position_size=position_size,
                    reasoning=f"SuperTrend downtrend signal with favorable volatility. Price: {current_price:.4f}, SuperTrend: {supertrend:.4f}"
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal SuperTrend: {e}")
            return None

    def _calculate_atr(self, klines: list[KlineData]) -> list[float]:
        """Calcula Average True Range."""
        atr_values = []
        
        for i in range(len(klines)):
            if i == 0:
                atr_values.append(float(klines[i].high) - float(klines[i].low))
                continue
                
            high = float(klines[i].high)
            low = float(klines[i].low)
            prev_close = float(klines[i-1].close)
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            true_range = max(tr1, tr2, tr3)
            
            if i < self.atr_period:
                atr_values.append(statistics.mean([atr_values[j] for j in range(i)] + [true_range]))
            else:
                # EMA del ATR
                prev_atr = atr_values[-1]
                alpha = 2 / (self.atr_period + 1)
                atr = alpha * true_range + (1 - alpha) * prev_atr
                atr_values.append(atr)
        
        return atr_values

    def _calculate_supertrend(self, klines: list[KlineData], atr_values: list[float]) -> Dict[str, list]:
        """Calcula el indicador SuperTrend."""
        hl2 = [(float(k.high) + float(k.low)) / 2 for k in klines]
        
        basic_upper_band = []
        basic_lower_band = []
        final_upper_band = []
        final_lower_band = []
        supertrend = []
        direction = []
        
        for i in range(len(klines)):
            atr = atr_values[i]
            
            # Bandas básicas
            upper = hl2[i] + (self.atr_multiplier * atr)
            lower = hl2[i] - (self.atr_multiplier * atr)
            
            basic_upper_band.append(upper)
            basic_lower_band.append(lower)
            
            # Bandas finales
            if i == 0:
                final_upper_band.append(upper)
                final_lower_band.append(lower)
            else:
                # Final Upper Band
                if upper < final_upper_band[i-1] or float(klines[i-1].close) > final_upper_band[i-1]:
                    final_upper_band.append(upper)
                else:
                    final_upper_band.append(final_upper_band[i-1])
                
                # Final Lower Band
                if lower > final_lower_band[i-1] or float(klines[i-1].close) < final_lower_band[i-1]:
                    final_lower_band.append(lower)
                else:
                    final_lower_band.append(final_lower_band[i-1])
            
            # SuperTrend y dirección
            if i == 0:
                supertrend.append(final_lower_band[i])
                direction.append(1)
            else:
                if (supertrend[i-1] == final_upper_band[i-1] and 
                    float(klines[i].close) <= final_upper_band[i]):
                    supertrend.append(final_upper_band[i])
                    direction.append(-1)
                elif (supertrend[i-1] == final_upper_band[i-1] and 
                      float(klines[i].close) > final_upper_band[i]):
                    supertrend.append(final_lower_band[i])
                    direction.append(1)
                elif (supertrend[i-1] == final_lower_band[i-1] and 
                      float(klines[i].close) >= final_lower_band[i]):
                    supertrend.append(final_lower_band[i])
                    direction.append(1)
                elif (supertrend[i-1] == final_lower_band[i-1] and 
                      float(klines[i].close) < final_lower_band[i]):
                    supertrend.append(final_upper_band[i])
                    direction.append(-1)
                else:
                    supertrend.append(supertrend[i-1])
                    direction.append(direction[i-1])
        
        return {
            "values": supertrend,
            "direction": direction,
            "upper_band": final_upper_band,
            "lower_band": final_lower_band
        }

    def _apply_volatility_filter(self, atr_values: list[float]) -> bool:
        """Aplica filtro de volatilidad basado en percentiles."""
        if len(atr_values) < self.volatility_lookback:
            return False
            
        recent_atr = atr_values[-self.volatility_lookback:]
        current_atr = atr_values[-1]
        
        sorted_atr = sorted(recent_atr)
        min_threshold_idx = int(len(sorted_atr) * self.min_volatility_percentile / 100)
        max_threshold_idx = int(len(sorted_atr) * self.max_volatility_percentile / 100)
        
        min_threshold = sorted_atr[min_threshold_idx]
        max_threshold = sorted_atr[max_threshold_idx]
        
        return min_threshold <= current_atr <= max_threshold

    def _calculate_trend_strength(self, klines: list[KlineData], supertrend_values: list[float]) -> float:
        """Calcula la fuerza de la tendencia."""
        if len(klines) < 20:
            return 0.0
            
        # Contar cuántas velas están del lado correcto del SuperTrend
        recent_klines = klines[-20:]
        recent_supertrend = supertrend_values[-20:]
        
        trend_aligned = 0
        for i, kline in enumerate(recent_klines):
            close_price = float(kline.close)
            st_value = recent_supertrend[i]
            
            # Determinar dirección esperada
            if i > 0:
                prev_st = recent_supertrend[i-1]
                if st_value < close_price and prev_st < float(recent_klines[i-1].close):
                    trend_aligned += 1  # Uptrend consistente
                elif st_value > close_price and prev_st > float(recent_klines[i-1].close):
                    trend_aligned += 1  # Downtrend consistente
        
        return trend_aligned / len(recent_klines)

    def _calculate_confidence(
        self, 
        trend_direction: int, 
        trend_strength: float, 
        volatility_filter: bool,
        current_atr: float
    ) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: fuerza de la tendencia
        confidence += trend_strength * 0.4
        
        # Bonus por filtro de volatilidad
        if volatility_filter:
            confidence += 0.3
        
        # Bonus por dirección de tendencia clara
        if abs(trend_direction) == 1:
            confidence += 0.2
        
        # Penalización por volatilidad extrema
        if current_atr > 0:
            volatility_factor = min(1.0, 1 / (current_atr * 100))  # Ajustar según escala
            confidence += volatility_factor * 0.1
        
        return min(1.0, confidence)

    def _get_volatility_percentile(self, atr_values: list[float]) -> float:
        """Obtiene el percentil de volatilidad actual."""
        if len(atr_values) < self.volatility_lookback:
            return 50.0
            
        recent_atr = atr_values[-self.volatility_lookback:]
        current_atr = atr_values[-1]
        
        sorted_atr = sorted(recent_atr)
        rank = sorted_atr.index(min(sorted_atr, key=lambda x: abs(x - current_atr)))
        
        return (rank / len(sorted_atr)) * 100

    def _get_signal_strength(self, confidence: float) -> SignalStrength:
        """Convierte confianza a fuerza de señal."""
        if confidence >= 0.8:
            return SignalStrength.STRONG
        elif confidence >= 0.6:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength) -> Decimal:
        """Calcula el tamaño de posición basado en la fuerza de la señal."""
        base_size = self.position_size_pct
        
        if signal_strength == SignalStrength.STRONG:
            multiplier = 1.5
        elif signal_strength == SignalStrength.MEDIUM:
            multiplier = 1.0
        else:
            multiplier = 0.5
            
        return Decimal(str(base_size * multiplier))

    def _calculate_take_profit(self, entry_price: float, stop_loss: float, signal_type: str) -> Decimal:
        """Calcula take profit usando ratio 2:1."""
        risk = abs(entry_price - stop_loss)
        reward = risk * 2  # Ratio 2:1
        
        if signal_type == "BUY":
            tp = entry_price + reward
        else:
            tp = entry_price - reward
            
        return Decimal(str(tp))
