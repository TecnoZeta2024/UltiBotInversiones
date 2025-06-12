"""
Módulos de eventos de dominio relacionados con la gestión de portafolios.

Estos eventos representan cambios significativos en el estado del portafolio
del usuario, como actualizaciones de balance, adiciones o eliminaciones de activos.
"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal, Optional

class PortfolioEvent(BaseModel):
    """
    Clase base abstracta para todos los eventos de portafolio.

    Atributos:
        timestamp (datetime): Marca de tiempo cuando ocurrió el evento.
        event_type (str): Tipo de evento, se establece automáticamente.
    """
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(default_factory=lambda: "PortfolioEvent")

    class Config:
        frozen = True
        extra = "forbid"

class BalanceUpdatedEvent(PortfolioEvent):
    """
    Evento que se dispara cuando el balance de un activo en el portafolio se actualiza.

    Atributos:
        asset (str): Símbolo del activo (ej., "USDT", "BTC").
        available_balance (Decimal): Balance disponible del activo.
        locked_balance (Decimal): Balance bloqueado del activo (en órdenes, etc.).
    """
    asset: str
    available_balance: Decimal
    locked_balance: Decimal
    event_type: Literal["BalanceUpdatedEvent"] = "BalanceUpdatedEvent"

class AssetAddedToPortfolioEvent(PortfolioEvent):
    """
    Evento que se dispara cuando un nuevo activo es añadido al portafolio.

    Atributos:
        asset (str): Símbolo del activo.
        initial_balance (Decimal): Balance inicial del activo.
    """
    asset: str
    initial_balance: Decimal
    event_type: Literal["AssetAddedToPortfolioEvent"] = "AssetAddedToPortfolioEvent"

class AssetRemovedFromPortfolioEvent(PortfolioEvent):
    """
    Evento que se dispara cuando un activo es completamente removido del portafolio.

    Atributos:
        asset (str): Símbolo del activo.
    """
    asset: str
    event_type: Literal["AssetRemovedFromPortfolioEvent"] = "AssetRemovedFromPortfolioEvent"

class PortfolioSnapshotEvent(PortfolioEvent):
    """
    Evento que representa un snapshot completo del portafolio en un momento dado.

    Atributos:
        total_value_usd (Decimal): Valor total del portafolio en USD.
        assets (dict[str, Decimal]): Diccionario de activos y sus balances.
    """
    total_value_usd: Decimal
    assets: dict[str, Decimal]
    event_type: Literal["PortfolioSnapshotEvent"] = "PortfolioSnapshotEvent"
