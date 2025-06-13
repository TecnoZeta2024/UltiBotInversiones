"""
Tests de integración para el motor de estrategias.

Este módulo valida la integración del sistema de estrategias:
- Carga dinámica de todas las estrategias
- Análisis de mercado con datos reales
- Performance de las 10 estrategias implementadas
- Integración con presets de escaneo
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal
from typing import List

# Strategy imports - todas las 10 estrategias
from ultibot_backend.strategies.macd_rsi_trend_rider import MACDRSITrendRider
from ultibot_backend.strategies.bollinger_squeeze_breakout import BollingerSqueezeBreakout
from ultibot_backend.strategies.triangular_arbitrage import TriangularArbitrage
from ultibot_backend.strategies.supertrend_volatility_filter import SuperTrendVolatilityFilter
from ultibot_backend.strategies.stochastic_rsi_overbought_oversold import StochasticRSIOverboughtOversold
from ultibot_backend.strategies.statistical_arbitrage_pairs import StatisticalArbitragePairs
from ultibot_backend.strategies.vwap_cross_strategy import VWAPCrossStrategy
from ultibot_backend.strategies.order_book_imbalance_scalper import OrderBookImbalanceScalper
from ultibot_backend.strategies.news_sentiment_spike_trader import NewsSentimentSpikeTrader
from ultibot_backend.strategies.onchain_metrics_divergence import OnChainMetricsDivergence

# Core imports
from ultibot_backend.strategies.base_strategy import BaseStrategy
from ultibot_backend.strategies.strategy_loader import load_strategies
from ultibot_backend.strategies.strategy_registry import StrategyRegistry
from ultibot_backend.core.domain_models.trading import AnalysisResult, TradingSignal, MarketSnapshot
from ultibot_backend.core.services.market_scanner import MarketScannerService

# Test fixtures
from tests.integration.fixtures import (
    create_bullish_market_snapshot,
    create_bearish_market_snapshot,
    create_sideways_market_snapshot,
    create_high_volatility_snapshot,
    create_arbitrage_opportunity_snapshots,
    create_news_sentiment_spike_data,
    create_onchain_metrics_data,
    get_test_symbols,
    create_multi_timeframe_data
)

class MockMarketDataProvider:
    """Mock provider de datos de mercado para tests."""
    
    def __init__(self):
        self.data_cache = {}
        
    def set_market_data(self, symbol: str, snapshot: MarketSnapshot):
        """Configura datos de mercado para un símbolo."""
        self.data_cache[symbol] = snapshot
    
    async def get_market_snapshot(self, symbol: str, timeframe: str = "1h") -> MarketSnapshot:
        """Obtiene snapshot de mercado."""
        if symbol in self.data_cache:
            return self.data_cache[symbol]
        
        # Datos por defecto si no están en caché
        return create_sideways_market_snapshot(symbol)
    
    async def get_all_symbols(self) -> List[str]:
        """Obtiene todos los símbolos disponibles."""
        return get_test_symbols()

class TestStrategyEngineIntegration:
    """Tests de integración del motor de estrategias."""
    
    @pytest.fixture
    def market_provider(self):
        """Fixture que proporciona un mock de market data provider."""
        return MockMarketDataProvider()
    
    @pytest.fixture
    async def strategy_registry(self, market_provider):
        """Fixture que crea un registry con todas las estrategias."""
        registry = StrategyRegistry()
        
        # Registrar todas las 10 estrategias con configuraciones por defecto
        strategies_config = {
            "macd_rsi_trend_rider": {
                "macd_fast_period": 12,
                "macd_slow_period": 26,
                "macd_signal_period": 9,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30
            },
            "bollinger_squeeze_breakout": {
                "bb_period": 20,
                "bb_std": 2.0,
                "kc_period": 20,
                "kc_multiplier": 1.5,
                "min_squeeze_periods": 5
            },
            "triangular_arbitrage": {
                "min_profit_threshold": 0.001,
                "max_position_size": 1000,
                "execution_timeout": 30
            },
            "supertrend_volatility_filter": {
                "supertrend_period": 14,
                "supertrend_multiplier": 3.0,
                "atr_period": 14,
                "volatility_threshold": 0.02
            },
            "stochastic_rsi_overbought_oversold": {
                "stoch_k_period": 14,
                "stoch_d_period": 3,
                "rsi_period": 14,
                "overbought_level": 80,
                "oversold_level": 20
            },
            "statistical_arbitrage_pairs": {
                "lookback_period": 60,
                "z_score_threshold": 2.0,
                "half_life_threshold": 10,
                "correlation_threshold": 0.8
            },
            "vwap_cross_strategy": {
                "vwap_period": 20,
                "price_deviation_threshold": 0.005,
                "volume_confirmation": True
            },
            "order_book_imbalance_scalper": {
                "imbalance_threshold": 0.7,
                "min_spread": 0.001,
                "max_position_time": 300
            },
            "news_sentiment_spike_trader": {
                "sentiment_threshold": 0.75,
                "volume_spike_threshold": 2.0,
                "news_velocity_threshold": 10
            },
            "onchain_metrics_divergence": {
                "whale_threshold": 1000,
                "exchange_flow_threshold": 500,
                "divergence_threshold": 0.15
            }
        }
        
        # Crear e instanciar estrategias
        strategy_classes = {
            "macd_rsi_trend_rider": MACDRSITrendRider,
            "bollinger_squeeze_breakout": BollingerSqueezeBreakout,
            "triangular_arbitrage": TriangularArbitrage,
            "supertrend_volatility_filter": SuperTrendVolatilityFilter,
            "stochastic_rsi_overbought_oversold": StochasticRSIOverboughtOversold,
            "statistical_arbitrage_pairs": StatisticalArbitragePairs,
            "vwap_cross_strategy": VWAPCrossStrategy,
            "order_book_imbalance_scalper": OrderBookImbalanceScalper,
            "news_sentiment_spike_trader": NewsSentimentSpikeTrader,
            "onchain_metrics_divergence": OnChainMetricsDivergence
        }
        
        for name, config in strategies_config.items():
            strategy_class = strategy_classes[name]
            strategy = strategy_class(config)
            await strategy.setup(market_provider)
            registry.register_strategy(name, strategy)
        
        return registry
    
    @pytest.mark.asyncio
    async def test_all_strategies_loaded(self, strategy_registry):
        """Test que todas las 10 estrategias se carguen correctamente."""
        strategies = strategy_registry.get_all_strategies()
        assert len(strategies) == 10, "Deben estar las 10 estrategias implementadas"
        
        expected_strategies = [
            "macd_rsi_trend_rider",
            "bollinger_squeeze_breakout", 
            "triangular_arbitrage",
            "supertrend_volatility_filter",
            "stochastic_rsi_overbought_oversold",
            "statistical_arbitrage_pairs",
            "vwap_cross_strategy",
            "order_book_imbalance_scalper",
            "news_sentiment_spike_trader",
            "onchain_metrics_divergence"
        ]
        
        for strategy_name in expected_strategies:
            assert strategy_name in strategies, f"Estrategia {strategy_name} no encontrada"
            strategy = strategies[strategy_name]
            assert isinstance(strategy, BaseStrategy)
            assert strategy.name == strategy_name
    
    @pytest.mark.asyncio
    async def test_strategies_analysis_with_different_market_conditions(self, strategy_registry, market_provider):
        """Test de análisis de estrategias bajo diferentes condiciones de mercado."""
        
        # Configurar diferentes escenarios de mercado
        market_scenarios = [
            ("bullish", create_bullish_market_snapshot("BTCUSDT")),
            ("bearish", create_bearish_market_snapshot("BTCUSDT")),
            ("sideways", create_sideways_market_snapshot("BTCUSDT")),
            ("high_volatility", create_high_volatility_snapshot("BTCUSDT"))
        ]
        
        strategies = strategy_registry.get_all_strategies()
        
        for scenario_name, market_snapshot in market_scenarios:
            market_provider.set_market_data("BTCUSDT", market_snapshot)
            
            for strategy_name, strategy in strategies.items():
                # Analizar mercado con cada estrategia
                analysis_result = await strategy.analyze(market_snapshot)
                
                # Verificaciones básicas
                assert isinstance(analysis_result, AnalysisResult)
                assert 0 <= analysis_result.confidence <= 1
                assert analysis_result.symbol == "BTCUSDT"
                
                # Verificar que las estrategias reaccionan apropiadamente a las condiciones
                if scenario_name == "high_volatility":
                    # Estrategias de volatilidad deben tener mayor confianza
                    if "volatility" in strategy_name or "scalper" in strategy_name:
                        assert analysis_result.confidence > 0.5
                
                elif scenario_name == "sideways":
                    # Estrategias de arbitraje deben funcionar mejor en mercados laterales
                    if "arbitrage" in strategy_name:
                        assert analysis_result.confidence >= 0.3
    
    @pytest.mark.asyncio
    async def test_strategy_performance_benchmarks(self, strategy_registry):
        """Test de performance: cada estrategia debe analizar en < 200ms."""
        strategies = strategy_registry.get_all_strategies()
        market_snapshot = create_bullish_market_snapshot("BTCUSDT")
        
        performance_results = {}
        
        for strategy_name, strategy in strategies.items():
            # Medir tiempo de análisis
            start_time = time.perf_counter()
            analysis_result = await strategy.analyze(market_snapshot)
            analysis_time = (time.perf_counter() - start_time) * 1000
            
            performance_results[strategy_name] = analysis_time
            
            # Verificar que cumple el SLA de performance
            assert analysis_time < 200, f"Estrategia {strategy_name} tardó {analysis_time:.2f}ms, debe ser < 200ms"
            assert analysis_result is not None
        
        # Reportar performance promedio
        avg_time = sum(performance_results.values()) / len(performance_results)
        print(f"\nPerformance promedio de estrategias: {avg_time:.2f}ms")
        
        # Verificar que el promedio sea bueno
        assert avg_time < 150, f"Performance promedio {avg_time:.2f}ms debe ser < 150ms"
    
    @pytest.mark.asyncio
    async def test_signal_generation_integration(self, strategy_registry):
        """Test de generación de señales de trading."""
        strategies = strategy_registry.get_all_strategies()
        
        # Test con mercado alcista fuerte
        bullish_snapshot = create_bullish_market_snapshot("BTCUSDT")
        
        signals_generated = 0
        
        for strategy_name, strategy in strategies.items():
            analysis_result = await strategy.analyze(bullish_snapshot)
            
            # Si la confianza es alta, debe generar señal
            if analysis_result.confidence > 0.7:
                signal = await strategy.generate_signal(analysis_result)
                
                if signal is not None:
                    signals_generated += 1
                    assert isinstance(signal, TradingSignal)
                    assert signal.action in ["BUY", "SELL", "HOLD"]
                    assert signal.symbol == "BTCUSDT"
                    assert signal.confidence > 0.7
                    assert signal.quantity > 0
        
        # Al menos algunas estrategias deben generar señales en mercado alcista
        assert signals_generated >= 3, f"Solo {signals_generated} estrategias generaron señales, esperadas >= 3"
    
    @pytest.mark.asyncio
    async def test_ai_powered_strategies_integration(self, strategy_registry):
        """Test específico para estrategias potenciadas por IA."""
        
        # Estrategias que usan herramientas MCP
        ai_strategies = [
            "news_sentiment_spike_trader",
            "onchain_metrics_divergence"
        ]
        
        strategies = strategy_registry.get_all_strategies()
        
        for strategy_name in ai_strategies:
            assert strategy_name in strategies, f"Estrategia IA {strategy_name} no encontrada"
            strategy = strategies[strategy_name]
            
            # Mock de herramientas MCP para estas estrategias
            mock_tool_hub = Mock()
            
            if strategy_name == "news_sentiment_spike_trader":
                # Configurar datos de sentimiento
                sentiment_data = create_news_sentiment_spike_data("BTCUSDT")
                market_snapshot = sentiment_data["market_snapshot"]
                
                # Mock de la herramienta de sentimiento
                mock_tool_hub.execute_tool = Mock(return_value={
                    "sentiment_score": sentiment_data["sentiment_data"]["overall_score"],
                    "news_velocity": sentiment_data["sentiment_data"]["news_velocity"]
                })
                
                # Inyectar herramienta mock en la estrategia
                strategy._tool_hub = mock_tool_hub
                
            elif strategy_name == "onchain_metrics_divergence":
                # Configurar datos on-chain
                onchain_data = create_onchain_metrics_data("BTCUSDT")
                market_snapshot = onchain_data["market_snapshot"]
                
                # Mock de la herramienta on-chain
                mock_tool_hub.execute_tool = Mock(return_value=onchain_data["onchain_data"])
                strategy._tool_hub = mock_tool_hub
            
            # Analizar con la estrategia IA
            analysis_result = await strategy.analyze(market_snapshot)
            
            # Verificar que el análisis IA funciona
            assert analysis_result.confidence > 0.5
            assert hasattr(analysis_result, 'ai_insights')
            
            # Verificar que se usaron herramientas MCP
            mock_tool_hub.execute_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_arbitrage_strategies_integration(self, strategy_registry):
        """Test específico para estrategias de arbitraje."""
        
        arbitrage_strategies = [
            "triangular_arbitrage",
            "statistical_arbitrage_pairs"
        ]
        
        strategies = strategy_registry.get_all_strategies()
        
        # Crear oportunidad de arbitraje
        btc_snapshot, eth_snapshot, btc_eth_snapshot = create_arbitrage_opportunity_snapshots()
        
        for strategy_name in arbitrage_strategies:
            strategy = strategies[strategy_name]
            
            if strategy_name == "triangular_arbitrage":
                # Configurar los 3 pares para arbitraje triangular
                strategy._market_data_cache = {
                    "BTCUSDT": btc_snapshot,
                    "ETHUSDT": eth_snapshot,
                    "BTCETH": btc_eth_snapshot
                }
                
                # Analizar oportunidad de arbitraje
                analysis_result = await strategy.analyze(btc_snapshot)
                
                # Debe detectar la oportunidad de arbitraje
                assert analysis_result.confidence > 0.6
                assert "arbitrage" in analysis_result.reasoning.lower()
                
            elif strategy_name == "statistical_arbitrage_pairs":
                # Configurar par de símbolos correlacionados
                strategy._pairs_data = {
                    ("BTCUSDT", "ETHUSDT"): {
                        "correlation": 0.85,
                        "zscore": 2.5,  # Oportunidad de pairs trading
                        "half_life": 8
                    }
                }
                
                analysis_result = await strategy.analyze(btc_snapshot)
                assert analysis_result.confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_concurrent_strategy_analysis(self, strategy_registry):
        """Test de análisis concurrente de múltiples estrategias."""
        strategies = strategy_registry.get_all_strategies()
        market_snapshot = create_high_volatility_snapshot("BTCUSDT")
        
        # Ejecutar todas las estrategias concurrentemente
        tasks = []
        for strategy_name, strategy in strategies.items():
            task = strategy.analyze(market_snapshot)
            tasks.append(task)
        
        # Medir tiempo total de análisis concurrente
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Verificar resultados
        assert len(results) == 10
        for result in results:
            assert isinstance(result, AnalysisResult)
            assert result.confidence >= 0
        
        # El análisis concurrente debe ser más rápido que secuencial
        # (estimado: < 500ms para todas las estrategias en paralelo)
        assert total_time < 500, f"Análisis concurrente tardó {total_time:.2f}ms, debe ser < 500ms"
    
    @pytest.mark.asyncio
    async def test_market_scanner_presets_integration(self, market_provider):
        """Test de integración con presets de escaneo de mercado."""
        
        # Configurar datos de mercado para diferentes símbolos
        symbols = get_test_symbols()
        scenarios = [
            create_high_volatility_snapshot,
            create_bullish_market_snapshot,
            create_sideways_market_snapshot
        ]
        
        for i, symbol in enumerate(symbols[:3]):
            scenario_func = scenarios[i % len(scenarios)]
            market_provider.set_market_data(symbol, scenario_func(symbol))
        
        # Crear scanner con presets
        scanner = MarketScannerService(market_provider)
        
        # Test presets específicos
        test_presets = [
            "explosive_volatility",
            "high_momentum", 
            "sleeping_giants"
        ]
        
        for preset_name in test_presets:
            # Escanear mercado con preset
            opportunities = await scanner.scan_market(preset_name)
            
            # Verificar que el scanner funciona
            assert isinstance(opportunities, list)
            # Puede o no encontrar oportunidades, depende de los datos mock
            
            if opportunities:
                for opp in opportunities:
                    assert hasattr(opp, 'symbol')
                    assert hasattr(opp, 'score')
                    assert opp.score >= 0
    
    @pytest.mark.asyncio
    async def test_strategy_error_handling(self, strategy_registry):
        """Test de manejo de errores en estrategias."""
        strategies = strategy_registry.get_all_strategies()
        
        # Test con datos de mercado malformados/incompletos
        incomplete_snapshot = create_bullish_market_snapshot("BTCUSDT")
        incomplete_snapshot.klines = []  # Quitar datos de velas
        
        for strategy_name, strategy in strategies.items():
            try:
                analysis_result = await strategy.analyze(incomplete_snapshot)
                
                # Si no falla, debe dar resultado con baja confianza
                if analysis_result is not None:
                    assert analysis_result.confidence <= 0.5
                    
            except Exception as e:
                # Si falla, debe ser un error manejado específicamente
                assert "insufficient data" in str(e).lower() or "invalid" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_strategy_diversity_validation(self, strategy_registry):
        """Test para validar la diversidad de estrategias implementadas."""
        strategies = strategy_registry.get_all_strategies()
        
        # Categorización de estrategias por tipo
        strategy_types = {
            "trend_following": ["macd_rsi_trend_rider", "supertrend_volatility_filter"],
            "mean_reversion": ["bollinger_squeeze_breakout", "stochastic_rsi_overbought_oversold"],
            "arbitrage": ["triangular_arbitrage", "statistical_arbitrage_pairs"],
            "volume_based": ["vwap_cross_strategy", "order_book_imbalance_scalper"],
            "ai_powered": ["news_sentiment_spike_trader", "onchain_metrics_divergence"]
        }
        
        # Verificar que cada categoría está representada
        for category, strategy_names in strategy_types.items():
            for strategy_name in strategy_names:
                assert strategy_name in strategies, f"Estrategia {strategy_name} de categoría {category} no encontrada"
        
        # Test de comportamiento diferente por categoría
        bullish_market = create_bullish_market_snapshot("BTCUSDT")
        
        category_responses = {}
        for category, strategy_names in strategy_types.items():
            confidences = []
            for strategy_name in strategy_names:
                strategy = strategies[strategy_name]
                result = await strategy.analyze(bullish_market)
                confidences.append(result.confidence)
            
            category_responses[category] = sum(confidences) / len(confidences)
        
        # Las estrategias de trend following deben responder mejor a mercados alcistas
        assert category_responses["trend_following"] > 0.5, "Estrategias de tendencia deben responder bien a mercado alcista"

if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"])
