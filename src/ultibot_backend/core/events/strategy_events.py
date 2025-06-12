"""
Módulos de eventos de dominio relacionados con la ejecución y gestión de estrategias.

Estos eventos representan el ciclo de vida de una estrategia, desde su activación
hasta la detección de señales y la finalización.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal, Optional

class StrategyEvent(BaseModel):
    """
    Clase base abstracta para todos los eventos de estrategia.

    Atributos:
        timestamp (datetime): Marca de tiempo cuando ocurrió el evento.
        strategy_id (str): Identificador único de la estrategia.
        event_type (str): Tipo de evento, se establece automáticamente.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    strategy_id: str
    event_type: str = Field(default_factory=lambda: "StrategyEvent")

    class Config:
        frozen = True
        extra = "forbid"

class StrategyActivatedEvent(StrategyEvent):
    """
    Evento que se dispara cuando una estrategia es activada.

    Atributos:
        strategy_name (str): Nombre de la estrategia.
        symbol (str): Símbolo en el que opera la estrategia.
        initial_parameters (dict): Parámetros iniciales con los que se activó la estrategia.
    """
    strategy_name: str
    symbol: str
    initial_parameters: dict
    event_type: Literal["StrategyActivatedEvent"] = "StrategyActivatedEvent"

class StrategyDeactivatedEvent(StrategyEvent):
    """
    Evento que se dispara cuando una estrategia es desactivada.

    Atributos:
        reason (Optional[str]): Razón de la desactivación.
    """
    reason: Optional[str] = None
    event_type: Literal["StrategyDeactivatedEvent"] = "StrategyDeactivatedEvent"

class SignalDetectedEvent(StrategyEvent):
    """
    Evento que se dispara cuando una estrategia detecta una señal de trading.

    Atributos:
        signal_type (Literal["BUY", "SELL", "HOLD"]): Tipo de señal detectada.
        confidence (Optional[Decimal]): Nivel de confianza de la señal (0-1).
        details (Optional[dict]): Detalles adicionales de la señal.
    """
    signal_type: Literal["BUY", "SELL", "HOLD"]
    confidence: Optional[Decimal] = None
    details: Optional[dict] = None
    event_type: Literal["SignalDetectedEvent"] = "SignalDetectedEvent"

class StrategyErrorEvent(StrategyEvent):
    """
    Evento que se dispara cuando ocurre un error dentro de una estrategia.

    Atributos:
        error_message (str): Mensaje de error.
        error_code (Optional[str]): Código de error, si aplica.
        traceback (Optional[str]): Stack trace del error.
    """
    error_message: str
    error_code: Optional[str] = None
    traceback: Optional[str] = None
    event_type: Literal["StrategyErrorEvent"] = "StrategyErrorEvent"

class StrategyPerformanceUpdateEvent(StrategyEvent):
    """
    Evento que se dispara para reportar una actualización del rendimiento de la estrategia.

    Atributos:
        current_pnl (Decimal): Ganancia o pérdida actual de la estrategia.
        open_positions (int): Número de posiciones abiertas.
        metrics (Optional[dict]): Métricas de rendimiento adicionales.
    """
    current_pnl: Decimal
    open_positions: int
    metrics: Optional[dict] = None
    event_type: Literal["StrategyPerformanceUpdateEvent"] = "StrategyPerformanceUpdateEvent"
