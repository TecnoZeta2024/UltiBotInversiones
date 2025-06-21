from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional
from uuid import UUID
from functools import lru_cache

# Determine which .env file to use based on the TESTING environment variable.
# Pydantic's BaseSettings will handle the loading.
env_file = ".env.test" if os.getenv("TESTING") == "True" else ".env"

class AppSettings(BaseSettings):
    # Let Pydantic handle loading the correct .env file.
    # It will automatically override with environment variables.
    model_config = SettingsConfigDict(env_file=env_file, env_file_encoding="utf-8", extra="ignore")

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

@lru_cache()
def get_app_settings() -> AppSettings:
    """
    Returns a cached instance of the application settings.
    Using lru_cache ensures the settings are loaded only once.
    """
    return AppSettings()  # type: ignore
