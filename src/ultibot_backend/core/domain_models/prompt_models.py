"""
Modelos de dominio para la gestión de prompts.
"""

import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class PromptTemplate(BaseModel):
    """
    Representa una plantilla de prompt reutilizable.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    template_text: str
    version: int = 1
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True

class PromptVersion(BaseModel):
    """
    Representa una versión específica de una plantilla de prompt.
    """
    version: int
    template_text: str
    created_at: datetime.datetime
    author: str

    class Config:
        frozen = True

class PromptRenderResult(BaseModel):
    """
    Representa el resultado de renderizar un template de prompt.
    """
    rendered_prompt: str
    variables: Dict[str, Any]
    errors: Optional[Dict[str, str]] = None

    class Config:
        frozen = True

class PromptCacheEntry(BaseModel):
    """
    Representa una entrada en la caché de prompts renderizados.
    """
    rendered_prompt: str
    timestamp: datetime.datetime

    class Config:
        frozen = True
