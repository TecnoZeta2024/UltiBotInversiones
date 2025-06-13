"""
News Sentiment Spike Trader Strategy

Esta estrategia utiliza herramientas MCP para detectar picos de sentimiento en noticias 
y redes sociales, operando en la dirección del sentimiento con confirmación de volumen.
Es una estrategia event-driven potenciada por IA.

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

class NewsSentimentParameters:
    """Parámetros configurables para News Sentiment Spike Trader."""
    
    def __init__(
        self,
        sentiment_threshold: float = 0.7,  # 70% sentimiento positivo/negativo
        spike_multiplier: float = 2.0,  # 2x el sentimiento normal
        news_freshness_hours: int = 4,  # Noticias de las últimas 4 horas
        min_news_volume: int = 10,  # Mínimo 10 menciones/noticias
        social_weight: float = 0.4,  # 40% peso a redes sociales
        news_weight: float = 0.6,  # 60% peso a noticias tradicionales
        volume_confirmation_multiplier: float = 1.5,
        position_size_pct: float = 0.025,
        max_position_duration_hours: int = 24,
        sentiment_decay_hours: int = 8  # El sentimiento pierde fuerza después de 8h
    ):
        self.sentiment_threshold = sentiment_threshold
        self.spike_multiplier = spike_multiplier
        self.news_freshness_hours = news_freshness_hours
        self.min_news_volume = min_news_volume
        self.social_weight = social_weight
        self.news_weight = news_weight
        self.volume_confirmation_multiplier = volume_confirmation_multiplier
        self.position_size_pct = position_size_pct
        self.max_position_duration_hours = max_position_duration_hours
        self.sentiment_decay_hours = sentiment_decay_hours

class NewsSentimentSpikeTrader(BaseStrategy):
    """
    Estrategia de trading basada en spikes de sentiment.
    
    Detecta cambios súbitos en el sentimiento de noticias y redes sociales
    sobre activos específicos y opera en la dirección del sentimiento.
    """
    
    def __init__(self, parameters: NewsSentimentParameters):
        super().__init__("News_Sentiment_Spike_Trader", parameters)
        self.sentiment_threshold = parameters.sentiment_threshold
        self.spike_multiplier = parameters.spike_multiplier
        self.news_freshness_hours = parameters.news_freshness_hours
        self.min_news_volume = parameters.min_news_volume
        self.social_weight = parameters.social_weight
        self.news_weight = parameters.news_weight
        self.volume_confirmation_multiplier = parameters.volume_confirmation_multiplier
        self.position_size_pct = parameters.position_size_pct
        self.max_position_duration_hours = parameters.max_position_duration_hours
        self.sentiment_decay_hours = parameters.sentiment_decay_hours
        
        self._sentiment_history = []
        self._news_cache = {}

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con sentiment threshold={self.sentiment_threshold}")

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza el sentimiento de noticias y detecta spikes significativos.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis de sentiment y oportunidades de trading
        """
        try:
            if len(market_snapshot.klines) < 10:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Obtener symbol del asset (asumir BTC por defecto)
            symbol = getattr(market_snapshot, 'symbol', 'BTC')
            
            # Simular obtención de sentiment via MCP tools
            # En implementación real: await self._tools.execute_tool("get_sentiment", {...})
            sentiment_data = await self._get_sentiment_data(symbol)
            
            # Analizar histórico de sentiment para detectar baseline
            sentiment_baseline = self._calculate_sentiment_baseline(sentiment_data)
            
            # Detectar spike de sentiment
            sentiment_spike = self._detect_sentiment_spike(sentiment_data, sentiment_baseline)
            
            # Analizar fuentes de noticias
            news_analysis = self._analyze_news_sources(sentiment_data)
            
            # Verificar confirmación de volumen
            volume_confirmation = self._analyze_volume_confirmation(market_snapshot.klines)
            
            # Analizar momentum de precio post-sentiment
            price_momentum = self._analyze_price_sentiment_correlation(
                market_snapshot.klines, sentiment_data
            )
            
            # Evaluar credibilidad de las fuentes
            source_credibility = self._evaluate_source_credibility(sentiment_data)
            
            # Detectar eventos específicos (earnings, launches, partnerships)
            event_detection = self._detect_significant_events(sentiment_data)
            
            # Calcular fuerza del sentimiento actual
            sentiment_strength = self._calculate_sentiment_strength(
                sentiment_data, sentiment_spike, news_analysis
            )
            
            # Evaluar oportunidad de trading
            trading_opportunity = self._evaluate_sentiment_trading_opportunity(
                sentiment_spike, volume_confirmation, source_credibility, event_detection
            )
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                sentiment_spike, volume_confirmation, source_credibility,
                event_detection, sentiment_strength, price_momentum
            )
            
            current_price = float(market_snapshot.klines[-1].close)
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "current_price": current_price,
                    "sentiment_data": sentiment_data,
                    "sentiment_spike": sentiment_spike,
                    "sentiment_baseline": sentiment_baseline,
                    "news_analysis": news_analysis,
                    "volume_confirmation": volume_confirmation,
                    "price_momentum": price_momentum,
                    "source_credibility": source_credibility,
                    "event_detection": event_detection,
                    "sentiment_strength": sentiment_strength,
                    "trading_opportunity": trading_opportunity
                },
                metadata={
                    "symbol": symbol,
                    "sentiment_threshold": self.sentiment_threshold,
                    "news_freshness_hours": self.news_freshness_hours
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis News Sentiment: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de trading basada en el análisis de sentiment.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se detecta spike significativo, None en caso contrario
        """
        try:
            if analysis.confidence < 0.7:  # Umbral alto para sentiment trading
                return None
                
            indicators = analysis.indicators
            trading_opportunity = indicators.get("trading_opportunity", {})
            sentiment_spike = indicators.get("sentiment_spike", {})
            volume_confirmation = indicators.get("volume_confirmation", {})
            
            if not trading_opportunity.get("valid_opportunity", False):
                return None
                
            current_price = indicators.get("current_price", 0)
            sentiment_direction = sentiment_spike.get("direction")
            sentiment_magnitude = sentiment_spike.get("magnitude", 0)
            
            # Señal de compra (sentiment alcista spike)
            if sentiment_direction == "bullish" and sentiment_magnitude >= self.spike_multiplier:
                signal_strength = self._get_signal_strength(analysis.confidence, sentiment_magnitude)
                position_size = self._calculate_position_size(signal_strength, sentiment_spike)
                
                # Calcular targets basados en sentiment y volatilidad esperada
                stop_loss = self._calculate_sentiment_stop_loss(current_price, sentiment_spike, "BUY")
                take_profit = self._calculate_sentiment_take_profit(current_price, sentiment_spike, "BUY")
                
                # Calcular duración máxima basada en decay del sentiment
                max_duration_hours = self._calculate_position_duration(sentiment_spike)
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Bullish sentiment spike detected. Magnitude: {sentiment_magnitude:.1f}x, Score: {sentiment_spike.get('current_score', 0):.1%}, Volume: {volume_confirmation.get('volume_multiple', 0):.1f}x, Sources: {sentiment_spike.get('source_count', 0)}",
                    metadata={
                        "strategy_type": "sentiment_driven",
                        "max_duration_hours": max_duration_hours,
                        "sentiment_score": sentiment_spike.get("current_score", 0),
                        "sentiment_sources": sentiment_spike.get("sources", [])
                    }
                )
                
            # Señal de venta (sentiment bajista spike)
            elif sentiment_direction == "bearish" and sentiment_magnitude >= self.spike_multiplier:
                signal_strength = self._get_signal_strength(analysis.confidence, sentiment_magnitude)
                position_size = self._calculate_position_size(signal_strength, sentiment_spike)
                
                # Calcular targets basados en sentiment y volatilidad esperada
                stop_loss = self._calculate_sentiment_stop_loss(current_price, sentiment_spike, "SELL")
                take_profit = self._calculate_sentiment_take_profit(current_price, sentiment_spike, "SELL")
                
                # Calcular duración máxima basada en decay del sentiment
                max_duration_hours = self._calculate_position_duration(sentiment_spike)
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(current_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Bearish sentiment spike detected. Magnitude: {sentiment_magnitude:.1f}x, Score: {sentiment_spike.get('current_score', 0):.1%}, Volume: {volume_confirmation.get('volume_multiple', 0):.1f}x, Sources: {sentiment_spike.get('source_count', 0)}",
                    metadata={
                        "strategy_type": "sentiment_driven",
                        "max_duration_hours": max_duration_hours,
                        "sentiment_score": sentiment_spike.get("current_score", 0),
                        "sentiment_sources": sentiment_spike.get("sources", [])
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal News Sentiment: {e}")
            return None

    async def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos de sentiment usando herramientas MCP.
        En implementación real, esto haría llamadas a APIs reales.
        """
        # Simular datos de sentiment para testing
        current_time = datetime.now(timezone.utc) # MODIFIED
        
        # Simular scores de diferentes fuentes
        base_sentiment = 0.5  # Neutral
        sentiment_variance = (hash(symbol + str(current_time.hour)) % 100 - 50) / 100  # -0.5 a 0.5
        
        current_sentiment_score = max(0, min(1, base_sentiment + sentiment_variance))
        
        # Simular fuentes de noticias
        news_sources = [
            {
                "source": "CoinDesk",
                "sentiment": current_sentiment_score + (hash("coindesk") % 20 - 10) / 100,
                "volume": hash("coindesk") % 50 + 10,
                "credibility": 0.9,
                "timestamp": current_time - timedelta(hours=hash("coindesk") % 4)
            },
            {
                "source": "Twitter",
                "sentiment": current_sentiment_score + (hash("twitter") % 30 - 15) / 100,
                "volume": hash("twitter") % 100 + 20,
                "credibility": 0.6,
                "timestamp": current_time - timedelta(hours=hash("twitter") % 2)
            },
            {
                "source": "Reddit",
                "sentiment": current_sentiment_score + (hash("reddit") % 25 - 12) / 100,
                "volume": hash("reddit") % 80 + 15,
                "credibility": 0.7,
                "timestamp": current_time - timedelta(hours=hash("reddit") % 3)
            }
        ]
        
        # Calcular sentiment agregado
        total_weighted_sentiment = 0
        total_weight = 0
        
        for source in news_sources:
            if source["source"] in ["Twitter", "Reddit"]:
                weight = source["volume"] * source["credibility"] * self.social_weight
            else:
                weight = source["volume"] * source["credibility"] * self.news_weight
            
            total_weighted_sentiment += source["sentiment"] * weight
            total_weight += weight
        
        aggregated_sentiment = total_weighted_sentiment / total_weight if total_weight > 0 else 0.5
        
        return {
            "current_score": aggregated_sentiment,
            "sources": news_sources,
            "total_volume": sum(s["volume"] for s in news_sources),
            "weighted_credibility": total_weight / len(news_sources) if news_sources else 0,
            "timestamp": current_time,
            "symbol": symbol
        }

    def _calculate_sentiment_baseline(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula el baseline histórico del sentiment."""
        # En implementación real, esto consultaría histórico de sentiment
        # Por ahora, simular baseline
        
        historical_scores = []
        for i in range(24):  # Últimas 24 horas simuladas
            score = 0.5 + (hash(f"baseline_{i}") % 40 - 20) / 200  # Variación pequeña
            historical_scores.append(max(0, min(1, score)))
        
        baseline_score = statistics.mean(historical_scores)
        baseline_volatility = statistics.stdev(historical_scores) if len(historical_scores) > 1 else 0.1
        
        return {
            "average_score": baseline_score,
            "volatility": baseline_volatility,
            "sample_size": len(historical_scores),
            "trend": "neutral"  # Simplificado
        }

    def _detect_sentiment_spike(self, sentiment_data: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta spikes significativos en el sentiment."""
        current_score = sentiment_data["current_score"]
        baseline_score = baseline["average_score"]
        baseline_volatility = baseline["volatility"]
        
        # Calcular desviación del baseline
        deviation = current_score - baseline_score
        z_score = deviation / baseline_volatility if baseline_volatility > 0 else 0
        
        # Determinar si es un spike significativo
        magnitude = abs(z_score)
        
        if z_score > 2.0:  # 2 desviaciones estándar arriba
            direction = "bullish"
            spike_detected = magnitude >= self.spike_multiplier
        elif z_score < -2.0:  # 2 desviaciones estándar abajo
            direction = "bearish"
            spike_detected = magnitude >= self.spike_multiplier
        else:
            direction = "neutral"
            spike_detected = False
        
        return {
            "spike_detected": spike_detected,
            "direction": direction,
            "magnitude": magnitude,
            "z_score": z_score,
            "current_score": current_score,
            "baseline_score": baseline_score,
            "deviation": deviation,
            "source_count": len(sentiment_data.get("sources", []))
        }

    def _analyze_news_sources(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la calidad y diversidad de las fuentes de noticias."""
        sources = sentiment_data.get("sources", [])
        
        if not sources:
            return {"quality": "poor", "diversity": 0, "credibility": 0}
        
        # Analizar credibilidad promedio
        avg_credibility = statistics.mean(s["credibility"] for s in sources)
        
        # Analizar diversidad de fuentes
        source_types = set()
        for source in sources:
            if source["source"] in ["Twitter", "Reddit", "Telegram"]:
                source_types.add("social")
            else:
                source_types.add("traditional")
        
        diversity_score = len(source_types) / 2  # Máximo 2 tipos
        
        # Analizar volumen total
        total_volume = sum(s["volume"] for s in sources)
        volume_score = min(total_volume / 100, 1.0)  # Normalizar a 1.0
        
        # Calificar calidad general
        quality_score = (avg_credibility + diversity_score + volume_score) / 3
        
        if quality_score >= 0.8:
            quality = "excellent"
        elif quality_score >= 0.6:
            quality = "good"
        elif quality_score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"
        
        return {
            "quality": quality,
            "quality_score": quality_score,
            "diversity": diversity_score,
            "credibility": avg_credibility,
            "total_volume": total_volume,
            "source_count": len(sources)
        }

    def _analyze_volume_confirmation(self, klines: List[KlineData]) -> Dict[str, Any]:
        """Analiza si hay confirmación de volumen para el sentiment."""
        if len(klines) < 10:
            return {"confirmed": False}
        
        # Volumen actual vs promedio
        current_volume = float(klines[-1].volume)
        avg_volume = statistics.mean(float(k.volume) for k in klines[-10:-1])
        
        volume_multiple = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Verificar incremento sostenido
        recent_volumes = [float(k.volume) for k in klines[-5:]]
        volume_trend = "increasing" if recent_volumes[-1] > recent_volumes[0] else "decreasing"
        
        # Confirmación si hay incremento significativo
        confirmed = (volume_multiple >= self.volume_confirmation_multiplier and 
                    volume_trend == "increasing")
        
        return {
            "confirmed": confirmed,
            "volume_multiple": volume_multiple,
            "volume_trend": volume_trend,
            "current_volume": current_volume,
            "average_volume": avg_volume
        }

    def _analyze_price_sentiment_correlation(self, klines: List[KlineData], sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la correlación entre precio y sentiment."""
        if len(klines) < 5:
            return {"correlation": "insufficient_data"}
        
        # Calcular cambio de precio reciente
        recent_prices = [float(k.close) for k in klines[-5:]]
        price_change_pct = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Sentiment actual vs neutral
        current_sentiment = sentiment_data["current_score"]
        sentiment_deviation = current_sentiment - 0.5  # Desviación de neutral
        
        # Evaluar correlación
        if sentiment_deviation > 0.1 and price_change_pct > 0.01:  # Ambos positivos
            correlation = "positive"
        elif sentiment_deviation < -0.1 and price_change_pct < -0.01:  # Ambos negativos
            correlation = "positive"
        elif abs(sentiment_deviation) > 0.1 and abs(price_change_pct) > 0.01:
            correlation = "negative"  # Direcciones opuestas
        else:
            correlation = "neutral"
        
        return {
            "correlation": correlation,
            "price_change_pct": price_change_pct,
            "sentiment_deviation": sentiment_deviation,
            "momentum_aligned": correlation == "positive"
        }

    def _evaluate_source_credibility(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la credibilidad de las fuentes de sentiment."""
        sources = sentiment_data.get("sources", [])
        
        if not sources:
            return {"overall_credibility": 0, "reliable_sources": 0}
        
        high_credibility_sources = [s for s in sources if s["credibility"] >= 0.8]
        medium_credibility_sources = [s for s in sources if 0.6 <= s["credibility"] < 0.8]
        
        overall_credibility = statistics.mean(s["credibility"] for s in sources)
        
        # Verificar consenso entre fuentes confiables
        if len(high_credibility_sources) >= 2:
            reliable_sentiments = [s["sentiment"] for s in high_credibility_sources]
            sentiment_consensus = statistics.stdev(reliable_sentiments) < 0.2  # Baja dispersión
        else:
            sentiment_consensus = False
        
        return {
            "overall_credibility": overall_credibility,
            "reliable_sources": len(high_credibility_sources),
            "medium_sources": len(medium_credibility_sources),
            "sentiment_consensus": sentiment_consensus,
            "credibility_category": "high" if overall_credibility >= 0.8 else "medium" if overall_credibility >= 0.6 else "low"
        }

    def _detect_significant_events(self, sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta eventos significativos en las noticias."""
        # Simular detección de eventos basada en volumen y timing
        total_volume = sentiment_data.get("total_volume", 0)
        
        # Ensure current_time is timezone-aware. sentiment_data["timestamp"] should ideally be aware.
        # If sentiment_data["timestamp"] is naive, this comparison might be problematic.
        # Assuming sentiment_data["timestamp"] (if present and datetime) is UTC.
        sentiment_time = sentiment_data.get("timestamp")
        if isinstance(sentiment_time, datetime):
            current_time = sentiment_time if sentiment_time.tzinfo else sentiment_time.replace(tzinfo=timezone.utc)
        else: # Fallback if timestamp is not a datetime object or not present
            current_time = datetime.now(timezone.utc) # MODIFIED

        # Eventos más probables en ciertos horarios (earnings, anuncios)
        hour = current_time.hour
        
        # Simular tipos de eventos
        event_indicators = {
            "earnings_release": total_volume > 80 and 14 <= hour <= 16,  # Horario típico de earnings
            "partnership_announcement": total_volume > 60 and 9 <= hour <= 11,
            "regulatory_news": total_volume > 70 and sentiment_data["current_score"] < 0.3,
            "product_launch": total_volume > 50 and sentiment_data["current_score"] > 0.7,
            "market_manipulation": total_volume > 100 and abs(sentiment_data["current_score"] - 0.5) > 0.4
        }
        
        detected_events = [event for event, detected in event_indicators.items() if detected]
        
        return {
            "events_detected": detected_events,
            "event_count": len(detected_events),
            "high_impact_event": len(detected_events) > 0 and total_volume > 90
        }

    def _calculate_sentiment_strength(self, sentiment_data: Dict[str, Any], spike: Dict[str, Any], news_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula la fuerza total del sentimiento."""
        # Componentes de fuerza
        spike_strength = spike.get("magnitude", 0) if spike.get("spike_detected", False) else 0
        volume_strength = min(sentiment_data.get("total_volume", 0) / 100, 1.0)
        credibility_strength = news_analysis.get("credibility", 0)
        diversity_strength = news_analysis.get("diversity", 0)
        
        # Fuerza combinada
        combined_strength = (
            spike_strength * 0.4 +
            volume_strength * 0.3 +
            credibility_strength * 0.2 +
            diversity_strength * 0.1
        )
        
        # Categorizar fuerza
        if combined_strength >= 0.8:
            strength_category = "very_strong"
        elif combined_strength >= 0.6:
            strength_category = "strong"
        elif combined_strength >= 0.4:
            strength_category = "moderate"
        else:
            strength_category = "weak"
        
        return {
            "combined_strength": combined_strength,
            "strength_category": strength_category,
            "spike_strength": spike_strength,
            "volume_strength": volume_strength,
            "credibility_strength": credibility_strength,
            "diversity_strength": diversity_strength
        }

    def _evaluate_sentiment_trading_opportunity(self, spike: Dict[str, Any], volume_confirmation: Dict[str, Any], source_credibility: Dict[str, Any], events: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa si existe una oportunidad válida de trading basada en sentiment."""
        opportunity = {
            "valid_opportunity": False,
            "reasons": []
        }
        
        # Verificar spike significativo
        if spike.get("spike_detected", False):
            opportunity["reasons"].append("significant_sentiment_spike")
        else:
            return opportunity
        
        # Verificar confirmación de volumen
        if volume_confirmation.get("confirmed", False):
            opportunity["reasons"].append("volume_confirmation")
        
        # Verificar credibilidad de fuentes
        if source_credibility.get("overall_credibility", 0) >= 0.7:
            opportunity["reasons"].append("high_source_credibility")
        
        # Verificar eventos de alto impacto
        if events.get("high_impact_event", False):
            opportunity["reasons"].append("high_impact_event")
        
        # Verificar volumen mínimo de noticias
        if spike.get("source_count", 0) >= self.min_news_volume / 2:  # Relajar un poco el req
            opportunity["reasons"].append("sufficient_news_volume")
        
        # Oportunidad válida si tenemos suficientes confirmaciones
        if len(opportunity["reasons"]) >= 2:
            opportunity["valid_opportunity"] = True
        
        return opportunity

    def _calculate_confidence(self, spike: Dict[str, Any], volume_confirmation: Dict[str, Any], source_credibility: Dict[str, Any], events: Dict[str, Any], sentiment_strength: Dict[str, Any], price_momentum: Dict[str, Any]) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: spike de sentiment
        if spike.get("spike_detected", False):
            magnitude = spike.get("magnitude", 0)
            if magnitude >= 3.0:
                confidence += 0.3
            elif magnitude >= self.spike_multiplier:
                confidence += 0.2
        
        # Confirmación de volumen
        if volume_confirmation.get("confirmed", False):
            confidence += 0.25
        
        # Credibilidad de fuentes
        credibility = source_credibility.get("overall_credibility", 0)
        confidence += credibility * 0.2
        
        # Eventos de alto impacto
        if events.get("high_impact_event", False):
            confidence += 0.15
        
        # Fuerza del sentiment
        strength = sentiment_strength.get("combined_strength", 0)
        confidence += strength * 0.1
        
        # Momentum de precio alineado
        if price_momentum.get("momentum_aligned", False):
            confidence += 0.1
        
        return min(1.0, confidence)

    def _get_signal_strength(self, confidence: float, sentiment_magnitude: float) -> SignalStrength:
        """Convierte confianza y magnitud de sentiment a fuerza de señal."""
        combined_score = confidence + (min(sentiment_magnitude / 4.0, 1.0) * 0.2)
        
        if combined_score >= 0.85:
            return SignalStrength.STRONG
        elif combined_score >= 0.7:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength, sentiment_spike: Dict[str, Any]) -> Decimal:
        """Calcula tamaño de posición basado en la fuerza del sentiment."""
        base_size = self.position_size_pct
        
        # Ajuste por fuerza de señal
        if signal_strength == SignalStrength.STRONG:
            strength_multiplier = 1.3
        elif signal_strength == SignalStrength.MEDIUM:
            strength_multiplier = 1.0
        else:
            strength_multiplier = 0.7
        
        # Ajuste por magnitud del spike
        magnitude = sentiment_spike.get("magnitude", 1.0)
        magnitude_multiplier = min(magnitude / 3.0, 1.5)  # Máximo 1.5x
        
        final_size = base_size * strength_multiplier * magnitude_multiplier
        return Decimal(str(final_size))

    def _calculate_position_duration(self, sentiment_spike: Dict[str, Any]) -> int:
        """Calcula duración máxima de la posición basada en decay del sentiment."""
        magnitude = sentiment_spike.get("magnitude", 1.0)
        
        # Sentiments más fuertes duran más tiempo
        if magnitude >= 4.0:
            duration_hours = self.max_position_duration_hours
        elif magnitude >= 3.0:
            duration_hours = int(self.max_position_duration_hours * 0.75)
        elif magnitude >= 2.0:
            duration_hours = int(self.max_position_duration_hours * 0.5)
        else:
            duration_hours = int(self.max_position_duration_hours * 0.25)
        
        return max(duration_hours, self.sentiment_decay_hours)

    def _calculate_sentiment_stop_loss(self, entry_price: float, sentiment_spike: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula stop loss basado en volatilidad esperada del sentiment."""
        # Stop loss más amplio para sentiment trading debido a volatilidad
        magnitude = sentiment_spike.get("magnitude", 1.0)
        base_stop_pct = 0.03  # 3% base
        
        # Ajustar según magnitud (más magnitud = más volátil = stop más amplio)
        stop_pct = base_stop_pct * (1 + magnitude / 10)
        
        if position_type == "BUY":
            stop_price = entry_price * (1 - stop_pct)
        else:  # SELL
            stop_price = entry_price * (1 + stop_pct)
        
        return Decimal(str(stop_price))

    def _calculate_sentiment_take_profit(self, entry_price: float, sentiment_spike: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula take profit basado en movimiento esperado del sentiment."""
        # Target más agresivo para sentiment trading
        magnitude = sentiment_spike.get("magnitude", 1.0)
        base_target_pct = 0.05  # 5% base
        
        # Más magnitud = mayor movimiento esperado
        target_pct = base_target_pct * magnitude
        
        if position_type == "BUY":
            tp_price = entry_price * (1 + target_pct)
        else:  # SELL
            tp_price = entry_price * (1 - target_pct)
        
        return Decimal(str(tp_price))
