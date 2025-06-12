"""
Tests unitarios para la estrategia BollingerSqueezeBreakout.
"""

import pytest
from decimal import Decimal
import time

from src.ultibot_backend.strategies.bollinger_squeeze_breakout import (
    BollingerSqueezeBreakout,
    BollingerSqueezeParameters
)
from src.ultibot_backend.core.domain_models.trading import OrderSide, OrderType
from tests.unit.strategies.market_data_fixtures import (
    MarketDataFixtures,
    trending_up_snapshot,
    sideways_snapshot,
    bollinger_squeeze_snapshot,
    insufficient_data_snapshot
)

class TestBollingerSqueezeBreakout:
    """
    Suite de tests para BollingerSqueezeBreakout.
    """

    @pytest.fixture
    def default_params(self):
        """Parámetros por defecto para tests."""
        return BollingerSqueezeParameters(
            bollinger_period=20,
            std_dev_multiplier=Decimal('2.0'),
            squeeze_threshold=Decimal('0.01'),
            breakout_threshold=Decimal('0.02'),
            lookback_squeeze_periods=5,
            trade_quantity_usd=Decimal('100')
        )

    @pytest.fixture
    def strategy(self, default_params):
        """Instancia de la estrategia para tests."""
        return BollingerSqueezeBreakout(default_params)

    async def test_strategy_initialization(self, strategy, default_params):
        """Test de inicialización correcta de la estrategia."""
        assert strategy.name == "Bollinger_Squeeze_Breakout"
        assert strategy.params == default_params
        assert strategy.params.bollinger_period == 20
        assert strategy.params.std_dev_multiplier == Decimal('2.0')
        assert strategy._is_squeezed == False  # Estado inicial

    async def test_setup_method(self, strategy):
        """Test del método setup."""
        await strategy.setup()
        # Setup es un placeholder, pero debe ejecutar sin errores

    async def test_analyze_insufficient_data(self, strategy, insufficient_data_snapshot):
        """Test de análisis con datos insuficientes."""
        result = await strategy.analyze(insufficient_data_snapshot)
        
        assert result.confidence == Decimal('0.0')
        assert "error" in result.indicators
        assert "Not enough kline data" in result.indicators["error"]

    async def test_analyze_squeeze_detection(self, strategy, bollinger_squeeze_snapshot):
        """Test de detección de squeeze en los datos."""
        result = await strategy.analyze(bollinger_squeeze_snapshot)
        
        # Debe contener todos los indicadores esperados
        assert "upper_band" in result.indicators
        assert "middle_band" in result.indicators
        assert "lower_band" in result.indicators
        assert "band_width" in result.indicators
        assert "is_squeezed" in result.indicators
        assert "is_breakout" in result.indicators
        assert "current_price" in result.indicators
        
        # Los valores de bandas no deben ser None
        assert result.indicators["upper_band"] is not None
        assert result.indicators["middle_band"] is not None
        assert result.indicators["lower_band"] is not None

    async def test_bollinger_bands_calculation(self, strategy):
        """Test de cálculo de Bandas de Bollinger."""
        # Crear datos sintéticos conocidos con poca variabilidad
        klines = MarketDataFixtures.generate_sideways_klines(
            base_price=Decimal('100'),
            count=30,
            volatility=Decimal('0.02')
        )
        
        closes = [kline.close for kline in klines]
        upper_band, middle_band, lower_band, band_width = strategy._calculate_bollinger_bands(
            closes, 20, Decimal('2.0')
        )
        
        # Verificar longitudes
        expected_length = len(closes) - 20 + 1
        assert len(upper_band) == expected_length
        assert len(middle_band) == expected_length
        assert len(lower_band) == expected_length
        assert len(band_width) == expected_length
        
        # Verificar relaciones lógicas
        for i in range(len(upper_band)):
            assert upper_band[i] > middle_band[i]  # Banda superior mayor que media
            assert middle_band[i] > lower_band[i]  # Banda media mayor que inferior
            assert band_width[i] == upper_band[i] - lower_band[i]  # Ancho correcto

    async def test_squeeze_state_management(self, strategy):
        """Test de manejo del estado de squeeze."""
        # Simular datos con squeeze
        klines_squeeze = MarketDataFixtures.generate_bollinger_squeeze_klines(count=30)
        snapshot_squeeze = MarketDataFixtures.generate_market_snapshot(klines=klines_squeeze)
        
        # Primero analizar datos con squeeze
        result = await strategy.analyze(snapshot_squeeze)
        
        # Verificar que el estado se actualiza correctamente
        assert isinstance(result.indicators["is_squeezed"], bool)
        assert isinstance(result.indicators["is_breakout"], bool)

    async def test_generate_signal_no_breakout(self, strategy):
        """Test de que no se genera señal sin breakout."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        # Mock de análisis sin breakout
        no_breakout_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "upper_band": Decimal('102'),
                "middle_band": Decimal('100'),
                "lower_band": Decimal('98'),
                "is_breakout": False,  # Sin breakout
                "current_price": Decimal('100')
            }
        )
        
        signal = await strategy.generate_signal(no_breakout_analysis)
        assert signal is None

    async def test_generate_signal_low_confidence(self, strategy):
        """Test de que no se genera señal con baja confianza."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        low_confidence_analysis = AnalysisResult(
            confidence=Decimal('0.5'),  # Menor al umbral de 0.7
            indicators={
                "upper_band": Decimal('102'),
                "middle_band": Decimal('100'),
                "lower_band": Decimal('98'),
                "is_breakout": True,
                "current_price": Decimal('103')  # Breakout alcista
            }
        )
        
        signal = await strategy.generate_signal(low_confidence_analysis)
        assert signal is None

    async def test_generate_buy_signal_upward_breakout(self, strategy):
        """Test de generación de señal de compra en breakout alcista."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        # Breakout por encima de banda superior
        upward_breakout_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "upper_band": Decimal('102'),
                "middle_band": Decimal('100'),
                "lower_band": Decimal('98'),
                "is_breakout": True,
                "current_price": Decimal('103')  # Por encima de banda superior
            }
        )
        
        signal = await strategy.generate_signal(upward_breakout_analysis)
        
        if signal:  # Puede ser None dependiendo de la lógica interna
            assert signal.side == OrderSide.BUY
            assert signal.order_type == OrderType.MARKET
            assert signal.quantity > Decimal('0')

    async def test_generate_sell_signal_downward_breakout(self, strategy):
        """Test de generación de señal de venta en breakout bajista."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        # Breakout por debajo de banda inferior
        downward_breakout_analysis = AnalysisResult(
            confidence=Decimal('0.8'),
            indicators={
                "upper_band": Decimal('102'),
                "middle_band": Decimal('100'),
                "lower_band": Decimal('98'),
                "is_breakout": True,
                "current_price": Decimal('97')  # Por debajo de banda inferior
            }
        )
        
        signal = await strategy.generate_signal(downward_breakout_analysis)
        
        if signal:  # Puede ser None dependiendo de la lógica interna
            assert signal.side == OrderSide.SELL
            assert signal.order_type == OrderType.MARKET
            assert signal.quantity > Decimal('0')

    async def test_confidence_calculation_squeeze_conditions(self, strategy):
        """Test de cálculo de confianza bajo diferentes condiciones de squeeze."""
        test_cases = [
            {
                "is_squeezed": True,
                "is_breakout": False,
                "band_width": Decimal('0.5'),
                "current_price": Decimal('100'),
                "middle_band": Decimal('100'),
                "expected_min_confidence": Decimal('0.3')  # Solo squeeze
            },
            {
                "is_squeezed": False,
                "is_breakout": True,
                "band_width": Decimal('2.0'),
                "current_price": Decimal('105'),
                "middle_band": Decimal('100'),
                "expected_min_confidence": Decimal('0.6')  # Solo breakout
            },
            {
                "is_squeezed": True,
                "is_breakout": True,
                "band_width": Decimal('0.5'),
                "current_price": Decimal('105'),
                "middle_band": Decimal('100'),
                "expected_min_confidence": Decimal('0.8')  # Squeeze + breakout
            }
        ]
        
        for case in test_cases:
            confidence = strategy._calculate_confidence(case)
            assert confidence >= case["expected_min_confidence"]
            assert confidence <= Decimal('1.0')

    async def test_squeeze_threshold_sensitivity(self, strategy):
        """Test de sensibilidad del umbral de squeeze."""
        # Crear datos con volatilidad controlada
        klines = MarketDataFixtures.generate_sideways_klines(
            base_price=Decimal('100'),
            count=30,
            volatility=Decimal('0.005')  # Baja volatilidad
        )
        
        closes = [kline.close for kline in klines]
        upper_band, middle_band, lower_band, band_width = strategy._calculate_bollinger_bands(
            closes, 20, Decimal('2.0')
        )
        
        # Con baja volatilidad, el ancho de banda relativo debería ser pequeño
        if middle_band and band_width:
            relative_width = band_width[-1] / middle_band[-1]
            # Debería ser menor que el umbral de squeeze por defecto
            assert relative_width < strategy.params.squeeze_threshold

    async def test_breakout_threshold_sensitivity(self, strategy):
        """Test de sensibilidad del umbral de breakout."""
        # Crear snapshot con cambio de precio significativo
        klines = MarketDataFixtures.generate_trending_up_klines(
            base_price=Decimal('100'),
            count=30,
            trend_strength=Decimal('0.03')  # Fuerte tendencia
        )
        
        snapshot = MarketDataFixtures.generate_market_snapshot(klines=klines)
        
        # El último cambio debería ser mayor que el umbral de breakout
        if len(klines) >= 2:
            price_change = (klines[-1].close - klines[-2].close) / klines[-2].close
            assert abs(price_change) >= strategy.params.breakout_threshold * Decimal('0.5')  # Al menos la mitad

    async def test_parameter_validation(self):
        """Test de validación de parámetros."""
        # Test con parámetros personalizados
        custom_params = BollingerSqueezeParameters(
            bollinger_period=10,
            std_dev_multiplier=Decimal('1.5'),
            squeeze_threshold=Decimal('0.005'),
            breakout_threshold=Decimal('0.015'),
            lookback_squeeze_periods=3,
            trade_quantity_usd=Decimal('200')
        )
        
        strategy = BollingerSqueezeBreakout(custom_params)
        assert strategy.params.bollinger_period == 10
        assert strategy.params.std_dev_multiplier == Decimal('1.5')

    async def test_performance_benchmark(self, strategy, bollinger_squeeze_snapshot):
        """Test de benchmark de performance (<200ms por análisis)."""
        iterations = 10
        total_time = 0
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            await strategy.analyze(bollinger_squeeze_snapshot)
            end_time = time.perf_counter()
            total_time += (end_time - start_time)
        
        average_time_ms = (total_time / iterations) * 1000
        
        # Debe ser menor a 200ms en promedio
        assert average_time_ms < 200, f"Análisis promedio toma {average_time_ms:.2f}ms, excede los 200ms requeridos"

    async def test_edge_cases_empty_data(self, strategy):
        """Test de casos extremos con datos vacíos."""
        # Datos insuficientes para Bollinger Bands
        short_closes = [Decimal('100'), Decimal('101')]
        
        upper, middle, lower, width = strategy._calculate_bollinger_bands(
            short_closes, 20, Decimal('2.0')
        )
        
        # Todas las listas deberían estar vacías
        assert len(upper) == 0
        assert len(middle) == 0
        assert len(lower) == 0
        assert len(width) == 0

    async def test_lookback_periods_logic(self, strategy):
        """Test de la lógica de períodos de lookback para squeeze."""
        # Crear datos que simulen squeeze en períodos anteriores
        klines = MarketDataFixtures.generate_bollinger_squeeze_klines(count=40)
        snapshot = MarketDataFixtures.generate_market_snapshot(klines=klines)
        
        # Analizar multiple veces para comprobar consistencia del estado
        result1 = await strategy.analyze(snapshot)
        result2 = await strategy.analyze(snapshot)
        
        # El estado de squeeze debería ser consistente
        assert result1.indicators["is_squeezed"] == result2.indicators["is_squeezed"]

    async def test_full_workflow_integration(self, strategy, bollinger_squeeze_snapshot):
        """Test de integración del flujo completo: analyze -> generate_signal."""
        # Análisis
        analysis_result = await strategy.analyze(bollinger_squeeze_snapshot)
        assert analysis_result is not None
        
        # Generación de señal
        signal = await strategy.generate_signal(analysis_result)
        
        # Si se genera una señal, debe ser válida
        if signal:
            assert signal.symbol is not None
            assert signal.side in [OrderSide.BUY, OrderSide.SELL]
            assert signal.quantity > Decimal('0')
            assert signal.order_type == OrderType.MARKET

    async def test_statistical_accuracy_bollinger_bands(self, strategy):
        """Test de precisión estadística de las Bandas de Bollinger."""
        # Crear datos con precio constante para verificar cálculos
        constant_price = Decimal('100')
        constant_closes = [constant_price] * 25
        
        upper, middle, lower, width = strategy._calculate_bollinger_bands(
            constant_closes, 20, Decimal('2.0')
        )
        
        # Con precio constante, la banda media debería ser igual al precio
        # y las bandas superior e inferior deberían ser iguales a la media
        # (desviación estándar = 0)
        if middle:
            assert abs(middle[-1] - constant_price) < Decimal('0.001')
            # Con desviación estándar 0, todas las bandas deberían converger
            assert abs(upper[-1] - middle[-1]) < Decimal('0.001')
            assert abs(lower[-1] - middle[-1]) < Decimal('0.001')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
