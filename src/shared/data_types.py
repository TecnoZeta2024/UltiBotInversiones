"""
Este archivo contendrá definiciones de tipos de datos compartidos,
por ejemplo, modelos Pydantic comunes si la UI los consume directamente
o si hay tipos de datos que tanto el backend como la UI necesitan conocer.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
from pydantic import BaseModel, Field

class ServiceName(str, Enum):
    BINANCE_SPOT = "BINANCE_SPOT"
    BINANCE_FUTURES = "BINANCE_FUTURES"
    TELEGRAM_BOT = "TELEGRAM_BOT"
    GEMINI_API = "GEMINI_API"
    MOBULA_API = "MOBULA_API"
    N8N_WEBHOOK = "N8N_WEBHOOK"
    SUPABASE_CLIENT = "SUPABASE_CLIENT"
    MCP_GENERIC = "MCP_GENERIC"
    MCP_DOGGYBEE_CCXT = "MCP_DOGGYBEE_CCXT"
    MCP_METATRADER_BRIDGE = "MCP_METATRADER_BRIDGE"
    MCP_WEB3_RESEARCH = "MCP_WEB3_RESEARCH"
    CUSTOM_SERVICE = "CUSTOM_SERVICE"

class APICredential(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    service_name: ServiceName
    credential_label: str

    encrypted_api_key: str
    encrypted_api_secret: Optional[str] = None
    encrypted_other_details: Optional[str] = None # JSON encriptado para detalles adicionales

    status: str = "verification_pending" # 'active' | 'inactive' | 'revoked' | 'verification_pending' | 'verification_failed' | 'expired'
    last_verified_at: Optional[datetime] = None
    
    permissions: Optional[List[str]] = None
    permissions_checked_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None
    rotation_reminder_policy_days: Optional[int] = None

    usage_count: int = 0
    last_used_at: Optional[datetime] = None

    purpose_description: Optional[str] = None
    tags: Optional[List[str]] = None

    notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat() + "Z",
            UUID: lambda uuid: str(uuid),
        }
        use_enum_values = True # Para que los enums se serialicen como sus valores de string

def add_numbers(a: int, b: int) -> int:
    """
    Suma dos números enteros y devuelve el resultado.

    Args:
        a: El primer número entero.
        b: El segundo número entero.

    Returns:
        La suma de los dos números.
    """
    return a + b
