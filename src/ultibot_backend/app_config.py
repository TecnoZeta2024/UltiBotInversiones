from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv # Importar load_dotenv
import os # Importar os
from typing import Optional # Importar Optional
from uuid import UUID # Add this import

# Cargar variables de entorno desde .env al inicio, permitiendo la sobreescritura
load_dotenv(override=True)

class AppSettings(BaseSettings):
    # No es necesario especificar env_file aquí si ya se cargó con load_dotenv()
    # Pero lo mantenemos para compatibilidad o si se desea un comportamiento específico de pydantic-settings
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    DATABASE_URL: str

    # Credential Encryption
    CREDENTIAL_ENCRYPTION_KEY: str

    # Exchange API Keys
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    MOBULA_API_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    # Fixed User ID for UI (can be overridden by .env)
    FIXED_USER_ID: UUID = UUID("00000000-0000-0000-0000-000000000001")
    # Fixed Credential ID for Binance (can be overridden by .env)
    FIXED_BINANCE_CREDENTIAL_ID: UUID = UUID("00000000-0000-0000-0000-000000000002")

    # Google Gemini API Key (optional)
    GEMINI_API_KEY: Optional[str] = None

    # Uvicorn server settings (can be overridden by .env)
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    DEBUG_MODE: bool = False # For Uvicorn reload

settings = AppSettings()
