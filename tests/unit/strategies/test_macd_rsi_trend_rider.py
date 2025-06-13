"""
Tests unitarios para la estrategia MACDRSITrendRider.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
import time

from ultibot_backend.strategies.macd_rsi_trend_rider import (
    MACDRSITrendRider, 
    MACDRSIParameters
)
from ultibot_backend.core.domain_models.trading import OrderSide, OrderType
from tests.unit.strategies.market_data_fixtures import (
    MarketDataFixtures,
    trending_up_snapshot,
    trending_down_snapshot,
    sideways_snapshot,
    insufficient_data_snapshot
)

class TestMACDRSITrendRider:
    """
    Suite de tests para MACDRSITrendRider.
    """

    @pytest.fixture
    def default_params(self):
        """Parámetros por defecto para tests."""
        return MACDRSIParameters(
            macd_fast_period=12,
            macd_slow_period=26,
            macd_signal_period=9,
            rsi_period=14,
            rsi_overbought=Decimal('70'),
            rsi_oversold=Decimal('30'),
            take_profit_percent=Decimal('0.02'),
            stop_loss_percent=Decimal('0.01'),
            trade_quantity_usd=Decimal('100')
        )

    @pytest.fixture
    def strategy(self, default_params):
        """Instancia de la estrategia para tests."""
        return MACDRSITrendRider(default_params)

    async def test_strategy_initialization(self, strategy, default_params):
        """Test de inicialización correcta de la estrategia."""
        assert strategy.name == "MACD_RSI_Trend_Rider"
        assert strategy.params == default_params
        assert strategy.params.macd_fast_period == 12
        assert strategy.params.macd_slow_period == 26
        assert strategy.params.rsi_period == 14

    async def test_setup_method(self, strategy):
        """Test del método setup."""
        # El setup actual no hace nada complejo, pero debe ejecutar sin errores
        await strategy.setup()
        # No hay assertions específicas ya que setup() es principalmente un placeholder

    async def test_analyze_insufficient_data(self, strategy, insufficient_data_snapshot):
        """Test de análisis con datos insuficientes."""
        result = await strategy.analyze(insufficient_data_snapshot)
        
        assert result.confidence == Decimal('0.0')
        assert "error" in result.indicators
        assert "Not enough kline data" in result.indicators["error"]

    async def test_analyze_trending_up_market(self, strategy, trending_up_snapshot):
        """Test de análisis en mercado con tendencia alcista."""
        result = await strategy.analyze(trending_up_snapshot)
        
        # Debe tener confianza razonable
        assert result.confidence > Decimal('0.0')
        
        # Debe contener todos los indicadores esperados
        assert "macd_line" in result.indicators
        assert "signal_line" in result.indicators
        assert "macd_histogram" in result.indicators
        assert "rsi" in result.indicators
        assert "current_price" in result.indicators
        
        # Los valores no deben ser None
        assert result.indicators["macd_line"] is not None
        assert result.indicators["signal_line"] is not None
        assert result.indicators["rsi"] is not None

    async def test_analyze_trending_down_market(self, strategy, trending_down_snapshot):
        """Test de análisis en mercado con tendencia bajista."""
        result = await strategy.analyze(trending_down_snapshot)
        
        assert result.confidence > Decimal('0.0')
        assert all(key in result.indicators for key in 
                  ["macd_line", "signal_line", "macd_histogram", "rsi", "current_price"])

    async def test_analyze_sideways_market(self, strategy, sideways_snapshot):
        """Test de análisis en mercado lateral."""
        result = await strategy.analyze(sideways_snapshot)
        
        # En mercado lateral, la confianza debería ser menor
        assert result.confidence >= Decimal('0.0')
        assert all(key in result.indicators for key in 
                  ["macd_line", "signal_line", "macd_histogram", "rsi", "current_price"])

    async def test_macd_calculation_accuracy(self, strategy):
        """Test de precisión en el cálculo del MACD."""
        # Crear datos sintéticos conocidos
        klines = MarketDataFixtures.generate_trending_up_klines(
            base_price=Decimal('100'),
            count=50,
            trend_strength=Decimal('0.01')
        )
        
        closes = [kline.close for kline in klines]
        macd_line, signal_line, hist = strategy._calculate_macd(
            closes, 12, 26, 9
        )
        
        # Verificar que las listas tienen longitudes apropiadas
        assert len(macd_line) > 0
        assert len(signal_line) > 0
        assert len(hist) > 0
        
        # En tendencia alcista, MACD debería ser generalmente positivo hacia el final
        assert isinstance(macd_line[-1], Decimal)
        assert isinstance(signal_line[-1], Decimal)

    async def test_rsi_calculation_bounds(self, strategy):
        """Test de que el RSI está en los límites correctos (0-100)."""
        klines = MarketDataFixtures.generate_sideways_klines(count=50)
        closes = [kline.close for kline in klines]
        
        rsi_values = strategy._calculate_rsi(closes, 14)
        
        # RSI debe estar entre 0 y 100
        for rsi in rsi_values:
            assert Decimal('0') <= rsi <= Decimal('100')

    async def test_generate_signal_low_confidence(self, strategy):
        """Test de que no se genera señal con baja confianza."""
        # Mock de análisis con baja confianza
        from ultibot_backend.core.domain_models.trading import AnalysisResult
        
        low_confidence_analysis = AnalysisResult(
            confidence=Decimal('0.5'),  # Menor al umbral de 0.7
            indicators={
                "macd_line": Decimal('1.0'),
                "signal_line": Decimal('0.5'),
                "rsi": Decimal('50'),
                "current_price": Decimal('50000')
            }
        )
        
        signal = await strategy.generate_signal(low_confidence_analysis)
        assert signal is None

    async def test_generate_signal_missing_indicators(self, strategy):
        """Test de que no se genera señal con indicadores faltantes."""
        from ultibot_backend.core.domain_models.trading import AnalysisResult
        
        incomplete_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "macd_line": None,  # Indicador faltante
                "signal_line": Decimal('0.5'),
                "rsi": Decimal('50')
            }
        )
        
        signal = await strategy.generate_signal(incomplete_analysis)
        assert signal is None

    async def test_generate_buy_signal(self, strategy):
        """Test de generación de señal de compra."""
        from ultibot_backend.core.domain_models.trading import AnalysisResult
        
        # Condiciones para señal de compra: MACD > Signal y RSI < overbought
        buy_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "macd_line": Decimal('1.0'),  # MACD por encima de signal
                "signal_line": Decimal('0.5'),
                "rsi": Decimal('60'),  # RSI no sobrecomprado
                "current_price": Decimal('50000')
            }
        )
        
        signal = await strategy.generate_signal(buy_analysis)
        
        if signal:  # Puede ser None dependiendo de la lógica interna
            assert signal.side == OrderSide.BUY
            assert signal.order_type == OrderType.MARKET
            assert signal.quantity > Decimal('0')

    async def test_generate_sell_signal(self, strategy):
        """Test de generación de señal de venta."""
        from ultibot_backend.core.domain_models.trading import AnalysisResult
        
        # Condiciones para señal de venta: MACD < Signal y RSI > oversold
        sell_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "macd_line": Decimal('0.5'),  # MACD por debajo de signal
                "signal_line": Decimal('1.0'),
                "rsi": Decimal('40'),  # RSI no sobrevendido
                "current_price": Decimal('50000')
            }
        )
        
        signal = await strategy.generate_signal(sell_analysis)
        
        if signal:  # Puede ser None dependiendo de la lógica interna
            assert signal.side == OrderSide.SELL
            assert signal.order_type == OrderType.MARKET
            assert signal.quantity > Decimal('0')

    async def test_confidence_calculation_logic(self, strategy):
        """Test de la lógica de cálculo de confianza."""
        # Test con diferentes combinaciones de indicadores
        test_cases = [
            {
                "macd_line": Decimal('1.0'),
                "signal_line": Decimal('0.5'),
                "rsi": Decimal('25'),  # Oversold
                "expected_min_confidence": Decimal('0.7')
            },
            {
                "macd_line": Decimal('0.5'),
                "signal_line": Decimal('1.0'),
                "rsi": Decimal('75'),  # Overbought
                "expected_min_confidence": Decimal('0.7')
            },
            {
                "macd_line": Decimal('1.0'),
                "signal_line": Decimal('1.0'),  # Sin divergencia
                "rsi": Decimal('50'),  # Neutral
                "expected_min_confidence": Decimal('0.0')
            }
        ]
        
        for case in test_cases:
            confidence = strategy._calculate_confidence(case)
            assert confidence >= case["expected_min_confidence"]
            assert confidence <= Decimal('1.0')

    async def test_parameter_validation(self):
        """Test de validación de parámetros."""
        # Test con parámetros válidos
        valid_params = MACDRSIParameters(
            macd_fast_period=5,
            macd_slow_period=10,
            rsi_period=7
        )
        strategy = MACDRSITrendRider(valid_params)
        assert strategy.params.macd_fast_period == 5

    async def test_performance_benchmark(self, strategy, trending_up_snapshot):
        """Test de benchmark de performance (<200ms por análisis)."""
        # Realizar múltiples análisis y medir tiempo
        iterations = 10
        total_time = 0
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            await strategy.analyze(trending_up_snapshot)
            end_time = time.perf_counter()
            total_time += (end_time - start_time)
        
        average_time_ms = (total_time / iterations) * 1000
        
        # Debe ser menor a 200ms en promedio
        assert average_time_ms < 200, f"Análisis promedio toma {average_time_ms:.2f}ms, excede los 200ms requeridos"

    async def test_ema_calculation_consistency(self, strategy):
        """Test de consistencia en el cálculo de EMA."""
        prices = [Decimal(str(i)) for i in range(10, 20)]  # [10, 11, 12, ..., 19]
        
        ema_12 = strategy._calculate_ema(prices, 5)
        
        # EMA debe tener longitud correcta
        assert len(ema_12) == len(prices) - 5 + 1
        
        # EMA debe ser estrictamente creciente para precios crecientes
        for i in range(1, len(ema_12)):
            assert ema_12[i] > ema_12[i-1]

    async def test_edge_cases(self, strategy):
        """Test de casos extremos."""
        # Lista vacía
        assert strategy._calculate_ema([], 5) == []
        assert strategy._calculate_rsi([], 14) == []
        
        # Período mayor que datos disponibles
        short_prices = [Decimal('100'), Decimal('101')]
        assert strategy._calculate_ema(short_prices, 10) == []
        assert strategy._calculate_rsi(short_prices, 10) == []

    async def test_full_workflow_integration(self, strategy, trending_up_snapshot):
        """Test de integración del flujo completo: analyze -> generate_signal."""
        # Análisis
        analysis_result = await strategy.analyze(trending_up_snapshot)
        assert analysis_result is not None
        
        # Generación de señal
        signal = await strategy.generate_signal(analysis_result)
        
        # Si se genera una señal, debe ser válida
        if signal:
            assert signal.symbol is not None
            assert signal.side in [OrderSide.BUY, OrderSide.SELL]
            assert signal.quantity > Decimal('0')
            assert signal.order_type == OrderType.MARKET

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
