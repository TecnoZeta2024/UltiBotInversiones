"""
Módulo que define las consultas relacionadas con el portfolio y datos de mercado.
Estas consultas son modelos Pydantic puros y representan intenciones de lectura
del estado del sistema.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

class GetPortfolioQuery(BaseModel):
    """Consulta para obtener el portfolio de un usuario."""
    query_id: UUID = Field(default_factory=uuid4)
    user_id: UUID

    model_config = ConfigDict(frozen=True)

class GetTradeHistoryQuery(BaseModel):
    """Consulta para obtener el historial de trades de un usuario."""
    query_id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    symbol: Optional[str] = None # Opcional: filtrar por símbolo

    model_config = ConfigDict(frozen=True)

class GetStrategyPerformanceQuery(BaseModel):
    """Consulta para obtener el rendimiento de una estrategia."""
    query_id: UUID = Field(default_factory=uuid4)
    strategy_name: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)

class GetMarketDataQuery(BaseModel):
    """Consulta para obtener datos de mercado (ticker o klines)."""
    query_id: UUID = Field(default_factory=uuid4)
    symbol: str
    data_type: str # "ticker" | "klines"
    interval: Optional[str] = None # Requerido para klines

    model_config = ConfigDict(frozen=True)

class GetConfigQuery(BaseModel):
    """Consulta para obtener una configuración específica del sistema."""
    query_id: UUID = Field(default_factory=uuid4)
    config_key: str
    user_id: Optional[UUID] = None

    model_config = ConfigDict(frozen=True)
