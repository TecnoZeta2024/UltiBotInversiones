from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional
from uuid import UUID
from functools import lru_cache

class AppSettings(BaseSettings):
    """
    Defines the application settings model. Pydantic's BaseSettings
    will automatically load values from environment variables or a specified
    .env file.
    """
    # We define the model_config here but specify the env_file during instantiation
    # in get_app_settings for dynamic loading (e.g., for tests).
    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

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
    It dynamically determines which .env file to load based on the
    TESTING environment variable.
    """
    env_file_to_use = ".env.test" if os.getenv("TESTING") == "True" else ".env"
    return AppSettings(_env_file=env_file_to_use)
