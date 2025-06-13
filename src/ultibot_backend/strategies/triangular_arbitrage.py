"""
Módulo que implementa la estrategia de trading Triangular_Arbitrage.
Esta estrategia busca explotar ineficiencias de precios entre tres pares de trading
para obtener ganancias sin riesgo.
"""

from decimal import Decimal, getcontext
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import Field, ConfigDict

from src.ultibot_backend.core.domain_models.market import MarketData, TickerData
from ultibot_backend.core.domain_models.trading import (
    BaseStrategyParameters, AnalysisResult, TradingSignal, OrderSide, OrderType
)
from ultibot_backend.strategies.base_strategy import BaseStrategy
from ultibot_backend.core.ports import IMarketDataProvider

# Configurar la precisión decimal global
getcontext().prec = 10

class TriangularArbitrageParameters(BaseStrategyParameters):
    """
    Parámetros de configuración para la estrategia Triangular_Arbitrage.
    """
    min_profit_percent: Decimal = Field(default=Decimal('0.001'), description="Porcentaje mínimo de ganancia para ejecutar el arbitraje (ej. 0.001 para 0.1%).")
    trade_quantity_base: Decimal = Field(default=Decimal('0.001'), description="Cantidad inicial de la moneda base para el arbitraje.")
    max_slippage_percent: Decimal = Field(default=Decimal('0.0005'), description="Porcentaje máximo de slippage permitido en cada trade.")

    model_config = ConfigDict(frozen=True)

