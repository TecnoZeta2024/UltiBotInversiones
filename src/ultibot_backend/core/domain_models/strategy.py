"""
Modelos de dominio relacionados con la ejecución y gestión de estrategias.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class StrategyAnalysis(BaseModel):
    """
    Contiene el análisis detallado de una estrategia para un símbolo específico.
    """
    strategy_name: str = Field(..., description="Nombre de la estrategia que generó el análisis.")
    symbol: str = Field(..., description="Símbolo del activo analizado.")
    timeframe: str = Field(..., description="Timeframe utilizado para el análisis (e.g., '1h', '4h').")
    indicators: Dict[str, Any] = Field(default_factory=dict, description="Valores de los indicadores técnicos calculados.")
    decision: str = Field(..., description="Decisión de trading sugerida ('BUY', 'SELL', 'HOLD').")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza en la decisión (de 0.0 a 1.0).")
    reasoning: str = Field(..., description="Explicación textual de por qué se tomó la decisión.")
    suggested_stop_loss: Optional[float] = Field(None, description="Precio sugerido para el stop-loss.")
    suggested_take_profit: Optional[float] = Field(None, description="Precio sugerido para el take-profit.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales.")

class StrategyExecution(BaseModel):
    """
    Representa el resultado de la ejecución de una única estrategia.
    """
    execution_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Identificador único de la ejecución.")
    strategy_name: str = Field(..., description="Nombre de la estrategia ejecutada.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Marca de tiempo de la ejecución.")
    decision: str = Field(..., description="Decisión tomada por la estrategia (e.g., 'BUY', 'SELL', 'HOLD').")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros utilizados en la ejecución.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales sobre la ejecución.")

    class Config:
        frozen = True
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda dt: dt.isoformat()
        }
