"""
Market Sentiment Adapter - Herramienta MCP para análisis de sentimiento.

Este adaptador proporciona análisis de sentimiento de mercado usando múltiples fuentes
incluyendo noticias, redes sociales y métricas on-chain.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_mcp_adapter import BaseMCPAdapter

class MarketSentimentAdapter(BaseMCPAdapter):
    """
    Adaptador MCP para análisis de sentimiento de mercado.
    
    Proporciona análisis de sentimiento agregado desde múltiples fuentes:
    - Noticias financieras
    - Redes sociales (Twitter, Reddit)
    - Métricas on-chain
    - Indicadores técnicos de sentimiento
    """
    
    def __init__(self):
        super().__init__(
            name="market_sentiment_analyzer",
            description="Analiza el sentimiento del mercado para activos específicos usando múltiples fuentes de datos",
            category="market_analysis"
        )
        self._sentiment_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry_minutes = 15
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Schema de parámetros para el análisis de sentimiento.
        
        Returns:
            dict: Schema JSON de parámetros
        """
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Símbolo del activo a analizar (ej. BTCUSDT, ETHUSDT)",
                    "pattern": "^[A-Z]+$"
                },
                "timeframe": {
                    "type": "string",
                    "description": "Marco temporal para el análisis",
                    "enum": ["1h", "4h", "12h", "24h", "7d"],
                    "default": "24h"
                },
                "sources": {
                    "type": "array",
                    "description": "Fuentes de datos a incluir en el análisis",
                    "items": {
                        "type": "string",
                        "enum": ["news", "social", "onchain", "technical"]
                    },
                    "default": ["news", "social", "technical"]
                },
                "include_details": {
                    "type": "boolean",
                    "description": "Incluir detalles granulares del análisis",
                    "default": False
                }
            },
            "required": ["symbol"],
            "additionalProperties": False
        }
    
    def _get_timeout_seconds(self) -> int:
        """Timeout personalizado para análisis de sentimiento."""
        return 45  # 45 segundos para permitir múltiples API calls
    
    def _requires_credentials(self) -> bool:
        """Este adaptador requiere credenciales para APIs de noticias y social."""
        return True
    
    async def _pre_execute_hook(self, parameters: Dict[str, Any]) -> None:
        """
        Hook pre-ejecución para validaciones específicas.
        
        Args:
            parameters: Parámetros de ejecución
        """
        symbol = parameters["symbol"]
        
        # Validar formato del símbolo
        if not symbol.isupper() or len(symbol) < 3:
            raise ValueError(f"Invalid symbol format: {symbol}")
        
        # Log del inicio del análisis
        print(f"Starting sentiment analysis for {symbol}")
    
    async def _execute_implementation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementación del análisis de sentimiento.
        
        Args:
            parameters: Parámetros de ejecución
            
        Returns:
            dict: Resultado del análisis de sentimiento
        """
        symbol = parameters["symbol"]
        timeframe = parameters.get("timeframe", "24h")
        sources = parameters.get("sources", ["news", "social", "technical"])
        include_details = parameters.get("include_details", False)
        
        # Verificar cache
        cache_key = f"{symbol}_{timeframe}_{'-'.join(sorted(sources))}"
        if self._is_cache_valid(cache_key):
            cached_result = self._sentiment_cache[cache_key]["result"]
            cached_result["from_cache"] = True
            return cached_result
        
        # Realizar análisis por fuentes
        sentiment_results = {}
        analysis_tasks = []
        
        if "news" in sources:
            analysis_tasks.append(self._analyze_news_sentiment(symbol, timeframe))
        if "social" in sources:
            analysis_tasks.append(self._analyze_social_sentiment(symbol, timeframe))
        if "onchain" in sources:
            analysis_tasks.append(self._analyze_onchain_sentiment(symbol, timeframe))
        if "technical" in sources:
            analysis_tasks.append(self._analyze_technical_sentiment(symbol, timeframe))
        
        # Ejecutar análisis concurrentemente
        if analysis_tasks:
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            for i, source in enumerate([s for s in sources if s in ["news", "social", "onchain", "technical"]]):
                if i < len(results) and not isinstance(results[i], Exception):
                    sentiment_results[source] = results[i]
        
        # Agregar sentimientos
        aggregated_sentiment = self._aggregate_sentiment_scores(sentiment_results)
        
        # Construir resultado
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_sentiment": aggregated_sentiment,
            "sentiment_score": aggregated_sentiment["score"],
            "confidence": aggregated_sentiment["confidence"],
            "signal_strength": self._calculate_signal_strength(aggregated_sentiment),
            "sources_analyzed": list(sentiment_results.keys()),
            "from_cache": False
        }
        
        # Incluir detalles si se solicita
        if include_details:
            result["detailed_analysis"] = sentiment_results
            result["sentiment_distribution"] = self._calculate_sentiment_distribution(sentiment_results)
            result["key_factors"] = self._extract_key_factors(sentiment_results)
        
        # Guardar en cache
        self._sentiment_cache[cache_key] = {
            "result": result.copy(),
            "timestamp": datetime.utcnow()
        }
        
        return result
    
    async def _analyze_news_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Analiza sentimiento desde noticias financieras.
        
        Args:
            symbol: Símbolo del activo
            timeframe: Marco temporal
            
        Returns:
            dict: Resultado del análisis de noticias
        """
        # Simular llamada a API de noticias
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Simular análisis de sentimiento de noticias
        sentiment_score = random.uniform(-1.0, 1.0)
        article_count = random.randint(5, 50)
        
        return {
            "source": "news",
            "sentiment_score": sentiment_score,
            "confidence": random.uniform(0.7, 0.95),
            "article_count": article_count,
            "positive_mentions": max(0, int(article_count * (sentiment_score + 1) / 2)),
            "negative_mentions": max(0, int(article_count * (1 - sentiment_score) / 2)),
            "key_topics": ["regulation", "adoption", "technology"] if sentiment_score > 0 else ["volatility", "concerns", "regulation"],
            "trending_keywords": ["bullish", "growth"] if sentiment_score > 0 else ["bearish", "decline"]
        }
    
    async def _analyze_social_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Analiza sentimiento desde redes sociales.
        
        Args:
            symbol: Símbolo del activo
            timeframe: Marco temporal
            
        Returns:
            dict: Resultado del análisis social
        """
        # Simular llamada a APIs sociales
        await asyncio.sleep(random.uniform(0.8, 2.0))
        
        sentiment_score = random.uniform(-1.0, 1.0)
        mention_count = random.randint(100, 5000)
        
        return {
            "source": "social",
            "sentiment_score": sentiment_score,
            "confidence": random.uniform(0.6, 0.9),
            "mention_count": mention_count,
            "engagement_score": random.uniform(0.3, 1.0),
            "viral_factor": random.uniform(0.1, 0.8),
            "influencer_sentiment": random.uniform(-1.0, 1.0),
            "platforms": {
                "twitter": {"mentions": mention_count // 2, "sentiment": sentiment_score + random.uniform(-0.2, 0.2)},
                "reddit": {"mentions": mention_count // 4, "sentiment": sentiment_score + random.uniform(-0.3, 0.3)},
                "telegram": {"mentions": mention_count // 4, "sentiment": sentiment_score + random.uniform(-0.1, 0.1)}
            }
        }
    
    async def _analyze_onchain_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Analiza sentimiento desde métricas on-chain.
        
        Args:
            symbol: Símbolo del activo
            timeframe: Marco temporal
            
        Returns:
            dict: Resultado del análisis on-chain
        """
        # Simular análisis de métricas on-chain
        await asyncio.sleep(random.uniform(0.3, 1.0))
        
        sentiment_score = random.uniform(-1.0, 1.0)
        
        return {
            "source": "onchain",
            "sentiment_score": sentiment_score,
            "confidence": random.uniform(0.8, 0.95),
            "whale_activity": random.uniform(0.0, 1.0),
            "network_growth": random.uniform(-0.5, 1.0),
            "transaction_volume": random.uniform(0.2, 2.0),
            "holder_distribution": {
                "concentration": random.uniform(0.3, 0.8),
                "new_addresses": random.randint(1000, 10000)
            },
            "staking_metrics": {
                "staking_ratio": random.uniform(0.4, 0.8),
                "unstaking_trend": random.uniform(-0.3, 0.3)
            }
        }
    
    async def _analyze_technical_sentiment(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        Analiza sentimiento desde indicadores técnicos.
        
        Args:
            symbol: Símbolo del activo
            timeframe: Marco temporal
            
        Returns:
            dict: Resultado del análisis técnico
        """
        # Simular análisis técnico
        await asyncio.sleep(random.uniform(0.2, 0.8))
        
        sentiment_score = random.uniform(-1.0, 1.0)
        
        return {
            "source": "technical",
            "sentiment_score": sentiment_score,
            "confidence": random.uniform(0.75, 0.95),
            "fear_greed_index": random.uniform(0.0, 100.0),
            "volatility_index": random.uniform(0.1, 2.0),
            "momentum_indicators": {
                "rsi": random.uniform(20, 80),
                "macd": random.uniform(-1.0, 1.0),
                "bollinger_position": random.uniform(0.0, 1.0)
            },
            "trend_strength": random.uniform(0.0, 1.0),
            "support_resistance": {
                "proximity_to_support": random.uniform(0.0, 1.0),
                "proximity_to_resistance": random.uniform(0.0, 1.0)
            }
        }
    
    def _aggregate_sentiment_scores(self, sentiment_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrega los scores de sentimiento de múltiples fuentes.
        
        Args:
            sentiment_results: Resultados por fuente
            
        Returns:
            dict: Sentimiento agregado
        """
        if not sentiment_results:
            return {
                "score": 0.0,
                "confidence": 0.0,
                "label": "neutral",
                "sources_count": 0
            }
        
        # Pesos por fuente
        source_weights = {
            "news": 0.3,
            "social": 0.25,
            "onchain": 0.35,
            "technical": 0.1
        }
        
        weighted_score = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for source, result in sentiment_results.items():
            weight = source_weights.get(source, 0.2)
            score = result.get("sentiment_score", 0.0)
            confidence = result.get("confidence", 0.5)
            
            weighted_score += score * weight * confidence
            weighted_confidence += confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            final_score = weighted_score / total_weight
            final_confidence = weighted_confidence / total_weight
        else:
            final_score = 0.0
            final_confidence = 0.0
        
        # Determinar etiqueta de sentimiento
        if final_score > 0.3:
            label = "bullish"
        elif final_score < -0.3:
            label = "bearish"
        else:
            label = "neutral"
        
        return {
            "score": round(final_score, 3),
            "confidence": round(final_confidence, 3),
            "label": label,
            "sources_count": len(sentiment_results)
        }
    
    def _calculate_signal_strength(self, aggregated_sentiment: Dict[str, Any]) -> str:
        """
        Calcula la fuerza de la señal basada en sentimiento y confianza.
        
        Args:
            aggregated_sentiment: Sentimiento agregado
            
        Returns:
            str: Fuerza de la señal (weak, moderate, strong)
        """
        score = abs(aggregated_sentiment["score"])
        confidence = aggregated_sentiment["confidence"]
        
        signal_strength = score * confidence
        
        if signal_strength > 0.7:
            return "strong"
        elif signal_strength > 0.4:
            return "moderate"
        else:
            return "weak"
    
    def _calculate_sentiment_distribution(self, sentiment_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcula la distribución de sentimientos por fuente.
        
        Args:
            sentiment_results: Resultados por fuente
            
        Returns:
            dict: Distribución de sentimientos
        """
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        
        for result in sentiment_results.values():
            score = result.get("sentiment_score", 0.0)
            if score > 0.2:
                bullish_count += 1
            elif score < -0.2:
                bearish_count += 1
            else:
                neutral_count += 1
        
        total = bullish_count + bearish_count + neutral_count
        if total == 0:
            return {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
        
        return {
            "bullish": round(bullish_count / total, 2),
            "bearish": round(bearish_count / total, 2),
            "neutral": round(neutral_count / total, 2)
        }
    
    def _extract_key_factors(self, sentiment_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Extrae factores clave que influyen en el sentimiento.
        
        Args:
            sentiment_results: Resultados por fuente
            
        Returns:
            List[str]: Lista de factores clave
        """
        factors = []
        
        for source, result in sentiment_results.items():
            score = result.get("sentiment_score", 0.0)
            confidence = result.get("confidence", 0.0)
            
            if confidence > 0.8:
                if score > 0.5:
                    factors.append(f"Strong positive {source} sentiment")
                elif score < -0.5:
                    factors.append(f"Strong negative {source} sentiment")
            
            # Factores específicos por fuente
            if source == "news" and "key_topics" in result:
                factors.extend([f"News topic: {topic}" for topic in result["key_topics"][:2]])
            elif source == "social" and result.get("viral_factor", 0) > 0.6:
                factors.append("High social media viral activity")
            elif source == "onchain" and result.get("whale_activity", 0) > 0.7:
                factors.append("Significant whale activity detected")
        
        return factors[:5]  # Limitar a 5 factores principales
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Verifica si el cache es válido para una clave específica.
        
        Args:
            cache_key: Clave del cache
            
        Returns:
            bool: True si el cache es válido
        """
        if cache_key not in self._sentiment_cache:
            return False
        
        cached_data = self._sentiment_cache[cache_key]
        cache_time = cached_data["timestamp"]
        expiry_time = cache_time + timedelta(minutes=self._cache_expiry_minutes)
        
        return datetime.utcnow() < expiry_time
    
    async def _post_execute_hook(
        self,
        parameters: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Hook post-ejecución para logging adicional.
        
        Args:
            parameters: Parámetros de ejecución
            result: Resultado de la ejecución
        """
        symbol = parameters["symbol"]
        sentiment_score = result.get("sentiment_score", 0.0)
        confidence = result.get("confidence", 0.0)
        
        print(f"Sentiment analysis completed for {symbol}: {sentiment_score:.3f} (confidence: {confidence:.3f})")
