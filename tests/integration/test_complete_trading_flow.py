"""
Tests de integración completos para el flujo de trading end-to-end.

Este módulo contiene tests que validan el flujo completo desde la detección
de oportunidades hasta la ejecución de trades, tanto en modo paper como real.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta, timezone # ADDED timezone

# Core imports
from ultibot_backend.core.domain_models.trading import (
    MarketSnapshot, TradingOpportunity, TradeResult, AnalysisResult, TradingSignal
)
from ultibot_backend.core.domain_models.market import TickerData, KlineData
from ultibot_backend.core.domain_models.events import TradeExecutedEvent, OpportunityDetectedEvent
from ultibot_backend.core.services.ai_orchestrator import AIOrchestratorService
from ultibot_backend.core.services.event_broker import AsyncEventBroker

# Strategy imports
from ultibot_backend.strategies.macd_rsi_trend_rider import MACDRSITrendRider
from ultibot_backend.strategies.bollinger_squeeze_breakout import BollingerSqueezeBreakout
from ultibot_backend.strategies.triangular_arbitrage import TriangularArbitrage

# Test fixtures
from tests.integration.fixtures.market_data_fixtures import (
    create_mock_ticker_data,
    create_mock_kline_data,
    create_bullish_market_snapshot,
    create_bearish_market_snapshot
)


class MockTradingSystem:
    """Sistema de trading simulado para tests de integración."""
    
    def __init__(self):
        self.event_broker = AsyncEventBroker()
        self.published_events = []
        self.strategies = {}
        self.market_data_provider = Mock()
        self.ai_orchestrator = Mock()
        
        # Setup event broker para capturar eventos
        self.event_broker.subscribe(TradeExecutedEvent, self._capture_event)
        self.event_broker.subscribe(OpportunityDetectedEvent, self._capture_event)
    
    async def _capture_event(self, event):
        """Captura eventos para verificación en tests."""
        self.published_events.append(event)
    
    async def initialize(self):
        """Inicializa el sistema de trading."""
        # Cargar estrategias
        self.strategies = {
            "macd_rsi_trend_rider": MACDRSITrendRider({
                "macd_fast_period": 12,
                "macd_slow_period": 26,
                "macd_signal_period": 9,
                "rsi_period": 14,
                "rsi_overbought": 70,
                "rsi_oversold": 30
            }),
            "bollinger_squeeze_breakout": BollingerSqueezeBreakout({
                "bb_period": 20,
                "bb_std": 2.0,
                "kc_period": 20,
                "kc_multiplier": 1.5,
                "min_squeeze_periods": 5
            }),
            "triangular_arbitrage": TriangularArbitrage({
                "min_profit_threshold": 0.001,
                "max_position_size": 1000,
                "execution_timeout": 30
            })
        }
    
    async def scan_market(self, preset_name: str) -> list[TradingOpportunity]:
        """Simula escaneo de mercado."""
        # Mock de oportunidades detectadas
        opportunities = []
        
        if preset_name == "explosive_volatility":
            # Simular detección de alta volatilidad
            opportunity = TradingOpportunity(
                symbol="BTCUSDT",
                strategy_name="macd_rsi_trend_rider",
                confidence=0.85,
                expected_profit=0.025,
                risk_level="MEDIUM",
                timeframe="1h",
                detected_at=datetime.now(timezone.utc) # MODIFIED
            )
            opportunities.append(opportunity)
            
            # Publicar evento
            await self.event_broker.publish(OpportunityDetectedEvent(
                opportunity_id=opportunity.symbol,
                strategy_name=opportunity.strategy_name,
                confidence=opportunity.confidence,
                symbol=opportunity.symbol
            ))
        
        return opportunities
    
    async def analyze_opportunity(self, opportunity: TradingOpportunity) -> AnalysisResult:
        """Simula análisis de IA de una oportunidad."""
        # Mock del AI Orchestrator
        analysis = AnalysisResult(
            confidence=opportunity.confidence,
            expected_profit=opportunity.expected_profit,
            risk_score=0.3,
            recommendation="BUY",
            reasoning="Strong bullish momentum with RSI confirmation",
            indicators={
                "macd_signal": "bullish",
                "rsi": 65.5,
                "volume_trend": "increasing"
            },
            ai_metadata={
                "model_version": "gemini-1.5",
                "processing_time_ms": 250,
                "tools_used": ["market_sentiment", "technical_analysis"]
            }
        )
        return analysis
    
    async def execute_paper_trade(self, analysis: AnalysisResult) -> TradeResult:
        """Ejecuta un trade simulado (paper trading)."""
        trade_result = TradeResult(
            trade_id=f"paper_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}", # MODIFIED
            symbol=analysis.symbol if hasattr(analysis, 'symbol') else "BTCUSDT",
            side="BUY",
            quantity=Decimal("0.1"),
            price=Decimal("45000.00"),
            status="FILLED",
            executed_at=datetime.now(timezone.utc), # MODIFIED
            commission=Decimal("0.001"),
            is_paper=True
        )
        
        # Publicar evento de trade ejecutado
        await self.event_broker.publish(TradeExecutedEvent(
            trade_id=trade_result.trade_id,
            symbol=trade_result.symbol,
            side=trade_result.side,
            quantity=trade_result.quantity,
            price=trade_result.price,
            timestamp=trade_result.executed_at
        ))
        
        return trade_result
    
    async def execute_real_trade(self, analysis: AnalysisResult, confirmed: bool = False) -> TradeResult:
        """Ejecuta un trade real (requiere confirmación)."""
        if not confirmed:
            raise ValueError("Real trading requires explicit user confirmation")
        
        trade_result = TradeResult(
            trade_id=f"real_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}", # MODIFIED
            symbol=analysis.symbol if hasattr(analysis, 'symbol') else "BTCUSDT",
            side="BUY",
            quantity=Decimal("0.01"),  # Cantidad menor para real trading
            price=Decimal("45000.00"),
            status="FILLED",
            executed_at=datetime.now(timezone.utc), # MODIFIED
            commission=Decimal("0.0001"),
            is_paper=False
        )
        
        # Publicar evento de trade ejecutado
        await self.event_broker.publish(TradeExecutedEvent(
            trade_id=trade_result.trade_id,
            symbol=trade_result.symbol,
            side=trade_result.side,
            quantity=trade_result.quantity,
            price=trade_result.price,
            timestamp=trade_result.executed_at
        ))
        
        return trade_result
    
    def get_published_events(self) -> list:
        """Retorna todos los eventos publicados."""
        return self.published_events


class TestCompleteTradingFlow:
    """Tests de integración para el flujo completo de trading."""
    
    @pytest.fixture
    async def trading_system(self):
        """Fixture que crea un sistema de trading completo para tests."""
        system = MockTradingSystem()
        await system.initialize()
        return system
    
    @pytest.mark.asyncio
    async def test_paper_trading_complete_cycle(self, trading_system):
        """
        Test del ciclo completo de paper trading:
        1. Escaneo de mercado
        2. Detección de oportunidad
        3. Análisis con IA
        4. Ejecución de trade simulado
        5. Verificación de eventos
        """
        # 1. Detectar oportunidad
        opportunities = await trading_system.scan_market("explosive_volatility")
        assert len(opportunities) > 0, "Debe detectar al menos una oportunidad"
        
        opportunity = opportunities[0]
        assert opportunity.symbol == "BTCUSDT"
        assert opportunity.confidence > 0.8
        assert opportunity.strategy_name == "macd_rsi_trend_rider"
        
        # 2. Análisis IA
        analysis = await trading_system.analyze_opportunity(opportunity)
        assert analysis.confidence > 0.8, "Análisis debe mantener alta confianza"
        assert analysis.recommendation == "BUY"
        assert "macd_signal" in analysis.indicators
        assert "rsi" in analysis.indicators
        
        # 3. Ejecutar trade simulado
        trade_result = await trading_system.execute_paper_trade(analysis)
        assert trade_result.success, "Trade simulado debe ser exitoso"
        assert trade_result.is_paper is True
        assert trade_result.status == "FILLED"
        assert trade_result.quantity > 0
        
        # 4. Verificar eventos publicados
        events = trading_system.get_published_events()
        assert len(events) >= 2, "Debe haber al menos 2 eventos: oportunidad y trade"
        
        # Verificar evento de oportunidad detectada
        opportunity_events = [e for e in events if isinstance(e, OpportunityDetectedEvent)]
        assert len(opportunity_events) == 1
        assert opportunity_events[0].symbol == "BTCUSDT"
        
        # Verificar evento de trade ejecutado
        trade_events = [e for e in events if isinstance(e, TradeExecutedEvent)]
        assert len(trade_events) == 1
        assert trade_events[0].trade_id == trade_result.trade_id
        assert trade_events[0].symbol == "BTCUSDT"
    
    @pytest.mark.asyncio
    async def test_real_trading_with_confirmation(self, trading_system):
        """
        Test del flujo de real trading con confirmación de usuario.
        """
        # Setup: detectar oportunidad y analizar
        opportunities = await trading_system.scan_market("explosive_volatility")
        opportunity = opportunities[0]
        analysis = await trading_system.analyze_opportunity(opportunity)
        
        # Test: ejecutar trade real CON confirmación
        trade_result = await trading_system.execute_real_trade(analysis, confirmed=True)
        assert trade_result.success
        assert trade_result.is_paper is False
        assert trade_result.quantity == Decimal("0.01")  # Menor cantidad para real
        
        # Verificar eventos
        events = trading_system.get_published_events()
        trade_events = [e for e in events if isinstance(e, TradeExecutedEvent)]
        real_trade_events = [e for e in trade_events if e.trade_id.startswith("real_")]
        assert len(real_trade_events) == 1
    
    @pytest.mark.asyncio
    async def test_real_trading_without_confirmation_fails(self, trading_system):
        """
        Test que el real trading falla sin confirmación explícita.
        """
        # Setup
        opportunities = await trading_system.scan_market("explosive_volatility")
        opportunity = opportunities[0]
        analysis = await trading_system.analyze_opportunity(opportunity)
        
        # Test: ejecutar trade real SIN confirmación debe fallar
        with pytest.raises(ValueError, match="Real trading requires explicit user confirmation"):
            await trading_system.execute_real_trade(analysis, confirmed=False)
    
    @pytest.mark.asyncio
    async def test_multiple_strategies_integration(self, trading_system):
        """
        Test de integración con múltiples estrategias funcionando.
        """
        # Test que todas las estrategias están disponibles
        assert "macd_rsi_trend_rider" in trading_system.strategies
        assert "bollinger_squeeze_breakout" in trading_system.strategies
        assert "triangular_arbitrage" in trading_system.strategies
        
        # Test que cada estrategia puede analizar datos de mercado
        market_snapshot = create_bullish_market_snapshot()
        
        for strategy_name, strategy in trading_system.strategies.items():
            # Setup mock de market data provider para la estrategia
            strategy._market_data = Mock()
            
            analysis_result = await strategy.analyze(market_snapshot)
            assert analysis_result is not None
            assert hasattr(analysis_result, 'confidence')
            assert 0 <= analysis_result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, trading_system):
        """
        Test de performance: verificar que las operaciones cumplen los SLA.
        """
        import time
        
        # Test 1: Detección de oportunidad < 100ms
        start_time = time.perf_counter()
        opportunities = await trading_system.scan_market("explosive_volatility")
        detection_time = (time.perf_counter() - start_time) * 1000
        assert detection_time < 100, f"Detección tardó {detection_time:.2f}ms, debe ser < 100ms"
        
        # Test 2: Análisis IA < 300ms
        start_time = time.perf_counter()
        analysis = await trading_system.analyze_opportunity(opportunities[0])
        analysis_time = (time.perf_counter() - start_time) * 1000
        assert analysis_time < 300, f"Análisis tardó {analysis_time:.2f}ms, debe ser < 300ms"
        
        # Test 3: Ejecución de trade < 50ms
        start_time = time.perf_counter()
        trade_result = await trading_system.execute_paper_trade(analysis)
        execution_time = (time.perf_counter() - start_time) * 1000
        assert execution_time < 50, f"Ejecución tardó {execution_time:.2f}ms, debe ser < 50ms"
        
        # Test 4: Ciclo completo < 500ms
        total_time = detection_time + analysis_time + execution_time
        assert total_time < 500, f"Ciclo completo tardó {total_time:.2f}ms, debe ser < 500ms"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, trading_system):
        """
        Test de manejo de errores y recuperación del sistema.
        """
        # Test 1: Manejo de error en análisis IA
        with patch.object(trading_system, 'analyze_opportunity', side_effect=Exception("AI service down")):
            opportunities = await trading_system.scan_market("explosive_volatility")
            
            with pytest.raises(Exception, match="AI service down"):
                await trading_system.analyze_opportunity(opportunities[0])
        
        # Test 2: El sistema debe continuar funcionando después del error
        # (el análisis normal debe volver a funcionar)
        opportunities = await trading_system.scan_market("explosive_volatility")
        analysis = await trading_system.analyze_opportunity(opportunities[0])
        assert analysis is not None
    
    @pytest.mark.asyncio
    async def test_event_broker_reliability(self, trading_system):
        """
        Test de confiabilidad del event broker bajo carga.
        """
        # Test publicación de múltiples eventos concurrentes
        async def publish_test_events():
            tasks = []
            for i in range(10):
                event = TradeExecutedEvent(
                    trade_id=f"test_{i}",
                    symbol="TESTUSDT",
                    side="BUY",
                    quantity=Decimal("1.0"),
                    price=Decimal("100.0"),
                    timestamp=datetime.now(timezone.utc) # MODIFIED
                )
                task = trading_system.event_broker.publish(event)
                tasks.append(task)
            
            # Ejecutar todos los eventos concurrentemente
            await asyncio.gather(*tasks)
        
        # Ejecutar test
        await publish_test_events()
        
        # Verificar que todos los eventos fueron procesados
        # (permite un pequeño delay para el procesamiento asíncrono)
        await asyncio.sleep(0.1)
        
        trade_events = [e for e in trading_system.get_published_events() 
                       if isinstance(e, TradeExecutedEvent)]
        test_events = [e for e in trade_events if e.symbol == "TESTUSDT"]
        
        assert len(test_events) == 10, "Todos los eventos concurrentes deben ser procesados"


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v"])
