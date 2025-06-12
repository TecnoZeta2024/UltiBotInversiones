"""
Stochastic RSI Overbought/Oversold Strategy

Esta estrategia busca reversiones en niveles extremos de sobrecompra/sobreventa
utilizando el indicador Stochastic RSI, que combina la sensibilidad del Stochastic
con la normalización del RSI.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
import statistics

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from src.ultibot_backend.core.domain_models.market import MarketData, KlineData

logger = logging.getLogger(__name__)

class StochasticRSIParameters:
    """Parámetros configurables para Stochastic RSI Overbought/Oversold."""
    
    def __init__(
        self,
        rsi_period: int = 14,
        stoch_k_period: int = 14,
        stoch_d_period: int = 3,
        overbought_level: float = 80.0,
        oversold_level: float = 20.0,
        extreme_overbought: float = 90.0,
        extreme_oversold: float = 10.0,
        divergence_lookback: int = 20,
        min_volume_increase: float = 1.2,
        position_size_pct: float = 0.015,
        risk_reward_ratio: float = 2.5
    ):
        self.rsi_period = rsi_period
        self.stoch_k_period = stoch_k_period
        self.stoch_d_period = stoch_d_period
        self.overbought_level = overbought_level
        self.oversold_level = oversold_level
        self.extreme_overbought = extreme_overbought
        self.extreme_oversold = extreme_oversold
        self.divergence_lookback = divergence_lookback
        self.min_volume_increase = min_volume_increase
        self.position_size_pct = position_size_pct
        self.risk_reward_ratio = risk_reward_ratio

class StochasticRSIOverboughtOversold(BaseStrategy):
    """
    Estrategia de reversión basada en Stochastic RSI.
    
    Identifica oportunidades de mean reversion cuando el Stochastic RSI alcanza
    niveles extremos, con confirmación adicional de volumen y divergencias.
    """
    
    def __init__(self, parameters: StochasticRSIParameters):
        super().__init__("Stochastic_RSI_Overbought_Oversold", parameters)
        self.rsi_period = parameters.rsi_period
        self.stoch_k_period = parameters.stoch_k_period
        self.stoch_d_period = parameters.stoch_d_period
        self.overbought_level = parameters.overbought_level
        self.oversold_level = parameters.oversold_level
        self.extreme_overbought = parameters.extreme_overbought
        self.extreme_oversold = parameters.extreme_oversold
        self.divergence_lookback = parameters.divergence_lookback
        self.min_volume_increase = parameters.min_volume_increase
        self.position_size_pct = parameters.position_size_pct
        self.risk_reward_ratio = parameters.risk_reward_ratio
        
        self._rsi_history = []
        self._stoch_rsi_history = []

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con RSI period={self.rsi_period}, Stoch K={self.stoch_k_period}")

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza el mercado usando Stochastic RSI para identificar extremos.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis de Stochastic RSI y condiciones de reversión
        """
        try:
            if len(market_snapshot.klines) < max(self.rsi_period, self.stoch_k_period, self.divergence_lookback) + 10:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Calcular RSI
            rsi_values = self._calculate_rsi(market_snapshot.klines)
            
            # Calcular Stochastic RSI
            stoch_rsi_data = self._calculate_stochastic_rsi(rsi_values)
            
            # Obtener valores actuales
            current_stoch_k = stoch_rsi_data["k"][-1]
            current_stoch_d = stoch_rsi_data["d"][-1]
            current_rsi = rsi_values[-1]
            current_price = float(market_snapshot.klines[-1].close)
            
            # Detectar condiciones de extremo
            extreme_condition = self._detect_extreme_condition(current_stoch_k, current_stoch_d)
            
            # Detectar divergencias
            divergence = self._detect_divergence(market_snapshot.klines, stoch_rsi_data["k"])
            
            # Analizar volumen
            volume_confirmation = self._analyze_volume_confirmation(market_snapshot.klines)
            
            # Detectar patrones de reversión en velas
            candle_pattern = self._detect_reversal_candle_patterns(market_snapshot.klines[-5:])
            
            # Calcular momentum del Stochastic RSI
            stoch_momentum = self._calculate_stoch_momentum(stoch_rsi_data)
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                extreme_condition, divergence, volume_confirmation, 
                candle_pattern, stoch_momentum
            )
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "stoch_rsi_k": current_stoch_k,
                    "stoch_rsi_d": current_stoch_d,
                    "rsi": current_rsi,
                    "price": current_price,
                    "extreme_condition": extreme_condition,
                    "divergence": divergence,
                    "volume_confirmation": volume_confirmation,
                    "candle_pattern": candle_pattern,
                    "stoch_momentum": stoch_momentum
                },
                metadata={
                    "overbought_level": self.overbought_level,
                    "oversold_level": self.oversold_level,
                    "extreme_levels": {
                        "overbought": self.extreme_overbought,
                        "oversold": self.extreme_oversold
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis Stochastic RSI: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de trading basada en el análisis Stochastic RSI.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se cumplen las condiciones, None en caso contrario
        """
        try:
            if analysis.confidence < 0.6:  # Umbral mínimo para reversión
                return None
                
            indicators = analysis.indicators
            extreme_condition = indicators.get("extreme_condition")
            volume_confirmation = indicators.get("volume_confirmation", False)
            divergence = indicators.get("divergence")
            
            current_price = indicators.get("price", 0)
            stoch_k = indicators.get("stoch_rsi_k", 50)
            stoch_d = indicators.get("stoch_rsi_d", 50)
            
            # Señal de compra (desde oversold)
            if (extreme_condition == "oversold" and 
                stoch_k > stoch_d and  # K cruzando hacia arriba de D
                (volume_confirmation or divergence == "bullish")):
                
                signal_strength = self._get_signal_strength(analysis.confidence)
                position_size = self._calculate_position_size(signal_strength)
                
                # Calcular stop loss y take profit
                atr_estimate = self._estimate_atr_from_recent_candles(analysis.metadata.get("recent_klines", []))
                stop_loss = current_price - (atr_estimate * 1.5)
                take_profit = current_price + (abs(current_price - stop_loss) * self.risk_reward_ratio)
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=Decimal(str(stop_loss)),
                    take_profit=Decimal(str(take_profit)),
                    position_size=position_size,
                    reasoning=f"Stochastic RSI oversold reversal. StochK: {stoch_k:.2f}, StochD: {stoch_d:.2f}, Div: {divergence}, Vol: {volume_confirmation}"
                )
                
            # Señal de venta (desde overbought)
            elif (extreme_condition == "overbought" and 
                  stoch_k < stoch_d and  # K cruzando hacia abajo de D
                  (volume_confirmation or divergence == "bearish")):
                
                signal_strength = self._get_signal_strength(analysis.confidence)
                position_size = self._calculate_position_size(signal_strength)
                
                # Calcular stop loss y take profit
                atr_estimate = self._estimate_atr_from_recent_candles(analysis.metadata.get("recent_klines", []))
                stop_loss = current_price + (atr_estimate * 1.5)
                take_profit = current_price - (abs(stop_loss - current_price) * self.risk_reward_ratio)
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=Decimal(str(stop_loss)),
                    take_profit=Decimal(str(take_profit)),
                    position_size=position_size,
                    reasoning=f"Stochastic RSI overbought reversal. StochK: {stoch_k:.2f}, StochD: {stoch_d:.2f}, Div: {divergence}, Vol: {volume_confirmation}"
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal Stochastic RSI: {e}")
            return None

    def _calculate_rsi(self, klines: list[KlineData]) -> list[float]:
        """Calcula Relative Strength Index."""
        closes = [float(k.close) for k in klines]
        rsi_values = []
        
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        for i in range(len(gains)):
            if i < self.rsi_period - 1:
                rsi_values.append(50)  # Valor neutro inicial
                continue
                
            if i == self.rsi_period - 1:
                # Primera medición
                avg_gain = statistics.mean(gains[:self.rsi_period])
                avg_loss = statistics.mean(losses[:self.rsi_period])
            else:
                # Suavizado exponencial
                alpha = 1 / self.rsi_period
                avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
                avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values

    def _calculate_stochastic_rsi(self, rsi_values: list[float]) -> Dict[str, list[float]]:
        """Calcula Stochastic RSI."""
        stoch_rsi_k = []
        stoch_rsi_d = []
        
        for i in range(len(rsi_values)):
            if i < self.stoch_k_period - 1:
                stoch_rsi_k.append(50)  # Valor neutro inicial
                continue
                
            # Tomar ventana de RSI
            rsi_window = rsi_values[i - self.stoch_k_period + 1:i + 1]
            
            rsi_max = max(rsi_window)
            rsi_min = min(rsi_window)
            current_rsi = rsi_values[i]
            
            if rsi_max == rsi_min:
                stoch_k = 50
            else:
                stoch_k = ((current_rsi - rsi_min) / (rsi_max - rsi_min)) * 100
            
            stoch_rsi_k.append(stoch_k)
        
        # Calcular %D (media móvil de %K)
        for i in range(len(stoch_rsi_k)):
            if i < self.stoch_d_period - 1:
                stoch_rsi_d.append(stoch_rsi_k[i])
                continue
                
            d_window = stoch_rsi_k[i - self.stoch_d_period + 1:i + 1]
            stoch_d = statistics.mean(d_window)
            stoch_rsi_d.append(stoch_d)
        
        return {
            "k": stoch_rsi_k,
            "d": stoch_rsi_d
        }

    def _detect_extreme_condition(self, stoch_k: float, stoch_d: float) -> Optional[str]:
        """Detecta condiciones extremas de sobrecompra/sobreventa."""
        # Condiciones extremas
        if stoch_k >= self.extreme_overbought and stoch_d >= self.extreme_overbought:
            return "extreme_overbought"
        elif stoch_k <= self.extreme_oversold and stoch_d <= self.extreme_oversold:
            return "extreme_oversold"
        
        # Condiciones normales de señal
        elif stoch_k >= self.overbought_level and stoch_d >= self.overbought_level:
            return "overbought"
        elif stoch_k <= self.oversold_level and stoch_d <= self.oversold_level:
            return "oversold"
        
        return None

    def _detect_divergence(self, klines: list[KlineData], stoch_k_values: list[float]) -> Optional[str]:
        """Detecta divergencias entre precio y Stochastic RSI."""
        if len(klines) < self.divergence_lookback:
            return None
            
        recent_klines = klines[-self.divergence_lookback:]
        recent_stoch = stoch_k_values[-self.divergence_lookback:]
        
        # Encontrar picos y valles en precio
        price_highs = []
        price_lows = []
        stoch_highs = []
        stoch_lows = []
        
        for i in range(2, len(recent_klines) - 2):
            price = float(recent_klines[i].close)
            stoch = recent_stoch[i]
            
            # Pico en precio
            if (float(recent_klines[i-1].close) < price > float(recent_klines[i+1].close) and
                float(recent_klines[i-2].close) < price > float(recent_klines[i+2].close)):
                price_highs.append((i, price))
                stoch_highs.append((i, stoch))
            
            # Valle en precio
            if (float(recent_klines[i-1].close) > price < float(recent_klines[i+1].close) and
                float(recent_klines[i-2].close) > price < float(recent_klines[i+2].close)):
                price_lows.append((i, price))
                stoch_lows.append((i, stoch))
        
        # Detectar divergencia alcista (precio hace mínimos más bajos, Stochastic mínimos más altos)
        if len(price_lows) >= 2 and len(stoch_lows) >= 2:
            latest_price_low = price_lows[-1][1]
            prev_price_low = price_lows[-2][1]
            latest_stoch_low = stoch_lows[-1][1]
            prev_stoch_low = stoch_lows[-2][1]
            
            if latest_price_low < prev_price_low and latest_stoch_low > prev_stoch_low:
                return "bullish"
        
        # Detectar divergencia bajista (precio hace máximos más altos, Stochastic máximos más bajos)
        if len(price_highs) >= 2 and len(stoch_highs) >= 2:
            latest_price_high = price_highs[-1][1]
            prev_price_high = price_highs[-2][1]
            latest_stoch_high = stoch_highs[-1][1]
            prev_stoch_high = stoch_highs[-2][1]
            
            if latest_price_high > prev_price_high and latest_stoch_high < prev_stoch_high:
                return "bearish"
        
        return None

    def _analyze_volume_confirmation(self, klines: list[KlineData]) -> bool:
        """Analiza si hay confirmación de volumen."""
        if len(klines) < 10:
            return False
            
        recent_volumes = [float(k.volume) for k in klines[-5:]]
        prev_volumes = [float(k.volume) for k in klines[-10:-5]]
        
        avg_recent = statistics.mean(recent_volumes)
        avg_prev = statistics.mean(prev_volumes)
        
        return avg_recent >= (avg_prev * self.min_volume_increase)

    def _detect_reversal_candle_patterns(self, recent_klines: list[KlineData]) -> Optional[str]:
        """Detecta patrones de velas de reversión."""
        if len(recent_klines) < 3:
            return None
            
        last_candle = recent_klines[-1]
        prev_candle = recent_klines[-2]
        
        open_price = float(last_candle.open)
        close_price = float(last_candle.close)
        high_price = float(last_candle.high)
        low_price = float(last_candle.low)
        
        body_size = abs(close_price - open_price)
        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price
        
        # Doji (cuerpo pequeño)
        candle_range = high_price - low_price
        if body_size < (candle_range * 0.1):
            return "doji"
        
        # Hammer (sombra inferior larga, cuerpo pequeño en la parte superior)
        if (lower_shadow > body_size * 2 and 
            upper_shadow < body_size * 0.5 and
            close_price > open_price):
            return "hammer"
        
        # Shooting star (sombra superior larga, cuerpo pequeño en la parte inferior)
        if (upper_shadow > body_size * 2 and 
            lower_shadow < body_size * 0.5 and
            close_price < open_price):
            return "shooting_star"
        
        return None

    def _calculate_stoch_momentum(self, stoch_data: Dict[str, list[float]]) -> float:
        """Calcula el momentum del Stochastic RSI."""
        k_values = stoch_data["k"]
        
        if len(k_values) < 5:
            return 0.0
            
        recent_k = k_values[-5:]
        
        # Calcular cambio promedio
        changes = []
        for i in range(1, len(recent_k)):
            changes.append(recent_k[i] - recent_k[i-1])
        
        return statistics.mean(changes) if changes else 0.0

    def _calculate_confidence(
        self,
        extreme_condition: Optional[str],
        divergence: Optional[str],
        volume_confirmation: bool,
        candle_pattern: Optional[str],
        stoch_momentum: float
    ) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: condición extrema
        if extreme_condition in ["extreme_overbought", "extreme_oversold"]:
            confidence += 0.4
        elif extreme_condition in ["overbought", "oversold"]:
            confidence += 0.25
        
        # Bonus por divergencia
        if divergence in ["bullish", "bearish"]:
            confidence += 0.25
        
        # Bonus por confirmación de volumen
        if volume_confirmation:
            confidence += 0.15
        
        # Bonus por patrones de velas
        if candle_pattern in ["hammer", "shooting_star", "doji"]:
            confidence += 0.1
        
        # Ajuste por momentum
        momentum_factor = min(abs(stoch_momentum) / 10, 0.1)  # Normalizar
        confidence += momentum_factor
        
        return min(1.0, confidence)

    def _estimate_atr_from_recent_candles(self, klines: list[KlineData]) -> float:
        """Estima ATR de velas recientes para cálculo de stop loss."""
        if len(klines) < 5:
            return 0.01  # Default 1%
            
        true_ranges = []
        for i in range(1, len(klines)):
            high = float(klines[i].high)
            low = float(klines[i].low)
            prev_close = float(klines[i-1].close)
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return statistics.mean(true_ranges)

    def _get_signal_strength(self, confidence: float) -> SignalStrength:
        """Convierte confianza a fuerza de señal."""
        if confidence >= 0.85:
            return SignalStrength.STRONG
        elif confidence >= 0.7:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength) -> Decimal:
        """Calcula el tamaño de posición basado en la fuerza de la señal."""
        base_size = self.position_size_pct
        
        if signal_strength == SignalStrength.STRONG:
            multiplier = 1.3
        elif signal_strength == SignalStrength.MEDIUM:
            multiplier = 1.0
        else:
            multiplier = 0.7
            
        return Decimal(str(base_size * multiplier))
