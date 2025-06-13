"""
Módulo que define los modelos de dominio puros relacionados con el mercado.
Estos modelos son agnósticos a la infraestructura y no deben importar frameworks externos.
Utilizan Pydantic para la validación y serialización de datos.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict

from .trading import TickerData, KlineData

class MarketData(BaseModel):
    """
    Representa los datos de mercado para un símbolo dado, incluyendo ticker y velas.
    """
    symbol: str
    ticker: TickerData
    klines: List[KlineData]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)
