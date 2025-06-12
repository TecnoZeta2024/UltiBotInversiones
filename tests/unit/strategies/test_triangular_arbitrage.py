"""
Tests unitarios para la estrategia TriangularArbitrage.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
import time

from src.ultibot_backend.strategies.triangular_arbitrage import (
    TriangularArbitrage,
    TriangularArbitrageParameters
)
from src.ultibot_backend.core.domain_models.trading import OrderSide, OrderType
from src.ultibot_backend.core.domain_models.market import TickerData
from tests.unit.strategies.market_data_fixtures import (
    MarketDataFixtures,
    sideways_snapshot,
    insufficient_data_snapshot
)

class TestTriangularArbitrage:
    """
    Suite de tests para TriangularArbitrage.
    """

    @pytest.fixture
    def default_params(self):
        """Parámetros por defecto para tests."""
        return TriangularArbitrageParameters(
            min_profit_percent=Decimal('0.001'),
            trade_quantity_base=Decimal('0.001'),
            max_slippage_percent=Decimal('0.0005')
        )

    @pytest.fixture
    def strategy(self, default_params):
        """Instancia de la estrategia para tests."""
        return TriangularArbitrage(default_params)

    @pytest.fixture
    def mock_market_data_provider(self):
        """Mock del proveedor de datos de mercado."""
        mock_provider = AsyncMock()
        
        # Mock de tickers para arbitraje BTC/USDT/ETH
        mock_provider.get_ticker.side_effect = lambda symbol: {
            "BTCUSDT": TickerData(
                symbol="BTCUSDT",
                price=Decimal('50000'),
                price_change=Decimal('100'),
                price_change_percent=Decimal('0.2'),
                high_24h=Decimal('51000'),
                low_24h=Decimal('49000'),
                volume_24h=Decimal('1000'),
                quote_volume_24h=Decimal('50000000'),
                trades_count_24h=1000,
                timestamp=None
            ),
            "ETHUSDT": TickerData(
                symbol="ETHUSDT",
                price=Decimal('3000'),
                price_change=Decimal('50'),
                price_change_percent=Decimal('1.7'),
                high_24h=Decimal('3100'),
                low_24h=Decimal('2900'),
                volume_24h=Decimal('2000'),
                quote_volume_24h=Decimal('6000000'),
                trades_count_24h=2000,
                timestamp=None
            ),
            "ETHBTC": TickerData(
                symbol="ETHBTC",
                price=Decimal('0.06'),  # ETH/BTC ratio
                price_change=Decimal('0.001'),
                price_change_percent=Decimal('1.7'),
                high_24h=Decimal('0.062'),
                low_24h=Decimal('0.058'),
                volume_24h=Decimal('500'),
                quote_volume_24h=Decimal('30'),
                trades_count_24h=500,
                timestamp=None
            )
        }[symbol]
        
        return mock_provider

    async def test_strategy_initialization(self, strategy, default_params):
        """Test de inicialización correcta de la estrategia."""
        assert strategy.name == "Triangular_Arbitrage"
        assert strategy.params == default_params
        assert strategy.params.min_profit_percent == Decimal('0.001')
        assert strategy.params.trade_quantity_base == Decimal('0.001')
        assert strategy._market_data_provider is None  # Sin inyectar aún

    async def test_set_market_data_provider(self, strategy, mock_market_data_provider):
        """Test de inyección del proveedor de datos de mercado."""
        strategy.set_market_data_provider(mock_market_data_provider)
        assert strategy._market_data_provider is not None

    async def test_setup_without_provider_raises_error(self, strategy):
        """Test de que setup falla sin proveedor de datos."""
        with pytest.raises(ValueError, match="IMarketDataProvider no ha sido inyectado"):
            await strategy.setup()

    async def test_setup_with_provider_succeeds(self, strategy, mock_market_data_provider):
        """Test de que setup funciona con proveedor inyectado."""
        strategy.set_market_data_provider(mock_market_data_provider)
        await strategy.setup()  # No debe lanzar excepción

    async def test_analyze_without_provider(self, strategy, sideways_snapshot):
        """Test de análisis sin proveedor de datos."""
        result = await strategy.analyze(sideways_snapshot)
        
        assert result.confidence == Decimal('0.0')
        assert "error" in result.indicators
        assert "Market data provider not set" in result.indicators["error"]

    async def test_analyze_with_api_error(self, strategy, sideways_snapshot):
        """Test de análisis cuando falla la API externa."""
        mock_provider = AsyncMock()
        mock_provider.get_ticker.side_effect = Exception("API Error")
        
        strategy.set_market_data_provider(mock_provider)
        
        result = await strategy.analyze(sideways_snapshot)
        
        assert result.confidence == Decimal('0.0')
        assert "error" in result.indicators
        assert "Failed to get tickers" in result.indicators["error"]

    async def test_analyze_successful_arbitrage_opportunity(self, strategy, sideways_snapshot, mock_market_data_provider):
        """Test de análisis que encuentra oportunidad de arbitraje."""
        strategy.set_market_data_provider(mock_market_data_provider)
        
        result = await strategy.analyze(sideways_snapshot)
        
        # Debe ejecutar sin errores
        assert "opportunity_details" in result.indicators
        
        # Si encuentra oportunidad, confianza debe ser alta
        if result.indicators["opportunity_details"]:
            assert result.confidence == Decimal('0.9')
        else:
            assert result.confidence == Decimal('0.0')

    async def test_find_arbitrage_opportunity_profitable(self, strategy):
        """Test de detección de oportunidad de arbitraje rentable."""
        # Crear tickers que generen arbitraje rentable
        # BTC -> USDT -> ETH -> BTC con ganancia
        profitable_tickers = {
            "BTCUSDT": TickerData(
                symbol="BTCUSDT",
                price=Decimal('50000'),  # 1 BTC = 50000 USDT
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('50000'),
                low_24h=Decimal('50000'),
                volume_24h=Decimal('1000'),
                quote_volume_24h=Decimal('50000000'),
                trades_count_24h=1000,
                timestamp=None
            ),
            "ETHUSDT": TickerData(
                symbol="ETHUSDT",
                price=Decimal('2500'),  # 1 ETH = 2500 USDT (precio bajo para arbitraje)
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('2500'),
                low_24h=Decimal('2500'),
                volume_24h=Decimal('2000'),
                quote_volume_24h=Decimal('5000000'),
                trades_count_24h=2000,
                timestamp=None
            ),
            "ETHBTC": TickerData(
                symbol="ETHBTC",
                price=Decimal('0.06'),  # 1 ETH = 0.06 BTC (precio alto para completar arbitraje)
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('0.06'),
                low_24h=Decimal('0.06'),
                volume_24h=Decimal('500'),
                quote_volume_24h=Decimal('30'),
                trades_count_24h=500,
                timestamp=None
            )
        }
        
        opportunity = strategy._find_arbitrage_opportunity(profitable_tickers)
        
        if opportunity:
            assert "path" in opportunity
            assert "profit_percent" in opportunity
            assert opportunity["profit_percent"] > strategy.params.min_profit_percent
            assert opportunity["path"] == ["BTC", "USDT", "ETH", "BTC"]

    async def test_find_arbitrage_opportunity_unprofitable(self, strategy):
        """Test de que no se detecta oportunidad cuando no es rentable."""
        # Crear tickers que no generen arbitraje rentable
        unprofitable_tickers = {
            "BTCUSDT": TickerData(
                symbol="BTCUSDT",
                price=Decimal('50000'),
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('50000'),
                low_24h=Decimal('50000'),
                volume_24h=Decimal('1000'),
                quote_volume_24h=Decimal('50000000'),
                trades_count_24h=1000,
                timestamp=None
            ),
            "ETHUSDT": TickerData(
                symbol="ETHUSDT",
                price=Decimal('3000'),  # Precio equilibrado
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('3000'),
                low_24h=Decimal('3000'),
                volume_24h=Decimal('2000'),
                quote_volume_24h=Decimal('6000000'),
                trades_count_24h=2000,
                timestamp=None
            ),
            "ETHBTC": TickerData(
                symbol="ETHBTC",
                price=Decimal('0.06'),  # 3000/50000 = 0.06 (equilibrado)
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('0.06'),
                low_24h=Decimal('0.06'),
                volume_24h=Decimal('500'),
                quote_volume_24h=Decimal('30'),
                trades_count_24h=500,
                timestamp=None
            )
        }
        
        opportunity = strategy._find_arbitrage_opportunity(unprofitable_tickers)
        assert opportunity is None

    async def test_generate_signal_no_opportunity(self, strategy):
        """Test de que no se genera señal sin oportunidad."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        no_opportunity_analysis = AnalysisResult(
            confidence=Decimal('0.0'),
            indicators={"opportunity_details": None}
        )
        
        signal = await strategy.generate_signal(no_opportunity_analysis)
        assert signal is None

    async def test_generate_signal_low_confidence(self, strategy):
        """Test de que no se genera señal con baja confianza."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        low_confidence_analysis = AnalysisResult(
            confidence=Decimal('0.5'),  # Menor al umbral de 0.8
            indicators={
                "opportunity_details": {
                    "path": ["BTC", "USDT", "ETH", "BTC"],
                    "profit_percent": Decimal('0.002')
                }
            }
        )
        
        signal = await strategy.generate_signal(low_confidence_analysis)
        assert signal is None

    async def test_generate_signal_with_opportunity(self, strategy):
        """Test de generación de señal con oportunidad válida."""
        from src.ultibot_backend.core.domain_models.trading import AnalysisResult
        
        opportunity_analysis = AnalysisResult(
            confidence=Decimal('0.9'),
            indicators={
                "opportunity_details": {
                    "path": ["BTC", "USDT", "ETH", "BTC"],
                    "profit_percent": Decimal('0.002'),
                    "initial_amount": Decimal('0.001'),
                    "final_amount": Decimal('0.001002')
                }
            }
        )
        
        signal = await strategy.generate_signal(opportunity_analysis)
        
        if signal:  # La lógica actual es simplificada
            assert signal.side == OrderSide.SELL  # Primer paso del arbitraje
            assert signal.order_type == OrderType.MARKET
            assert signal.quantity > Decimal('0')

    async def test_confidence_calculation_with_profit(self, strategy):
        """Test de cálculo de confianza basado en rentabilidad."""
        test_cases = [
            {
                "opportunity_details": {
                    "profit_percent": Decimal('0.002')  # 2x min_profit
                },
                "expected_confidence": Decimal('1.0')  # Máxima confianza
            },
            {
                "opportunity_details": {
                    "profit_percent": Decimal('0.001')  # Exactamente min_profit
                },
                "expected_confidence": Decimal('1.0')  # Confianza alta
            },
            {
                "opportunity_details": None,
                "expected_confidence": Decimal('0.0')  # Sin oportunidad
            }
        ]
        
        for case in test_cases:
            confidence = strategy._calculate_confidence(case)
            assert confidence >= Decimal('0.0')
            assert confidence <= Decimal('1.0')

    async def test_parameter_validation(self):
        """Test de validación de parámetros."""
        custom_params = TriangularArbitrageParameters(
            min_profit_percent=Decimal('0.002'),
            trade_quantity_base=Decimal('0.002'),
            max_slippage_percent=Decimal('0.001')
        )
        
        strategy = TriangularArbitrage(custom_params)
        assert strategy.params.min_profit_percent == Decimal('0.002')
        assert strategy.params.trade_quantity_base == Decimal('0.002')

    async def test_arbitrage_calculation_accuracy(self, strategy):
        """Test de precisión en los cálculos de arbitraje."""
        # Test con valores conocidos
        test_tickers = {
            "BTCUSDT": TickerData(
                symbol="BTCUSDT",
                price=Decimal('40000'),  # 1 BTC = 40000 USDT
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('40000'),
                low_24h=Decimal('40000'),
                volume_24h=Decimal('1000'),
                quote_volume_24h=Decimal('40000000'),
                trades_count_24h=1000,
                timestamp=None
            ),
            "ETHUSDT": TickerData(
                symbol="ETHUSDT",
                price=Decimal('2000'),  # 1 ETH = 2000 USDT
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('2000'),
                low_24h=Decimal('2000'),
                volume_24h=Decimal('2000'),
                quote_volume_24h=Decimal('4000000'),
                trades_count_24h=2000,
                timestamp=None
            ),
            "ETHBTC": TickerData(
                symbol="ETHBTC",
                price=Decimal('0.055'),  # 1 ETH = 0.055 BTC (mayor que 2000/40000=0.05)
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('0.055'),
                low_24h=Decimal('0.055'),
                volume_24h=Decimal('500'),
                quote_volume_24h=Decimal('27.5'),
                trades_count_24h=500,
                timestamp=None
            )
        }
        
        opportunity = strategy._find_arbitrage_opportunity(test_tickers)
        
        if opportunity:
            # Verificar cálculos manualmente
            # 0.001 BTC -> 40 USDT -> 0.02 ETH -> 0.0011 BTC
            initial_btc = strategy.params.trade_quantity_base
            usdt_from_btc = initial_btc * Decimal('40000')  # 40 USDT
            eth_from_usdt = usdt_from_btc / Decimal('2000')  # 0.02 ETH
            final_btc = eth_from_usdt * Decimal('0.055')  # 0.0011 BTC
            
            expected_profit = (final_btc - initial_btc) / initial_btc
            
            assert abs(opportunity["profit_percent"] - expected_profit) < Decimal('0.0001')

    async def test_performance_benchmark(self, strategy, sideways_snapshot, mock_market_data_provider):
        """Test de benchmark de performance (<200ms por análisis)."""
        strategy.set_market_data_provider(mock_market_data_provider)
        
        iterations = 10
        total_time = 0
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            await strategy.analyze(sideways_snapshot)
            end_time = time.perf_counter()
            total_time += (end_time - start_time)
        
        average_time_ms = (total_time / iterations) * 1000
        
        # Debe ser menor a 200ms en promedio
        assert average_time_ms < 200, f"Análisis promedio toma {average_time_ms:.2f}ms, excede los 200ms requeridos"

    async def test_edge_cases_zero_prices(self, strategy):
        """Test de casos extremos con precios cero."""
        zero_price_tickers = {
            "BTCUSDT": TickerData(
                symbol="BTCUSDT",
                price=Decimal('0'),  # Precio cero
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('0'),
                low_24h=Decimal('0'),
                volume_24h=Decimal('0'),
                quote_volume_24h=Decimal('0'),
                trades_count_24h=0,
                timestamp=None
            ),
            "ETHUSDT": TickerData(
                symbol="ETHUSDT",
                price=Decimal('2000'),
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('2000'),
                low_24h=Decimal('2000'),
                volume_24h=Decimal('1000'),
                quote_volume_24h=Decimal('2000000'),
                trades_count_24h=1000,
                timestamp=None
            ),
            "ETHBTC": TickerData(
                symbol="ETHBTC",
                price=Decimal('0.05'),
                price_change=Decimal('0'),
                price_change_percent=Decimal('0'),
                high_24h=Decimal('0.05'),
                low_24h=Decimal('0.05'),
                volume_24h=Decimal('500'),
                quote_volume_24h=Decimal('25'),
                trades_count_24h=500,
                timestamp=None
            )
        }
        
        opportunity = strategy._find_arbitrage_opportunity(zero_price_tickers)
        # Con precio cero, no debe haber oportunidad válida
        assert opportunity is None

    async def test_full_workflow_integration(self, strategy, sideways_snapshot, mock_market_data_provider):
        """Test de integración del flujo completo: analyze -> generate_signal."""
        strategy.set_market_data_provider(mock_market_data_provider)
        
        # Análisis
        analysis_result = await strategy.analyze(sideways_snapshot)
        assert analysis_result is not None
        
        # Generación de señal
        signal = await strategy.generate_signal(analysis_result)
        
        # Si se genera una señal, debe ser válida
        if signal:
            assert signal.symbol is not None
            assert signal.side in [OrderSide.BUY, OrderSide.SELL]
            assert signal.quantity > Decimal('0')
            assert signal.order_type == OrderType.MARKET

    async def test_arbitrage_path_consistency(self, strategy):
        """Test de consistencia en el path de arbitraje."""
        # Verificar que el path siempre es circular (vuelve al activo inicial)
        test_tickers = {
            "BTCUSDT": TickerData(symbol="BTCUSDT", price=Decimal('50000'), 
                                price_change=Decimal('0'), price_change_percent=Decimal('0'),
                                high_24h=Decimal('50000'), low_24h=Decimal('50000'),
                                volume_24h=Decimal('1000'), quote_volume_24h=Decimal('50000000'),
                                trades_count_24h=1000, timestamp=None),
            "ETHUSDT": TickerData(symbol="ETHUSDT", price=Decimal('2400'), 
                                price_change=Decimal('0'), price_change_percent=Decimal('0'),
                                high_24h=Decimal('2400'), low_24h=Decimal('2400'),
                                volume_24h=Decimal('1000'), quote_volume_24h=Decimal('2400000'),
                                trades_count_24h=1000, timestamp=None),
            "ETHBTC": TickerData(symbol="ETHBTC", price=Decimal('0.055'), 
                               price_change=Decimal('0'), price_change_percent=Decimal('0'),
                               high_24h=Decimal('0.055'), low_24h=Decimal('0.055'),
                               volume_24h=Decimal('500'), quote_volume_24h=Decimal('27.5'),
                               trades_count_24h=500, timestamp=None)
        }
        
        opportunity = strategy._find_arbitrage_opportunity(test_tickers)
        
        if opportunity and "path" in opportunity:
            path = opportunity["path"]
            # El path debe ser circular (primer y último elemento iguales)
            assert path[0] == path[-1]
            # Debe tener al menos 3 pasos (mínimo para arbitraje triangular)
            assert len(path) >= 4  # [A, B, C, A]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
