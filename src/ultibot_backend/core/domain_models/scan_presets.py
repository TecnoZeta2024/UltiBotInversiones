"""
Módulo que define los modelos de dominio puros relacionados con los presets de escaneo de mercado.
Estos modelos son agnósticos a la infraestructura y no deben importar frameworks externos.
Utilizan Pydantic para la validación y serialización de datos.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

from ultibot_backend.core.domain_models.trading import TickerData

class ScanCriteria(BaseModel):
    """Define los criterios para un escaneo de mercado."""
    min: Optional[Decimal] = None
    max: Optional[Decimal] = None
    trend: Optional[str] = None # "increasing", "decreasing", "stable"
    value: Optional[Any] = None # Para criterios exactos

    model_config = ConfigDict(frozen=True)

class ScanPreset(BaseModel):
    """Representa un preset de escaneo de mercado configurable."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    criteria: Dict[str, ScanCriteria]
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)

    def matches(self, ticker: TickerData) -> bool:
        """
        Verifica si un ticker dado cumple con los criterios de este preset.
        Nota: La lógica de evaluación real se haría en una capa de servicio.
        Aquí solo se define la interfaz.
        """
        # Simplificación: la lógica real sería más compleja y dinámica
        for criterion_name, criterion_value in self.criteria.items():
            if criterion_name == "price_change_24h":
                if criterion_value.min is not None and ticker.price_change_24h < criterion_value.min:
                    return False
                if criterion_value.max is not None and ticker.price_change_24h > criterion_value.max:
                    return False
            # Se añadirían más criterios aquí (ej. volume_24h, atr_percentile, etc.)
        return True

    def calculate_score(self, ticker: TickerData) -> Decimal:
        """
        Calcula un score para un ticker basado en los criterios del preset.
        """
        # Simplificación: la lógica real sería más compleja
        score = Decimal('0.0')
        if self.matches(ticker):
            score = Decimal('1.0') # Si cumple, al menos 1.0
            # Añadir lógica para ponderar criterios y calcular un score más granular
        return score

class ScanResult(BaseModel):
    """Representa el resultado de un escaneo de mercado para un símbolo."""
    result_id: UUID = Field(default_factory=uuid4)
    preset_name: str
    symbol: str
    score: Decimal
    matched_criteria: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(frozen=True)
