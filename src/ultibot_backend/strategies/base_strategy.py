"""
Módulo que define la interfaz base para todas las estrategias de trading.
Todas las estrategias deben heredar de BaseStrategy y implementar sus métodos abstractos.
"""

from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from src.ultibot_backend.core.domain_models.market import MarketSnapshot
from src.ultibot_backend.core.domain_models.trading import (
    StrategyParameters, AnalysisResult, TradingSignal, OrderSide, OrderType
)
from src.ultibot_backend.core.ports import IMarketDataProvider # Se asume que se inyectará

class SignalStrength(Enum):
    """
    Representa la fuerza o confianza de una señal de trading.
    """
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"

class BaseStrategy(ABC):
    """
    Clase base abstracta para todas las estrategias de trading.
    Define la interfaz común que deben implementar todas las estrategias.
    """
    def __init__(self, name: str, parameters: StrategyParameters):
        """
        Inicializa la estrategia base.

        Args:
            name (str): El nombre de la estrategia.
            parameters (StrategyParameters): Los parámetros de configuración de la estrategia.
        """
        self.name = name
        self.parameters = parameters
        self._market_data_provider: Optional[IMarketDataProvider] = None

    def set_market_data_provider(self, provider: IMarketDataProvider) -> None:
        """
        Establece el proveedor de datos de mercado para la estrategia.
        Esto se hace por inyección de dependencia.

        Args:
            provider (IMarketDataProvider): El proveedor de datos de mercado.
        """
        self._market_data_provider = provider

    @abstractmethod
    async def setup(self) -> None:
        """
        Método asíncrono para la configuración inicial de la estrategia.
        Puede usarse para cargar datos históricos, inicializar indicadores, etc.
        """
        pass
    
    @abstractmethod
    async def analyze(self, market_snapshot: MarketSnapshot) -> AnalysisResult:
        """
        Método asíncrono para analizar el estado actual del mercado y generar un resultado de análisis.

        Args:
            market_snapshot (MarketSnapshot): Una instantánea del estado actual del mercado.

        Returns:
            AnalysisResult: El resultado del análisis, incluyendo la confianza y los indicadores.
        """
        pass
    
    @abstractmethod
    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Método asíncrono para generar una señal de trading basada en el resultado del análisis.

        Args:
            analysis (AnalysisResult): El resultado del análisis de mercado.

        Returns:
            Optional[TradingSignal]: Una señal de trading si se detecta una oportunidad, de lo contrario None.
        """
        pass

    def _create_trading_signal(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None
    ) -> TradingSignal:
        """
        Método de utilidad para crear una señal de trading.

        Args:
            symbol (str): El símbolo del activo.
            side (OrderSide): El lado de la orden (BUY/SELL).
            quantity (Decimal): La cantidad a operar.
            order_type (OrderType): El tipo de orden (por defecto MARKET).
            price (Optional[Decimal]): El precio para órdenes límite (opcional).

        Returns:
            TradingSignal: La señal de trading creada.
        """
        return TradingSignal(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            strategy_name=self.name
        )
