"""
On-Chain Metrics Divergence Strategy

Esta estrategia usa herramientas MCP para encontrar divergencias entre el precio y métricas 
on-chain clave como flujos de exchange, grandes transacciones, y actividad de direcciones.
Es específica para criptomonedas y utiliza datos fundamentales blockchain.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List
import statistics
from datetime import datetime, timedelta, timezone # ADDED timezone

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from src.ultibot_backend.core.domain_models.market import MarketData, KlineData

logger = logging.getLogger(__name__)

class OnChainParameters:
    """Parámetros configurables para On-Chain Metrics Divergence."""
    
    def __init__(
        self,
        divergence_threshold: float = 0.6,  # 60% mínimo de divergencia
        metrics_lookback_days: int = 7,  # Análisis de 7 días
        whale_transaction_threshold: float = 1000000,  # $1M+ para considerar whale
        exchange_flow_threshold: float = 0.15,  # 15% cambio en flujos
        address_activity_weight: float = 0.3,
        transaction_volume_weight: float = 0.35,
        exchange_flows_weight: float = 0.35,
        min_network_activity: float = 10000,  # Actividad mínima de red
        position_size_pct: float = 0.03,
        correlation_period: int = 14  # Días para correlación precio-métricas
    ):
        self.divergence_threshold = divergence_threshold
        self.metrics_lookback_days = metrics_lookback_days
        self.whale_transaction_threshold = whale_transaction_threshold
        self.exchange_flow_threshold = exchange_flow_threshold
        self.address_activity_weight = address_activity_weight
        self.transaction_volume_weight = transaction_volume_weight
        self.exchange_flows_weight = exchange_flows_weight
        self.min_network_activity = min_network_activity
        self.position_size_pct = position_size_pct
        self.correlation_period = correlation_period

class OnChainMetricsDivergence(BaseStrategy):
    """
    Estrategia basada en divergencias de métricas on-chain.
    
    Identifica cuando el precio se mueve en dirección opuesta a los fundamentales
    de blockchain, indicando posibles correcciones o confirmaciones de tendencia.
    """
    
    def __init__(self, parameters: OnChainParameters):
        super().__init__("OnChain_Metrics_Divergence", parameters)
        self.divergence_threshold = parameters.divergence_threshold
        self.metrics_lookback_days = parameters.metrics_lookback_days
        self.whale_transaction_threshold = parameters.whale_transaction_threshold
        self.exchange_flow_threshold = parameters.exchange_flow_threshold
        self.address_activity_weight = parameters.address_activity_weight
        self.transaction_volume_weight = parameters.transaction_volume_weight
        self.exchange_flows_weight = parameters.exchange_flows_weight
        self.min_network_activity = parameters.min_network_activity
        self.position_size_pct = parameters.position_size_pct
        self.correlation_period = parameters.correlation_period
        
        self._onchain_history = []
        self._metrics_cache = {}

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con divergence threshold={self.divergence_threshold}")

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza métricas on-chain y detecta divergencias con el precio.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis on-chain y oportunidades de trading
        """
        try:
            if len(market_snapshot.klines) < self.correlation_period:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Obtener symbol del asset (asumir BTC por defecto)
            symbol = getattr(market_snapshot, 'symbol', 'BTC')
            
            # Solo procesar criptomonedas principales
            if symbol not in ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'MATIC', 'AVAX']:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": f"On-chain analysis not supported for {symbol}"}
                )

            # Obtener métricas on-chain via MCP tools
            # En implementación real: await self._tools.execute_tool("get_onchain_data", {...})
            onchain_data = await self._get_onchain_metrics(symbol)
            
            # Analizar actividad de direcciones
            address_activity = self._analyze_address_activity(onchain_data)
            
            # Analizar transacciones de ballenas
            whale_analysis = self._analyze_whale_transactions(onchain_data)
            
            # Analizar flujos de exchanges
            exchange_flows = self._analyze_exchange_flows(onchain_data)
            
            # Calcular score compuesto de métricas on-chain
            composite_onchain_score = self._calculate_composite_onchain_score(
                address_activity, whale_analysis, exchange_flows
            )
            
            # Detectar divergencias precio vs on-chain
            divergence_analysis = self._detect_price_onchain_divergence(
                market_snapshot.klines, composite_onchain_score
            )
            
            # Analizar network health
            network_health = self._analyze_network_health(onchain_data)
            
            # Detectar patrones de acumulación/distribución
            accumulation_distribution = self._detect_accumulation_distribution_patterns(
                whale_analysis, exchange_flows, address_activity
            )
            
            # Evaluar fortaleza de la tendencia on-chain
            onchain_trend_strength = self._evaluate_onchain_trend_strength(
                composite_onchain_score, divergence_analysis
            )
            
            # Evaluar oportunidad de trading
            trading_opportunity = self._evaluate_onchain_trading_opportunity(
                divergence_analysis, network_health, accumulation_distribution
            )
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                divergence_analysis, network_health, onchain_trend_strength,
                accumulation_distribution, trading_opportunity
            )
            
            current_price = float(market_snapshot.klines[-1].close)
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "current_price": current_price,
                    "onchain_data": onchain_data,
                    "address_activity": address_activity,
                    "whale_analysis": whale_analysis,
                    "exchange_flows": exchange_flows,
                    "composite_onchain_score": composite_onchain_score,
                    "divergence_analysis": divergence_analysis,
                    "network_health": network_health,
                    "accumulation_distribution": accumulation_distribution,
                    "onchain_trend_strength": onchain_trend_strength,
                    "trading_opportunity": trading_opportunity
                },
                metadata={
                    "symbol": symbol,
                    "divergence_threshold": self.divergence_threshold,
                    "metrics_lookback_days": self.metrics_lookback_days
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis OnChain Metrics: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de trading basada en divergencias on-chain.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se detecta divergencia significativa, None en caso contrario
        """
        try:
            if analysis.confidence < 0.65:  # Umbral para on-chain analysis
                return None
                
            indicators = analysis.indicators
            trading_opportunity = indicators.get("trading_opportunity", {})
            divergence_analysis = indicators.get("divergence_analysis", {})
            accumulation_distribution = indicators.get("accumulation_distribution", {})
            
            if not trading_opportunity.get("valid_opportunity", False):
                return None
                
            current_price = indicators.get("current_price", 0)
            divergence_type = divergence_analysis.get("divergence_type")
            divergence_strength = divergence_analysis.get("divergence_strength", 0)
            
            # Señal de compra (divergencia alcista: precio baja, métricas suben)
            if (divergence_type == "bullish_divergence" and 
                divergence_strength >= self.divergence_threshold):
                
                signal_strength = self._get_signal_strength(analysis.confidence, divergence_strength)
                position_size = self._calculate_position_size(signal_strength, accumulation_distribution)
                
                # Calcular targets basados en fuerza de divergencia
                stop_loss = self._calculate_onchain_stop_loss(current_price, divergence_analysis, "BUY")
                take_profit = self._calculate_onchain_take_profit(current_price, divergence_analysis, "BUY")
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Bullish on-chain divergence detected. Strength: {divergence_strength:.1%}, Pattern: {accumulation_distribution.get('pattern', 'unknown')}, Network health: {indicators.get('network_health', {}).get('health_score', 0):.2f}",
                    metadata={
                        "strategy_type": "onchain_fundamental",
                        "divergence_strength": divergence_strength,
                        "onchain_score": indicators.get("composite_onchain_score", {}).get("current_score", 0),
                        "accumulation_pattern": accumulation_distribution.get("pattern")
                    }
                )
                
            # Señal de venta (divergencia bajista: precio sube, métricas bajan)
            elif (divergence_type == "bearish_divergence" and 
                  divergence_strength >= self.divergence_threshold):
                
                signal_strength = self._get_signal_strength(analysis.confidence, divergence_strength)
                position_size = self._calculate_position_size(signal_strength, accumulation_distribution)
                
                # Calcular targets basados en fuerza de divergencia
                stop_loss = self._calculate_onchain_stop_loss(current_price, divergence_analysis, "SELL")
                take_profit = self._calculate_onchain_take_profit(current_price, divergence_analysis, "SELL")
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Bearish on-chain divergence detected. Strength: {divergence_strength:.1%}, Pattern: {accumulation_distribution.get('pattern', 'unknown')}, Network health: {indicators.get('network_health', {}).get('health_score', 0):.2f}",
                    metadata={
                        "strategy_type": "onchain_fundamental",
                        "divergence_strength": divergence_strength,
                        "onchain_score": indicators.get("composite_onchain_score", {}).get("current_score", 0),
                        "accumulation_pattern": accumulation_distribution.get("pattern")
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal OnChain Metrics: {e}")
            return None

    async def _get_onchain_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene métricas on-chain usando herramientas MCP.
        En implementación real, esto haría llamadas a APIs como Glassnode, etc.
        """
        current_time = datetime.now(timezone.utc) # MODIFIED
        
        # Simular métricas on-chain para testing
        base_seed = hash(symbol + str(current_time.date()))
        
        # Simular datos históricos de los últimos días
        daily_metrics = []
        for days_ago in range(self.metrics_lookback_days):
            date = current_time - timedelta(days=days_ago)
            day_seed = hash(symbol + str(date.date()))
            
            # Actividad de direcciones (direcciones activas diarias)
            base_active_addresses = 100000 if symbol == 'BTC' else 50000
            active_addresses = base_active_addresses + (day_seed % 20000 - 10000)
            
            # Volumen de transacciones on-chain (USD)
            base_tx_volume = 50000000000 if symbol == 'BTC' else 10000000000  # 50B para BTC
            tx_volume = base_tx_volume + (day_seed % 10000000000 - 5000000000)
            
            # Flujos netos de exchanges (positivo = inflow, negativo = outflow)
            exchange_netflow = (day_seed % 2000000000 - 1000000000)  # -1B a +1B
            
            # Transacciones de ballenas (>$1M)
            whale_tx_count = max(0, 50 + (day_seed % 100 - 50))
            whale_tx_volume = whale_tx_count * (1000000 + (day_seed % 5000000))
            
            # Métricas de network
            hash_rate = 200000000 + (day_seed % 50000000)  # Para BTC
            network_difficulty = 30000000000000 + (day_seed % 5000000000000)
            
            daily_metrics.append({
                "date": date,
                "active_addresses": active_addresses,
                "transaction_volume": tx_volume,
                "exchange_netflow": exchange_netflow,
                "whale_transactions": {
                    "count": whale_tx_count,
                    "volume": whale_tx_volume
                },
                "network_metrics": {
                    "hash_rate": hash_rate,
                    "difficulty": network_difficulty
                }
            })
        
        # Invertir para tener cronológico (más antiguo primero)
        daily_metrics.reverse()
        
        return {
            "symbol": symbol,
            "daily_metrics": daily_metrics,
            "last_updated": current_time,
            "data_source": "simulated_onchain_provider"
        }

    def _analyze_address_activity(self, onchain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la actividad de direcciones en la red."""
        daily_metrics = onchain_data.get("daily_metrics", [])
        
        if len(daily_metrics) < 3:
            return {"trend": "insufficient_data"}
        
        # Extraer datos de direcciones activas
        active_addresses = [d["active_addresses"] for d in daily_metrics]
        
        # Calcular tendencia
        recent_avg = statistics.mean(active_addresses[-3:])  # Últimos 3 días
        historical_avg = statistics.mean(active_addresses[:-3])  # Días anteriores
        
        trend_change = (recent_avg - historical_avg) / historical_avg if historical_avg > 0 else 0
        
        # Categorizar tendencia
        if trend_change > 0.1:  # 10% aumento
            trend = "increasing_strongly"
        elif trend_change > 0.05:  # 5% aumento
            trend = "increasing"
        elif trend_change < -0.1:  # 10% disminución
            trend = "decreasing_strongly"
        elif trend_change < -0.05:  # 5% disminución
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calcular volatilidad de actividad
        address_volatility = statistics.stdev(active_addresses) if len(active_addresses) > 1 else 0
        
        return {
            "trend": trend,
            "trend_change_pct": trend_change,
            "current_active_addresses": active_addresses[-1],
            "recent_average": recent_avg,
            "historical_average": historical_avg,
            "volatility": address_volatility,
            "activity_score": min(recent_avg / 100000, 2.0)  # Normalizar
        }

    def _analyze_whale_transactions(self, onchain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza las transacciones de ballenas."""
        daily_metrics = onchain_data.get("daily_metrics", [])
        
        if len(daily_metrics) < 3:
            return {"activity": "insufficient_data"}
        
        # Extraer datos de ballenas
        whale_counts = [d["whale_transactions"]["count"] for d in daily_metrics]
        whale_volumes = [d["whale_transactions"]["volume"] for d in daily_metrics]
        
        # Analizar actividad reciente vs histórica
        recent_count_avg = statistics.mean(whale_counts[-3:])
        historical_count_avg = statistics.mean(whale_counts[:-3])
        
        recent_volume_avg = statistics.mean(whale_volumes[-3:])
        historical_volume_avg = statistics.mean(whale_volumes[:-3])
        
        # Calcular cambios
        count_change = (recent_count_avg - historical_count_avg) / historical_count_avg if historical_count_avg > 0 else 0
        volume_change = (recent_volume_avg - historical_volume_avg) / historical_volume_avg if historical_volume_avg > 0 else 0
        
        # Determinar actividad de ballenas
        if count_change > 0.2 and volume_change > 0.2:  # 20% aumento en ambos
            activity = "very_active"
        elif count_change > 0.1 or volume_change > 0.1:  # 10% aumento en alguno
            activity = "active"
        elif count_change < -0.2 and volume_change < -0.2:  # 20% disminución
            activity = "very_quiet"
        elif count_change < -0.1 or volume_change < -0.1:  # 10% disminución
            activity = "quiet"
        else:
            activity = "normal"
        
        return {
            "activity": activity,
            "count_change_pct": count_change,
            "volume_change_pct": volume_change,
            "current_whale_count": whale_counts[-1],
            "current_whale_volume": whale_volumes[-1],
            "recent_count_avg": recent_count_avg,
            "recent_volume_avg": recent_volume_avg,
            "whale_dominance": recent_volume_avg / sum(whale_volumes) if sum(whale_volumes) > 0 else 0
        }

    def _analyze_exchange_flows(self, onchain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza los flujos hacia/desde exchanges."""
        daily_metrics = onchain_data.get("daily_metrics", [])
        
        if len(daily_metrics) < 3:
            return {"flow_type": "insufficient_data"}
        
        # Extraer flujos netos (positivo = inflow, negativo = outflow)
        netflows = [d["exchange_netflow"] for d in daily_metrics]
        
        # Analizar flujo reciente
        recent_netflow = statistics.mean(netflows[-3:])
        total_netflow = sum(netflows)
        
        # Determinar tipo de flujo
        if recent_netflow > 100000000:  # $100M+ inflow
            flow_type = "strong_inflow"
            sentiment = "bearish"  # Inflow típicamente bajista
        elif recent_netflow > 50000000:  # $50M+ inflow
            flow_type = "moderate_inflow"
            sentiment = "slightly_bearish"
        elif recent_netflow < -100000000:  # $100M+ outflow
            flow_type = "strong_outflow"
            sentiment = "bullish"  # Outflow típicamente alcista
        elif recent_netflow < -50000000:  # $50M+ outflow
            flow_type = "moderate_outflow"
            sentiment = "slightly_bullish"
        else:
            flow_type = "neutral"
            sentiment = "neutral"
        
        # Calcular volatilidad de flujos
        flow_volatility = statistics.stdev(netflows) if len(netflows) > 1 else 0
        
        # Detectar cambios súbitos
        flow_changes = [(netflows[i] - netflows[i-1]) / abs(netflows[i-1]) if netflows[i-1] != 0 else 0 
                       for i in range(1, len(netflows))]
        
        sudden_changes = [abs(change) > 0.5 for change in flow_changes]  # 50%+ cambio
        has_sudden_change = any(sudden_changes)
        
        return {
            "flow_type": flow_type,
            "sentiment": sentiment,
            "recent_netflow": recent_netflow,
            "total_netflow": total_netflow,
            "flow_volatility": flow_volatility,
            "has_sudden_change": has_sudden_change,
            "flow_strength": min(abs(recent_netflow) / 1000000000, 2.0)  # Normalizar a 2.0
        }

    def _calculate_composite_onchain_score(self, address_activity: Dict[str, Any], whale_analysis: Dict[str, Any], exchange_flows: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula un score compuesto de todas las métricas on-chain."""
        # Convertir análisis a scores numéricos
        activity_score = address_activity.get("activity_score", 1.0)
        
        # Score de ballenas
        whale_activity = whale_analysis.get("activity", "normal")
        whale_score_map = {
            "very_active": 2.0,
            "active": 1.5,
            "normal": 1.0,
            "quiet": 0.5,
            "very_quiet": 0.2
        }
        whale_score = whale_score_map.get(whale_activity, 1.0)
        
        # Score de flujos de exchange
        flow_strength = exchange_flows.get("flow_strength", 1.0)
        flow_sentiment = exchange_flows.get("sentiment", "neutral")
        
        # Ajustar score según sentiment de flujos
        if flow_sentiment in ["bullish", "slightly_bullish"]:
            flow_score = flow_strength
        elif flow_sentiment in ["bearish", "slightly_bearish"]:
            flow_score = 2.0 - flow_strength  # Invertir
        else:
            flow_score = 1.0
        
        # Calcular score compuesto
        composite_score = (
            activity_score * self.address_activity_weight +
            whale_score * self.transaction_volume_weight +
            flow_score * self.exchange_flows_weight
        )
        
        # Normalizar a 0-1
        normalized_score = composite_score / 2.0
        
        # Categorizar score
        if normalized_score >= 0.8:
            category = "very_bullish"
        elif normalized_score >= 0.6:
            category = "bullish"
        elif normalized_score <= 0.2:
            category = "very_bearish"
        elif normalized_score <= 0.4:
            category = "bearish"
        else:
            category = "neutral"
        
        return {
            "current_score": normalized_score,
            "category": category,
            "activity_component": activity_score,
            "whale_component": whale_score,
            "flow_component": flow_score,
            "raw_score": composite_score
        }

    def _detect_price_onchain_divergence(self, klines: List[KlineData], onchain_score: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta divergencias entre precio y métricas on-chain."""
        if len(klines) < self.correlation_period:
            return {"divergence_type": "insufficient_data"}
        
        # Calcular cambio de precio
        prices = [float(k.close) for k in klines[-self.correlation_period:]]
        price_change = (prices[-1] - prices[0]) / prices[0]
        
        # Obtener tendencia on-chain
        current_onchain_score = onchain_score.get("current_score", 0.5)
        
        # Simular score histórico (en implementación real vendría de datos históricos)
        historical_onchain_score = 0.5 + (hash(str(len(klines))) % 40 - 20) / 100
        onchain_change = current_onchain_score - historical_onchain_score
        
        # Detectar divergencias
        price_direction = "up" if price_change > 0.02 else "down" if price_change < -0.02 else "neutral"
        onchain_direction = "up" if onchain_change > 0.1 else "down" if onchain_change < -0.1 else "neutral"
        
        # Determinar tipo de divergencia
        if price_direction == "down" and onchain_direction == "up":
            divergence_type = "bullish_divergence"
        elif price_direction == "up" and onchain_direction == "down":
            divergence_type = "bearish_divergence"
        elif price_direction == onchain_direction and price_direction != "neutral":
            divergence_type = "confirmation"
        else:
            divergence_type = "no_divergence"
        
        # Calcular fuerza de divergencia
        if divergence_type in ["bullish_divergence", "bearish_divergence"]:
            divergence_strength = min(abs(price_change) + abs(onchain_change), 1.0)
        else:
            divergence_strength = 0.0
        
        return {
            "divergence_type": divergence_type,
            "divergence_strength": divergence_strength,
            "price_change": price_change,
            "onchain_change": onchain_change,
            "price_direction": price_direction,
            "onchain_direction": onchain_direction,
            "correlation_period": self.correlation_period
        }

    def _analyze_network_health(self, onchain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la salud general de la red blockchain."""
        daily_metrics = onchain_data.get("daily_metrics", [])
        
        if len(daily_metrics) < 2:
            return {"health_score": 0.5}
        
        latest_metrics = daily_metrics[-1]
        
        # Métricas de salud
        active_addresses = latest_metrics.get("active_addresses", 0)
        tx_volume = latest_metrics.get("transaction_volume", 0)
        network_data = latest_metrics.get("network_metrics", {})
        
        # Calcular scores de salud (0-1)
        address_health = min(active_addresses / self.min_network_activity, 1.0)
        volume_health = min(tx_volume / 10000000000, 1.0)  # $10B baseline
        
        # Network security (hash rate, difficulty)
        hash_rate = network_data.get("hash_rate", 0)
        hash_health = min(hash_rate / 200000000, 1.0)  # 200 EH/s baseline
        
        # Score compuesto
        health_score = (address_health + volume_health + hash_health) / 3
        
        # Categorizar salud
        if health_score >= 0.8:
            health_category = "excellent"
        elif health_score >= 0.6:
            health_category = "good"
        elif health_score >= 0.4:
            health_category = "fair"
        else:
            health_category = "poor"
        
        return {
            "health_score": health_score,
            "health_category": health_category,
            "address_health": address_health,
            "volume_health": volume_health,
            "network_security": hash_health,
            "network_congestion": "low"  # Simplificado
        }

    def _detect_accumulation_distribution_patterns(self, whale_analysis: Dict[str, Any], exchange_flows: Dict[str, Any], address_activity: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta patrones de acumulación o distribución."""
        # Indicadores de acumulación
        whale_activity = whale_analysis.get("activity", "normal")
        flow_type = exchange_flows.get("flow_type", "neutral")
        address_trend = address_activity.get("trend", "stable")
        
        accumulation_signals = 0
        distribution_signals = 0
        
        # Señales de acumulación
        if whale_activity in ["very_active", "active"]:
            accumulation_signals += 1
        
        if flow_type in ["strong_outflow", "moderate_outflow"]:
            accumulation_signals += 1
        
        if address_trend in ["increasing_strongly", "increasing"]:
            accumulation_signals += 1
        
        # Señales de distribución
        if whale_activity in ["very_quiet", "quiet"]:
            distribution_signals += 1
        
        if flow_type in ["strong_inflow", "moderate_inflow"]:
            distribution_signals += 1
        
        if address_trend in ["decreasing_strongly", "decreasing"]:
            distribution_signals += 1
        
        # Determinar patrón
        if accumulation_signals >= 2:
            pattern = "accumulation"
            strength = accumulation_signals / 3
        elif distribution_signals >= 2:
            pattern = "distribution"
            strength = distribution_signals / 3
        else:
            pattern = "neutral"
            strength = 0.5
        
        return {
            "pattern": pattern,
            "strength": strength,
            "accumulation_signals": accumulation_signals,
            "distribution_signals": distribution_signals,
            "confidence": max(accumulation_signals, distribution_signals) / 3
        }

    def _evaluate_onchain_trend_strength(self, onchain_score: Dict[str, Any], divergence_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la fuerza de la tendencia on-chain."""
        current_score = onchain_score.get("current_score", 0.5)
        category = onchain_score.get("category", "neutral")
        divergence_type = divergence_analysis.get("divergence_type", "no_divergence")
        
        # Calcular fuerza base
        distance_from_neutral = abs(current_score - 0.5)
        base_strength = distance_from_neutral * 2  # 0-1 scale
        
        # Ajustar por divergencia
        if divergence_type in ["bullish_divergence", "bearish_divergence"]:
            divergence_multiplier = 1.5  # Divergencias indican fuerza
        elif divergence_type == "confirmation":
            divergence_multiplier = 1.2  # Confirmación es buena señal
        else:
            divergence_multiplier = 1.0
        
        trend_strength = min(base_strength * divergence_multiplier, 1.0)
        
        # Categorizar fuerza
        if trend_strength >= 0.8:
            strength_category = "very_strong"
        elif trend_strength >= 0.6:
            strength_category = "strong"
        elif trend_strength >= 0.4:
            strength_category = "moderate"
        else:
            strength_category = "weak"
        
        return {
            "trend_strength": trend_strength,
            "strength_category": strength_category,
            "onchain_bias": category,
            "divergence_impact": divergence_multiplier
        }

    def _evaluate_onchain_trading_opportunity(self, divergence_analysis: Dict[str, Any], network_health: Dict[str, Any], accumulation_distribution: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa si existe una oportunidad válida de trading basada en on-chain."""
        opportunity = {
            "valid_opportunity": False,
            "reasons": []
        }
        
        # Verificar divergencia significativa
        divergence_type = divergence_analysis.get("divergence_type", "no_divergence")
        divergence_strength = divergence_analysis.get("divergence_strength", 0)
        
        if divergence_type in ["bullish_divergence", "bearish_divergence"] and divergence_strength >= self.divergence_threshold:
            opportunity["reasons"].append("significant_divergence")
        else:
            return opportunity
        
        # Verificar salud de la red
        health_score = network_health.get("health_score", 0)
        if health_score >= 0.6:
            opportunity["reasons"].append("healthy_network")
        
        # Verificar patrón de acumulación/distribución
        pattern = accumulation_distribution.get("pattern", "neutral")
        pattern_strength = accumulation_distribution.get("strength", 0)
        
        if pattern != "neutral" and pattern_strength >= 0.6:
            opportunity["reasons"].append("clear_accumulation_distribution_pattern")
        
        # Verificar consistencia de señales
        if len(opportunity["reasons"]) >= 2:
            opportunity["valid_opportunity"] = True
        
        return opportunity

    def _calculate_confidence(self, divergence_analysis: Dict[str, Any], network_health: Dict[str, Any], onchain_trend_strength: Dict[str, Any], accumulation_distribution: Dict[str, Any], trading_opportunity: Dict[str, Any]) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: fuerza de divergencia
        divergence_strength = divergence_analysis.get("divergence_strength", 0)
        if divergence_strength >= 0.8:
            confidence += 0.35
        elif divergence_strength >= self.divergence_threshold:
            confidence += 0.25
        
        # Salud de la red
        health_score = network_health.get("health_score", 0)
        confidence += health_score * 0.2
        
        # Fuerza de tendencia on-chain
        trend_strength = onchain_trend_strength.get("trend_strength", 0)
        confidence += trend_strength * 0.2
        
        # Patrón de acumulación/distribución
        pattern_confidence = accumulation_distribution.get("confidence", 0)
        confidence += pattern_confidence * 0.15
        
        # Oportunidad válida
        if trading_opportunity.get("valid_opportunity", False):
            confidence += 0.1
        
        return min(1.0, confidence)

    def _get_signal_strength(self, confidence: float, divergence_strength: float) -> SignalStrength:
        """Convierte confianza y fuerza de divergencia a fuerza de señal."""
        combined_score = confidence + (divergence_strength * 0.3)
        
        if combined_score >= 0.85:
            return SignalStrength.STRONG
        elif combined_score >= 0.7:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength, accumulation_distribution: Dict[str, Any]) -> Decimal:
        """Calcula tamaño de posición basado en la fuerza on-chain."""
        base_size = self.position_size_pct
        
        # Ajuste por fuerza de señal
        if signal_strength == SignalStrength.STRONG:
            strength_multiplier = 1.2
        elif signal_strength == SignalStrength.MEDIUM:
            strength_multiplier = 1.0
        else:
            strength_multiplier = 0.8
        
        # Ajuste por patrón de acumulación/distribución
        pattern_strength = accumulation_distribution.get("strength", 0.5)
        pattern_multiplier = 0.8 + (pattern_strength * 0.4)  # 0.8 - 1.2
        
        final_size = base_size * strength_multiplier * pattern_multiplier
        return Decimal(str(final_size))

    def _calculate_onchain_stop_loss(self, entry_price: float, divergence_analysis: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula stop loss basado en fuerza de divergencia on-chain."""
        divergence_strength = divergence_analysis.get("divergence_strength", 0.5)
        
        # Stop loss más amplio para on-chain (movimientos más lentos)
        base_stop_pct = 0.04  # 4% base
        
        # Ajustar según fuerza de divergencia
        stop_pct = base_stop_pct * (1 + divergence_strength)
        
        if position_type == "BUY":
            stop_price = entry_price * (1 - stop_pct)
        else:  # SELL
            stop_price = entry_price * (1 + stop_pct)
        
        return Decimal(str(stop_price))

    def _calculate_onchain_take_profit(self, entry_price: float, divergence_analysis: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula take profit basado en movimiento esperado de divergencia."""
        divergence_strength = divergence_analysis.get("divergence_strength", 0.5)
        
        # Target basado en fuerza de divergencia
        base_target_pct = 0.06  # 6% base
        target_pct = base_target_pct * (1 + divergence_strength)
        
        if position_type == "BUY":
            tp_price = entry_price * (1 + target_pct)
        else:  # SELL
            tp_price = entry_price * (1 - target_pct)
        
        return Decimal(str(tp_price))
