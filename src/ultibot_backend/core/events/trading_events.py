"""
Módulos de eventos de dominio relacionados con operaciones de trading.

Estos eventos representan cambios significativos en el estado del sistema
relacionados con la ejecución de órdenes, actualizaciones de precios y
otras actividades de trading.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal, Optional

class TradingEvent(BaseModel):
    """
    Clase base abstracta para todos los eventos de trading.

    Atributos:
        timestamp (datetime): Marca de tiempo cuando ocurrió el evento.
        event_type (str): Tipo de evento, se establece automáticamente.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(default_factory=lambda: "TradingEvent")

    class Config:
        frozen = True
        extra = "forbid"

class OrderPlacedEvent(TradingEvent):
    """
    Evento que se dispara cuando una nueva orden ha sido colocada.

    Atributos:
        order_id (str): Identificador único de la orden.
        symbol (str): Símbolo del par de trading (ej., "BTCUSDT").
        order_type (Literal["LIMIT", "MARKET"]): Tipo de orden.
        side (Literal["BUY", "SELL"]): Lado de la orden.
        price (Optional[Decimal]): Precio de la orden (para órdenes LIMIT).
        quantity (Decimal): Cantidad de la orden.
        client_order_id (Optional[str]): ID de orden del cliente, si aplica.
    """
    order_id: str
    symbol: str
    order_type: Literal["LIMIT", "MARKET"]
    side: Literal["BUY", "SELL"]
    price: Optional[Decimal]
    quantity: Decimal
    client_order_id: Optional[str] = None
    event_type: Literal["OrderPlacedEvent"] = "OrderPlacedEvent"

class OrderFilledEvent(TradingEvent):
    """
    Evento que se dispara cuando una orden ha sido total o parcialmente ejecutada.

    Atributos:
        order_id (str): Identificador único de la orden.
        symbol (str): Símbolo del par de trading.
        filled_quantity (Decimal): Cantidad ejecutada en esta transacción.
        filled_price (Decimal): Precio promedio de ejecución de esta transacción.
        commission (Optional[Decimal]): Comisión pagada por la transacción.
        commission_asset (Optional[str]): Activo en el que se pagó la comisión.
        is_partial_fill (bool): Indica si la orden fue parcialmente ejecutada.
    """
    order_id: str
    symbol: str
    filled_quantity: Decimal
    filled_price: Decimal
    commission: Optional[Decimal] = None
    commission_asset: Optional[str] = None
    is_partial_fill: bool
    event_type: Literal["OrderFilledEvent"] = "OrderFilledEvent"

class OrderCanceledEvent(TradingEvent):
    """
    Evento que se dispara cuando una orden ha sido cancelada.

    Atributos:
        order_id (str): Identificador único de la orden.
        symbol (str): Símbolo del par de trading.
        reason (Optional[str]): Razón de la cancelación.
    """
    order_id: str
    symbol: str
    reason: Optional[str] = None
    event_type: Literal["OrderCanceledEvent"] = "OrderCanceledEvent"

class PriceUpdateEvent(TradingEvent):
    """
    Evento que se dispara cuando hay una actualización de precio para un símbolo.

    Atributos:
        symbol (str): Símbolo del par de trading.
        current_price (Decimal): Precio actual del activo.
    """
    symbol: str
    current_price: Decimal
    event_type: Literal["PriceUpdateEvent"] = "PriceUpdateEvent"

class MarketDataReceivedEvent(TradingEvent):
    """
    Evento que se dispara cuando se recibe un nuevo conjunto de datos de mercado.

    Atributos:
        symbol (str): Símbolo del par de trading.
        data_type (str): Tipo de datos de mercado (ej., "kline", "ticker").
        data (dict): Los datos de mercado recibidos.
    """
    symbol: str
    data_type: str
    data: dict
    event_type: Literal["MarketDataReceivedEvent"] = "MarketDataReceivedEvent"