class TriangularArbitrage(BaseStrategy):
    """
    Estrategia de trading que busca oportunidades de arbitraje triangular.
    """
    def __init__(self, parameters: TriangularArbitrageParameters):
        """
        Inicializa la estrategia TriangularArbitrage.

        Args:
            parameters (TriangularArbitrageParameters): Parámetros específicos de la estrategia.
        """
        super().__init__(parameters)
        self.params: TriangularArbitrageParameters = parameters
        self._market_data_provider: Optional[IMarketDataProvider] = None # Se inyectará desde el StrategyLoader

    def set_market_data_provider(self, provider: IMarketDataProvider) -> None:
        """
        Establece el proveedor de datos de mercado para la estrategia.
        Esto se hace por inyección de dependencia.
        """
        self._market_data_provider = provider

    async def setup(self) -> None:
        """
        Configuración inicial de la estrategia.
        """
        if self._market_data_provider is None:
            raise ValueError("IMarketDataProvider no ha sido inyectado en TriangularArbitrage.")
        # Podría pre-calcular pares de arbitraje aquí si la lista de símbolos es estática
        pass

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza el estado actual del mercado para detectar oportunidades de arbitraje triangular.
        Nota: Esta estrategia requiere acceso a múltiples tickers, no solo el del snapshot.
        El market_snapshot se usa para el símbolo base, pero se necesitan otros tickers.

        Args:
            market_snapshot (MarketData): Una instantánea del estado actual del mercado (usado como punto de partida).

        Returns:
            AnalysisResult: El resultado del análisis, incluyendo la confianza y los detalles del arbitraje.
        """
        if self._market_data_provider is None:
            return AnalysisResult(
                confidence=Decimal('0.0'),
                indicators={"error": "Market data provider not set."}
            )

        # Para simplificar, asumimos un conjunto fijo de símbolos para buscar triángulos.
        # En un sistema real, esto sería dinámico o pre-calculado.
        # Ejemplo: BTC, ETH, USDT
        # Pares: BTCUSDT, ETHUSDT, BTCTH
        
        # Obtener precios de los tickers relevantes
        # Esto es un ejemplo simplificado. En un entorno real, se obtendrían todos los tickers necesarios.
        try:
            btc_usdt_ticker = await self._market_data_provider.get_ticker("BTCUSDT")
            eth_usdt_ticker = await self._market_data_provider.get_ticker("ETHUSDT")
            btc_eth_ticker = await self._market_data_provider.get_ticker("ETHBTC") # ETH/BTC
        except Exception as e:
            return AnalysisResult(
                confidence=Decimal('0.0'),
                indicators={"error": f"Failed to get tickers: {e}"}
            )

        tickers = {
            "BTCUSDT": btc_usdt_ticker,
            "ETHUSDT": eth_usdt_ticker,
            "ETHBTC": btc_eth_ticker
        }

        opportunity_details = self._find_arbitrage_opportunity(tickers)

        if opportunity_details:
            confidence = Decimal('0.9') # Alta confianza si se encuentra una oportunidad
        else:
            confidence = Decimal('0.0')

        return AnalysisResult(
            confidence=confidence,
            indicators={"opportunity_details": opportunity_details}
        )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera una señal de trading si se detecta una oportunidad de arbitraje rentable.

        Args:
            analysis (AnalysisResult): El resultado del análisis de mercado.

        Returns:
            Optional[TradingSignal]: Una señal de trading si se detecta una oportunidad, de lo contrario None.
        """
        opportunity_details = analysis.indicators.get("opportunity_details")
        if not opportunity_details or analysis.confidence < Decimal('0.8'): # Requiere alta confianza
            return None

        # Para arbitraje triangular, la "señal" es la secuencia de trades.
        # No se genera una única TradingSignal, sino una serie de ellas.
        # Aquí, por simplicidad, solo se devuelve la primera parte del trade.
        # En un sistema real, esto se manejaría como un "ArbitrageCommand" que contiene múltiples sub-órdenes.
        
        # Ejemplo: BTC -> USDT -> ETH -> BTC
        # Trade 1: Sell BTC for USDT
        # Trade 2: Buy ETH with USDT
        # Trade 3: Sell ETH for BTC

        # Para este ejemplo, solo crearemos una señal de "inicio de arbitraje"
        # La ejecución real de los 3 trades sería responsabilidad de un handler de comandos.
        
        # Asumimos que la oportunidad_details contiene la secuencia de trades
        # Ejemplo: opportunity_details = { "path": ["BTC", "USDT", "ETH", "BTC"], "profit": Decimal('0.002'), "trades": [...] }
        
        # Aquí, solo se genera una señal genérica para indicar que se ha encontrado una oportunidad.
        # La lógica de ejecución de arbitraje real es más compleja y va más allá de una sola TradingSignal.
        
        # Si la oportunidad es rentable, se podría generar una señal para iniciar el proceso.
        # La cantidad a operar sería la cantidad base definida en los parámetros.
        
        # Para fines de demostración, creamos una señal de compra en el primer par del ciclo.
        # Esto es una simplificación.
        
        # Ejemplo de un trade inicial para el ciclo:
        # Si el camino es BTC -> USDT -> ETH -> BTC
        # El primer trade sería vender BTC por USDT
        
        # Esto es un placeholder. La lógica real de arbitraje es compleja.
        symbol_to_trade = opportunity_details.get("path", [])[0] + opportunity_details.get("path", [])[1]
        side = OrderSide.SELL # Vender la primera moneda para obtener la segunda
        quantity = self.params.trade_quantity_base # Cantidad inicial
        
        # Esto es una simplificación. En un arbitraje real, se ejecutarían múltiples órdenes.
        # La señal aquí es más bien una "intención de arbitraje".
        signal = self._create_trading_signal(
            symbol=symbol_to_trade,
            side=side,
            quantity=quantity,
            order_type=OrderType.MARKET, # Las órdenes de arbitraje suelen ser de mercado para velocidad
            price=None # Precio de mercado
        )
        
        return signal

    def _find_arbitrage_opportunity(self, tickers: Dict[str, TickerData]) -> Optional[Dict[str, Any]]:
        """
        Busca una oportunidad de arbitraje triangular entre los tickers proporcionados.
        Esta es una implementación simplificada para BTC, ETH, USDT.
        """
        btc_usdt_bid = tickers.get("BTCUSDT").price if tickers.get("BTCUSDT") else Decimal('0')
        eth_usdt_bid = tickers.get("ETHUSDT").price if tickers.get("ETHUSDT") else Decimal('0')
        eth_btc_bid = tickers.get("ETHBTC").price if tickers.get("ETHBTC") else Decimal('0') # ETH/BTC

        # Asumimos que los tickers son precios de "bid" (lo que puedes vender)
        # Para comprar, usaríamos "ask" prices, pero para simplificar, usamos el mismo.
        # En un sistema real, se usarían bid/ask apropiados.

        # Ruta 1: BTC -> USDT -> ETH -> BTC
        # 1. Vender BTC por USDT: cantidad_usdt = cantidad_btc * btc_usdt_bid
        # 2. Comprar ETH con USDT: cantidad_eth = cantidad_usdt / eth_usdt_bid
        # 3. Vender ETH por BTC: cantidad_btc_final = cantidad_eth * eth_btc_bid
        
        initial_btc = self.params.trade_quantity_base
        if btc_usdt_bid > 0 and eth_usdt_bid > 0 and eth_btc_bid > 0:
            try:
                usdt_from_btc = initial_btc * btc_usdt_bid
                eth_from_usdt = usdt_from_btc / eth_usdt_bid
                final_btc = eth_from_usdt * eth_btc_bid
                
                profit_btc = final_btc - initial_btc
                profit_percent = profit_btc / initial_btc if initial_btc > 0 else Decimal('0')

                if profit_percent > self.params.min_profit_percent:
                    return {
                        "path": ["BTC", "USDT", "ETH", "BTC"],
                        "profit_percent": profit_percent,
                        "initial_amount": initial_btc,
                        "final_amount": final_btc,
                        "trade_prices": {
                            "BTCUSDT_sell": btc_usdt_bid,
                            "ETHUSDT_buy": eth_usdt_bid,
                            "ETHBTC_sell": eth_btc_bid
                        }
                    }
            except Exception:
                pass # Ignorar errores de división por cero o datos inválidos

        # Ruta 2: BTC -> ETH -> USDT -> BTC (inverso)
        # 1. Comprar ETH con BTC: cantidad_eth = cantidad_btc / eth_btc_ask (usamos bid para simplificar)
        # 2. Vender ETH por USDT: cantidad_usdt = cantidad_eth * eth_usdt_bid
        # 3. Comprar BTC con USDT: cantidad_btc_final = cantidad_usdt / btc_usdt_ask (usamos bid para simplificar)
        
        # Para simplificar, solo se implementa una ruta.
        # Una implementación completa consideraría todas las permutaciones y bid/ask prices.

        return None

    def _calculate_confidence(self, indicators: Dict[str, Any]) -> Decimal:
        """
        Calcula un nivel de confianza basado en la existencia y rentabilidad de la oportunidad.
        """
        opportunity_details = indicators.get("opportunity_details")
        if opportunity_details:
            profit_percent = opportunity_details.get("profit_percent", Decimal('0'))
            if profit_percent > self.params.min_profit_percent:
                # La confianza es proporcional a la rentabilidad por encima del mínimo
                confidence = min(Decimal('1.0'), (profit_percent / self.params.min_profit_percent) * Decimal('0.5') + Decimal('0.5'))
                return confidence
        return Decimal('0.0')
