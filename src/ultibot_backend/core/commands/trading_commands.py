"""
Módulo que define los comandos relacionados con operaciones de trading.
Estos comandos son modelos Pydantic puros y representan intenciones de mutación
del estado del sistema.
"""

from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from src.ultibot_backend.core.domain_models.trading import OrderSide, OrderType

class PlaceOrderCommand(BaseModel):
    """Comando para colocar una nueva orden de trading."""
    command_id: UUID = Field(default_factory=uuid4)
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Optional[Decimal] = None  # Para órdenes límite
    order_type: OrderType
    strategy_id: Optional[str] = None
    user_id: Optional[UUID] = None # Para identificar al usuario que emite el comando

    model_config = ConfigDict(frozen=True)

class CancelOrderCommand(BaseModel):
    """Comando para cancelar una orden de trading existente."""
    command_id: UUID = Field(default_factory=uuid4)
    order_id: str # ID de la orden en el exchange
    symbol: str # Símbolo del par de la orden
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)

class ActivateStrategyCommand(BaseModel):
    """Comando para activar una estrategia de trading."""
    command_id: UUID = Field(default_factory=uuid4)
    strategy_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    mode: str  # "PAPER" | "REAL"
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)

class DeactivateStrategyCommand(BaseModel):
    """Comando para desactivar una estrategia de trading."""
    command_id: UUID = Field(default_factory=uuid4)
    strategy_name: str
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)

class UpdateConfigCommand(BaseModel):
    """Comando para actualizar una configuración del sistema."""
    command_id: UUID = Field(default_factory=uuid4)
    config_key: str
    config_value: Any
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)
