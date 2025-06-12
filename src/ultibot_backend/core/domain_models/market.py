"""
Módulo que define los modelos de dominio puros relacionados con el mercado.
Estos modelos son agnósticos a la infraestructura y no deben importar frameworks externos.
Utilizan Pydantic para la validación y serialización de datos.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict

from ultibot_backend.core.domain_models.trading import TickerData, KlineData

class MarketSnapshot(BaseModel):
    """
    Representa una instantánea del estado actual del mercado para un símbolo dado.
    Contiene los datos más recientes del ticker y las velas.
    """
    symbol: str
    ticker: TickerData
    klines: List[KlineData]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)
