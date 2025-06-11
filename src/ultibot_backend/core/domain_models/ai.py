from pydantic import BaseModel, Field, validator
from typing import Any, Dict, Optional, Literal
from enum import Enum

class TradingRecommendation(str, Enum):
    """Enum para las recomendaciones de trading."""
    COMPRAR = "COMPRAR"
    VENDER = "VENDER"
    ESPERAR = "ESPERAR"

class AIResponse(BaseModel):
    """
    Modelo de dominio para encapsular la respuesta de un servicio de IA.
    """
    content: str = Field(..., description="El contenido principal de la respuesta de la IA.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales de la respuesta, como el uso de tokens o información de la fuente.")
    error: Optional[str] = Field(None, description="Si ocurrió un error durante la generación de la respuesta.")

class TradingAIResponse(BaseModel):
    """
    Modelo de dominio específico para respuestas de IA relacionadas con trading.
    Incluye campos estructurados para análisis de oportunidades de inversión.
    """
    recommendation: TradingRecommendation = Field(
        ..., 
        description="Recomendación clara: COMPRAR, VENDER o ESPERAR"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Nivel de confianza en la recomendación (0.0 a 1.0)"
    )
    reasoning: str = Field(
        ..., 
        description="Razonamiento detallado detrás de la recomendación"
    )
    warnings: Optional[str] = Field(
        None, 
        description="Advertencias o riesgos identificados"
    )
    entry_price: Optional[float] = Field(
        None, 
        description="Precio de entrada sugerido (si aplica)"
    )
    stop_loss: Optional[float] = Field(
        None, 
        description="Precio de stop loss sugerido (si aplica)"
    )
    take_profit: Optional[float] = Field(
        None, 
        description="Precio de take profit sugerido (si aplica)"
    )
    risk_level: Optional[Literal["BAJO", "MEDIO", "ALTO"]] = Field(
        None, 
        description="Nivel de riesgo estimado de la operación"
    )
    timeframe: Optional[str] = Field(
        None, 
        description="Marco temporal sugerido para la operación"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Metadatos adicionales del análisis"
    )
    analysis_id: Optional[str] = Field(
        None, 
        description="ID único del análisis para trazabilidad"
    )

    @validator('confidence')
    def validate_confidence(cls, v):
        """Valida que la confianza esté en el rango correcto."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('La confianza debe estar entre 0.0 y 1.0')
        return v

    @validator('reasoning')
    def validate_reasoning(cls, v):
        """Valida que el razonamiento no esté vacío."""
        if not v or v.strip() == "":
            raise ValueError('El razonamiento no puede estar vacío')
        return v.strip()

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Determina si la recomendación tiene alta confianza.
        
        Args:
            threshold: Umbral de confianza (por defecto 0.8)
            
        Returns:
            bool: True si la confianza supera el umbral
        """
        return self.confidence >= threshold

    def is_suitable_for_real_trading(self, min_confidence: float = 0.95) -> bool:
        """
        Determina si la recomendación es adecuada para trading real.
        
        Args:
            min_confidence: Confianza mínima para trading real (por defecto 0.95)
            
        Returns:
            bool: True si es adecuada para trading real
        """
        return (
            self.confidence >= min_confidence and 
            self.recommendation in [TradingRecommendation.COMPRAR, TradingRecommendation.VENDER]
        )

    def get_summary(self) -> str:
        """
        Genera un resumen conciso del análisis.
        
        Returns:
            str: Resumen del análisis
        """
        summary = f"{self.recommendation.value} (Confianza: {self.confidence:.1%})"
        if self.risk_level:
            summary += f" - Riesgo: {self.risk_level}"
        return summary

    def to_telegram_message(self) -> str:
        """
        Convierte la respuesta a un mensaje formateado para Telegram.
        
        Returns:
            str: Mensaje formateado para Telegram
        """
        message = f"🤖 *Análisis de IA - Trading*\n\n"
        message += f"📊 *Recomendación:* {self.recommendation.value}\n"
        message += f"🎯 *Confianza:* {self.confidence:.1%}\n\n"
        message += f"💡 *Razonamiento:*\n{self.reasoning}\n"
        
        if self.warnings:
            message += f"\n⚠️ *Advertencias:*\n{self.warnings}\n"
        
        if self.entry_price:
            message += f"\n💰 *Precio entrada:* ${self.entry_price:,.2f}"
        if self.stop_loss:
            message += f"\n🛑 *Stop Loss:* ${self.stop_loss:,.2f}"
        if self.take_profit:
            message += f"\n🎯 *Take Profit:* ${self.take_profit:,.2f}"
        
        if self.risk_level:
            message += f"\n📈 *Nivel de Riesgo:* {self.risk_level}"
        
        return message
