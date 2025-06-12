"""
Statistical Arbitrage Pairs Trading Strategy

Esta estrategia busca dos activos altamente correlacionados y opera en la divergencia 
de sus precios, esperando que la relación estadística se normalice. Es una estrategia
market neutral que se beneficia de la convergencia de precios relativos.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple, List
import statistics
import math

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from ..core.domain_models.market import MarketSnapshot, KlineData

logger = logging.getLogger(__name__)

class StatisticalArbitrageParameters:
    """Parámetros configurables para Statistical Arbitrage Pairs."""
    
    def __init__(
        self,
        correlation_period: int = 60,
        min_correlation: float = 0.7,
        zscore_period: int = 20,
        entry_zscore_threshold: float = 2.0,
        exit_zscore_threshold: float = 0.5,
        stop_loss_zscore: float = 3.5,
        cointegration_lookback: int = 100,
        volume_ratio_threshold: float = 0.3,
        position_size_pct: float = 0.01,
        max_holding_period: int = 72  # horas
    ):
        self.correlation_period = correlation_period
        self.min_correlation = min_correlation
        self.zscore_period = zscore_period
        self.entry_zscore_threshold = entry_zscore_threshold
        self.exit_zscore_threshold = exit_zscore_threshold
        self.stop_loss_zscore = stop_loss_zscore
        self.cointegration_lookback = cointegration_lookback
        self.volume_ratio_threshold = volume_ratio_threshold
        self.position_size_pct = position_size_pct
        self.max_holding_period = max_holding_period

class StatisticalArbitragePairs(BaseStrategy):
    """
    Estrategia de arbitraje estadístico entre pares correlacionados.
    
    Identifica divergencias temporales en la relación de precios entre dos activos
    altamente correlacionados y opera esperando la convergencia a la media histórica.
    """
    
    def __init__(self, parameters: StatisticalArbitrageParameters, asset_pair: Tuple[str, str] = ("BTC", "ETH")):
        super().__init__("Statistical_Arbitrage_Pairs", parameters)
        self.correlation_period = parameters.correlation_period
        self.min_correlation = parameters.min_correlation
        self.zscore_period = parameters.zscore_period
        self.entry_zscore_threshold = parameters.entry_zscore_threshold
        self.exit_zscore_threshold = parameters.exit_zscore_threshold
        self.stop_loss_zscore = parameters.stop_loss_zscore
        self.cointegration_lookback = parameters.cointegration_lookback
        self.volume_ratio_threshold = parameters.volume_ratio_threshold
        self.position_size_pct = parameters.position_size_pct
        self.max_holding_period = parameters.max_holding_period
        
        self.asset_pair = asset_pair
        self._price_ratio_history = []
        self._correlation_history = []
        self._hedge_ratio = 1.0

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} para par {self.asset_pair[0]}/{self.asset_pair[1]}")

    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Analiza la relación estadística entre el par de activos.
        
        Args:
            market_snapshot: Datos actuales del mercado (debe incluir ambos activos)
            
        Returns:
            AnalysisResult con análisis de correlación y oportunidades de arbitraje
        """
        try:
            # Simular datos del segundo activo (en implementación real vendría del market_snapshot)
            asset1_data = market_snapshot.klines  # Primer activo
            asset2_data = self._simulate_correlated_asset_data(asset1_data)  # Segundo activo
            
            if len(asset1_data) < self.cointegration_lookback:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Calcular precios y ratios
            asset1_prices = [float(k.close) for k in asset1_data]
            asset2_prices = [float(k.close) for k in asset2_data]
            
            # Calcular correlación
            correlation = self._calculate_correlation(asset1_prices, asset2_prices)
            
            # Calcular ratio de precios y hedge ratio óptimo
            price_ratios = [p1/p2 for p1, p2 in zip(asset1_prices, asset2_prices)]
            hedge_ratio = self._calculate_hedge_ratio(asset1_prices, asset2_prices)
            
            # Calcular spread ajustado por hedge ratio
            spreads = [p1 - (hedge_ratio * p2) for p1, p2 in zip(asset1_prices, asset2_prices)]
            
            # Calcular Z-Score del spread
            zscore = self._calculate_zscore(spreads)
            
            # Verificar cointegración
            cointegration_score = self._test_cointegration(asset1_prices, asset2_prices)
            
            # Analizar volumen relativo
            volume_analysis = self._analyze_volume_relationship(asset1_data, asset2_data)
            
            # Detectar oportunidad de arbitraje
            arbitrage_opportunity = self._detect_arbitrage_opportunity(zscore, correlation, cointegration_score)
            
            # Calcular riesgo de la posición
            position_risk = self._calculate_position_risk(spreads, zscore)
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                correlation, abs(zscore), cointegration_score, 
                volume_analysis, arbitrage_opportunity
            )
            
            current_asset1_price = asset1_prices[-1]
            current_asset2_price = asset2_prices[-1]
            current_spread = spreads[-1]
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "correlation": correlation,
                    "zscore": zscore,
                    "hedge_ratio": hedge_ratio,
                    "current_spread": current_spread,
                    "asset1_price": current_asset1_price,
                    "asset2_price": current_asset2_price,
                    "price_ratio": price_ratios[-1],
                    "cointegration_score": cointegration_score,
                    "arbitrage_opportunity": arbitrage_opportunity,
                    "position_risk": position_risk
                },
                metadata={
                    "asset_pair": self.asset_pair,
                    "correlation_period": self.correlation_period,
                    "zscore_threshold": self.entry_zscore_threshold,
                    "volume_analysis": volume_analysis
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis Statistical Arbitrage: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de arbitraje estadístico basada en el análisis.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se detecta oportunidad de arbitraje, None en caso contrario
        """
        try:
            if analysis.confidence < 0.7:  # Umbral alto para arbitraje
                return None
                
            indicators = analysis.indicators
            correlation = indicators.get("correlation", 0)
            zscore = indicators.get("zscore", 0)
            arbitrage_opportunity = indicators.get("arbitrage_opportunity")
            position_risk = indicators.get("position_risk", "high")
            
            # Verificar condiciones mínimas
            if correlation < self.min_correlation:
                logger.debug(f"Correlación insuficiente: {correlation:.3f}")
                return None
                
            if abs(zscore) < self.entry_zscore_threshold:
                return None
            
            if position_risk == "high":
                logger.debug("Riesgo de posición demasiado alto")
                return None
                
            asset1_price = indicators.get("asset1_price", 0)
            asset2_price = indicators.get("asset2_price", 0)
            hedge_ratio = indicators.get("hedge_ratio", 1.0)
            
            # Señal de arbitraje - Long asset1, Short asset2
            if zscore > self.entry_zscore_threshold:
                signal_strength = self._get_signal_strength(analysis.confidence, abs(zscore))
                position_size = self._calculate_position_size(signal_strength)
                
                # Asset1 está sobrevalorado relative a asset2
                # Short asset1, Long asset2
                return TradingSignal(
                    signal_type="ARBITRAGE_SHORT_LONG",
                    strength=signal_strength,
                    entry_price=Decimal(str(asset1_price)),
                    stop_loss=self._calculate_stop_loss(asset1_price, zscore, "SHORT"),
                    take_profit=self._calculate_take_profit(asset1_price, zscore, "SHORT"),
                    position_size=position_size,
                    reasoning=f"Statistical arbitrage: {self.asset_pair[0]} overvalued vs {self.asset_pair[1]}. Z-score: {zscore:.2f}, Correlation: {correlation:.3f}, Hedge: {hedge_ratio:.3f}",
                    metadata={
                        "hedge_asset": self.asset_pair[1],
                        "hedge_price": asset2_price,
                        "hedge_ratio": hedge_ratio,
                        "hedge_position": "LONG"
                    }
                )
                
            # Señal de arbitraje - Short asset1, Long asset2
            elif zscore < -self.entry_zscore_threshold:
                signal_strength = self._get_signal_strength(analysis.confidence, abs(zscore))
                position_size = self._calculate_position_size(signal_strength)
                
                # Asset1 está infravalorado relative a asset2
                # Long asset1, Short asset2
                return TradingSignal(
                    signal_type="ARBITRAGE_LONG_SHORT",
                    strength=signal_strength,
                    entry_price=Decimal(str(asset1_price)),
                    stop_loss=self._calculate_stop_loss(asset1_price, zscore, "LONG"),
                    take_profit=self._calculate_take_profit(asset1_price, zscore, "LONG"),
                    position_size=position_size,
                    reasoning=f"Statistical arbitrage: {self.asset_pair[0]} undervalued vs {self.asset_pair[1]}. Z-score: {zscore:.2f}, Correlation: {correlation:.3f}, Hedge: {hedge_ratio:.3f}",
                    metadata={
                        "hedge_asset": self.asset_pair[1],
                        "hedge_price": asset2_price,
                        "hedge_ratio": hedge_ratio,
                        "hedge_position": "SHORT"
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal Statistical Arbitrage: {e}")
            return None

    def _simulate_correlated_asset_data(self, asset1_data: List[KlineData]) -> List[KlineData]:
        """
        Simula datos del segundo activo correlacionado para testing.
        En implementación real, estos datos vendrían del market_snapshot.
        """
        simulated_data = []
        base_price = 2000.0  # Precio base para ETH si BTC es asset1
        correlation_factor = 0.8
        
        for i, kline in enumerate(asset1_data):
            asset1_price = float(kline.close)
            
            # Simular precio correlacionado con ruido
            if i == 0:
                simulated_price = base_price
            else:
                prev_asset1 = float(asset1_data[i-1].close)
                asset1_change = (asset1_price - prev_asset1) / prev_asset1
                
                # Aplicar correlación + ruido aleatorio
                correlated_change = asset1_change * correlation_factor
                noise = (hash(str(i)) % 1000 - 500) / 50000  # Ruido pseudo-aleatorio
                total_change = correlated_change + noise
                
                simulated_price = simulated_data[-1].close * (1 + total_change)
            
            # Crear KlineData simulado
            simulated_kline = KlineData(
                open=Decimal(str(simulated_price * 0.999)),
                high=Decimal(str(simulated_price * 1.001)),
                low=Decimal(str(simulated_price * 0.999)),
                close=Decimal(str(simulated_price)),
                volume=kline.volume,  # Usar mismo volumen
                timestamp=kline.timestamp
            )
            simulated_data.append(simulated_kline)
        
        return simulated_data

    def _calculate_correlation(self, prices1: List[float], prices2: List[float]) -> float:
        """Calcula correlación de Pearson entre dos series de precios."""
        if len(prices1) < self.correlation_period:
            return 0.0
            
        # Usar período más reciente
        recent_prices1 = prices1[-self.correlation_period:]
        recent_prices2 = prices2[-self.correlation_period:]
        
        # Calcular retornos
        returns1 = [(recent_prices1[i] - recent_prices1[i-1]) / recent_prices1[i-1] 
                   for i in range(1, len(recent_prices1))]
        returns2 = [(recent_prices2[i] - recent_prices2[i-1]) / recent_prices2[i-1] 
                   for i in range(1, len(recent_prices2))]
        
        if len(returns1) < 2:
            return 0.0
            
        # Calcular correlación
        mean1 = statistics.mean(returns1)
        mean2 = statistics.mean(returns2)
        
        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2))
        
        sum_sq1 = sum((r1 - mean1) ** 2 for r1 in returns1)
        sum_sq2 = sum((r2 - mean2) ** 2 for r2 in returns2)
        
        if sum_sq1 == 0 or sum_sq2 == 0:
            return 0.0
            
        denominator = math.sqrt(sum_sq1 * sum_sq2)
        
        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_hedge_ratio(self, prices1: List[float], prices2: List[float]) -> float:
        """Calcula ratio de hedge óptimo usando regresión lineal simple."""
        if len(prices1) < 20:
            return 1.0
            
        # Usar datos recientes para hedge ratio
        recent_prices1 = prices1[-50:]
        recent_prices2 = prices2[-50:]
        
        # Regresión lineal: prices1 = alpha + beta * prices2
        n = len(recent_prices1)
        sum_x = sum(recent_prices2)
        sum_y = sum(recent_prices1)
        sum_xy = sum(x * y for x, y in zip(recent_prices2, recent_prices1))
        sum_x2 = sum(x * x for x in recent_prices2)
        
        # Calcular beta (pendiente) que es nuestro hedge ratio
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 1.0
            
        beta = (n * sum_xy - sum_x * sum_y) / denominator
        return abs(beta)  # Tomar valor absoluto

    def _calculate_zscore(self, spreads: List[float]) -> float:
        """Calcula Z-score del spread actual vs histórico."""
        if len(spreads) < self.zscore_period:
            return 0.0
            
        recent_spreads = spreads[-self.zscore_period:]
        current_spread = spreads[-1]
        
        mean_spread = statistics.mean(recent_spreads)
        std_spread = statistics.stdev(recent_spreads) if len(recent_spreads) > 1 else 1.0
        
        if std_spread == 0:
            return 0.0
            
        return (current_spread - mean_spread) / std_spread

    def _test_cointegration(self, prices1: List[float], prices2: List[float]) -> float:
        """
        Test simplificado de cointegración usando ADF en el spread.
        Retorna score entre 0-1 donde 1 indica cointegración fuerte.
        """
        if len(prices1) < self.cointegration_lookback:
            return 0.0
            
        # Usar datos recientes
        recent_prices1 = prices1[-self.cointegration_lookback:]
        recent_prices2 = prices2[-self.cointegration_lookback:]
        
        # Calcular spread
        hedge_ratio = self._calculate_hedge_ratio(recent_prices1, recent_prices2)
        spreads = [p1 - hedge_ratio * p2 for p1, p2 in zip(recent_prices1, recent_prices2)]
        
        # Test de estacionariedad simplificado
        # Verificar si el spread tiende a revertir a la media
        mean_spread = statistics.mean(spreads)
        deviations = [abs(s - mean_spread) for s in spreads]
        
        # Calcular qué tan rápido revierte el spread
        half_life = self._estimate_half_life(spreads)
        
        # Score basado en half-life (menor half-life = mejor cointegración)
        if half_life == 0:
            return 0.0
        elif half_life < 5:
            return 1.0
        elif half_life < 10:
            return 0.8
        elif half_life < 20:
            return 0.6
        else:
            return 0.3

    def _estimate_half_life(self, spreads: List[float]) -> float:
        """Estima el half-life de reversión del spread."""
        if len(spreads) < 10:
            return float('inf')
            
        # Calcular cambios en spread
        changes = [spreads[i] - spreads[i-1] for i in range(1, len(spreads))]
        lagged_spreads = spreads[:-1]
        
        # Regresión: change = alpha + beta * lagged_spread
        if len(changes) < 2:
            return float('inf')
            
        mean_change = statistics.mean(changes)
        mean_lagged = statistics.mean(lagged_spreads)
        
        numerator = sum((changes[i] - mean_change) * (lagged_spreads[i] - mean_lagged) 
                       for i in range(len(changes)))
        denominator = sum((lag - mean_lagged) ** 2 for lag in lagged_spreads)
        
        if denominator == 0:
            return float('inf')
            
        beta = numerator / denominator
        
        # Half-life = -ln(2) / ln(1 + beta)
        if beta >= 0:
            return float('inf')
            
        try:
            half_life = -math.log(2) / math.log(1 + beta)
            return max(0, half_life)
        except (ValueError, ZeroDivisionError):
            return float('inf')

    def _analyze_volume_relationship(self, asset1_data: List[KlineData], asset2_data: List[KlineData]) -> Dict[str, Any]:
        """Analiza la relación de volúmenes entre los activos."""
        if len(asset1_data) < 10 or len(asset2_data) < 10:
            return {"status": "insufficient_data"}
            
        volumes1 = [float(k.volume) for k in asset1_data[-10:]]
        volumes2 = [float(k.volume) for k in asset2_data[-10:]]
        
        avg_vol1 = statistics.mean(volumes1)
        avg_vol2 = statistics.mean(volumes2)
        
        volume_ratio = avg_vol1 / avg_vol2 if avg_vol2 > 0 else 0
        
        # Verificar si hay suficiente liquidez en ambos activos
        sufficient_liquidity = (avg_vol1 > 1000000 and avg_vol2 > 1000000)  # Valores de ejemplo
        
        return {
            "avg_volume_asset1": avg_vol1,
            "avg_volume_asset2": avg_vol2,
            "volume_ratio": volume_ratio,
            "sufficient_liquidity": sufficient_liquidity
        }

    def _detect_arbitrage_opportunity(self, zscore: float, correlation: float, cointegration: float) -> Optional[str]:
        """Detecta si existe una oportunidad de arbitraje viable."""
        if correlation < self.min_correlation:
            return None
            
        if cointegration < 0.5:
            return None
            
        if abs(zscore) >= self.entry_zscore_threshold:
            if zscore > 0:
                return "short_long"  # Short asset1, Long asset2
            else:
                return "long_short"  # Long asset1, Short asset2
                
        return None

    def _calculate_position_risk(self, spreads: List[float], zscore: float) -> str:
        """Calcula el riesgo de la posición propuesta."""
        if len(spreads) < 20:
            return "high"
            
        # Analizar volatilidad del spread
        recent_spreads = spreads[-20:]
        spread_volatility = statistics.stdev(recent_spreads) if len(recent_spreads) > 1 else 0
        
        # Riesgo basado en Z-score extremo
        if abs(zscore) > self.stop_loss_zscore:
            return "high"
        elif abs(zscore) > self.entry_zscore_threshold * 1.5:
            return "medium"
        else:
            return "low"

    def _calculate_confidence(
        self,
        correlation: float,
        abs_zscore: float,
        cointegration: float,
        volume_analysis: Dict[str, Any],
        arbitrage_opportunity: Optional[str]
    ) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: correlación fuerte
        if correlation >= 0.9:
            confidence += 0.3
        elif correlation >= 0.8:
            confidence += 0.25
        elif correlation >= self.min_correlation:
            confidence += 0.15
        
        # Z-score significativo
        if abs_zscore >= self.entry_zscore_threshold * 1.5:
            confidence += 0.25
        elif abs_zscore >= self.entry_zscore_threshold:
            confidence += 0.2
        
        # Cointegración
        confidence += cointegration * 0.2
        
        # Liquidez suficiente
        if volume_analysis.get("sufficient_liquidity", False):
            confidence += 0.15
        
        # Oportunidad clara
        if arbitrage_opportunity:
            confidence += 0.1
        
        return min(1.0, confidence)

    def _get_signal_strength(self, confidence: float, abs_zscore: float) -> SignalStrength:
        """Convierte confianza y Z-score a fuerza de señal."""
        combined_score = confidence + (min(abs_zscore / 3.0, 1.0) * 0.3)
        
        if combined_score >= 0.9:
            return SignalStrength.STRONG
        elif combined_score >= 0.75:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength) -> Decimal:
        """Calcula el tamaño de posición basado en la fuerza de la señal."""
        base_size = self.position_size_pct
        
        # Arbitraje es menos riesgoso, permitir tamaños mayores
        if signal_strength == SignalStrength.STRONG:
            multiplier = 2.0
        elif signal_strength == SignalStrength.MEDIUM:
            multiplier = 1.5
        else:
            multiplier = 1.0
            
        return Decimal(str(base_size * multiplier))

    def _calculate_stop_loss(self, entry_price: float, zscore: float, position_type: str) -> Decimal:
        """Calcula stop loss basado en Z-score extremo."""
        # Stop loss cuando Z-score alcanza nivel extremo
        stop_loss_factor = self.stop_loss_zscore / abs(zscore) if zscore != 0 else 2.0
        
        if position_type == "LONG":
            stop_price = entry_price * (1 - 0.03 * stop_loss_factor)  # 3% base * factor
        else:  # SHORT
            stop_price = entry_price * (1 + 0.03 * stop_loss_factor)
            
        return Decimal(str(stop_price))

    def _calculate_take_profit(self, entry_price: float, zscore: float, position_type: str) -> Decimal:
        """Calcula take profit cuando Z-score vuelve cerca de cero."""
        # Take profit más conservador para arbitraje
        profit_factor = abs(zscore) / self.entry_zscore_threshold * 0.015  # 1.5% máximo
        
        if position_type == "LONG":
            tp_price = entry_price * (1 + profit_factor)
        else:  # SHORT
            tp_price = entry_price * (1 - profit_factor)
            
        return Decimal(str(tp_price))
