"""
Módulo que define la clase base abstracta para todas las estrategias de trading.
Establece la interfaz común que todas las estrategias deben implementar,
asegurando la compatibilidad con el motor de trading.
"""

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime # Importar datetime

from src.ultibot_backend.core.domain_models.market import MarketData
from ultibot_backend.core.domain_models.trading import (
    BaseStrategyParameters, AnalysisResult, TradingSignal, OrderSide, OrderType, SignalStrength
)

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """
    Clase base abstracta para todas las estrategias de trading.
    Define la interfaz mínima que una estrategia debe implementar.
    """
    def __init__(self, parameters: BaseStrategyParameters):
        """
        Inicializa la estrategia con sus parámetros.

        Args:
            parameters (BaseStrategyParameters): Los parámetros de configuración de la estrategia.
        """
        self._parameters = parameters
        self._strategy_id: UUID = uuid4()
        self._name: str = parameters.name

    @property
    def strategy_id(self) -> UUID:
        """Retorna el ID único de la instancia de la estrategia."""
        return self._strategy_id

    @property
    def name(self) -> str:
        """Retorna el nombre de la estrategia."""
        return self._name

    @property
    def parameters(self) -> BaseStrategyParameters:
        """Retorna los parámetros de la estrategia."""
        return self._parameters

    @abstractmethod
    async def setup(self) -> None:
        """
        Método asíncrono para la configuración inicial de la estrategia.
        Puede usarse para cargar datos históricos, inicializar indicadores, etc.
        """
        pass

    @abstractmethod
    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Método asíncrono para analizar el snapshot de mercado y generar una señal de trading.

        Args:
            market_snapshot (MarketData): El snapshot actual del mercado.

        Returns:
            AnalysisResult: El resultado del análisis, incluyendo una posible señal de trading.
        """
        pass

    def _create_trading_signal(
        self,
        symbol: str,
        side: OrderSide,
        quantity: Decimal,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[Decimal] = None,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        strength: SignalStrength = SignalStrength.MODERATE,
        reasoning: Optional[str] = None,
        timestamp: datetime = datetime.utcnow() # Añadir timestamp como argumento
    ) -> TradingSignal:
        """
        Método auxiliar para crear una señal de trading.
        """
        return TradingSignal(
            strategy_name=self.name,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strength=strength,
            reasoning=reasoning,
            timestamp=timestamp # Usar el timestamp pasado como argumento
        )
