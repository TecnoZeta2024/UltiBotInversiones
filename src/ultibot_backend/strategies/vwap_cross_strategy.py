"""
VWAP Cross Strategy

Esta estrategia opera cruces del precio con el VWAP (Volume-Weighted Average Price),
un indicador que combina precio y volumen para identificar niveles de valor justo
y momentum institucional.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
import statistics

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from ..core.domain_models.market import MarketSnapshot, KlineData

logger = logging.getLogger(__name__)

class VWAPParameters:
    """Parámetros configurables para VWAP Cross Strategy."""
    
    def __init__(
        self,
        vwap_period: int = 100,
        volume_ma_period: int = 20,
        min_volume_threshold: float = 1.5,  # Múltiplo del volumen promedio
        deviation_bands: bool = True,
        deviation_multiplier: float = 2.0,
        trend_confirmation_period: int = 10,
        min_price_deviation: float = 0.002,  # 0.2% mínimo de desviación
        position_size_pct: float = 0.02,
        risk_reward_ratio: float = 2.0
    ):
        self.vwap_period = vwap_period
        self.volume_ma_period = volume_ma_period
        self.min_volume_threshold = min_volume_threshold
        self.deviation_bands = deviation_bands
        self.deviation_multiplier = deviation_multiplier
        self.trend_confirmation_period = trend_confirmation_period
        self.min_price_deviation = min_price_deviation
        self.position_size_pct = position_size_pct
        self.risk_reward_ratio = risk_reward_ratio

class VWAPCrossStrategy(BaseStrategy):
    """
    Estrategia basada en cruces del precio con VWAP.
    
    Opera cuando el precio cruza el VWAP con confirmación de volumen significativo,
    indicando movimientos institucionales y cambios en el momentum del mercado.
    """
    
    def __init__(self, parameters: VWAPParameters):
        super().__init__("VWAP_Cross_Strategy", parameters)
        self.vwap_period = parameters.vwap_period
        self.volume_ma_period = parameters.volume_ma_period
        self.min_volume_threshold = parameters.min_volume_threshold
        self.deviation_bands = parameters.deviation_bands
        self.deviation_multiplier = parameters.deviation_multiplier
        self.trend_confirmation_period = parameters.trend_confirmation_period
        self.min_price_deviation = parameters.min_price_deviation
        self.position_size_pct = parameters.position_size_pct
        self.risk_reward_ratio = parameters.risk_reward_ratio
        
        self._vwap_history = []
        self._volume_profile = []

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con VWAP period={self.vwap_period}")

    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Analiza el mercado usando VWAP y confirmación de volumen.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis de VWAP y oportunidades de cruce
        """
        try:
            if len(market_snapshot.klines) < self.vwap_period:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Calcular VWAP
            vwap_data = self._calculate_vwap(market_snapshot.klines)
            current_vwap = vwap_data["vwap"][-1]
            
            # Calcular bandas de desviación si están habilitadas
            deviation_data = None
            if self.deviation_bands:
                deviation_data = self._calculate_vwap_bands(market_snapshot.klines, vwap_data["vwap"])
            
            # Obtener precio actual
            current_price = float(market_snapshot.klines[-1].close)
            
            # Detectar cruce de VWAP
            vwap_cross = self._detect_vwap_cross(market_snapshot.klines, vwap_data["vwap"])
            
            # Analizar volumen
            volume_analysis = self._analyze_volume_profile(market_snapshot.klines)
            
            # Confirmar momentum del volumen
            volume_momentum = self._calculate_volume_momentum(market_snapshot.klines)
            
            # Analizar relación precio-volumen
            price_volume_relationship = self._analyze_price_volume_relationship(market_snapshot.klines)
            
            # Detectar zonas de soporte/resistencia en VWAP
            vwap_zones = self._identify_vwap_zones(vwap_data["vwap"], current_price)
            
            # Calcular desvío del precio respecto al VWAP
            price_deviation = (current_price - current_vwap) / current_vwap
            
            # Verificar condiciones de trading
            trading_conditions = self._evaluate_trading_conditions(
                vwap_cross, volume_analysis, price_deviation, volume_momentum
            )
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                vwap_cross, volume_analysis, abs(price_deviation), 
                volume_momentum, trading_conditions
            )
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "current_vwap": current_vwap,
                    "current_price": current_price,
                    "price_deviation": price_deviation,
                    "vwap_cross": vwap_cross,
                    "volume_analysis": volume_analysis,
                    "volume_momentum": volume_momentum,
                    "price_volume_relationship": price_volume_relationship,
                    "vwap_zones": vwap_zones,
                    "trading_conditions": trading_conditions
                },
                metadata={
                    "vwap_period": self.vwap_period,
                    "deviation_bands": deviation_data,
                    "min_volume_threshold": self.min_volume_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis VWAP Cross: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de trading basada en el análisis VWAP.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se detecta cruce válido, None en caso contrario
        """
        try:
            if analysis.confidence < 0.65:  # Umbral para VWAP
                return None
                
            indicators = analysis.indicators
            vwap_cross = indicators.get("vwap_cross")
            volume_analysis = indicators.get("volume_analysis", {})
            trading_conditions = indicators.get("trading_conditions", {})
            
            # Verificar volumen suficiente
            if not volume_analysis.get("sufficient_volume", False):
                logger.debug("Volumen insuficiente para VWAP cross")
                return None
                
            # Verificar condiciones de trading
            if not trading_conditions.get("valid_setup", False):
                return None
                
            current_price = indicators.get("current_price", 0)
            current_vwap = indicators.get("current_vwap", 0)
            price_deviation = indicators.get("price_deviation", 0)
            
            # Señal de compra (precio cruza arriba del VWAP)
            if vwap_cross == "bullish" and price_deviation > self.min_price_deviation:
                signal_strength = self._get_signal_strength(analysis.confidence, abs(price_deviation))
                position_size = self._calculate_position_size(signal_strength, volume_analysis)
                
                # Calcular stop loss y take profit
                stop_loss = self._calculate_stop_loss(current_price, current_vwap, "BUY")
                take_profit = self._calculate_take_profit(current_price, stop_loss, "BUY")
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"VWAP bullish cross with volume confirmation. Price: {current_price:.4f}, VWAP: {current_vwap:.4f}, Dev: {price_deviation:.3%}, Vol: {volume_analysis.get('volume_multiple', 0):.1f}x"
                )
                
            # Señal de venta (precio cruza abajo del VWAP)
            elif vwap_cross == "bearish" and price_deviation < -self.min_price_deviation:
                signal_strength = self._get_signal_strength(analysis.confidence, abs(price_deviation))
                position_size = self._calculate_position_size(signal_strength, volume_analysis)
                
                # Calcular stop loss y take profit
                stop_loss = self._calculate_stop_loss(current_price, current_vwap, "SELL")
                take_profit = self._calculate_take_profit(current_price, stop_loss, "SELL")
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"VWAP bearish cross with volume confirmation. Price: {current_price:.4f}, VWAP: {current_vwap:.4f}, Dev: {price_deviation:.3%}, Vol: {volume_analysis.get('volume_multiple', 0):.1f}x"
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal VWAP Cross: {e}")
            return None

    def _calculate_vwap(self, klines: List[KlineData]) -> Dict[str, List[float]]:
        """Calcula Volume-Weighted Average Price."""
        vwap_values = []
        cumulative_volume = 0.0
        cumulative_pv = 0.0
        
        for i, kline in enumerate(klines):
            # Precio típico (HLC/3)
            typical_price = (float(kline.high) + float(kline.low) + float(kline.close)) / 3
            volume = float(kline.volume)
            
            # Usar ventana deslizante si superamos el período
            if i >= self.vwap_period:
                # Restar la vela más antigua
                old_kline = klines[i - self.vwap_period]
                old_typical_price = (float(old_kline.high) + float(old_kline.low) + float(old_kline.close)) / 3
                old_volume = float(old_kline.volume)
                
                cumulative_pv -= old_typical_price * old_volume
                cumulative_volume -= old_volume
            
            # Agregar vela actual
            cumulative_pv += typical_price * volume
            cumulative_volume += volume
            
            # Calcular VWAP
            if cumulative_volume > 0:
                vwap = cumulative_pv / cumulative_volume
            else:
                vwap = typical_price
                
            vwap_values.append(vwap)
        
        return {
            "vwap": vwap_values,
            "cumulative_volume": cumulative_volume,
            "cumulative_pv": cumulative_pv
        }

    def _calculate_vwap_bands(self, klines: List[KlineData], vwap_values: List[float]) -> Dict[str, List[float]]:
        """Calcula bandas de desviación del VWAP."""
        upper_bands = []
        lower_bands = []
        
        for i, (kline, vwap) in enumerate(zip(klines, vwap_values)):
            # Calcular desviación estándar del precio respecto al VWAP
            start_idx = max(0, i - self.vwap_period + 1)
            price_deviations = []
            
            for j in range(start_idx, i + 1):
                typical_price = (float(klines[j].high) + float(klines[j].low) + float(klines[j].close)) / 3
                deviation = (typical_price - vwap_values[j]) ** 2
                price_deviations.append(deviation)
            
            if len(price_deviations) > 1:
                variance = statistics.mean(price_deviations)
                std_dev = variance ** 0.5
            else:
                std_dev = 0.0
            
            upper_band = vwap + (std_dev * self.deviation_multiplier)
            lower_band = vwap - (std_dev * self.deviation_multiplier)
            
            upper_bands.append(upper_band)
            lower_bands.append(lower_band)
        
        return {
            "upper_band": upper_bands,
            "lower_band": lower_bands
        }

    def _detect_vwap_cross(self, klines: List[KlineData], vwap_values: List[float]) -> Optional[str]:
        """Detecta cruces del precio con el VWAP."""
        if len(klines) < 3:
            return None
            
        # Obtener precios de cierre recientes
        current_close = float(klines[-1].close)
        prev_close = float(klines[-2].close)
        
        current_vwap = vwap_values[-1]
        prev_vwap = vwap_values[-2]
        
        # Detectar cruce alcista
        if prev_close <= prev_vwap and current_close > current_vwap:
            return "bullish"
        
        # Detectar cruce bajista
        elif prev_close >= prev_vwap and current_close < current_vwap:
            return "bearish"
        
        return None

    def _analyze_volume_profile(self, klines: List[KlineData]) -> Dict[str, Any]:
        """Analiza el perfil de volumen actual vs histórico."""
        if len(klines) < self.volume_ma_period + 5:
            return {"sufficient_volume": False}
            
        # Calcular volumen promedio
        recent_volumes = [float(k.volume) for k in klines[-self.volume_ma_period:]]
        avg_volume = statistics.mean(recent_volumes)
        
        # Volumen actual
        current_volume = float(klines[-1].volume)
        
        # Múltiplo del volumen
        volume_multiple = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Analizar últimas 5 velas para confirmar sostenimiento
        recent_5_volumes = [float(k.volume) for k in klines[-5:]]
        avg_recent_5 = statistics.mean(recent_5_volumes)
        
        # Verificar volumen suficiente
        sufficient_volume = volume_multiple >= self.min_volume_threshold
        sustained_volume = avg_recent_5 >= (avg_volume * 1.2)  # 20% sobre promedio
        
        return {
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_multiple": volume_multiple,
            "sufficient_volume": sufficient_volume,
            "sustained_volume": sustained_volume,
            "volume_trend": "increasing" if recent_5_volumes[-1] > recent_5_volumes[0] else "decreasing"
        }

    def _calculate_volume_momentum(self, klines: List[KlineData]) -> Dict[str, Any]:
        """Calcula el momentum del volumen."""
        if len(klines) < 10:
            return {"momentum": "neutral"}
            
        # Volúmenes recientes vs anteriores
        recent_volumes = [float(k.volume) for k in klines[-5:]]
        previous_volumes = [float(k.volume) for k in klines[-10:-5]]
        
        avg_recent = statistics.mean(recent_volumes)
        avg_previous = statistics.mean(previous_volumes)
        
        momentum_ratio = avg_recent / avg_previous if avg_previous > 0 else 1.0
        
        # Determinar momentum
        if momentum_ratio >= 1.3:
            momentum = "strong_increasing"
        elif momentum_ratio >= 1.1:
            momentum = "increasing"
        elif momentum_ratio <= 0.7:
            momentum = "decreasing"
        else:
            momentum = "neutral"
        
        return {
            "momentum": momentum,
            "momentum_ratio": momentum_ratio,
            "recent_avg_volume": avg_recent,
            "previous_avg_volume": avg_previous
        }

    def _analyze_price_volume_relationship(self, klines: List[KlineData]) -> Dict[str, Any]:
        """Analiza la relación entre movimientos de precio y volumen."""
        if len(klines) < 5:
            return {"relationship": "insufficient_data"}
            
        price_changes = []
        volume_changes = []
        
        for i in range(1, min(6, len(klines))):  # Últimas 5 velas
            price_change = (float(klines[-i].close) - float(klines[-i-1].close)) / float(klines[-i-1].close)
            volume_change = (float(klines[-i].volume) - float(klines[-i-1].volume)) / float(klines[-i-1].volume)
            
            price_changes.append(price_change)
            volume_changes.append(volume_change)
        
        # Calcular correlación precio-volumen
        if len(price_changes) >= 3:
            correlation = self._calculate_correlation(price_changes, volume_changes)
        else:
            correlation = 0.0
        
        # Determinar relación
        if correlation > 0.6:
            relationship = "positive_correlation"  # Volumen confirma precio
        elif correlation < -0.6:
            relationship = "negative_correlation"  # Divergencia
        else:
            relationship = "neutral"
        
        return {
            "relationship": relationship,
            "correlation": correlation,
            "price_changes": price_changes,
            "volume_changes": volume_changes
        }

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calcula correlación simple entre dos listas."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(len(y)))
        
        if sum_sq_x == 0 or sum_sq_y == 0:
            return 0.0
            
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0

    def _identify_vwap_zones(self, vwap_values: List[float], current_price: float) -> Dict[str, Any]:
        """Identifica zonas de soporte/resistencia en el VWAP."""
        if len(vwap_values) < 20:
            return {"zones": []}
            
        recent_vwap = vwap_values[-20:]
        vwap_levels = []
        
        # Encontrar niveles donde el precio ha interactuado múltiples veces
        for vwap in recent_vwap:
            distance = abs(current_price - vwap) / current_price
            if distance <= 0.01:  # Dentro del 1%
                vwap_levels.append(vwap)
        
        # Determinar si VWAP actúa como soporte o resistencia
        current_vwap = vwap_values[-1]
        
        if current_price > current_vwap:
            zone_type = "support"
        else:
            zone_type = "resistance"
        
        return {
            "current_zone_type": zone_type,
            "key_level": current_vwap,
            "distance_percent": abs(current_price - current_vwap) / current_price * 100
        }

    def _evaluate_trading_conditions(
        self,
        vwap_cross: Optional[str],
        volume_analysis: Dict[str, Any],
        price_deviation: float,
        volume_momentum: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evalúa si las condiciones son favorables para trading."""
        conditions = {
            "valid_setup": False,
            "reasons": []
        }
        
        # Verificar cruce válido
        if vwap_cross in ["bullish", "bearish"]:
            conditions["reasons"].append("valid_vwap_cross")
        else:
            return conditions
        
        # Verificar volumen
        if volume_analysis.get("sufficient_volume", False):
            conditions["reasons"].append("sufficient_volume")
        else:
            return conditions
        
        # Verificar desviación mínima
        if abs(price_deviation) >= self.min_price_deviation:
            conditions["reasons"].append("sufficient_deviation")
        else:
            return conditions
        
        # Verificar momentum de volumen
        if volume_momentum.get("momentum") in ["increasing", "strong_increasing"]:
            conditions["reasons"].append("positive_volume_momentum")
        
        # Si llegamos aquí, es un setup válido
        conditions["valid_setup"] = True
        
        return conditions

    def _calculate_confidence(
        self,
        vwap_cross: Optional[str],
        volume_analysis: Dict[str, Any],
        abs_price_deviation: float,
        volume_momentum: Dict[str, Any],
        trading_conditions: Dict[str, Any]
    ) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: cruce válido
        if vwap_cross in ["bullish", "bearish"]:
            confidence += 0.25
        
        # Volumen suficiente
        if volume_analysis.get("sufficient_volume", False):
            confidence += 0.3
        
        # Volumen sostenido
        if volume_analysis.get("sustained_volume", False):
            confidence += 0.1
        
        # Desviación significativa
        deviation_score = min(abs_price_deviation / 0.01, 1.0)  # Máximo en 1%
        confidence += deviation_score * 0.15
        
        # Momentum de volumen
        momentum = volume_momentum.get("momentum", "neutral")
        if momentum == "strong_increasing":
            confidence += 0.15
        elif momentum == "increasing":
            confidence += 0.1
        
        # Setup válido completo
        if trading_conditions.get("valid_setup", False):
            confidence += 0.05
        
        return min(1.0, confidence)

    def _get_signal_strength(self, confidence: float, abs_deviation: float) -> SignalStrength:
        """Convierte confianza y desviación a fuerza de señal."""
        combined_score = confidence + (min(abs_deviation / 0.02, 1.0) * 0.2)  # Máximo en 2%
        
        if combined_score >= 0.85:
            return SignalStrength.STRONG
        elif combined_score >= 0.7:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength, volume_analysis: Dict[str, Any]) -> Decimal:
        """Calcula el tamaño de posición basado en la fuerza de la señal y volumen."""
        base_size = self.position_size_pct
        
        # Ajuste por fuerza de señal
        if signal_strength == SignalStrength.STRONG:
            strength_multiplier = 1.4
        elif signal_strength == SignalStrength.MEDIUM:
            strength_multiplier = 1.0
        else:
            strength_multiplier = 0.7
        
        # Ajuste por volumen excepcional
        volume_multiple = volume_analysis.get("volume_multiple", 1.0)
        if volume_multiple >= 3.0:
            volume_multiplier = 1.2
        elif volume_multiple >= 2.0:
            volume_multiplier = 1.1
        else:
            volume_multiplier = 1.0
        
        final_size = base_size * strength_multiplier * volume_multiplier
        return Decimal(str(final_size))

    def _calculate_stop_loss(self, entry_price: float, vwap: float, position_type: str) -> Decimal:
        """Calcula stop loss basado en VWAP y ATR estimado."""
        # Usar VWAP como referencia para stop loss
        vwap_distance = abs(entry_price - vwap)
        
        # Stop loss más allá del VWAP con margen adicional
        if position_type == "BUY":
            stop_price = vwap - (vwap_distance * 0.5)  # 50% más allá del VWAP
        else:  # SELL
            stop_price = vwap + (vwap_distance * 0.5)
        
        return Decimal(str(stop_price))

    def _calculate_take_profit(self, entry_price: float, stop_loss: Decimal, position_type: str) -> Decimal:
        """Calcula take profit usando ratio riesgo-recompensa."""
        risk = abs(entry_price - float(stop_loss))
        reward = risk * self.risk_reward_ratio
        
        if position_type == "BUY":
            tp_price = entry_price + reward
        else:  # SELL
            tp_price = entry_price - reward
        
        return Decimal(str(tp_price))
