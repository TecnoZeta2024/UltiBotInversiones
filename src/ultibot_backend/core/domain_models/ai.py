from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class AIResponse(BaseModel):
    """
    Modelo de dominio para encapsular la respuesta de un servicio de IA.
    """
    content: str = Field(..., description="El contenido principal de la respuesta de la IA.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales de la respuesta, como el uso de tokens o información de la fuente.")
    error: Optional[str] = Field(None, description="Si ocurrió un error durante la generación de la respuesta.")
