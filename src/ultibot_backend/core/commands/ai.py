"""
AI Commands Module.

This module defines the command models for AI operations, following the
CQRS pattern. These commands represent an intent to trigger complex
AI-driven analysis or actions.
"""

from typing import Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class TriggerAIAnalysisCommand(BaseModel):
    """Command to trigger an AI analysis for a given opportunity."""
    opportunity_id: str
    market_data: Dict[str, Any]

    class Config:
        frozen = True
